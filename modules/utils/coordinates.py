from mathutils import Vector, Euler, Quaternion
import math
import typing

class Coordinates:
    """Helper class for converting between IIIF and Blender coordinates

    This implementation is intended to be compatible with the conversion
    that is by default carried out when a glTF model is imported with a call
    such as:
    bpy.ops.import_scene.gltf(filepath=filepath)

    The conversion performed internally -- that is, in the coordinates of the
    points of the mesh as they are stored in Blender data, can be described by the
    relation between the XB, YB, ZB vectors that defined the Blender coordinate system
    and the XI, YI, ZI vectors which define the IIIF coordinate system in IIIF

    Those relations are:
    XI =  XB : # the X axis vector is the same in both coordinate systems
    YI =  ZB : # this is the vector which conventionally points UP in each system
    ZI = -YB : # this is the vectors which points "forward"  in the IIIF (and glTF)
               # usage of the term forward, for a humanoid model such as an astronaut
               # this is the conventoional front of the model, the direction in which
               # the astronaut is looking.
               # Blender however, uses a different semantics of the term forward, in
               # Blender "forward" means the direction in which a defaulte camera or
               # UI viewpoint is looking, in this Blender usage "forward" is +YB

    From these relations can derive the relations between xi,yi,zi coordinates in
    IIIF system with xb,yb,zb coordinates in

    in following, dot(A,B) denoted the conventional vector dot-product between
    two 3D vectors A,B

    For a vector P interpreted as location of a point in space with Coordinates
    (xi,yi,zi) in IIIF system and (xb,yb,zb) in Blender

    xi = dot(P,XI) = dot(P,XB) =   xb
    yi = dot(P,YI) = dot(P,ZB) =   zb
    zi = dot(P,ZI) = dot(P,-YB) = -yb

    or in reverse
    xb =  i
    yb = -zi
    zb =  yi

    During the import of a IIIF manifest a typical calculation will be to
    convert the (xi,yi,zi) coordinates of a PointSelectore resource into
    the (xb,yb,zb) coordinated of where to "locate" a mesh in Blender scene.

    This is the conversion implemented by function iiif_position_to_blender_vector
    """

    @staticmethod
    def iiif_position_to_blender_vector(
        iiif_coords: tuple[float, float, float]
    ) -> Vector:
        return Vector((iiif_coords[0], -iiif_coords[2], iiif_coords[1]))
        
    @staticmethod
    def blender_vector_to_iiif_position(
        vec: Vector
    ) -> tuple[float, float, float]:
        return (vec[0], vec[2], -vec[1] )

    @staticmethod
    def model_transform_angles_to_blender_euler(
        angles: tuple[float, float, float],
    ) -> Euler:
        """
        Returrns a Blender Euler instance that gives same geometric rotation as an
        IIIF RotateTransform

        angles argument: a sequence of (at least 3) numbers; the values of the
        "x","y","z" properties of the Presentation 4 RotateTransform class. These
        values are counterclocwise rotations about coordinate axes in degrees.

        RotateTransform rotation is interpreted as Euler Angles rotations about
        intrinsic axes in XYZ order. These XYZ axes are as defined in IIIF coordinate
        system.

        This function returns an instance of mathutils.Euler
        see https://docs.blender.org/api/current/mathutils.html#mathutils.Euler

        In the constructor for Euler, the angle values are in radians, and the
        arguments are given in XYZ order, referring to the Blender X,Y,Z axes.

        The Blender Euler class allows several options for the order if axes rotation
        in defining the effect of rotations. In conversions of IIIF RotateTransform the
        natural Euler ordering for Blender will be "YZX" because of:
                -- the relation between axes in IIIF to Blender systems
                -- the shift from intrinic axis rotation to extrinsic

        The Euler instance returned from this function is what should be entered as the
        rotate property of an import gltf/glb model to give the effect of a
        RotateTransform applied to an IIIF model.
        """
        y_blender_angle = -math.radians(angles[2])
        z_blender_angle = math.radians(angles[1])
        x_blender_angle = math.radians(angles[0])
        order = "YZX"

        blender_axes = (x_blender_angle, y_blender_angle, z_blender_angle)
        return Euler(blender_axes, order)

    @staticmethod
    def blender_rotation_to_model_transform_angles(
        rotation: Euler | Quaternion
    ) -> tuple[float, float, float]:
        euler_rotation = Coordinates.coerce_to_euler(rotation,"YZX")
        return (
            math.degrees( euler_rotation.x),
            math.degrees( euler_rotation.z),
            math.degrees(-euler_rotation.y)
        )
        

    @staticmethod
    def coerce_to_euler( rotation : Euler | Quaternion , order:str ) -> Euler:
        if isinstance(rotation, Euler) and rotation.order != order :
            return rotation.to_quaternion().to_euler(order)
        elif isinstance(rotation, Quaternion):
            return rotation.to_euler(order)
        return rotation
        
    @staticmethod
    def camera_transform_angles_to_blender_euler(
        angles: tuple[float, float, float],
    ) -> Euler:
        """
        Returns a Blender Euler instance that applied to a Blender camera results
        in the same camera orientation as a RotateTransform applied to a IIIF Camera.

        This calculation differs from the calculation for model_transform_angles_to_blender_euler_angle
        because the initial state of a Blender camera is pointing downward, along
        the -Z Blender axis, while the initial state of an IIIF camera is points
        in the +Z IIIF axes, which is the -Y Blender axis

        The calculation below is the result of first rotating a Blender camera by
        90 degrees ccw about the Blender X axis, then applying the model transform
        as would be returned by model_transform_angles_to_blender_euler_angle

        angles argument: a sequence of (at least 3) numbers; the values of the
        "x","y","z" properties of the Presentation 4 RotateTransform class. These
        values are counterclocwise rotations about coordinate axes in degrees.

        RotateTransform rotation is interpreted as Euler Angles rotations about
        intrinsic axes in XYZ order. These XYZ axes are as defined in IIIF coordinate
        system.

        This function returns an instance of mathutils.Euler
        see https://docs.blender.org/api/current/mathutils.html#mathutils.Euler

        In the constructor for Euler, the angle values are in radians, and the
        arguments are given in XYZ order, referring to the Blender X,Y,Z axes.



        The Euler instance returned from this function is what should be entered as the
        rotate property of an new Blender camera to give the effect of a
        RotateTransform applied to an IIIF camera.
        """
        x_blender_angle = math.radians(angles[0] + 90.0)
        y_blender_angle = math.radians(angles[1])
        z_blender_angle = math.radians(angles[2])

        blender_axes = (x_blender_angle, y_blender_angle, z_blender_angle)
        order = "ZYX"
        return Euler(blender_axes, order)

    @staticmethod
    def blender_rotation_to_camera_transform_angles(
        rotation: Euler | Quaternion 
    ) -> tuple[float, float, float]:
        euler_rotation=Coordinates.coerce_to_euler( rotation, "ZYX")
        return (
            math.degrees(euler_rotation.x) - 90.0,
            math.degrees(euler_rotation.y),
            math.degrees(euler_rotation.z)
        )
        
    @staticmethod
    def iiif_to_blender(iiif_coords):
        return (iiif_coords[0], iiif_coords[1], iiif_coords[2])

    @staticmethod
    def blender_to_iiif(blender_coords):
        return (blender_coords[0], blender_coords[1], blender_coords[2])

    @staticmethod
    def get_iiif_coords_from_pointselector(selector: dict) -> Vector:
        return Vector(
            (
                float(selector.get("x", 0)),
                float(selector.get("y", 0)),
                float(selector.get("z", 0)),
            )
        )

    @staticmethod
    def convert_to_vector(coords: dict | tuple[float, float, float] | Vector) -> Vector:
        if isinstance(coords, dict):
            return Coordinates.get_iiif_coords_from_pointselector(coords)
        elif type(coords) is type( () ) and len(coords) == 3:            
            return Vector( typing.cast( tuple, coords ) )
        else:
            return typing.cast(Vector, coords)
