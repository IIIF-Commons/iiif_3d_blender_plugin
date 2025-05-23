from typing import Set
import json

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

import math

from .initialize_collections import initialize_annotation

import logging
logger = logging.getLogger("iiif.new_camera")

class NewCamera(Operator):
    """Create empty 3D Manifest"""

    bl_idname = "iiif.new_camera"
    bl_label = "Create Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        annotation_page_collection = context.collection
        if not annotation_page_collection.get("iiif_type","") == "AnnotationPage":
            logger.warning("invalid context.collection: %r" % (annotation_page_collection,))
            return {"CANCELLED"}

        try:
            # developer note: eventually an initial location, rotation, scale can be
            # set here
            retCode = bpy.ops.object.camera_add()
            logger.info("obj.camera_add %r" % (retCode,))
        except Exception as exc:
            logger.error("glTF import error", exc)
            return {"FINISHED"}
        
        new_camera = bpy.context.active_object
        logger.info("new_camera: %r" % (new_camera,))

        annotation_collection=bpy.data.collections.new("Annotation")
        initialize_annotation( annotation_collection )    
        annotation_page_collection.children.link(annotation_collection) 
                
        for col in new_camera.users_collection:
            col.objects.unlink(new_camera)
        annotation_collection.objects.link(new_camera)
        
        return {"FINISHED"}

