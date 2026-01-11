"""
Layout Indexer für RAG-Service

Indexiert Layout JSON mit allen Objekten und Zuordnungen.
"""

from typing import Dict, List, Any, Union
from .database import RAGDatabase
from .embeddings import EmbeddingModels
import json
import uuid


def _clean_metadata_value(value: Any) -> Union[str, int, float, bool]:
    """
    Bereinigt Metadata-Werte für ChromaDB.
    ChromaDB akzeptiert nur: str, int, float, bool (keine None!)
    """
    if value is None:
        return ""
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, (dict, list)):
        return json.dumps(value) if value else ""
    else:
        return str(value) if value else ""


def _safe_metadata(metadata: Dict) -> Dict:
    """Bereinigt alle Werte in einem Metadata-Dict"""
    return {k: _clean_metadata_value(v) for k, v in metadata.items()}


class LayoutIndexer:
    """Indexiert Layout-Strukturen in ChromaDB"""
    
    def __init__(self, db: RAGDatabase, embeddings: EmbeddingModels):
        """
        Initialisiert Layout Indexer.
        
        Args:
            db: RAGDatabase Instanz
            embeddings: EmbeddingModels Instanz
        """
        self.db = db
        self.embeddings = embeddings
    
    def index_layout(self, layout_json: Dict, source: str = "unknown") -> str:
        """
        Indexiert Layout JSON mit allen Objekten und Zuordnungen.
        
        Args:
            layout_json: Layout JSON Schema
            source: Quelle (figma|scribus|llm|unknown)
            
        Returns:
            Layout-ID
        """
        layout_id = str(uuid.uuid4())
        
        # 1. Layout-Struktur → Text-Embedding
        structure_text = self._extract_layout_structure(layout_json)
        structure_embedding = self.embeddings.embed_text(structure_text)
        
        # Speichere Layout-Struktur
        self.db.layouts_collection.add(
            ids=[layout_id],
            embeddings=[structure_embedding],
            documents=[structure_text],
            metadatas=[_safe_metadata({
                "source": source or "unknown",
                "layout_json": json.dumps(layout_json) if layout_json else "{}",
                "version": layout_json.get("version") or "1.0.0",
            })]
        )
        
        # 2. Text-Objekte → Text-Embeddings
        self._index_text_objects(layout_json, layout_id)
        
        # 3. Bild-Objekte → Bild-Embeddings (CLIP)
        self._index_image_objects(layout_json, layout_id)
        
        # 4. Text-Bild-Zuordnungen → Kombinierte Embeddings
        self._index_text_image_pairs(layout_json, layout_id)
        
        # 5. Gescannte Inhalte → Separate Embeddings
        self._index_scanned_content(layout_json, layout_id)
        
        return layout_id
    
    def _extract_layout_structure(self, layout_json: Dict) -> str:
        """
        Konvertiert Layout-Struktur in Text-Repräsentation für Embedding.
        
        Beispiel: "Layout: 2480x3508px, 1 page, 3 text objects, 2 images,
                   text_001 (124,1502,2232x140) related to image_001..."
        """
        doc = layout_json.get("document", {})
        width = doc.get("width", 0)
        height = doc.get("height", 0)
        dpi = doc.get("dpi", 300)
        
        pages = layout_json.get("pages", [])
        num_pages = len(pages)
        
        parts = [f"Layout: {width}x{height}px, {num_pages} page(s), DPI: {dpi}"]
        
        text_count = 0
        image_count = 0
        
        for page in pages:
            objects = page.get("objects", [])
            for obj in objects:
                obj_type = obj.get("type", "")
                obj_id = obj.get("id", "")
                bbox = obj.get("bbox", {})
                x = bbox.get("x", 0)
                y = bbox.get("y", 0)
                w = bbox.get("w", 0)
                h = bbox.get("h", 0)
                
                if obj_type == "text":
                    text_count += 1
                    content = obj.get("content", "")[:50]  # Erste 50 Zeichen
                    related = obj.get("relatedImageIds", [])
                    if related:
                        parts.append(f"text_{obj_id} ({x},{y},{w}x{h}) '{content}' related to {related}")
                    else:
                        parts.append(f"text_{obj_id} ({x},{y},{w}x{h}) '{content}'")
                
                elif obj_type == "image":
                    image_count += 1
                    media_id = obj.get("mediaId", "")
                    related = obj.get("relatedTextIds", [])
                    if related:
                        parts.append(f"image_{obj_id} ({x},{y},{w}x{h}) {media_id} related to {related}")
                    else:
                        parts.append(f"image_{obj_id} ({x},{y},{w}x{h}) {media_id}")
        
        parts.insert(1, f"{text_count} text objects, {image_count} images")
        
        return ". ".join(parts)
    
    def _index_text_objects(self, layout_json: Dict, layout_id: str):
        """Indexiert Text-Objekte aus Layout"""
        for page in layout_json.get("pages", []):
            for obj in page.get("objects", []):
                if obj.get("type") == "text":
                    obj_id = obj.get("id") or "unknown"
                    text_id = f"{layout_id}_{obj_id}"
                    content = obj.get("content", "") or ""
                    
                    if content:
                        embedding = self.embeddings.embed_text(content)
                        
                        bbox = obj.get("bbox", {}) or {}
                        
                        self.db.texts_collection.add(
                            ids=[text_id],
                            embeddings=[embedding],
                            documents=[content],
                            metadatas=[_safe_metadata({
                                "layout_id": layout_id or "",
                                "object_id": obj.get("id") or "",
                                "type": "layout_text",
                                "bbox": json.dumps(bbox) if bbox else "{}",
                            })]
                        )
    
    def _index_image_objects(self, layout_json: Dict, layout_id: str):
        """Indexiert Bild-Objekte aus Layout (CLIP-Embeddings)"""
        for page in layout_json.get("pages", []):
            for obj in page.get("objects", []):
                if obj.get("type") == "image":
                    obj_id = obj.get("id") or "unknown"
                    image_id = f"{layout_id}_{obj_id}"
                    media_id = obj.get("mediaId", "") or ""
                    
                    if media_id:
                        # Versuche Bild zu laden (MinIO-URL oder lokaler Pfad)
                        try:
                            # TODO: MinIO-Client für Bild-Download
                            # Für jetzt: Nur Metadaten indexieren
                            metadata_text = obj.get("metadata", {}).get("altText", "")
                            if not metadata_text:
                                metadata_text = obj.get("metadata", {}).get("description", "")
                            
                            if metadata_text:
                                # Verwende Text-Embedding für Metadaten
                                embedding = self.embeddings.embed_text(metadata_text)
                            else:
                                # Fallback: Struktur-Embedding
                                bbox = obj.get("bbox", {})
                                structure = f"image {bbox.get('w', 0)}x{bbox.get('h', 0)}"
                                embedding = self.embeddings.embed_text(structure)
                            
                            bbox = obj.get("bbox", {}) or {}
                            
                            self.db.images_collection.add(
                                ids=[image_id],
                                embeddings=[embedding],
                                documents=[metadata_text or media_id or ""],
                                metadatas=[_safe_metadata({
                                    "layout_id": layout_id or "",
                                    "object_id": obj.get("id") or "",
                                    "media_id": media_id or "",
                                    "type": "layout_image",
                                    "bbox": json.dumps(bbox) if bbox else "{}",
                                })]
                            )
                        except Exception as e:
                            # Fehler beim Indexieren ignorieren
                            pass
    
    def _index_text_image_pairs(self, layout_json: Dict, layout_id: str):
        """Indexiert Text-Bild-Zuordnungen mit CLIP-Embeddings"""
        for page in layout_json.get("pages", []):
            objects = {obj.get("id"): obj for obj in page.get("objects", [])}
            
            # Finde Text-Bild-Paare
            for obj_id, obj in objects.items():
                if obj.get("type") == "text":
                    related_images = obj.get("relatedImageIds", [])
                    for image_id in related_images:
                        if image_id in objects:
                            image_obj = objects[image_id]
                            self._index_pair(
                                layout_id,
                                obj_id,
                                image_id,
                                obj.get("content", ""),
                                image_obj.get("mediaId", ""),
                                image_obj.get("metadata", {})
                            )
                
                elif obj.get("type") == "image":
                    related_texts = obj.get("relatedTextIds", [])
                    for text_id in related_texts:
                        if text_id in objects:
                            text_obj = objects[text_id]
                            self._index_pair(
                                layout_id,
                                text_id,
                                obj_id,
                                text_obj.get("content", ""),
                                obj.get("mediaId", ""),
                                obj.get("metadata", {})
                            )
    
    def _index_pair(
        self,
        layout_id: str,
        text_id: str,
        image_id: str,
        text_content: str,
        image_media_id: str,
        image_metadata: Dict
    ):
        """Indexiert ein Text-Bild-Paar"""
        pair_id = f"{layout_id}_{text_id}_{image_id}"
        
        # Kombiniertes Embedding
        image_text = image_metadata.get("altText") or image_metadata.get("description") or image_media_id
        
        try:
            embedding = self.embeddings.embed_text_image_pair(text_content, image_media_id)
        except:
            # Fallback: Text-Embedding
            combined_text = f"{text_content} {image_text}"
            embedding = self.embeddings.embed_text(combined_text)
        
        self.db.pairs_collection.add(
            ids=[pair_id],
            embeddings=[embedding],
            documents=[f"Text: {text_content or ''} | Image: {image_text or ''}"],
            metadatas=[_safe_metadata({
                "layout_id": layout_id or "",
                "text_id": text_id or "",
                "image_id": image_id or "",
                "relationship": "related",
            })]
        )
    
    def _index_scanned_content(self, layout_json: Dict, layout_id: str):
        """Indexiert gescannte Inhalte aus scannedContent-Sektion"""
        for page in layout_json.get("pages", []):
            scanned = page.get("scannedContent", {})
            
            # Gescannte Texte
            for text_item in scanned.get("texts", []):
                item_id = text_item.get("id") or "unknown"
                text_id = f"{layout_id}_scanned_{item_id}"
                content = text_item.get("content", "") or ""
                
                if content:
                    embedding = self.embeddings.embed_text(content)
                    
                    self.db.texts_collection.add(
                        ids=[text_id],
                        embeddings=[embedding],
                        documents=[content],
                        metadatas=[_safe_metadata({
                            "layout_id": layout_id or "",
                            "type": "scanned_text",
                            "source": text_item.get("source") or "",
                            "page_number": int(text_item.get("pageNumber") or 0),
                        })]
                    )
            
            # Gescannte Bilder
            for image_item in scanned.get("images", []):
                item_id = image_item.get("id") or "unknown"
                image_id = f"{layout_id}_scanned_{item_id}"
                image_path = image_item.get("path", "") or ""
                metadata = image_item.get("metadata", {}) or {}
                
                if image_path:
                    try:
                        embedding = self.embeddings.embed_image(image_path)
                    except:
                        # Fallback: Metadaten-Text
                        alt_text = metadata.get("altText", "") or metadata.get("extractedText", "")
                        embedding = self.embeddings.embed_text(alt_text) if alt_text else None
                    
                    if embedding:
                        self.db.images_collection.add(
                            ids=[image_id],
                            embeddings=[embedding],
                            documents=[metadata.get("altText") or image_path or ""],
                            metadatas=[_safe_metadata({
                                "layout_id": layout_id or "",
                                "type": "scanned_image",
                                "source": image_item.get("source") or "",
                                "path": image_path or "",
                            })]
                        )

