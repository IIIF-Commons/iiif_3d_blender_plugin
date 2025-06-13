
import bpy
from bpy.types import Operator


from .initialize_collections import initialize_annotation, generate_uri

from ..utils.blender_setup import configure_camera
from ..utils.coordinates import Coordinates
from ..utils.blender_naming import generate_name_from_id

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
            init_location = Coordinates.iiif_position_to_blender_vector( (0,0,10.0))
            init_rotation = Coordinates.camera_transform_angles_to_blender_euler( (0,0,0))
            retCode = bpy.ops.object.camera_add(    location=init_location, 
                                                    rotation=init_rotation
                                                )
            logger.info("obj.camera_add %r" % (retCode,))
        except Exception as exc:
            logger.error("add camera error", exc)
            return {"FINISHED"}
        
        new_camera = bpy.context.active_object
        logger.info("new_camera: %r" % (new_camera,))
        configure_camera(new_camera)
        
        # at this stage only support creating a PerspectiveCamera
        # TODO will be to present a UI that will allow user to 
        # choose what type of camera; and potentially a value for a label
        new_camera.data.type = "PERSP"
        
        new_camera["iiif_id"]=  generate_uri("PerspectiveCamera")

        new_camera['iiif_type']="PerspectiveCamera"
        

        annotation_collection=bpy.data.collections.new("Annotation")
        initialize_annotation( annotation_collection )    
        annotation_page_collection.children.link(annotation_collection) 
        annotation_collection.name = generate_name_from_id( annotation_collection ) or annotation_collection.name

                
        for col in new_camera.users_collection:
            col.objects.unlink(new_camera)
        annotation_collection.objects.link(new_camera)
        
        return {"FINISHED"}

