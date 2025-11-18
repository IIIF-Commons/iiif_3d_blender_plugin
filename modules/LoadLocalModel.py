from typing import Set, Callable, Tuple


from .editing.models import  (  IIIF_TEMP_FORMAT, 
                                INITIAL_TRANSFORM ,
                                encode_blender_placement,
                                walk_object_tree  )
from .editing.transforms import  get_object_placement

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

import logging
logger = logging.getLogger("iiif.import_local_model")



            
class LoadLocalModel(Operator):
    """
    Operator that imports a 3D model into blender
    
    This Operator is intended to be a common service for use by
    both the operator that "loads" a model from a URL (by downloading
    first to the local filesystem) and by a UI-based operator that prompts
    the user to pick a local file. 
    
    This Opertor does not define a UI panel and it does not configure the
    loaded Blender model for use in a Blender representation of an IIIF Scene.
    
    precontract:
    string filepath will be to a local filesystem file
    string mimetype will be a mimetype of the resource
        typical value of a mimetyp would be "model/gltf-binary"
        Its the responsibility of clients that execute this Operator
        to set the mimetype, based on :
           -- the value of IIIF format property in an IIIF resource
           -- the Content-Type from a HTTP header in a network fetch
           -- a file extension
        
    post-contract, on SUCCESS return
    The single new Blender object that supports having location, rotation, scaling
    properties will be the active_object. There may be other Blender objects created,
    particularly if the imported resource gets imported as a multiple number of meshes,
    in which case this Operator will create a parent structure so that they will all be
    collectively moved,rotated,scaled.
    
    No placement of new objects into Blender collections will be made.
    
    The initial Blender location, rotation, scaling will be converted into a json-encoded
    string as a custom property "iiif_initial_placement" of the active_object
    
    Developer Note: This operator does not have invoke method or setup of a UI. In the
    scenarios at present this operator will be executed from within another Operator 
    instance that provides an required UI
    """
    bl_idname = "iiif.load_local_model"
    bl_label = "Load local file as model"    
    
    filepath: StringProperty(  # type: ignore
        name="File Path",
        description="Path to the input file",
        maxlen=0,
        subtype="FILE_PATH",
        options={'HIDDEN'}
    )
    
    mimetype: StringProperty(  # type: ignore
        name="MIMETYPE",
        description="MIMETYPE as returned from fetch headers",
        maxlen=0,
        subtype="NONE",
        options={'HIDDEN'}
    )
        
    def execute(self, context: Context) -> Set[str]:
        # the key string is a mimetype
        # the value is callable object compatible with
        # the Operator.execute method; it will accept a filepath argument
        # and return set of result values
        
        # Developer note: this dictionary is constructed at run time
        # so that an existing importer Operator can be wrapped at run-time
        # with a wrapper function that supplied other import arguments

        try:
            handler, handler_name = handler_for_mimetype(self.mimetype)
        except KeyError:
            message = "unsupported mimetype : %s" % self.mimetype
            logger.warn(message)
            return {'CANCELLED'}
           
        try:
            retCode = handler(filepath=self.filepath)
            if "FINISHED" not in retCode:
                logger.warn("import handler returned %r"  % (retCode,))
                return retCode
            if len(retCode) > 1:
                logger.info( "import handler returned %r"  % (retCode,) )
        except Exception as exc:
            logger.error("glTF import error", exc)
            return {"CANCELLED"}
        
        new_model = context.active_object
        if new_model is None:
            logger.warn("context.active_object is None")
            return {"CANCELLED"}

        # reminder: The IIIF_TEMP_FORMAT value is defined in editing.models
        # this custom property is defined here and removed by the configure_model
        # function; it is essentially a way of passing data from this Operator instance
        # to client code that executes it. 
        new_model[IIIF_TEMP_FORMAT] = self.mimetype
        
        
        blender_transform_encoding : str  = encode_blender_placement(
                                                get_object_placement(new_model)
                                            )
        logger.debug(f"initial transform: {blender_transform_encoding}")
        new_model[INITIAL_TRANSFORM] = blender_transform_encoding

        LOOP_GUARD_MAX=8
        for depth, _obj in walk_object_tree(new_model):
            if depth > LOOP_GUARD_MAX:
                raise Exception("infinite (or too deep) object parent-child tree")
            if depth > 0:
                _obj.rotation_mode="ZYX"
                _obj.lock_rotation = (True,True,True)
                _obj.lock_scale = (True,True,True)
                _obj.lock_location = (True,True,True)
            
            
        
        # properties 
        return {"FINISHED"}


def wrapped_gltf(*args, **keyw) -> Set[str]:
    """
    A wrapper around the Blender addon-core gltf Importer.
    this wrapper serves the purpose of quieting the logging INFO messages
    see:
    blender/scripts/addons_core/io_scene_gltf2/__init__.py
    class ImportGLTF2; function set_debug_log
    """
    saved_debug_value = bpy.app.debug_value
    bpy.app.debug_value = 1 # this is equivalent to logging.WARN
    try:
        return bpy.ops.import_scene.gltf(*args, **keyw)
    finally:
        bpy.app.debug_value = saved_debug_value

def handler_for_mimetype( mimetype:str) -> Tuple[Callable[..., Set[str]] , str] :
    """
    return 2-tuple (func, label)
    function is the callable, may be Blender defined operator call such as 
    bpy.ops.import_scene.gltf 
    label a string used only for logging messages
    
    """
    
    GLTF_IMPORTER : Tuple[Callable[..., Set[str]] , str] = \
        (wrapped_gltf, "glTF/glb Blender core add-on")
        
        
    mimetype_importer_dict = {
        "model/gltf-binary" :           GLTF_IMPORTER,
        "model/gltf+json"   :           GLTF_IMPORTER,
        "application/octet-stream"  :   GLTF_IMPORTER   
    }
    
    return mimetype_importer_dict[mimetype]
