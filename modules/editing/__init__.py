def generate_id(resource_type="Manifest"):
    """
    generates an identifier following the convention for a 
    'blank node identifier' (see https://www.w3.org/TR/rdf11-concepts/#dfn-blank-node-identifier)
    as references in JSON-LD 1.1 document (see https://www.w3.org/TR/json-ld11/ )
    """
    import re
    prefix = "_:%s/" % resource_type.lower()
    re_pattern= re.compile( prefix+r"([0-9]+)\s*$" )
    imax=0
    for obj_or_col in ( list(bpy.data.objects) + list(bpy.data.collections) ):
        match = re_pattern.match( obj_or_col.get("iiif_id", ""))
        if match:
            val = int( match.group(1) )
            
            imax = max(imax,val)
    retVal = prefix + str(imax+1)
    return retVal
