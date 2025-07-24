import bpy
import json
from bpy.types import Collection
from  typing import Optional

from . import generate_id, generate_name_from_data

import logging
logger = logging.getLogger("iiif.collections")
logger.setLevel(logging.INFO)

# Developer note 
# The name of this module, collections, is intended to refer to the
# Blender concept of the a collection which in Blender provides a 
# grouping structure to the objects in a scene but does not itself 
# play a role in rendering. 
# 
# A Blender collection is used to implement the IIIF resources
# Manifest, Scene, AnnotationPage, and Annotation




MANIFEST_TYPE="Manifest"
SCENE_TYPE=   "Scene"
ANNOTATIONPAGE_TYPE= "AnnotationPage"
ANNOTATION_TYPE = "Annotation"



def _new_collection( data:dict) -> Collection:
    """
    returns a Blender collection for which:
    the custom properties iiif_type, iiif_id have been set to string values
        custom property iiif_data has been set to json-encoded dictionary
        property name is defined
        
    collection will have no children, and will not have been added as child of
    a parent collection  
    """

    collection_type : str = data["type"]

    if "id" not in data:
        data["id"] = generate_id(collection_type)
    
    blender_name : str = generate_name_from_data( data ) or collection_type.lower()
    
    retVal  = bpy.data.collections.new(blender_name)
    retVal["iiif_data"] =  json.dumps( data )
    retVal["iiif_id"] =    data["id"]
    retVal["iiif_type"] =  data["type"]
    return retVal
    

def new_manifest( data:Optional[dict] = None ) -> Collection:
    
    valid_data : dict = data or _initial_data(MANIFEST_TYPE)    
    return _new_collection(valid_data)
        
def new_scene( data:Optional[dict] = None ) -> Collection:
    
    valid_data : dict = data or _initial_data(SCENE_TYPE)   
    return _new_collection(valid_data)

def new_annotation_page( data:Optional[dict] = None ) -> Collection:
    
    valid_data : dict = data or _initial_data(ANNOTATIONPAGE_TYPE)    
    return _new_collection(valid_data)

def new_annotation( data:Optional[dict] = None ) -> Collection:
    
    valid_data : dict = data or _initial_data(ANNOTATION_TYPE)    
    return _new_collection(valid_data)

_collection_template_dict  = {
    MANIFEST_TYPE : {
        "@context": "http://iiif.io/api/presentation/4/context.json",
        "id" : None,
        "type" : "Manifest",
        "label" : {},
        # By default the manifest is assigned the Creative Commons
        # CC BY 4.0 : Attribution 4.0 International license
        # https://creativecommons.org/licenses/by/4.0
        # 
        # See Presentation 3 API 
        # https://iiif.io/api/presentation/3.0/#rights
        # for allowed value of the 'rights' property
        "rights": "https://creativecommons.org/licenses/by/4.0/",
        "items" : []
    },
    
    SCENE_TYPE : {
        "id" : None,
        "type" : "Scene",
        "label" : {},
        "items" : []
    },
    
    ANNOTATIONPAGE_TYPE : {
        "id" : None,
        "type" : "Scene",
        "label" : {},
        "items" : []    
    },
    
    ANNOTATION_TYPE : {
        "id" : None,
        "type" : "Scene",
        "motivation" : [],
        "body" : None,
        "target" : None,
        "label" : {}
    }
}
    
def _initial_data(str : str ) -> dict:
    original = _collection_template_dict[str]
    # the following:
    # makes  deep copy of the original  dict
    # verifies that the result is compatible with json
    return json.loads( json.dumps(original ))
    
"""
collection_types is the list
of IIIF resource types which are represented as 
Blender collections
"""


def _find_resources_by_type(what_iiif_type:str) -> list[Collection]:
    return [
        coll for coll in bpy.data.collections \
        if coll.get("iiif_type", None) == what_iiif_type \
    ]
        

def _find_enclosing_resource(iiif_resource : Collection, enclosing_type : str ):
    """
    iiif_resource must be a Python instances for which the calls
    iiif_resource.get("iiif_id") and
    iiif_resource.get("iiif_type")
    return strings, 
    
    enclosing_type will be one of:
    Manifest, Scene, AnnotationPage
    
    will return the Blender Collection instance that matches teh enclosing_type
    """
    parent_type_dict = {
        ANNOTATION_TYPE : ANNOTATIONPAGE_TYPE ,
        ANNOTATIONPAGE_TYPE : SCENE_TYPE,
        SCENE_TYPE : MANIFEST_TYPE
    }
    search_id = iiif_resource.get("iiif_id", None)
    if search_id is None:
        return None
        
    for coll in _find_resources_by_type(parent_type_dict[iiif_resource.get("iiif_type",None)]):
        
        for ch in coll.children:
            if ch.get("iiif_id",None) == search_id:
                if coll.get("iiif_type", None) == enclosing_type:
                    return coll
                else:
                    return _find_enclosing_resource(coll, enclosing_type)

def _find_child_resources_by_type( parent_collection, what_iiif_type ):
    return [coll for coll in parent_collection.children \
            if coll.get("iiif_type",None) == what_iiif_type ]
              
def getTargetScene(iiif_resource):
    """
    Intended for case where iiif_resource is an Annotation
    returns the Blender Collection for the parent collection that represents
    the Scene, from which the iiii_id can be retrieved to form the Annotation target
    or the source of an SpecificResource
    """
    return _find_enclosing_resource(iiif_resource, "Scene")
    
def getManifests():
    return _find_resources_by_type("Manifest")
    
def getScenes(manifest_collection):
    """
    manifest_collection the Blender Collection representing a manifest
    """
    return _find_child_resources_by_type( manifest_collection, "Scene" )
    
def getAnnotationPages(scene_collection):
    return _find_child_resources_by_type( scene_collection, "AnnotationPage" )
    
def getAnnotations(page_collection):
    return _find_child_resources_by_type( page_collection, "Annotation" )

    
def getBodyObject(anno_collection) -> bpy.types.Object | None:
    
    bodyObjList = [obj for obj in anno_collection.objects if obj.get("iiif_type", None)]
    if len(bodyObjList) == 0:
        return None
    if len(bodyObjList) > 1:
        logger.warning("multiple body objects in single Annotation")
    return bodyObjList[0]