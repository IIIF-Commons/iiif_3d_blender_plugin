import json
from datetime import datetime
from typing import Any, Dict, Optional


class IIIFMetadata:
    """Helper class to manage IIIF metadata on Blender objects
    Instances of this class only store a reference to a Blender object
    and implement a mechanism to store key-value pairs (dict-like behavior)
    but with the key string prefixed with "iiif_" to avoid key collisions
    Blender properties defined on the Blender obj
    
    the values stored are strings, often json encoded data.
    
    For example, the store_manifest method is used in the importer.process_manifest
    method to attach a json-encoded manifest_data (a json object) in the main_collection,
    which is the topmost created collection named "IIIF Manifest"
    
    It appears to be used in process_annotation_model to store a copy of the 
    annotation_data (dict); encoded as json, with the model object
    
    And likewise a copy of the annotation_data is stored in the camera obj
    """

    def __init__(self, obj: Any):
        """Initialize with a Blender object"""
        self.obj = obj
        self._prefix = "iiif_"

    def _get_key(self, name: str) -> str:
        """Get prefixed key name"""
        return f"{self._prefix}{name}"

    def store_manifest(self, data: Dict) -> None:
        """Store complete manifest data"""
        self.obj[self._get_key("manifest")] = json.dumps(data)
        self.obj[self._get_key("import_date")] = datetime.now().isoformat()
        self.obj[self._get_key("type")] = "Manifest"
        self.obj[self._get_key("id")] = data.get("id","not_supplied")

    def store_annotation(self, data: Dict) -> None:
        """Store annotation data and its body"""
        self.obj[self._get_key("annotation")] = json.dumps(data)
        if "body" in data:
            self.obj[self._get_key("body")] = json.dumps(data["body"])
        if "id" in data:
            self.obj[self._get_key("id")] = data["id"]
        if "type" in data:
            self.obj[self._get_key("type")] = data["type"]

    def store_scene(self, data: Dict) -> None:
        """Store scene data"""
        self.obj[self._get_key("scene")] = json.dumps(data)
        self.obj[self._get_key("type")] = "Scene"
        if "id" in data:
            self.obj[self._get_key("id")] = data.get("id","not_supplied")

    def get_manifest(self) -> Optional[Dict]:
        """Retrieve stored manifest data"""
        data = self.obj.get(self._get_key("manifest"))
        return json.loads(data) if data else None

    def get_annotation(self) -> Optional[Dict]:
        """Retrieve stored annotation data"""
        data = self.obj.get(self._get_key("annotation"))
        return json.loads(data) if data else None

    def get_scene(self) -> Optional[Dict]:
        """Retrieve stored scene data"""
        data = self.obj.get(self._get_key("scene"))
        return json.loads(data) if data else None

    def get_import_date(self) -> Optional[str]:
        """Get the import date"""
        return self.obj.get(self._get_key("import_date"))

    def get_id(self) -> Optional[str]:
        """Get the IIIF ID"""
        return self.obj.get(self._get_key("id"))

    def has_metadata(self) -> bool:
        """Check if object has any IIIF metadata"""
        return any(key.startswith(self._prefix) for key in self.obj.keys())
