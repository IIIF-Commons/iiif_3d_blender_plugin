"""
Function which configures Blender to be more amenable to IIIF 3D Manifest
authoring
"""

import bpy

import logging
logger = logging.getLogger("iiif.blender_setup")

def configure_blender_scene():
    """
    actions:
    1. Set the aspect ratio of the scene cameras to be more
    appropriate to most web based 3D viewports, rather than
    the Blender default which is more cinema/video appropriate
    """
    ASPECT_RATIO = 1.25  # Will be the camera width to height ratio
    scene = bpy.context.scene
    
    resolutionY = 1024
    resolutionX = int( ASPECT_RATIO * resolutionY)
    
    scene.render.resolution_x = resolutionX
    scene.render.resolution_y = resolutionY
    
    logger.info("Scene resolution set to %i x %i" % (resolutionX,resolutionY))
    return 
    
def configure_camera(cameraObj):
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