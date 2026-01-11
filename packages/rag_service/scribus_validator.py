"""
Scribus XML Validator - Digital Twin

Nutzt RAG-Speicher, um zu wissen, wie Scribus auf bestimmte XML-Konstrukte reagiert.
Fungiert als Schutzschild, das nur "sauberen" Code an Scribus durchlässt.
"""

from typing import Dict, List, Optional, Tuple
from .database import RAGDatabase
from .embeddings import EmbeddingModels
import xml.etree.ElementTree as ET
import json


class ScribusValidator:
    """
    Digital Twin für Scribus XML-Validierung.
    
    Nutzt RAG-Speicher, um XML-Patterns und deren Verhalten zu speichern
    und zu validieren, bevor Code an Scribus gesendet wird.
    """
    
    def __init__(self, db: RAGDatabase, embeddings: EmbeddingModels):
        """
        Initialisiert Scribus Validator.
        
        Args:
            db: RAGDatabase Instanz
            embeddings: EmbeddingModels Instanz
        """
        self.db = db
        self.embeddings = embeddings
        
        # Erstelle Collection für Scribus-XML-Patterns falls nicht vorhanden
        try:
            self.xml_patterns_collection = self.db.client.get_or_create_collection(
                name="scribus_xml_patterns",
                metadata={"hnsw:space": "cosine"}
            )
        except:
            # Falls Collection bereits existiert
            self.xml_patterns_collection = self.db.client.get_collection("scribus_xml_patterns")
    
    def validate_xml_construct(
        self,
        xml_element: ET.Element,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        Validiert ein XML-Konstrukt gegen bekannte Patterns.
        
        Args:
            xml_element: XML-Element zum Validieren
            context: Zusätzlicher Kontext (Layout JSON, etc.)
            
        Returns:
            Tuple von (is_valid, warnings, suggested_fix)
        """
        # Extrahiere XML-Pattern
        pattern_text = self._extract_xml_pattern(xml_element)
        
        # Suche nach ähnlichen Patterns im RAG-Speicher
        pattern_embedding = self.embeddings.embed_text(pattern_text)
        
        try:
            results = self.xml_patterns_collection.query(
                query_embeddings=[pattern_embedding],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            
            warnings = []
            suggested_fix = None
            
            # Prüfe bekannte Probleme
            for i, metadata in enumerate(results["metadatas"][0]):
                distance = results["distances"][0][i]
                similarity = 1.0 - distance
                
                # Wenn sehr ähnlich zu einem bekannten Problem
                if similarity > 0.8:
                    behavior = metadata.get("behavior", "unknown")
                    if behavior == "error" or behavior == "warning":
                        issue = metadata.get("issue", "")
                        fix = metadata.get("suggested_fix", "")
                        
                        warnings.append(f"Known issue (similarity: {similarity:.2f}): {issue}")
                        
                        if fix and not suggested_fix:
                            suggested_fix = {
                                "fix": fix,
                                "pattern": results["documents"][0][i],
                                "similarity": similarity,
                            }
            
            # Wenn keine bekannten Probleme: Konstrukt ist wahrscheinlich sauber
            is_valid = len(warnings) == 0 or all("warning" in w.lower() for w in warnings)
            
            return is_valid, warnings, suggested_fix
            
        except Exception as e:
            # Falls RAG-Suche fehlschlägt: Standard-Validierung
            return self._basic_validation(xml_element)
    
    def learn_xml_pattern(
        self,
        xml_element: ET.Element,
        behavior: str,
        issue: Optional[str] = None,
        suggested_fix: Optional[str] = None,
        test_result: Optional[Dict] = None
    ):
        """
        Lernt ein neues XML-Pattern und dessen Verhalten.
        
        Args:
            xml_element: XML-Element
            behavior: "success" | "warning" | "error"
            issue: Beschreibung des Problems (falls vorhanden)
            suggested_fix: Vorschlag zur Behebung (falls vorhanden)
            test_result: Testergebnis (Scribus-Reaktion)
        """
        pattern_text = self._extract_xml_pattern(xml_element)
        pattern_embedding = self.embeddings.embed_text(pattern_text)
        
        pattern_id = f"pattern_{hash(pattern_text)}"
        
        metadata = {
            "behavior": behavior,
            "pattern_type": xml_element.tag,
        }
        
        if issue:
            metadata["issue"] = issue
        if suggested_fix:
            metadata["suggested_fix"] = suggested_fix
        if test_result:
            metadata["test_result"] = json.dumps(test_result)
        
        # Prüfe ob Pattern bereits existiert
        try:
            existing = self.xml_patterns_collection.get(ids=[pattern_id])
            if existing["ids"]:
                # Update existierendes Pattern
                self.xml_patterns_collection.update(
                    ids=[pattern_id],
                    embeddings=[pattern_embedding],
                    documents=[pattern_text],
                    metadatas=[metadata]
                )
            else:
                # Neues Pattern
                self.xml_patterns_collection.add(
                    ids=[pattern_id],
                    embeddings=[pattern_embedding],
                    documents=[pattern_text],
                    metadatas=[metadata]
                )
        except:
            # Pattern existiert nicht, füge hinzu
            self.xml_patterns_collection.add(
                ids=[pattern_id],
                embeddings=[pattern_embedding],
                documents=[pattern_text],
                metadatas=[metadata]
            )
    
    def _extract_xml_pattern(self, xml_element: ET.Element) -> str:
        """
        Extrahiert ein XML-Pattern als Text-Repräsentation.
        
        Beispiel: "ITEM tag with ITEMTEXT='...', FONT='Minion Pro', FONTSIZE='12'"
        """
        parts = [f"XML Element: {xml_element.tag}"]
        
        # Attribute
        attrs = xml_element.attrib
        if attrs:
            attr_parts = [f"{k}='{v[:50]}'" for k, v in list(attrs.items())[:10]]
            parts.append(f"Attributes: {', '.join(attr_parts)}")
        
        # Text-Content (erste 100 Zeichen)
        text = xml_element.text
        if text and text.strip():
            parts.append(f"Content: {text[:100]}")
        
        # Children (erste 3)
        children = list(xml_element)[:3]
        if children:
            child_tags = [child.tag for child in children]
            parts.append(f"Children: {', '.join(child_tags)}")
        
        return " | ".join(parts)
    
    def _basic_validation(self, xml_element: ET.Element) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        Basis-Validierung ohne RAG (Fallback).
        
        Prüft grundlegende XML-Struktur und bekannte Scribus-Anforderungen.
        """
        warnings = []
        
        # Prüfe auf leere Elemente
        if not xml_element.text and len(list(xml_element)) == 0:
            warnings.append("Empty element may cause issues")
        
        # Prüfe auf ungültige Attribute
        required_attrs = {
            "ITEM": ["ITEMTEXT"],
            "PAGEOBJECT": ["XPOS", "YPOS", "WIDTH", "HEIGHT"],
        }
        
        tag = xml_element.tag
        if tag in required_attrs:
            for req_attr in required_attrs[tag]:
                if req_attr not in xml_element.attrib:
                    warnings.append(f"Missing required attribute: {req_attr}")
        
        is_valid = len(warnings) == 0
        return is_valid, warnings, None
    
    def get_safe_xml_patterns(
        self,
        element_type: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Gibt bekannte "saubere" XML-Patterns für einen Element-Typ zurück.
        
        Args:
            element_type: XML-Element-Tag (z.B. "ITEM", "PAGEOBJECT")
            top_k: Anzahl der Ergebnisse
            
        Returns:
            Liste von sicheren Patterns
        """
        query_text = f"XML Element: {element_type} behavior: success"
        query_embedding = self.embeddings.embed_text(query_text)
        
        try:
            results = self.xml_patterns_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"behavior": "success", "pattern_type": element_type},
                include=["documents", "metadatas", "distances"]
            )
            
            patterns = []
            for i, metadata in enumerate(results["metadatas"][0]):
                patterns.append({
                    "pattern": results["documents"][0][i],
                    "similarity": 1.0 - results["distances"][0][i],
                    "metadata": metadata,
                })
            
            return patterns
        except:
            return []

