from typing import Set
import json

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

import math

from .initialize_collections import initialize_manifest,initialize_scene,initialize_anotation_page

from ..utils.blender_setup import configure_blender_scene

import logging
logger = logging.getLogger("iiif.new_manifest")

class NewManifest(Operator):
    """Create empty 3D Manifest"""

    bl_idname = "iiif.new_manifest"
    bl_label = "Create Empty IIIF 3D Manifest"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        logger.info("called build")
        configure_blender_scene()
        
        manifest=bpy.data.collections.new("IIIF Manifest")
        initialize_manifest( manifest )    
        bpy.context.scene.collection.children.link(manifest)
        
        iiif_scene = bpy.data.collections.new("IIIF Scene")
        manifest.children.link(iiif_scene)
        initialize_scene( iiif_scene )
    
        annotation_page = bpy.data.collections.new("Annotation Page")
        iiif_scene.children.link(annotation_page)
        initialize_anotation_page( annotation_page )
        
        return {"FINISHED"}

