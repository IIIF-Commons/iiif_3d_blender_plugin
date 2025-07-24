import json
from bpy.types import Object
from mathutils import Vector

from ..utils.coordinates import Coordinates

import logging
logger = logging.getLogger("iiif.models")

# The string constant is shared between this module and the ImportLocalModel class.
# It is the key for a custom property attached to a Blender object when it 
# is loaded, it will be the mimetype as which the object was successfully loaded
# from a file
IIIF_TEMP_FORMAT="iiif.temp.format"


def configure_model(    new_model : Object,
                        resource_data  : dict,
                        placement_data : dict ) -> None :
    """
    Initialize the custom properties of the Blender object
    and set the Blender location, rotation, scale properties
    of the obect to place it in the screen
    
    If the new_model has a custom_property for "iiif.temp.format"
    then it will be inserted into the resource data
    
    input arguments:
    resource_data must contain an "id" value
    
    """
    try:
        model_id = resource_data["id"]
    except KeyError:
        logger.warn("logic error: configure_model : no id value")
        raise ValueError()
        
    new_model["iiif_id"] = model_id
    MODEL="Model"
    
    try:
        existing_type = resource_data["type"]
    except KeyError:
        pass
    else:
        if existing_type != MODEL:
            logger.warn
            
    if IIIF_TEMP_FORMAT in new_model:
        mimetype = new_model[IIIF_TEMP_FORMAT]
        if "format" in resource_data and resource_data["format"] != mimetype:
            logger.warn
    new_model["iiif_type"] = "Model"
    new_model["iiif_json"] = json.dumps(resource_data)
    if placement_data is not None:
        if placement_data["location"] is not None:
            new_model.location = Coordinates.iiif_position_to_blender_vector( placement_data["location"] )
         
        if placement_data["rotation"] is not None:
            saved_mode = new_model.rotation_mode
        try:
            euler = Coordinates.model_transform_angles_to_blender_euler( placement_data["rotation"] )
            new_model.rotation_mode = euler.order
            new_model.rotation_euler = euler
        finally:
            new_model.rotation_mode = saved_mode            
        
        if placement_data["scale"] is not None:
            new_model.scale = Vector( placement_data["scale"] )
    return    


_ext_to_mime_dict = {
    "GLB" : "model/gltf-binary",
    "GLTF": "model/gltf+json"
}

def mimetype_from_extension( fname: str ) -> str:
    """
    fname a filename like object which will be parsed by 
    os.path.splitext
    
    returns empty atring if no matchine mimetyoe identifies
    """
    from os.path import splitext
    # put in standard form: remove leading . characters, go upper case
    ext = splitext(fname)[1].strip(".").upper()
    
    try:
        return _ext_to_mime_dict[ext]
    except KeyError:
        return ""