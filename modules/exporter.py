import json
from typing import Set, List

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator, Object
from bpy_extras.io_utils import ExportHelper
from mathutils import Vector, Quaternion

from .utils.color import rgba_to_hex

from .editing.collections import (getScenes, 
                    getTargetScene, 
                    getAnnotations, 
                    getAnnotationPages,
                    getBodyObject,
                    getManifests)
                    
from .editing.transforms import (   Transform, 
                                    Placement, 
                                    Rotation,
                                    Translation, 
                                    get_object_placement, 
                                    simplifyTransforms )
     
#   INITIAL_TRANSFORM is string-valued constant
#   shared with the models module, it is used as the
#   key for storing the Blender placement (location, rotation, scale ) 
#   that the model had on import from glTF         
from .editing.models import INITIAL_TRANSFORM, decode_blender_transform

from .utils.blender_setup import get_scene_background_color

import math

import logging
logger = logging.getLogger("iiif.export")

class ExportManifest(Operator, ExportHelper):
    """Export IIIF 3D Manifest"""

    bl_idname = "export_scene.iiif_manifest"
    bl_label = "Export IIIF 3D Manifest"

    filename_ext = ".json"
    filter_glob: StringProperty( # type: ignore
        default="*.json",
        options={"HIDDEN"}
    )
    filepath: StringProperty( # type: ignore
        name="File Path",
        description="Path to the output file",
        maxlen=1024,
        subtype='FILE_PATH',
    )


    def get_base_data(self, iiif_object) -> dict:
        """
        iiif_object is either a Blender collection or Blender object
        for which custom properties iiif_id, iiif_type, and iiif_json
        have been defined. Returns a python dict which contains information
        for the json output in Manifest.
        
        Design intent is that client will start with this base_data dict
        and then add and or modify properties which are determined by
        the Blender data structure
        
        label properties, metadata, and other none - 3d properties
        will be in stored restored in the this base_data dict. 
        """
        base_json = iiif_object.get("iiif_json",None)
        if base_json:
            base_data = json.loads( base_json )
        else:
            base_data = dict()
            
        base_data["id"] = iiif_object.get("iiif_id")
        base_data["type"] = iiif_object.get("iiif_type")
        return base_data

    def get_manifest_data(self, manifest_collection: bpy.types.Collection) -> dict:
        manifest_data = self.get_base_data(manifest_collection)
        
        manifest_data["items"] = manifest_data.get("items", None) or []
        for scene_collection in getScenes(manifest_collection):
            manifest_data["items"].append(self.get_scene_data(scene_collection))
        return manifest_data
        
    def get_scene_data(self, scene_collection: bpy.types.Collection) -> dict:
        scene_data = self.get_base_data(scene_collection)
        
        backgroundColor = get_scene_background_color()
        
        if backgroundColor is not None:
            color_hex = rgba_to_hex( backgroundColor )
            logger.info("setting scene backgroundColor to %s" % color_hex)
            scene_data["backgroundColor"] = color_hex
        
        scene_data["items"] = scene_data.get("items", None) or []
        for page_collection in getAnnotationPages(scene_collection):
            scene_data["items"].append(self.get_annotation_page_data(page_collection))
        return scene_data


    def get_annotation_page_data(self, page_collection: bpy.types.Collection) -> dict:
        page_data = self.get_base_data(page_collection)
        
        page_data["items"] = page_data.get("items", None) or []
        for anno_collection in getAnnotations(page_collection):
            page_data["items"].append(self.get_annotation_data(anno_collection))

        
        return page_data

    def get_annotation_data(self, anno_collection ):
        anno_data = self.get_base_data(anno_collection)
        anno_data["motivation"] = ["painting"]
