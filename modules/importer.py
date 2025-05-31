import datetime
import json
import os
import urllib.request
from typing import Set

import bpy
from bpy.props import StringProperty
from bpy.types import Collection, Context, Object, Operator
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector

from .metadata import IIIFMetadata
from .utils.color import hex_to_rgba
from .utils.coordinates import Coordinates
from .utils.json_patterns import (
    force_as_object,
    force_as_singleton,
    force_as_list,
    axes_named_values,
)

from .utils.blender_setup import configure_camera

import math

import logging

logger = logging.getLogger("Import")


class ImportIIIF3DManifest(Operator, ImportHelper):
    """Import IIIF 3D Manifest"""

    bl_idname = "import_scene.iiif_manifest"
    bl_label = "Import IIIF 3D Manifest"

    filename_ext = ".json"
    filter_glob: StringProperty(  # type: ignore
        default="*.json", options={"HIDDEN"}
    )
    filepath: StringProperty(  # type: ignore
        name="File Path",
        description="Path to the input file",
        maxlen=1024,
        subtype="FILE_PATH",
    )

    manifest_data: dict

    def download_model(self, url: str) -> str:
        """Download the model file from the given URL"""
        temp_dir = bpy.app.tempdir
        time_string = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        model_name = os.path.basename(url)
        model_extension = os.path.splitext(model_name)[1]
        temp_file = os.path.join(
            temp_dir, f"temp_model_{time_string}_{model_name}{model_extension}"
        )

        try:
            self.report({"DEBUG"}, f"Downloading model from {url} to {temp_file}")
            urllib.request.urlretrieve(url, temp_file)
            self.report({"DEBUG"}, f"Successfully downloaded model to {temp_file}")
            return temp_file
        except Exception as e:
            self.report({"ERROR"}, f"Error downloading model: {str(e)}")
            raise

    def import_model(self, filepath: str) -> None:
        """Import the model file using the appropriate Blender importer"""
        file_ext = os.path.splitext(filepath)[1].lower()

        if file_ext == ".glb" or file_ext == ".gltf":
            bpy.ops.import_scene.gltf(filepath=filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def get_annotation_bounds_center(self, annotation_id: str) -> Vector:
        """Calculate the center point of all objects belonging to an annotation"""
        annotation_objects = [
            obj for obj in bpy.data.objects if obj.get("annotation_id") == annotation_id
        ]

        if not annotation_objects:
            return Vector((0, 0, 0))

        # Calculate combined bounds
        min_x = min_y = min_z = float("inf")
        max_x = max_y = max_z = float("-inf")

        for obj in annotation_objects:
            # Get world space corners
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ Vector(corner)
                min_x = min(min_x, world_corner.x)
                min_y = min(min_y, world_corner.y)
                min_z = min(min_z, world_corner.z)
                max_x = max(max_x, world_corner.x)
                max_y = max(max_y, world_corner.y)
                max_z = max(max_z, world_corner.z)

        # Calculate center
        center = Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2))

        return center

    def create_camera(self, camera_data: dict, parent_collection: Collection) -> Object:
        """Create a camera with the specified parameters"""
        # Create camera data block
        cam_data = bpy.data.cameras.new(
            name=camera_data.get("label", {}).get("en", ["Camera"])[0]
        )

        # Create camera object
        cam_obj = bpy.data.objects.new(
            camera_data.get("label", {}).get("en", ["Camera"])[0], cam_data
        )

        # Link camera to collection
        parent_collection.objects.link(cam_obj)

        # Set camera type (perspective is default in Blender)
        if camera_data.get("type") == "PerspectiveCamera":
            cam_data.type = "PERSP"
            """
            field of view review
            In draft 3D API https://github.com/IIIF/3d/blob/main/temp-draft-4.md
            the fieldOfView property on PerspectiveCamera is the 
            angular size of the viewport in the vertical -- meaning the top-to-bottom
            dimension of the 2 rendering. Angle is in degrees,
            The default value is client-dependent
            Here the default is defined as 53 (degrees); the angular size of a 
            6 ft person viewed from 6 ft away.
            """
            foV_default = 53.0
            foV = force_as_singleton(camera_data.get("fieldOfView", foV_default))
            if foV is not None:
                try:
                    foV = float(foV)
                except (TypeError, ValueError):
                    logger.error(
                        "fieldOfView value %r cannot be cast to number" % (foV,)
                    )
            foV = foV or foV_default
            cam_obj.data.angle_y = math.radians(foV)  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]

            # this assignment just directs the Blender UI to show the
            # Field Of View vertical angle value
            cam_obj.data.sensor_fit = "VERTICAL"  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        return cam_obj

    def position_camera(self, cam_obj: Object, target_data: dict) -> None:
        """Position the camera based on target data"""
        # Get camera position from selector
        selector = force_as_singleton(
            target_data.get("type") in {"SpecificResource"}
            and target_data.get("selector", None)
        )

        if selector and selector.get("type") == "PointSelector":
            iiif_coords = axes_named_values(selector)
        else:
            iiif_coords = (0.0, 0.0, 0.0)
        cam_obj.location = Coordinates.iiif_position_to_blender_vector(iiif_coords)

    def set_camera_target(self, cam_obj: Object, look_at_data: dict) -> None:
        """Set the camera's look-at target"""
        if look_at_data.get("type") == "PointSelector":
            target_location = Coordinates.iiif_position_to_blender_vector(
                axes_named_values(look_at_data)
            )
            logger.info("lookAt PointSelector: %r" % target_location)
            self.point_camera_at_target(cam_obj, target_location)
        elif look_at_data.get("type") == "Annotation":
            target_id = look_at_data.get("id")
            if target_id:
                center = self.get_annotation_bounds_center(target_id)
                logger.info("lookAt Annotation: %r" % center)
                self.point_camera_at_target(cam_obj, center)

    def point_camera_at_target(self, cam_obj: Object, target_location: Vector) -> None:
        """
        Point the camera at a specific location
        target_location is to be a Vector instance in Blender coordinate system
        """
        # Convert target location if it's not already a Vector
        direction = target_location - cam_obj.location
        logger.info(
            "point_camera_at_target from %r to %r" % (cam_obj.location, target_location)
        )
        rot_quat = direction.to_track_quat("-Z", "Y")
        logger.info("lookAt direction: %r as rotation %r" % (direction, rot_quat))
        cam_obj.rotation_mode = "QUATERNION"
        cam_obj.rotation_quaternion = rot_quat

    def create_or_get_collection(
        self, name: str, parent: Collection | None = None
    ) -> Collection:
        """Create a new collection or get existing one"""
        if name in bpy.data.collections:
            collection = bpy.data.collections[name]
        else:
            collection = bpy.data.collections.new(name)
            if parent:
                parent.children.link(collection)
            else:
                bpy.context.scene.collection.children.link(collection)

        return collection

    def get_iiif_id_or_label(self, data: dict) -> str:
        """Get the IIIF ID or label from the given data"""
        iiif_id = data.get("id", "Unnamed ID")
        label = data.get("label", {}).get("en", [iiif_id])[0]
        return label

    def process_annotation_light(
        self, annotation_data: dict, parent_collection: Collection
    ) -> None:
        """Process and create lights from annotation data"""
        body = annotation_data.get("body", {})
        light_type = body.get("type")
        light_name = body.get("label", {}).get("en", ["Light"])[0]

        # Create light data
        light_data = bpy.data.lights.new(
            name=light_name, type=self.get_blender_light_type(light_type)
        )
        light_obj = bpy.data.objects.new(name=light_name, object_data=light_data)

        # Link to collection
        parent_collection.objects.link(light_obj)

        # Store original IDs
        light_obj["original_annotation_id"] = annotation_data.get("id")
        light_obj["original_body_id"] = body.get("id")

        # Set light properties
        if "target" in annotation_data:
            light_obj["original_target"] = json.dumps(annotation_data["target"])

        # Store lookAt data if present
        if "lookAt" in body:
            light_obj["original_lookAt"] = json.dumps(body["lookAt"])
            look_at_data = body["lookAt"]
            if look_at_data.get("type") == "Annotation":
                # Store the annotation ID to look at
                light_obj["lookAt_annotation_id"] = look_at_data.get("id", "")

        if "color" in body:
            light_data.color = hex_to_rgba(body["color"])[:3]  # Exclude alpha
            light_obj["original_color"] = body["color"]

        if "intensity" in body:
            intensity_data = body["intensity"]
            if isinstance(intensity_data, dict):
                light_data.energy = float(intensity_data.get("value", 1.0))
                light_obj["original_intensity"] = json.dumps(intensity_data)

        # Store metadata
        metadata = IIIFMetadata(light_obj)
        metadata.store_annotation(annotation_data)

    def get_blender_light_type(self, iiif_light_type: str) -> str:
        """Convert IIIF light type to Blender light type"""
        light_type_map = {
            "AmbientLight": "POINT",  # Blender doesn't have ambient lights, approximate with point
            "DirectionalLight": "SUN",
        }
        return light_type_map.get(iiif_light_type, "POINT")


    def process_annotation(
        self, annotation_data: dict, parent_collection: Collection
    ) -> None:
        target_data =  force_as_object(
            force_as_singleton(annotation_data.get("target", None)), default_type="Scene"
        )
        if target_data:
            del annotation_data["target"]
        
        body_data = force_as_object(
            force_as_singleton(annotation_data.get("body", None)), default_type="Model"
        )
        if body_data:
            del annotation_data["body"]
        else: 
            bodyValue = force_as_singleton(annotation_data.get("bodyValue", None))
            if type(bodyValue) is str:
                body_data = {"type": "TextualBody", "value": bodyValue}
                del annotation_data["bodyValue"]
            else:
                logger.warning(
                    "annotation %s has no body property" % annotation_data["id"]
                )
                
        anno_collection = self.create_or_get_collection(annotation_data["id"], parent_collection)
        anno_collection["iiif_id"]   = annotation_data["id"]
        anno_collection["iiif_type"] = annotation_data["type"]
        anno_collection["iiif_json"] = json.dumps(annotation_data)
        
        bodyObj = self.body_to_object(body_data, target_data, anno_collection )
        return

    def body_to_object(self, body_data : dict, target_data: dict, anno_collection:Collection) -> bpy.types.Object:
        """
        body is the  python dictionry obtained by unpacking hte json value of the body property.
        type of the outer layer of th dictionary may be SpecificResource, or may
        be Model, PerspectiveCamera
        
        The action of this function will be to create the Blender object, locate and
        orient the blender object; configure the Blender object via the properties in the
        body (or, as necesssary, SpecificResource.source). The created Blender object is returned
        
        returns a tuple of the dict obtained from the body or source, and the object itself
        These will contain information necessary to constr
        """     
        # placement_data is a dictionary whose entries will be filled with 
        # values from target and body, if either or both are SpecificResources   
        placement_data = {
        "location" : None,
        "rotation" : None,
        "scale"    : None
        }
        
        self.update_placement_from_target(target_data, placement_data)
        if body_data["type"] == "SpecificResource":
            resource_data = force_as_object(
                force_as_singleton(body_data.get("source", None)), default_type="Model"
            )
            self.update_placement_from_body(body_data, placement_data)
        else:
            resource_data = body_data
        bodyObj = self.resource_data_to_object(resource_data, placement_data, anno_collection)
        return bodyObj
        
    def resource_data_to_object(self, resource_data, placement_data, anno_collection):
        resource_type = resource_data["type"]
        if resource_type == "Model":
            return self.resource_data_to_model(resource_data, placement_data, anno_collection)
        elif resource_type in ("PerspectiveCamera",):
            return self.resource_data_to_camera(resource_data, placement_data, anno_collection)
        else:
            logger.warning("Resource type %s not supported for annotation body" % resource_type)
        return None

    def resource_data_to_model(self, resource_data, placement_data, anno_collection):
        """
        download, create, and configure model object
        """
        model_id = resource_data.get("id", None)
        temp_file = self.download_model(model_id)
        self.import_model(temp_file)
        new_model = bpy.context.active_object
        
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
            
        # ensure the model is in the anno_collection; this is
        # required for IIIF Manifest export
        for col in new_model.users_collection:
            col.objects.unlink(new_model)
        anno_collection.objects.link(new_model)
        return new_model
        
    def resource_data_to_camera(self, resource_data, placement_data, anno_collection):
        """
        download, create, and configure camera object
        """

        try:
            # developer note: eventually an initial location, rotation, scale can be
            # set here
            retCode = bpy.ops.object.camera_add()
            logger.info("obj.camera_add %r" % (retCode,))
        except Exception as exc:
            logger.error("add camera error", exc)

        new_camera = bpy.context.active_object
        configure_camera( new_camera )
        
        if placement_data["location"] is not None:
            new_camera.location = Coordinates.iiif_position_to_blender_vector( placement_data["location"] )
            
        if placement_data["rotation"] is not None:
            euler = Coordinates.camera_transform_angles_to_blender_euler( placement_data["rotation"] )
            new_camera.rotation_mode = euler.order
            new_camera.rotation_euler = euler

            
        # ensure the model is in the anno_collection; this is
        # required for IIIF Manifest export
        for col in new_camera.users_collection:
            col.objects.unlink(new_camera)
        anno_collection.objects.link(new_camera)
        return new_camera

    
    def update_placement_from_target(self, target_data, placement_data):
        """
        examines the content of target_data dictionary and identify if
        properties of the target determine information on placement of model 
        in the Blender scene
        
        At this implementation the case of the target_data representing a SpecificResource
        with a PointSelector will be handled.
        
        value of the location property will be set with a 3-tuple in IIIIF Coordinates       
        """
        if  target_data["type"] == "SpecificResource":
            sel = force_as_singleton( target_data["selector"] )
            if sel and sel["type"] == "PointSelector":
                placement_data["location"] = axes_named_values( sel )
        return
        
    def update_placement_from_body(self, body_data, placement_data):
        """
        examines the content of body_data dictionary and identify if
        properties of the body determine information on placement of model 
        in the Blender scene
        
        At this implementation the case of the target_data representing a SpecificResource
        with a transform property
        
        value of the rotation and scale property will be set with a 3-tuple in IIIIF Coordinates 
        """
        if  body_data["type"] == "SpecificResource" and \
            body_data.get("transform", False):
            for transform in force_as_list(body_data["transform"]):
                for transform_compare, placement_property in (
                    ("RotateTransform","rotation"),
                    ("ScaleTransform","scale"),
                ):
                    transform_type = transform["type"]
                    if transform_type == transform_compare:
                        if placement_data[placement_property] is not None:
                            logger.warning("%s is being overwritten" % placement_property)
                        placement_data[placement_property] = axes_named_values(transform)
        return
           
    def process_annotation_page(
        self, annotation_page_data: dict, scene_collection: Collection
    ) -> None:
        page_collection = self.create_or_get_collection(
            self.get_iiif_id_or_label(annotation_page_data), scene_collection
        )
        
        for item in annotation_page_data.get("items", []):
            if item.get("type") == "Annotation":
                self.process_annotation(item, page_collection)
            else:
                self.report({"WARNING"}, f"Unknown item type: {item.get('type')}")

    def process_scene(self, scene_data: dict, manifest_collection) -> None:
        """Process annotation pages in a scene"""
        scene_collection = self.create_or_get_collection(
            self.get_iiif_id_or_label(scene_data), manifest_collection
        )
        context = bpy.context

        metadata = IIIFMetadata(scene_collection)
        metadata.store_scene(scene_data)

        if "backgroundColor" in scene_data:
            self.report(
                {"DEBUG"}, f"Setting background color: {scene_data['backgroundColor']}"
            )
            try:
                bpy.context.scene.world.use_nodes = True
                background_node = bpy.context.scene.world.node_tree.nodes["Background"]
                background_node.inputs[0].default_value = hex_to_rgba(
                    scene_data["backgroundColor"]
                )
            except Exception as e:
                self.report({"ERROR"}, f"Error setting background color: {e}")

        scene_collection["iiif_id"] = scene_data["id"]
        scene_collection["iiif_type"] = "Scene"
        
        if "items" in scene_data:
            for item in scene_data.get("items", [])[:]:
                if item.get("type") == "AnnotationPage":
                    self.process_annotation_page(item, scene_collection)
                    scene_data["items"].remove(item)
        scene_collection["iiif_json"] = json.dumps( scene_data )

    def process_manifest(self, manifest_data: dict) -> None:
        """Process the manifest data and import the model"""

        # Store manifest metadata on the main scene collection
        main_collection = self.create_or_get_collection("IIIF Manifest")
        metadata = IIIFMetadata(main_collection)
        metadata.store_manifest(manifest_data)
        
        main_collection["iiif_id"] = manifest_data["id"]
        main_collection["iiif_type"] = "Manifest"

        if "items" in manifest_data:
            for item in manifest_data["items"][:]: # iterate over a copy
                if item.get("type",None) == "Scene":
                    self.process_scene(item, main_collection)
                    manifest_data["items"].remove(item)

        main_collection["iiif_json"] = json.dumps(manifest_data)
                
    def execute(self, context: Context) -> Set[str]:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.manifest_data = json.load(f)

            self.report({"DEBUG"}, f"Successfully read manifest from {self.filepath}")
            self.report({"DEBUG"}, f"Manifest data: {self.manifest_data}")
            self.process_manifest(self.manifest_data)
            self.report(
                {"DEBUG"}, f"Successfully imported manifest from {self.filepath}"
            )

            return {"FINISHED"}
        except Exception as e:
            import traceback

            self.report({"ERROR"}, f"Error reading manifest: {str(e)}")
            traceback.print_exc()
            return {"CANCELLED"}
