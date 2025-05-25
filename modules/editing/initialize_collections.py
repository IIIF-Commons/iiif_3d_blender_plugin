import logging
logger = logging.getLogger("iiif.initialize_collections")
logger.setLevel(logging.INFO)

import bpy
import json


def initialize_manifest( manifest_collection ):
    manifest_collection["iiif_id"] = generate_uri("Manifest")
    manifest_collection["iiif_type"] = "Manifest"

    """
    Design intent is that the manifest_init_data will be a core of
    the final json representation of the manifest.
    
    the values for id and type will be populated upon export from the 
    corresponding iiif_id and iiif_type Blender custom properties    
    
    Intent is that the iiif properties label and rights for the manifest will be
    editable. They are initialized here within the manifest_init_data dictionary, 
    upon execution of the to-be implemented Blender Operator instance the label / rights
    value will be retrieved from the manifest_init_data, edited by user, then upon
    confirmation entered back into the manifest_init_data dictionary
    
    Note: This initialization will NOT be invoked when a manifest is imported.
    For imported manifests the id and type iiif properties will be moved into
    iiif_* custom properties; a Scene instance will be removed from items list and
    will populate the Scene Blender collection, any Canvas in items will just remain 
    in the iiif_json dictionary. All other iiif properties will be maintained in the
    iiif_json custom property. The editing code for "label" and "rights" will decide 
    what to do if those iiif properties are not defined in the imported manifest, or
    are defined in a non-standard way.
    
    In following initialization of data, entering invalid None values for several
    properties. It's been seen that in Python 3.11 the the output printed json
    text will be in this order, which is more judged more readable.
    """
    manifest_init_data = {
        "@context": "http://iiif.io/api/presentation/4/context.json",
        "id" : None,
        "type" : None,
        "rights" : None,
        "label" : None,
        "items" : []
    }
    
    """
    By default the manifest is assigned the Creative Commons
    CC BY 4.0 : Attribution 4.0 International license
    https://creativecommons.org/licenses/by/4.0
    
    See Presentation 3 API 
    https://iiif.io/api/presentation/3.0/#rights
    for allowed value of the 'rights' property
    """

    manifest_init_data["rights"] = "https://creativecommons.org/licenses/by/4.0/"
    manifest_init_data["label"] = {"none" : ["default-manifest-label"]}
    
    manifest_collection["iiif_json"] = json.dumps(manifest_init_data)
 
def initialize_scene( scene_collection ):  

    scene_collection["iiif_id"]  = generate_uri(resource_type="Scene")
    scene_collection["iiif_type"]  = "Scene"
    

    scene_init_data = {
        "id" : None,
        "type" : None,
        "label" : {"none":["default-scene-label"]},
        "items" : []
    }
    scene_collection["iiif_json"] = json.dumps(scene_init_data)

def initialize_anotation_page( page_collection ):  

    page_collection[ "iiif_id"] = generate_uri(resource_type="AnnotationPage")
    page_collection["iiif_type"]  = "AnnotationPage"  
      
    page_init_data = {
        "id" : None,
        "type" : None,
        "label" : {"none":["default-annotation-page-label"]},
        "items" : []
    }
    page_collection["iiif_json"] = json.dumps(page_init_data)
    
def initialize_annotation( annotation_collection ):  

    annotation_collection[ "iiif_id"] = generate_uri(resource_type="Annotation")
    annotation_collection["iiif_type"]  = "Annotation"  
      
    anno_init_data = {
        "id" : None,
        "type" : None
    }
    annotation_collection["iiif_json"] = json.dumps(anno_init_data)
 
    
def generate_uri(resource_type="Manifest"):
    """
    this is the stub for a future implementation that will 
    generate a more useful valid , globally unique, and publically
    accessible URI 
    """
    import re
    prefix = "https://example.com/iiif_blender_plugin/%s/" % resource_type.lower()
    re_pattern= re.compile( prefix+r"([0-9]+)\s*$" )
    imax=0
    for obj_or_col in ( list(bpy.data.objects) + list(bpy.data.collections) ):
        match = re_pattern.match( obj_or_col.get("iiif_id", ""))
        if match:
            val = int( match.group(1) )
            
            imax = max(imax,val)
    retVal = prefix + str(imax+1)
    return retVal
