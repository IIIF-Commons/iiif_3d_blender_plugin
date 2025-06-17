import bpy

import logging
logger = logging.getLogger("iiif.navigation")
logger.setLevel(logging.INFO)




"""
collection_types is the list
of IIIF resource types which are represented as 
Blender collections
"""
collection_types = [
    "Manifest",
    "Scene",
    "AnnotationPage",
    "Annotation"
]

def _find_resources_by_type(what_iiif_type:str) -> list:
    if what_iiif_type in collection_types:
        return [
            coll for coll in bpy.data.collections \
            if coll.get("iiif_type", None) == what_iiif_type \
        ]
    else:
        raise ValueError("_find_resources_by_type unimplemented for type %s" 
        % what_iiif_type)
        

def _find_enclosing_resource(iiif_resource, enclosing_type):
    """
    iiif_resource must be a Python instances for which the calls
    iiif_resource.get("iiif_id") and
    iiif_resource.get("iiif_type")
    return strings, 
    
    enclosing_type will be one of:
    Manifest, Scene, AnnotationPage, Annotation
    
    will return the Blender Collection instance that matches teh enclosing_type
    """
    parent_type_dict = {
        "Annotation" : "AnnotationPage",
        "AnnotationPage" : "Scene",
        "Scene" : "Manifest"
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
    
