import json
import math
from bpy.types import Object
import typing

from . import generate_id
from ..utils.coordinates import Coordinates
from ..utils.json_patterns import force_as_singleton

import logging
logger = logging.getLogger("iiif.cameras")
logger.setLevel(logging.INFO)

def configure_camera(   new_camera : Object,
                        *,                                                  
                        resource_data : typing.Optional[dict] = None,
                        placement_data : typing.Optional[dict] = None) -> None :
    data:dict = resource_data or _initial_data()
    data["id"] = data.get("id", None) or generate_id("perspectivecamera")

    if "fieldOfView" in data:
        foV = force_as_singleton(data["fieldOfView"])
        if foV is not None: 
            new_camera.data.angle_y = math.radians( float( foV )) # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
            del data["fieldOfView"]
        
    
    new_camera["iiif_type"] = "PerspectiveCamera"
    new_camera["iiif_json"] = json.dumps(data)
    
    if placement_data is not None:
        if placement_data["location"] is not None:
            new_camera.location = Coordinates.iiif_position_to_blender_vector( placement_data["location"] )
            
        if placement_data["rotation"] is not None:
            euler = Coordinates.camera_transform_angles_to_blender_euler( placement_data["rotation"] )
            new_camera.rotation_mode = euler.order
            new_camera.rotation_euler = euler

    # set the "units" for the camera field to be "FOV", this 
    # gives a more useful UI for adjusting the focal length of the
    # camera
    new_camera.data.lens_unit='FOV' # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]

    # This will cause the value displayed in UI in Field Of View to
    # be the vertical angle in degrees,
    new_camera.data.sensor_fit = 'VERTICAL' # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    return


def _initial_data() -> dict :
    return {
        "id" : None,
        "type": "PerspectiveCamera"
    }