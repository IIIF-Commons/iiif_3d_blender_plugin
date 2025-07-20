import json
from bpy.types import Object
import typing
from mathutils import Vector

from ..utils.coordinates import Coordinates

import logging
logger = logging.getLogger("iiif.models")
logger.setLevel(logging.INFO)


def configure_model(    new_model : Object,
                        model_url : str = "",
                        *,                                                  
                        resource_data : typing.Optional[dict] = None,
                        placement_data : typing.Optional[dict] = None) -> None :
    
    def choose_id():
        if model_url: 
            return model_url
        if resource_data and "id" in resource_data:
            return resource_data["id"]
        raise ValueError("no valud id provided for condigure_model")
        
    model_id = choose_id()
    data =  resource_data or _initial_data()
    
    data["id"] = model_id,
    new_model["iiif_id"] = model_id
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


def _initial_data() -> dict :
    return {
        "id" : None,
        "type": "Model"
    }