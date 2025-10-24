
from bpy.types import Operator, Context, View3DShading


import logging
logger = logging.getLogger("iiif.configure_viewport")


def findSpaceView3D(c:Context):
    for window in c.window_manager.windows:
         for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        yield space # This is your SpaceView3D instance

class Configure3DViewport(Operator):
    """
    """
    bl_idname = "iiif.configure_viewport"
    bl_label = "Configure 3D Viewport"    

    def execute(self, context):
        logger.info("enter Configure3DViewport")
        try:
            # for simplicity  specify that the Blender scene world data
            # specifies its color through a simple color, rather than a
            # appearance defined by Blender shader nodes
            context.scene.world.use_nodes = False

            for space_data in findSpaceView3D(context):
                # space_data is type SpaceView3D
                # https://docs.blender.org/api/current/bpy.types.SpaceView3D.html
                logger.info("located space_data: %s" % space_data)
                
                shading : View3DShading = space_data.shading
                
                # this configures the viewport to use the Blender scene world data
                # to determine it's background_type
                shading.background_type="WORLD"
                
                shading.color_type="TEXTURE"
                
        except Exception as exc:
            logger.exception("exception thrown", exc)
            
        return {"FINISHED"}