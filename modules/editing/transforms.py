
from  typing import Optional, Tuple, Set, Any, Dict
from mathutils import Vector, Quaternion, Euler
from math import radians, degrees, log

import logging
logger = logging.getLogger("editing.transforms")

"""
modules for manipulations of IIIF transforms, expressed as ordered lists
of RotateTransform, ScaleTransform, and TranslateTransform, with transform
parameters expressed in IIIF axes

and Blender transforms expressed as (3,) tuple-like objects 
(Vector, Quaternion, Vector) : where the 0 element is the 'scale' transform
and the [2] element is the translate  transform

Geometrically the active operatation of a Blender transform , considered to be
operating on xyz coordinates of a point on an object is:
1. Apply scaling relative to origin
2. apply rotation with origin the fixed point
3. Apply translation
"""

ROTATE_TRANSFORM    = "RotateTransform"
SCALE_TRANSFORM     = "ScaleTransform"
TRANSLATE_TRANSFORM = "TranslateTransform"

BLENDER_EULER_ORDER = "YZX"

# this parameter commented out because it is never used in code
# but included as documentation
# IIIF_EULER_ORDER    = "ZYX" 

TINY_VALUE = 1.0e-6
AXIS_KEYS = ("x","y","z")

def iiif_to_blender_transform( iiif_transform : dict ) -> Tuple[str,Vector|Quaternion]:
    """
    argument in: a dict from the json encoding of a RotateTransform, TranslateTransform
    or ScaleTransform
    
    return: one of following
    ("RotateTransform", Quaternion )
    ("ScaleTransform" , Vector )
    ("TranslateTransform" , Vector )
    """
    transformType:str = iiif_transform["type"]
    default_value = (0.0,1.0)[transformType == SCALE_TRANSFORM]
    def coordinates( transform ):
        """
        Pulls out coordinates in x,y,z order, allowing for missing
        components that are filled in with default 0.0
        """
        for axis in AXIS_KEYS:
            yield float( transform.get(axis,default_value))
    iiif_vector = Vector(list(coordinates( iiif_transform )))
    
    
    if transformType == ROTATE_TRANSFORM:
        """
        the iiif_vector represents the angles in degrees, for ccw rotations about
        the intrinsic axea in XYZ order. That Euler rotation is equal to the rotation
        about the extrinsic axes in ZYX order, of the following rotation in Euler
        axes
        """
        blender_angles = (   radians(iiif_vector.x),
                            -radians(iiif_vector.z),
                             radians(iiif_vector.y))
                             
        
        quat = Euler( blender_angles, BLENDER_EULER_ORDER).to_quaternion()
        return (ROTATE_TRANSFORM, quat)
        
    elif transformType == SCALE_TRANSFORM:
        blender_scales = ( iiif_vector.x, iiif_vector.z, iiif_vector.y)
        return (SCALE_TRANSFORM, Vector(blender_scales))
        
    elif transformType == TRANSLATE_TRANSFORM:
        blender_components = ( iiif_vector.x, -iiif_vector.z, iiif_vector.y)
        return (TRANSLATE_TRANSFORM, Vector(blender_components))
        
    raise ValueError(f"transformType : {transformType}")
    
    
def blender_to_iiif_transform( blender_transform : Tuple[str, Vector|Quaternion])  -> Dict[str,Any]:
    """
    """
    retVal : Dict[str,Any] = {}
    transformType = blender_transform[0]
    if transformType == ROTATE_TRANSFORM:
        if not isinstance( blender_transform[1], Quaternion):
            raise Exception(f"blender_to_iiif_transform: invalid transform data for {transformType}")
        quat: Quaternion = blender_transform[1]
        euler:Euler = quat.to_euler(BLENDER_EULER_ORDER)
        
        iiif_angles_radians=(euler.x, euler.z, -euler.y)
        retVal["type"] = ROTATE_TRANSFORM
        for i in range(3):
            if abs( iiif_angles_radians[i] ) > TINY_VALUE:
                retVal[ AXIS_KEYS[i]]=degrees(iiif_angles_radians[i])
    
    else:
        if not isinstance( blender_transform[1], Vector):
            raise Exception(f"blender_to_iiif_transform: invalid transform data for {transformType}")
        blender_vec : Vector =  blender_transform[1]  
        iiif_components = Vector((blender_vec.x,blender_vec.z,-blender_vec.y))
                    
        if transformType == TRANSLATE_TRANSFORM:
            retVal["type"] = TRANSLATE_TRANSFORM
            for i in range(3):
                if abs( iiif_components[i] ) > TINY_VALUE:
                    retVal[ AXIS_KEYS[i]]=iiif_components[i]

        elif transformType == SCALE_TRANSFORM:
            retVal["type"] = SCALE_TRANSFORM 
            for i in range(3):
                if iiif_components[i] <= 0.0 or log( iiif_components[i] ) > TINY_VALUE:
                    retVal[ AXIS_KEYS[i]]=iiif_components[i]
    return retVal


def decompose_scaling_vector( vec: Vector ) -> Tuple[int,float,Optional[Quaternion], Optional[Vector]]:
    """
    element 0 : +1 or -1
    elemrnt 1 : a uniform scaling  >= 0 . If this element = 0, it it makes all further calculations 
                irrelevant, the model is reduced to a point. This will only return when all
                the components of vec are 0.0
    element 2 : This is a rotation by 180 degrees around an axis to allowing to negate
                two of the scaling components.
    element 3 : if present, this is nonuniform scaling by non-negative values.
    """
    neg_scaled_axes :Set[int] = set()
    zero_scaled_axes:Set[int] = set()
    pos_scaled_axes :Set[int] = set()
    all_axes        :Set[int] = set(range(3))
    
    for i in range(3):
        if vec[i] == 0.0:
            zero_scaled_axes.add(i)
        elif vec[i] < 0.0:
            neg_scaled_axes.add(i)
        else:
            pos_scaled_axes.add(i)
            
    parity : int = +1
    uniform_scale : float = 0.0
    rotation : Optional[Quaternion] = None
    nonuniform_scale : Optional[Vector] = Vector()
    
    if  len(zero_scaled_axes) != 3:
        if len( neg_scaled_axes ) in (1,2):
            if len(neg_scaled_axes) == 1:
                rotation_axis_index = list(neg_scaled_axes)[0]
            else:
                rotation_axis_index = list(all_axes - neg_scaled_axes)[0]
            rotation_axis = Vector()
            rotation_axis[rotation_axis_index] = 1.0
            rotation = Quaternion( rotation_axis, radians(180))
            
        if len( neg_scaled_axes ) in (1,3):
            parity = -1
            
        abs_vec = Vector( [abs(x) for x in vec])
        for i in range(1,3):
            if abs_vec[i] != abs_vec[0]:
                uniform_scale = 1.0
                nonuniform_scale = abs_vec
            else:
                uniform_scale = abs_vec[0]
    return (parity, uniform_scale, rotation, nonuniform_scale)
        
    
    
        
        
    
