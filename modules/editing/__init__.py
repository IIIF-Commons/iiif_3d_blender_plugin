from typing import Optional
import bpy
import uuid
    
# module level constant
RANDOM_TEXT  = str(uuid.uuid4())[:8]

def generate_id(resource_type="Manifest") -> str:
    """
    
    """
    import re
    
    
    prefix = "https://%s/%s/" % ( RANDOM_TEXT, resource_type.lower())
    re_pattern= re.compile( prefix+r"([0-9]+)\s*$" )
    imax=0
    for obj_or_col in ( list(bpy.data.objects) + list(bpy.data.collections) ):
        match = re_pattern.match( obj_or_col.get("iiif_id", ""))
        if match:
            val = int( match.group(1) )
            
            imax = max(imax,val)
    retVal = prefix + str(imax+1)
    return retVal

def generate_name_from_data( data : dict ) -> Optional[str] : 
    """
    Will try to identify a suitable string to identity the collection
    in the Blender UI Outline UI panel.
    
    Will first try to identify a string from the label entry of data, then
    use the id if available
    """
    
    if "label" in data:
        for language,label_items in data["label"].items():
            if len(label_items) > 0:
                return label_items[0]
    
    try:
        id_copy = data["id"]
    except KeyError:
        pass
    else:
        colon_index = id_copy.find(":") 
        if colon_index >= 0:
            id_copy = id_copy[colon_index+1:] # strip off scheme, "http","file", or "_"
        if id_copy:
            comps =  id_copy.split("/")[-2:]
            if comps:
                return "/".join(comps)  
    return None