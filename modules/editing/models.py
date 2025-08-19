import json
from bpy.types import Object
from typing import  Tuple
from mathutils import Vector, Quaternion

from .transforms import Placement

import logging
logger = logging.getLogger("iiif.models")

# The string constant is shared between this module and the ImportLocalModel class.
# It is the key for a custom property attached to a Blender object when it 
# is loaded, it will be the mimetype as which the object was successfully loaded
# from a file
IIIF_TEMP_FORMAT="iiif.temp.format"

# the string constant INITIAL_TRANSFORM is shared between the ImportLocalModel class,
# as the key for a custom property attached to a Blender object when it is loaded,
# the value of the custom property is a string encoding of glTF properties which
# may rotate, translate, and scale the mesh defined in the glTF binary buffers.
INITIAL_TRANSFORM="iiif.initial.transform"


def configure_model(    new_model : Object,
                        resource_data  : dict,
                        placement      : Placement ) -> None :
    """
    Initialize the custom properties of the Blender object
    and set the Blender location, rotation, scale properties
    of the obect to place it in the screen
    
    If the new_model has a custom_property for "iiif.temp.format"
    then it will be inserted into the resource data
    
    input arguments:
    resource_data must contain an "id" value
    
    """
    logger.debug(f"configure_model : placement : {repr(placement)}")
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
            logger.warn("TODO: fix this message")
            
    if IIIF_TEMP_FORMAT in new_model:
        mimetype = new_model[IIIF_TEMP_FORMAT]
        if "format" in resource_data and resource_data["format"] != mimetype:
            message=f'resource format ${resource_data["format"]} does not match ${mimetype}'
            logger.warn(message)
    new_model["iiif_type"] = "Model"
    new_model["iiif_json"] = json.dumps(resource_data)

    new_model.location = placement.translation.data
    new_model.rotation_mode = "QUATERNION"
    new_model.rotation_quaternion = placement.rotation.data
    new_model.scale = placement.scaling.data
    
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
        
def encode_blender_transform(location : Vector, rotation : Quaternion, scale : Vector ) -> str:
    """
    encode the 3 values used in Blender object into a string that can be stored
    as a Blender custom property, and decoded back into the original values
    
    encoding strategy: encode as the string representation of a 3-tuple,
    each element of the tuple is the string returned by the repr() value
    of a Blender python API object
    """
    
    argTuple = tuple( [ repr(s) for s in [location, rotation, scale ]])
    return repr( argTuple )
    

def decode_blender_transform( encoding : str ) -> Tuple[Vector, Quaternion, Vector]:
    """
    reverses the encoding performed by function encode_blender_transform
    """
    try:
        argTuple = eval(encoding)
        retVal = tuple( [eval(s) for s in argTuple])
    except Exception:
        logger.error(f"unable to decode transform: {repr(encoding)}")
        return (Vector(), Quaternion(), Vector())
    return retVal