#        Developer Note:
#        The reason we need to pass the bodyObj into the function
#        to create the target is that in the Prezi 4 API for Scenes,
#        the location of the model in the Scene is represented by
#        a PointSelector-based SpecificResource considered to be
#        a refinement of the target Scene. But in Blender, the location
#        is represented in the data for the Model
        bodyObj = getBodyObject(anno_collection)
        
        if bodyObj is not None:
            resource_data = self.resource_data_for_object( bodyObj )
            transforms    = simplifyTransforms(
                                self.applied_transforms_for_object( bodyObj )
                            )
            anno_data["target"] = self.target_data_for_object(  resource_data, 
                                                                transforms, 
                                                                anno_collection)
                                                                
            anno_data["body"]= self.body_data_for_object(   resource_data, 
                                                            transforms,
                                                            anno_collection)

        return anno_data



    def body_data_for_object(self,  resource_data:dict, 
                                    transforms: List[Transform], 
                                    anno_collection:bpy.types.Collection) -> dict:
        
        # will use the logic that the final transform of the list, if it is a 
        # Translation, will be encoded in the target. The remaining transforms will
        # be simplified to list of placements, and then converted back to a list of
        # transforms and then iiif Tranform resources
        if len(transforms) > 0 and isinstance( transforms[-1], Translation):
            transforms = transforms[:-1]

        if (len(transforms) > 0):
            specific_resource = {
                "type" : "SpecificResource",
                "transform" : [
                    t.to_iiif_dict() for t in transforms
                ],
                "source" : resource_data
            }
            return specific_resource
        else:
            return resource_data

        
    def target_data_for_object(self,    resource_data:dict, 
                                        transforms: List[Transform], 
                                        anno_collection:bpy.types.Collection) -> dict:
        target = getTargetScene( anno_collection )
        scene_resource = {
            "id": target["iiif_id"],
            "type" : "Scene"
        }
        
        if len(transforms) > 0 and isinstance( transforms[-1], Translation):
            def build_selector(tt:Translation) -> dict:
                tmp = tt.to_iiif_dict()
                tmp["type"]="PointSelector"
                return tmp
                
            selector = build_selector( transforms[-1] )
            
            return {
                "type": "SpecificResource",
                "selector" : selector,
                "source"   : scene_resource
            }
        else:
            return scene_resource


    def resource_data_for_object(self, blender_obj:bpy.types.Object) -> dict:
        """
        returns the IIIF data for a Model, Camera, Light that is not position or orientation
        description; this would be the body data if no Transform were needed for orientation
        and scale.
        """
        resource_type = blender_obj.get("iiif_type","")
        logger.debug("getting resource data for %s" % resource_type)
        
        try:
            return {
                "Model" :               self.resource_data_for_model,
                "PerspectiveCamera" :   self.resource_data_for_camera,
                "OrthographicCamera" :  self.resource_data_for_camera,
            }[blender_obj.get("iiif_type","")](blender_obj)
        except KeyError as badKey:
            logger.error(f"unsupported type {repr(badKey)} in resource_data_for_object")
            raise

    def resource_data_for_camera(self, blender_obj:bpy.types.Object) -> dict:
        resource_data = self.get_base_data(blender_obj)
        
        # July 3 2025 : We do not want to output an id for cameras that look like URLS
        # because some viewers are trying to download these that are body resources
        # of "painting" motivation annotations
        if "id" in resource_data:
            del resource_data["id"]

        foValue : float = float(blender_obj.data.angle_y) # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        resource_data["fieldOfView"] =  math.degrees(foValue) 
        return resource_data
        
    def resource_data_for_model(self, blender_obj:bpy.types.Object) -> dict:
        return self.get_base_data(blender_obj)

    def applied_transforms_for_object(self, blender_obj:bpy.types.Object ) -> List[Transform]:
        try:
            return {
                "Model" :               self.applied_transforms_for_model,
                "PerspectiveCamera" :   self.applied_transforms_for_camera,
                "OrthographicCamera" :  self.applied_transforms_for_camera,
            }[blender_obj.get("iiif_type","")](blender_obj)
        except KeyError as badKey:
            logger.error(f"unsupported type {repr(badKey)} in resource_data_for_object")
            raise
            
     
    def applied_transforms_for_model(self, model:Object) -> List[Transform] :
        """
        The applied transforms list is a list of geometric transforms that will be applied
        to an imported model to achieve the current (to-be-exported) placing of the model
        in the Blender coordinate system.
        
        It allows for the possibility that the mesh coordinates of the imported model have
        been modifed by rotations,scalings, translations defined within the imported model
        file format. 
        
        If the orientation, scale, location of the imported model have not been modified
        by the user then this set of transforms should reduce to the identity.
        """
        current_placement : Placement = get_object_placement( model )
        
        exported_transform_list: List[Transform] = []
        try:
            initial_transform = model[INITIAL_TRANSFORM]
        except KeyError:
            exported_transform_list.extend(
            [
                current_placement.scaling,
                current_placement.rotation,
                current_placement.translation
            ])
        else:
            initial_placement = decode_blender_transform(initial_transform)
            
            # following calculation 
            exported_transform_list.extend(
            [
                initial_placement.translation.inverse(),
                initial_placement.rotation.inverse(),
                initial_placement.scaling.inverse(),
                current_placement.scaling,
                current_placement.rotation,
                current_placement.translation
            ]
            )        
        return exported_transform_list


    def applied_transforms_for_camera(self, camera:Object) -> List[Transform] :
        """
        """
        current_placement : Placement = get_object_placement( camera )
        initial_rotation = Rotation( Quaternion( Vector((1.0,0.0,0.0)), math.pi/2))
        exported_transform_list: List[Transform] = []
        exported_transform_list.extend(
            [
                initial_rotation.inverse(),
                current_placement.scaling,
                current_placement.rotation,
                current_placement.translation
            ]
        ) 
        return exported_transform_list  
        
        
        
