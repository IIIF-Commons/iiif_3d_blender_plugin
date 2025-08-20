from __future__ import annotations
from  typing import  Any, Dict, List,  Callable, Generator, Iterable
from mathutils import Vector, Quaternion, Euler
from math import radians, degrees,   pi


# Dev Note: 9 Aug 2025
# this import of annotations will allow the type hint system
# to understand the forward references in the definition of the



import logging
logger = logging.getLogger("editing.transforms")


ROTATE_TRANSFORM    = "RotateTransform"
SCALE_TRANSFORM     = "ScaleTransform"
TRANSLATE_TRANSFORM = "TranslateTransform"
POINT_SELECTOR      = "PointSelector"



class Transform:
        
    def inverse(self) -> Transform:
        raise NotImplementedError()
        
    def isIdentity(self) -> bool :
        raise NotImplementedError()
        
    def applyToCoordinate(self, coord : Vector ) -> Vector :
        raise NotImplementedError()
        
    def applyToPlacement(self,placement:Placement) -> bool:
        raise NotImplementedError() 
        
    @staticmethod
    def from_iiif_dict( iiif_data : dict )  -> Transform:
        try:
            ttype : str = iiif_data.get("type", "")
            handler = import_transform_callables[ttype]
        except KeyError as exc:
            raise Exception("unsupported iiif transform type: %s" % str(exc))
        return handler(iiif_data)
        
    def to_iiif_dict( self )  -> dict :
        raise NotImplementedError() 

XYZ : List[str] = ["x" , "y" , "z"]

class Translation(Transform):
    def __init__(self, vec : Vector):
        self.data : Vector = vec

    def applyToPlacement(self,placement:Placement) -> bool:        
        placement.translation = Translation( placement.translation.data + self.data )
        return True
            
    def inverse(self) -> Translation:
        return Translation( -1 * self.data )
        
    def isIdentity(self) -> bool :
        for val in self.data.to_tuple():
            if val != 0.0:
                return False
        return True

    def applyToCoordinate(self, coord : Vector ) -> Vector :
        return coord + self.data
    
    @staticmethod
    def from_iiif_dict( iiif_data : dict )  -> Transform:
        # 1. get the axes value, convention is that omitted axes are 0
        iv = [ float(iiif_data.get(axis, 0.0)) for axis in XYZ]
        
        # Given the 
        # Blender <- IIIF axes mapping: X <- X ; Y <- -Z ; Z <- Y
        bv = [iv[0], -iv[2], iv[1]]
        
        vec = Vector(bv)
        return Translation(vec)
        
    def to_iiif_dict( self ) -> dict:
        
        # 1. convert back to iiif axes under 
        # iiif <- Blender axes mapping X <- X. Y <- Z; Z <- -Y
        iv = [self.data.x, self.data.z, -self.data.y]
        
        # express as dictionary
        retVal : Dict[str,Any] = {"type": TRANSLATE_TRANSFORM}
        for label, v in zip( XYZ, iv):
            if v != 0.0:
                retVal[label] = v
        return retVal

    def __repr__(self):
        return "Translation(%r)" % repr(self.data)   
                
class Rotation(Transform):
    def __init__(self, quat : Quaternion ):
        self.data : Quaternion = quat
        
    def commuteWithTranslation( self, t : Translation ) -> Translation:
        return  Translation(self.data @ t.data )
        
    
    def commuteWithRotation( self, r : Rotation ) -> Rotation:
        return  Rotation( self.data @ r.data @ self.data.inverted() )
        
    def isIdentity(self) -> bool :
        return self.data.angle == 0.0
        
    def inverse(self) -> Rotation:
        return Rotation( self.data.inverted() )

    def applyToCoordinate(self, coord : Vector ) -> Vector :
        return self.data @ coord
        
    def applyToPlacement(self,placement:Placement) -> bool:        
        placement.translation = self.commuteWithTranslation(placement.translation)
        placement.rotation  = Rotation( self.data @ placement.rotation.data )
        return True
        
    @staticmethod
    def from_iiif_dict( iiif_data : dict )  -> Transform:
        # 1. get the axes value, convention is that omitted axes are 0
        iv = [ float(iiif_data.get(axis, 0.0)) for axis in XYZ]
        
        # iiif_values are rotations in degrees, representing Euler rotation in
        # XYZ intrinsic order, which ZYX in extrinsic order. Given the 
        # Blender <- IIIF axes mapping: X <- X ; Y <- -Z ; Z <- Y
        # also perform the conversion to radians
        # these will then denote a Euler rotation in YZX extrinsic order
        bv = [radians(d) for d in [iv[0], -iv[2], iv[1]]]
        
        quat:Quaternion = Euler(bv, "YZX").to_quaternion()
        return Rotation(quat)
        
    def to_iiif_dict( self ) -> dict:
        
        # 1. convert to Euler rotation in YZX extrinsic order
        euler:Euler = self.data.to_euler("YZX")
        
        # 2. convert back to iiif axes under 
        # iiif <- Blender axes mapping X <- X. Y <- Z; Z <- -Y
        iv = [degrees(r) for r in [euler.x, euler.z, -euler.y]]
        
        # express as dictionary
        retVal : Dict[str,Any] = {"type": ROTATE_TRANSFORM}
        for label, v in zip( XYZ, iv):
            if v != 0.0:
                retVal[label] = v
        return retVal

    def __repr__(self):
        return "Rotation(%r)" % repr(self.data)    
    
