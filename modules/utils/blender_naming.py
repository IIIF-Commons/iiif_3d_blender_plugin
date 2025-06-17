
"""
functions to generate names for Blender display
"""

def generate_name_from_id( blender_thing ):
    """
    blender_thing a Collection or Object
    
    will return a string based on the iiif_id, or None
    
    will not modify blender_thing, client code is resposible
    for changing the name
    """
    iiif_id = blender_thing.get("iiif_id", None)
    if not iiif_id:
        return None
    # items the non-empty parts of the url path separated by / character
    items = [txt for txt in iiif_id.split("/") if iiif_id]
    shortened_path =  "/".join(items[-2:])
    return shortened_path or None