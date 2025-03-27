import logging

logger = logging.getLogger("json_patterns")

"""
collection of module level functions to support some of the json patterns which
are expicitly allowed by IIIF API or which occur anyway, and which can be factored
into readily isolated functions here

patterns:
-- A property value which inherently a single resource object may be represented as a list 
of resources with just one entry

== A property value which is inherently a list of resources may be represented by
a single resource, to be interpreted as a list of one

-- A resource may be represented by a single string value to be interpreted as the URI
"""


def force_as_object(json_data, default_type=None) -> dict:
    """
    argument
    json_data : None, a python dict, or a StringProperty

    default_type : string, hint as to what type the resulting
                    object will be

    None and python dict are returned back
    otherwise attempt, from the string value and default_type, if
    provided, a dict with id


    If string, and can be interprerted as a URI, will
    be returned wrapped in a dict with that value as the id property
    """
    if json_data is None or type(json_data) is dict:
        return json_data

    if type(json_data) is str:
        # placeholder: at this point in code eventually will
        # determine if json_data is a URI from which the resource
        # can be rechieved by a remote query
        determined_type = None

        _type = determined_type or default_type
        retVal = {"id": json_data}

        if _type:
            retVal["type"] = _type

        return retVal

    raise ValueError(
        "force_as_object : cannot interpret %r as a resource" % (json_data,)
    )


def force_as_singleton(obj):
    """
    A way of dealing with json-ld which is flexible
    with regards to objects (python dictionaries) and lists
    This function will follow rule:
    If obj is None or an empty list : return None
    if obj is a non-empty list:
        return the 0th element, a report a warning message if some instances are being
            ignore
    otherwist, return obj

    Use this if you expect value of property to be a single resource
    """

    if obj is None or obj == []:
        return None
    if isinstance(obj, list):
        if len(obj) != 1:
            logger.warn("list of %i elements being coerced to singleton" % len(obj))
        return obj[0]
    return obj


def force_as_list(obj):
    """
    A way of dealing with json-ld which is flexible
    with regards to objects (python dictionaries) and lists
    This function will follow rule:
    If obj is None  return empty list
    if obj is not a list: return [obj]
    else return obj


    Use this if you expect value of property to be a list of resources, possible empty
    """

    if obj is None:
        return []
    if not isinstance(obj, list):
        return [obj]
    return obj


def axes_named_values(xyzObj: dict) -> tuple[float, float, float]:
    """
    xyzObj a python dictionary with optional
    value x, y,z  that have values convertible to floats
    if valuues not present they will be assigned to 0.0
    returned as a (3,) tuple in xyz order
    """
    return (
        float(xyzObj.get("x", 0)),
        float(xyzObj.get("y", 0)),
        float(xyzObj.get("z", 0)),
    )
