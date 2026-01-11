"""
Figma Asset Downloader

Lädt Images aus Figma Frames herunter und speichert sie in MinIO.
"""

import requests
from typing import Dict, List, Optional
import os
from urllib.parse import urlparse


class FigmaAssetDownloader:
    """Lädt Figma Images herunter und speichert sie in MinIO"""
    
    def __init__(
        self,
        minio_client=None,
        minio_bucket: str = "figma-assets"
    ):
        """
        Initialisiert Asset Downloader.
        
        Args:
            minio_client: MinIO Client Instanz (optional)
            minio_bucket: MinIO Bucket Name
        """
        self.minio_client = minio_client
        self.minio_bucket = minio_bucket
    
    def download_frame_images(
        self,
        figma_client,
        file_key: str,
        frame_json: Dict,
        image_objects: List[Dict]
    ) -> Dict[str, str]:
        """
        Lädt alle Images aus einem Frame herunter.
        
        Args:
            figma_client: FigmaClient Instanz
            file_key: Figma File Key
            frame_json: Frame JSON
            image_objects: Liste von Image-Objekten aus Layout JSON
            
        Returns:
            Dict: {image_object_id: minio_url}
        """
        # Finde alle Image-Node-IDs im Frame
        image_node_ids = self._extract_image_node_ids(frame_json, image_objects)
        
        if not image_node_ids:
            return {}
        
        # Hole Image-URLs von Figma
        image_urls = figma_client.get_frame_images(file_key, list(image_node_ids.keys()))
        figma_images = image_urls.get("images", {})
        
        # Download und Upload zu MinIO
        minio_urls = {}
        
        for node_id, image_url in figma_images.items():
            object_id = image_node_ids[node_id]
            
            try:
                # Download von Figma
                image_data = self._download_image(image_url)
                
                # Upload zu MinIO
                minio_url = self._upload_to_minio(image_data, object_id)
                
                minio_urls[object_id] = minio_url
            except Exception as e:
                # Fehler beim Download/Upload
                print(f"Error downloading image {node_id}: {e}")
                continue
        
        return minio_urls
    
    def _extract_image_node_ids(
        self,
        frame_json: Dict,
        image_objects: List[Dict]
    ) -> Dict[str, str]:
        """
        Extrahiert Image-Node-IDs aus Frame.
        
        Returns:
            Dict: {figma_node_id: layout_object_id}
        """
        image_node_ids = {}
        
        # Erstelle Mapping von Layout Object IDs zu Figma Node IDs
        object_id_to_figma_id = {}
        
        def traverse_nodes(node: Dict, parent_path: str = ""):
            """Rekursiv durch Nodes traversieren"""
            node_id = node.get("id", "")
            node_type = node.get("type", "")
            
            # Prüfe ob es ein Image ist
            if node_type in ["VECTOR", "RECTANGLE", "ELLIPSE"]:
                fills = node.get("fills", [])
                is_image = any(
                    fill.get("type") == "IMAGE"
                    for fill in fills
                )
                
                if is_image:
                    # Finde entsprechendes Layout Object
                    for img_obj in image_objects:
                        layout_id = img_obj.get("id", "").replace("_", ":")
                        if layout_id == node_id or node_id.endswith(layout_id.split("_")[-1]):
                            image_node_ids[node_id] = img_obj.get("id", "")
                            break
            
            # Rekursiv durch Children
            children = node.get("children", [])
            for child in children:
                traverse_nodes(child)
        
        traverse_nodes(frame_json)
        
        return image_node_ids
    
    def _download_image(self, url: str) -> bytes:
        """
        Lädt Image von URL herunter.
        
        Args:
            url: Image-URL
            
        Returns:
            Image-Daten als Bytes
        """
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    
    def _upload_to_minio(self, image_data: bytes, object_id: str) -> str:
        """
        Upload Image zu MinIO.
        
        Args:
            image_data: Image-Daten
            object_id: Object ID (für Dateiname)
            
        Returns:
            MinIO URL
        """
        if not self.minio_client:
            # Fallback: Lokale Speicherung
            local_path = f"./figma_assets/{object_id}.png"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(image_data)
            return f"file://{local_path}"
        
        # Upload zu MinIO
        filename = f"{object_id}.png"
        
        try:
            from io import BytesIO
            from minio import Minio
            from minio.error import S3Error
            
            # Prüfe ob Bucket existiert
            if not self.minio_client.bucket_exists(self.minio_bucket):
                self.minio_client.make_bucket(self.minio_bucket)
            
            # Upload
            self.minio_client.put_object(
                self.minio_bucket,
                filename,
                BytesIO(image_data),
                length=len(image_data),
                content_type="image/png"
            )
            
            # MinIO URL
            return f"minio://{self.minio_bucket}/{filename}"
            
        except Exception as e:
            raise ValueError(f"MinIO upload failed: {e}")

