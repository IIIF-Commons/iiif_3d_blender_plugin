import json
import math
from bpy.types import Object
from mathutils import Quaternion

from typing import List

from . import generate_id
from ..utils.json_patterns import force_as_singleton
from ..editing.transforms import Transform, Rotation, Placement, transformsToPlacements

import logging
logger = logging.getLogger("iiif.cameras")
logger.setLevel(logging.INFO)

def configure_camera(   new_camera : Object,                                                 
                        resource_data : dict,
                        placement : Placement ) -> None:
    if len(resource_data) == 0:
        resource_data = _initial_data()
        resource_data["id"]=generate_id(resource_data["type"])
        
    if "type" not in resource_data:
        logger.warn("camera type not specified")

    if "fieldOfView" in resource_data:
        foV = force_as_singleton(resource_data["fieldOfView"])
        if foV is not None: 
            new_camera.data.angle_y = math.radians( float( foV )) # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
            del resource_data["fieldOfView"]
        
    
    new_camera["iiif_type"] = resource_data["type"]
    new_camera["iiif_json"] = json.dumps(resource_data)
    
    new_camera.location = placement.translation.data
     
    initial_camera_rotation : List[Transform]  = [ Rotation(Quaternion( (1.0,0.0,0.0), math.pi/2)) ]
    full_camera_transforms : List[Transform]   =  initial_camera_rotation   + placement.to_transform_list()

    full_camera_placement = list( transformsToPlacements(   full_camera_transforms ) )                           

    new_camera.rotation_mode = "QUATERNION"
    new_camera.rotation_quaternion = full_camera_placement[0].rotation.data # pyright: ignore[reportAttributeAccessIssue]

    return


def _initial_data() -> dict :
    return {
        "id" : None,
        "type": "PerspectiveCamera"
    }