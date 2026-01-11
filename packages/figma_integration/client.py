"""
Figma API Client

REST API Wrapper für Figma API mit Frame-spezifischen Methoden.
"""

import requests
from typing import Dict, List, Optional
import os


class FigmaClient:
    """Figma REST API Client"""
    
    BASE_URL = "https://api.figma.com/v1"
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialisiert Figma Client.
        
        Args:
            access_token: Figma Personal Access Token (oder aus ENV)
        """
        self.access_token = access_token or os.getenv("FIGMA_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("FIGMA_ACCESS_TOKEN not set. Provide token or set environment variable.")
        
        # Figma REST API verwendet X-Figma-Token Header (nicht Authorization Bearer)
        self.headers = {
            "X-Figma-Token": self.access_token,
            "Content-Type": "application/json",
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Führt HTTP-Request aus.
        
        Args:
            method: HTTP-Methode (GET, POST, etc.)
            endpoint: API-Endpoint (ohne Base URL)
            **kwargs: Zusätzliche Request-Parameter
            
        Returns:
            JSON Response als Dict
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            body = getattr(getattr(e, "response", None), "text", None)
            details = f"{e}"
            if status is not None:
                details = f"HTTP {status}: {details}"
            if body:
                details = f"{details} | Body: {body[:2000]}"
            raise ValueError(f"Figma API Error: {details}")

    def get_me(self) -> Dict:
        """
        Aktuellen User abrufen (inkl. Team-Zugehörigkeiten).
        """
        return self._request("GET", "/me")

    def list_team_projects(self, team_id: str) -> List[Dict]:
        """
        Projekte eines Teams abrufen.

        Figma REST API: GET /v1/teams/{team_id}/projects
        """
        response = self._request("GET", f"/teams/{team_id}/projects")
        return response.get("projects", [])

    def list_project_files(self, project_id: str) -> List[Dict]:
        """
        Dateien eines Projekts abrufen.

        Figma REST API: GET /v1/projects/{project_id}/files
        """
        response = self._request("GET", f"/projects/{project_id}/files")
        return response.get("files", [])
    
    def list_files(
        self,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Dateien auflisten.

        Wichtig: Die Figma REST API bietet kein generisches "GET /files" f◌┤r alle User-Dateien.
        Stattdessen: Teams -> Projekte -> Dateien.

        Args:
            team_id: Optional Team ID; wenn gesetzt und project_id leer: aggregiert Dateien ◌┤ber alle Projekte des Teams
            project_id: Optional Project ID; wenn gesetzt: listet Dateien des Projekts

        Returns:
            Liste von File-Objekten
        """
        if project_id:
            return self.list_project_files(project_id)

        files: List[Dict] = []

        team_ids: List[str] = []
        if team_id:
            team_ids = [team_id]
        else:
            me = self.get_me()
            teams = me.get("teams", []) or []
            team_ids = [t.get("id") for t in teams if t.get("id")]

        for tid in team_ids:
            try:
                projects = self.list_team_projects(tid)
                for project in projects:
                    pid = project.get("id")
                    if not pid:
                        continue
                    try:
                        files.extend(self.list_project_files(pid))
                    except Exception:
                        # Einzelne Projekte d◌┤rfen fehlschlagen (z.B. Rechte), ohne alles zu stoppen.
                        continue
            except Exception:
                continue

        # Dedup nach file_key/key, falls mehrfach in Projekten auftaucht
        seen = set()
        deduped: List[Dict] = []
        for f in files:
            key = f.get("key") or f.get("file_key") or f.get("id")
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(f)

        return deduped
    
    def get_file(self, file_key: str) -> Dict:
        """
        File-Metadaten abrufen.
        
        Args:
            file_key: Figma File Key
            
        Returns:
            File-Objekt mit Metadaten
        """
        return self._request("GET", f"/files/{file_key}")
    
    def get_file_nodes(
        self,
        file_key: str,
        node_ids: List[str]
    ) -> Dict:
        """
        Spezifische Nodes aus File abrufen.
        
        Args:
            file_key: Figma File Key
            node_ids: Liste von Node IDs
            
        Returns:
            Dict mit "nodes" (Node-ID → Node-Objekt)
        """
        ids_param = ",".join(node_ids)
        return self._request("GET", f"/files/{file_key}/nodes", params={"ids": ids_param})
    
    def list_frames(self, file_key: str) -> List[Dict]:
        """
        Liste aller Frames in einem File.
        
        Args:
            file_key: Figma File Key
            
        Returns:
            Liste von Frame-Objekten
        """
        file_data = self.get_file(file_key)
        document = file_data.get("document", {})
        
        frames = []
        self._extract_frames(document, frames)
        
        return frames
    
    def _extract_frames(self, node: Dict, frames: List[Dict], parent_path: str = ""):
        """
        Rekursiv Frames aus Document-Struktur extrahieren.
        
        Args:
            node: Node-Objekt
            frames: Liste zum Sammeln von Frames
            parent_path: Pfad zum Parent-Node
        """
        node_type = node.get("type", "")
        node_name = node.get("name", "")
        node_id = node.get("id", "")
        
        current_path = f"{parent_path}/{node_name}" if parent_path else node_name
        
        # Frame gefunden
        if node_type == "FRAME":
            frame_data = {
                "id": node_id,
                "name": node_name,
                "path": current_path,
                "type": node_type,
                "absoluteBoundingBox": node.get("absoluteBoundingBox", {}),
                "children": node.get("children", []),
            }
            frames.append(frame_data)
        
        # Rekursiv durch Children
        children = node.get("children", [])
        for child in children:
            self._extract_frames(child, frames, current_path)
    
    def get_frame(self, file_key: str, frame_id: str) -> Dict:
        """
        Frame mit allen Children abrufen.
        
        Args:
            file_key: Figma File Key
            frame_id: Frame Node ID
            
        Returns:
            Frame-Objekt mit vollständiger Struktur
        """
        response = self.get_file_nodes(file_key, [frame_id])
        nodes = response.get("nodes", {})
        
        if frame_id not in nodes:
            raise ValueError(f"Frame {frame_id} not found in file {file_key}")
        
        return nodes[frame_id].get("document", {})
    
    def get_frame_images(
        self,
        file_key: str,
        node_ids: List[str],
        format: str = "png",
        scale: float = 1.0
    ) -> Dict:
        """
        Images für Nodes abrufen.
        
        Args:
            file_key: Figma File Key
            node_ids: Liste von Node IDs
            format: Bild-Format (png, jpg, svg, pdf)
            scale: Skalierung (1.0, 2.0, etc.)
            
        Returns:
            Dict mit "images" (Node-ID → Image-URL)
        """
        ids_param = ",".join(node_ids)
        params = {
            "ids": ids_param,
            "format": format,
            "scale": scale,
        }
        
        return self._request("GET", f"/images/{file_key}", params=params)
    
    def create_frame(
        self,
        file_key: str,
        frame_data: Dict,
        parent_id: Optional[str] = None
    ) -> Dict:
        """
        Neuen Frame erstellen (via Figma Plugin API oder REST API).
        
        Hinweis: Figma REST API unterstützt keine direkte Frame-Erstellung.
        Diese Methode ist für zukünftige Plugin-Integration vorbereitet.
        
        Args:
            file_key: Figma File Key
            frame_data: Frame-Daten (name, width, height, etc.)
            parent_id: Parent Node ID (optional)
            
        Returns:
            Erstelltes Frame-Objekt
        """
        # TODO: Implementierung über Figma Plugin API
        raise NotImplementedError("Frame creation requires Figma Plugin API")
    
    def update_frame(
        self,
        file_key: str,
        frame_id: str,
        changes: Dict
    ) -> Dict:
        """
        Frame aktualisieren (via Figma Plugin API oder REST API).
        
        Hinweis: Figma REST API unterstützt keine direkte Frame-Aktualisierung.
        Diese Methode ist für zukünftige Plugin-Integration vorbereitet.
        
        Args:
            file_key: Figma File Key
            frame_id: Frame Node ID
            changes: Änderungen (properties to update)
            
        Returns:
            Aktualisiertes Frame-Objekt
        """
        # TODO: Implementierung über Figma Plugin API
        raise NotImplementedError("Frame update requires Figma Plugin API")