##    def target_data_for_object(self, blender_obj:bpy.types.Object, anno_collection:bpy.types.Collection) -> dict:
##        if blender_obj.get("iiif_type", None) in ("Model","PerspectiveCamera"):
##            return self.target_data_for_model(blender_obj, anno_collection )
##        else:
##            logger.warning("invalid object %r in target_data_for_object" % (blender_obj),)
##            return {}
##        
##    def target_data_for_model(self, blender_obj:bpy.types.Object, anno_collection:bpy.types.Collection) -> dict:
##        """
##        Examines the Blender "location" of the blender_obj and returns a SpecificResource data
##        with a PointSelector and source of the enclosing scene
##        """  
##        ALWAYS_USE_POINTSELECTOR=False
##         
##        enclosing_scene=getTargetScene(anno_collection)
##        if enclosing_scene is not None:
##            scene_ref_data = {
##                "id" :   enclosing_scene.get("iiif_id"),
##                "type" : enclosing_scene.get("iiif_type")
##            }
##            
##            blender_location = blender_obj.location
##            iiif_position = Coordinates.blender_vector_to_iiif_position(blender_location)
##            
##            if iiif_position != (0.0,0.0,0.0) or ALWAYS_USE_POINTSELECTOR:
##                target_data = {
##                "type" : "SpecificResource",
##                "source" : scene_ref_data,
##                "selector" : create_axes_named_values("PointSelector", iiif_position)
##                }
##            else:
##                target_data = scene_ref_data
##            return target_data
##        else:
##            raise  Exception("enclosing scene not identified to for model target")
        



    def execute(self, context: Context) -> Set[str]:
        """Export Blender scene as IIIF manifest"""
        manifests = getManifests()
        
        if manifests:   # that is, not an empty list
            if len(manifests) > 1:
                logger.warning("Multiple manifests not supported")
            manifest_collection=manifests[0]
            manifest_data = self.get_manifest_data(manifest_collection)
        
            # Write manifest
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)
        else:
            logger.warning("No manifest collections identified")

        return {"FINISHED"}
