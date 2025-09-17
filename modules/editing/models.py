import json
from bpy.types import Object
from typing import  List

# Developer Note 9/15/2025: the following types not appear explicitly
# in the code but are required to decode the INITIAL_TRANSFORM string
from mathutils import Vector, Quaternion # noqa: F401
from .transforms import Placement, Scaling, Translation, Rotation # noqa: F401

from .transforms import  Transform, transformsToPlacements

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

    # now combine any placement defined during the resource import
    # with that that defined in the placment passed INITIAL_TRANSFORM
    
    transform_list : List[Transform] = list()
    try:
        initial_placement_encoded = new_model[INITIAL_TRANSFORM]
        logger.debug("repr(initial_placement_encoded) %s" % initial_placement_encoded)
    except KeyError:
        pass
    else:
        initial_placement = decode_blender_transform(initial_placement_encoded)
        transform_list.extend([
            initial_placement.scaling,
            initial_placement.rotation,
            initial_placement.translation
        ])
    transform_list.extend([
        placement.scaling,
        placement.rotation,
        placement.translation
    ])
    
    logger.debug("traanform_list in configure_model %s" % repr(transform_list))
    
    # convert this list to a list of Placement instances, hopefully there's
    # only one
    
    placements = list( transformsToPlacements(transform_list ))
    
    configured_placement : Placement = Placement()
    if len(placements) > 0:
        configured_placement = placements[0]
    if len(placements) > 1:
        logger.warning("combination of transforms on import cannot be reduced to 1 placement")
        
        
    new_model.location = configured_placement.translation.data
    new_model.rotation_mode = "QUATERNION"
    new_model.rotation_quaternion = configured_placement.rotation.data
    new_model.scale = configured_placement.scaling.data
    
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
        
def encode_blender_placement( placement : Placement ) -> str:
    """
    encode the 3 values used in Blender object into a string that can be stored
    as a Blender custom property, and decoded back into the original values
    
    uses the repr function to encode
    """
    return repr(placement)
    

def decode_blender_transform( encoding : str ) -> Placement:
    """
    reverses the encoding performed by function encode_blender_transform
    """
    try:
        return eval( encoding )
    except Exception as exc:
        logger.error(f"unable to decode transform: {repr(encoding)}", exc)
        return Placement()