class Scaling(Transform):
    def __init__(self, vec: Vector ):
        self.data : Vector = vec
        
    def isIdentity(self) :
        for s in self.data.to_tuple():
            if s != 1.0:
                return False
        return True
        
    def commuteWithRotation( self, r: Rotation) -> Rotation:
        if (r.isIdentity() or self.isUniform()):
            rotationPart:Rotation = self.rotationComponent()
            return rotationPart.commuteWithRotation(r)
        else:
            raise NotImplementedError()
           
    def commuteWithTranslation( self, t : Translation ) -> Translation:
        return Translation( self.data * t.data )
        

    def isUniform(self) -> bool :
        """
        returns true only if all components of scaling have same absolute values
        The significance of this is that if the scaling is not uniform, then the
        commutator with a non-zero rotation cannot be expresses as a Rotation, Scaling,
        or Translation
        """
        s = abs(self.data[0])
        for i in range(1,3):
            if abs(self.data[i]) != s:
                return False
        else:
            return True
            
    # developer note: 11 Aug 2025 : As this code has been developed the need
    # for an explicit calculation has disappeared; as the commutation with translation
    # is done explicitly with the scale data, while the commutation with rotation
    # does not depend on the value of parity.
    def parity(self) -> int :
        """
        returns -1 if the scaling transform includes a reflection in 1 axis
        or all axes.
        """
        acc = +1
        for i in range(3):
            if self.data[i] < 0:
                acc *= -1
        return acc
        
    def rotationComponent(self) -> Rotation :
        pos_axes = list()
        neg_axes = list()
        for i in range(3):
            if self.data[i] < 0:
                neg_axes.append(i)
            else:
                pos_axes.append(i)
        if len(pos_axes) in (0,3):
            return Rotation(Quaternion()) # the identity, zero rotation

        rotation_axis : List[float]= [0.0,0.0,0.0]
        if len(pos_axes) == 1:
            rotation_axis[pos_axes[0]] = 1.0
        else:
            rotation_axis[neg_axes[0]] = 1.0
        return Rotation(Quaternion( rotation_axis, pi) )

    def inverse(self) -> Scaling:        
        try:
            return  Scaling( Vector(list(map( lambda x : 1.0/x, self.data.to_tuple() ))))
        except ZeroDivisionError:
            raise
            
    def applyToPlacement(self,placement:Placement) -> bool: 
        # following is the test of whether this scale transformation
        # can be commuted with the previous Rotation
        if self.isUniform() or placement.rotation.isIdentity():            
            placement.translation = self.commuteWithTranslation(placement.translation)
            placement.rotation = self.commuteWithRotation(placement.rotation)
            placement.scaling = Scaling( placement.scaling.data * self.data )
            return True
        return False

    @staticmethod
    def from_iiif_dict( iiif_data : dict )  -> Scaling:
        # 1. get the axes value, convention is that omitted axes are 1
        iv = [ float(iiif_data.get(axis, 1.0)) for axis in XYZ]
        
        # Given the 
        # Blender <- IIIF axes mapping: X <- X ; Y <- -Z ; Z <- Y
        bv = [iv[0], iv[2], iv[1]]
        
        vec = Vector(bv)
        return Scaling(vec)
        
    def to_iiif_dict( self ) -> dict:
        
        # 1. convert back to iiif axes under 
        # iiif <- Blender axes mapping X <- X. Y <- Z; Z <- -Y
        iv = [self.data.x, self.data.z,self.data.y]
        
        # express as dictionary
        retVal : Dict[str,Any] = {"type": SCALE_TRANSFORM}
        for label, v in zip( XYZ, iv):
            if v != 1.0:
                retVal[label] = v
        return retVal
        
    def __repr__(self):
        return "Scaling(%r)" % repr(self.data)
        

class Placement:
    def __init__(self, scaling=None, rotation=None, translation=None):
        self.scaling :  Scaling = scaling or Scaling(Vector((1,1,1)))
        self.rotation : Rotation = rotation or Rotation(Quaternion((1,0,0),0.0))
        self.translation : Translation = translation or Translation(Vector((0,0,0)))
        
    def isIdentity(self) -> bool :
        return  self.scaling.isIdentity() and \
                self.rotation.isIdentity() and \
                self.translation.isIdentity()
                
    def to_transform_list(self) -> List[Transform]:
        return [self.scaling, self.rotation, self.translation]

    def __repr__(self):
        return "Placement( %r, %r, %r)" % (self.scaling, self.rotation, self.translation)
              
def transformsToPlacements( transforms:Iterable[Transform]) -> Generator[Placement]:
    accum : Placement = Placement()
    for transform in transforms:
        if not transform.isIdentity():
            if transform.applyToPlacement(accum):
                continue
            else:
                yield accum
                accum = Placement()
                transform.applyToPlacement(accum)
    if not accum.isIdentity():
        yield accum
            


import_transform_callables : Dict[str,Callable] = {
    ROTATE_TRANSFORM :    Rotation.from_iiif_dict,
    TRANSLATE_TRANSFORM : Translation.from_iiif_dict,
    POINT_SELECTOR      : Translation.from_iiif_dict,
    SCALE_TRANSFORM :     Scaling.from_iiif_dict,
    
}        
