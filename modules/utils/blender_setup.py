"""
Function which configures Blender to be more amenable to IIIF 3D Manifest
authoring
"""

import bpy
import typing 

import logging
logger = logging.getLogger("iiif.blender_setup")

def configure_blender_scene():
    """
    actions:
    1. Set the aspect ratio of the scene cameras to be more
    appropriate to most web based 3D viewports, rather than
    the Blender default which is more cinema/video appropriate
    """
    # developer note: 5 June 2025 : disabled this  configuration step
    # replaced by loading an inital .blend file which will
    # have this quantity configured
    # in 30 days remove this code unless decided otherwise
    if False:
        ASPECT_RATIO = 1.25  # Will be the camera width to height ratio
        
        scene = bpy.context.scene
        
        resolutionY = 1024
        resolutionX = int( ASPECT_RATIO * resolutionY)
        
        scene.render.resolution_x = resolutionX
        scene.render.resolution_y = resolutionY
    return 
    
def setup_camera(cameraObj):
    """
    argument is the bpy.types.object for a camera
    """
    
    # set the "units" for the camera field to be "FOV", this 
    # gives a more useful UI for adjusting the focal length of the
    # camera
    cameraObj.data.lens_unit='FOV' 
    # This will cause the value displayed in UI in Field Of View to
    # be the vertical angle in degrees,
    cameraObj.data.sensor_fit = 'VERTICAL' 
    return
    

    

    
def set_scene_background_color(blenderColor):
    """
    scene here referring to the Blender scene
    Sets the background color using the node-graph
    
    blenderColor a (4,) array of floats in range [0.0,1.0]
    denoting red-green-blue-alpha color channel values
    generally will have rgba[3] = 1.0; no transparency
    """
    
    bpy.context.scene.world.use_nodes = False        # type: ignore
    bpy.context.scene.world.color = blenderColor[:3] # type: ignore
    return None
    
def get_scene_background_color() -> tuple[float,float,float,float] | None :
    """
    scene here referring to the Blender scene
    returns the background color using the node-graph
    
    returns a (4,) array of floats in range [0.0,1.0]
    denoting red-green-blue-alpha color channel values
    generally will have rgba[3] = 1.0; no transparency
    """
    raw_color = bpy.context.scene.world.color # type: ignore
        
    try:
        raw_color_list = [float(x) for x in raw_color]
        raw_color_list.extend([1.0] * 4)
        return typing.cast( tuple[float,float,float,float], tuple(raw_color_list)[:4])
    except Exception:
        logger.warn("background raw color was not rgba format: %r" % (raw_color,))
        return None
        
            

    
    
