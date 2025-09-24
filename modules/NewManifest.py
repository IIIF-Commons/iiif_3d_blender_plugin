import json

import bpy
from bpy.types import Operator


from .editing.collections import new_manifest,new_scene,new_annotation_page


import logging
logger = logging.getLogger("iiif.new_manifest")

class NewManifest(Operator):
    """Create empty 3D Manifest"""

    bl_idname = "iiif.new_manifest"
    bl_label = "Create Empty IIIF 3D Manifest"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        logger.info("called build")
        #configure_blender_scene()
        
        manifest=new_manifest()
        # for new manifests add a default label, some viewers
        # require one
        manifest_data : dict = json.loads( manifest["iiif_json"])
        label : dict = manifest_data["label"]
        label["en"] = ["Blender generated IIIF manifest"]
        manifest["iiif_json"] = json.dumps( manifest_data )
        
        bpy.context.scene.collection.children.link(manifest)
        
        iiif_scene = new_scene()
        manifest.children.link(iiif_scene)
    
        annotation_page = new_annotation_page()
        iiif_scene.children.link(annotation_page)
        
        return {"FINISHED"}

