from typing import Set


from .editing.models import  IIIF_TEMP_FORMAT, mimetype_from_extension

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

import logging
logger = logging.getLogger("iiif.import_local_model")



            
class ImportLocalModel(Operator):
    """
    Operator that imports a 3D model into blender
    
    precontract:
    string filepath will be to a local filesystem file
    string mime_type will be a mime_type of the resource
        typical value of a mimetyp would be "model/gltf-binary"
        Its the responsibility of clients that execute this Operator
        to set the mime_type, based on :
           -- the value of IIIF format property in an IIIF resource
           -- the Content-Type from a HTTP header in a network fetch
           -- 
        
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
    bl_idname = "iiif.import_local_model"
    bl_label = "Import local file as model"    
    
    filepath: StringProperty(  # type: ignore
        name="File Path",
        description="Path to the input file",
        maxlen=0,
        subtype="FILE_PATH",
        options={'HIDDEN'}
    )
    
    mime_type: StringProperty(  # type: ignore
        name="MIMETYPE",
        description="MIMETYPE as returned from fetch headers",
        maxlen=0,
        subtype="NONE",
        options={'HIDDEN'}
    )
        
    def execute(self, context: Context) -> Set[str]:

        mime_type = self.mime_type or mimetype_from_extension(self.filepath)
            
        # the key string is a mimetype
        # the value is callable object compatible with
        # the Operator.execute method; it will accept a filepath argument
        # and return set of result values
        
        # Developer note: this dictionary is constructed at run time
        # so that an existing importer Operator can be wrapped at run-time
        # with a wrapper function that supplied other import arguments
        
        GLTF_IMPORTER = (bpy.ops.import_scene.gltf,"glTF/glb Blender core add-on")
        importer_dict = {
            "model/gltf-binary" : GLTF_IMPORTER,
            "model/gltf+json"   : GLTF_IMPORTER,
        }

        try:
            handler, handler_name = importer_dict[mime_type]
        except KeyError:
            message = "unsupported mime_type : %s" % mime_type
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
        
        #new_model = bpy.context.active_object -- potential cruft, remove if when this code works
        new_model = context.active_object
        if new_model is None:
            logger.warn("context.active_object is None")
            return {"CANCELLED"}
        else: 
            # reminder: The IIIF_TEMP_FORMAT value is defined in editing.models
            # this custom property is defined here and removed by the configure_model
            # function; it is essentially a way of passing data from this Operator instance
            # to client code that executes it. 
            new_model[IIIF_TEMP_FORMAT] = self.mime_type
        
        # TODO: insert code to record the new_model location, rotation, scaling
        # properties 
        return {"FINISHED"}


