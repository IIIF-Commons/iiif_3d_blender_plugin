import bpy
from bpy.types import Operator  
from mathutils import Vector, Quaternion

from .editing.collections import new_annotation
from .editing.transforms import Translation, Rotation, transformsToPlacements
from .editing.cameras import configure_camera
#from .utils.coordinates import Coordinates
from .utils.blender_setup import setup_camera

import logging
logger = logging.getLogger("iiif.new_camera")

class NewCamera(Operator):
    """Create empty 3D Manifest"""

    bl_idname = "iiif.new_camera"
    bl_label = "Create Camera"

    # developer note 10/27/2025
    # the code in this operator parallels the code in
    # function ImportManifest.resource_data_to_camera
    def execute(self, context):
        
        annotation_page_collection = context.collection
        if not annotation_page_collection.get("iiif_type","") == "AnnotationPage":
            logger.warning("invalid context.collection: %r" % (annotation_page_collection,))
            return {"CANCELLED"}

        try:
            retCode = bpy.ops.object.camera_add()
            logger.info("obj.camera_add %r" % (retCode,))
        except Exception as exc:
            logger.error("add camera error", exc)
            return {"FINISHED"}
        
        new_camera = bpy.context.active_object
        if new_camera is not None:
            logger.info("new_camera: %r" % (new_camera,))
            # reminder 10/27/2025: The setup camera condigures the
            # Blender camera focal length control and sensor 
            # operations for field of view are done according to IIIF spec
            setup_camera(new_camera)
            
            resource_data = {
                "type" : "PerspectiveCamera"
            }

            # the placement of the camera is intended to be out 
            # in front of a model at (0,0,0) looking back at the model
            # in Blender coordinate system this is out along the -Y axix
            location = Translation(Vector([0.0,-10.0,0.0]))  
            
            # the intention is that the orientation of the new camera will 
            # will be the IIIF default, which is to have the camera look in
            # the -Z (IIIF coordinate axes) , which is the +Y axis in Blender 
            # coordinate system. This rotation is declared as a 0 rotation.
            # the configure_camera is responsible for correctly 
            # rotating the camera object to this orientation, taking into account
            # the way new camera objects in Blender are created
            rotation = Rotation( Quaternion([1,0,0], 0.0) )             

            # in this case we're confident this list of transfforms
            # will be siplified to a single placement
            placement = list(transformsToPlacements([rotation, location]))[0]
            


            configure_camera(new_camera, resource_data, placement )

            annotation_collection=new_annotation()
            annotation_page_collection.children.link(annotation_collection) 

            for col in new_camera.users_collection:
                col.objects.unlink(new_camera)
            annotation_collection.objects.link(new_camera)
        
        return {"FINISHED"}

