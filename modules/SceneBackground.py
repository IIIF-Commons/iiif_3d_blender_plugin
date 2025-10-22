from typing import Set



#import bpy
from bpy.props import FloatVectorProperty
from bpy.types import Context, Operator

import logging
logger = logging.getLogger("iiif.scene_background")



            
class SceneBackground(Operator):
    """
    Operator that sets the color of the 
    """
    bl_options = {'REGISTER', 'UNDO'}
    bl_idname = "iiif.scene_background"
    bl_label = "Set background color"    
    
    bgcolor: FloatVectorProperty( # type: ignore
             name = "Background Color",
             subtype = "COLOR",
             default = (1.0,1.0,1.0,1.0),
             size = 4
             )

    def invoke(self, context, event):
        logger.info("SceneBackground.invoke entered")
        self.bgcolor=(1.0,0.5,0.5,1.0)
        rv = context.window_manager.invoke_props_dialog(self, width=640)
        logger.info("return from invoke_props_dialog %r : %r" % (rv, self.bgcolor) )
        return rv
        
    def execute(self, context: Context) -> Set[str]:
        logger.info("SceneBackground.execute entered")
        return {"FINISHED"}
