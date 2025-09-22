from typing import Set


from .editing.models import  mimetype_from_extension , configure_model, walk_object_tree
from .editing.transforms import Placement
from .editing.collections import move_object_into_collection

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

import pathlib # standard package supporting creating
               # file-schema url from filesystem path
import logging
logger = logging.getLogger("iiif.import_local_model")



            
class ImportLocalModel(Operator,  ImportHelper):
    """
    Operator that imports a 3D model into blender
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
    
    mimetype: StringProperty(  # type: ignore
        name="MIMETYPE",
        description="MIMETYPE as returned from fetch headers",
        maxlen=0,
        subtype="NONE",
        options={'HIDDEN'}
    )

    # Developer Note 8/19/2025 : Since this class inherits from ImportHelper,
    # this invoke definition just repeats the built-in inheritance behavior of
    # calling the invoke method of a superclass.
    # 
    # The only reason for adding this definition is to add the informative
    # logging message.
    def invoke(self, context, event):
        logger.info("ImportLocalModel.invoke entered")
        rv = ImportHelper.invoke(self, context,event)
        return rv
        
    def execute(self, context: Context) -> Set[str]:

        self.mimetype = self.mimetype or mimetype_from_extension(self.filepath)
            
        # the key string is a mimetype
        # the value is callable object compatible with
        # the Operator.execute method; it will accept a filepath argument
        # and return set of result values
        
        local_loader = bpy.ops.iiif.load_local_model # pyright: ignore[reportAttributeAccessIssue]
        load_result = local_loader(filepath = self.filepath,  mimetype= self.mimetype)
        if 'FINISHED' not in load_result:
            return load_result
            
        new_model = context.active_object
        if new_model is None:
            logger.warn("context.active_object is None")
            return {"CANCELLED"}
            
        # configure model by definine IIIF resource properties.
        # the id will be set based on the local file system path.
        # if this function is called by the LoadNetworkModel it will
        # be the responsibility of that client to replace the id
        # with an id from the network URL
        model_data = {
            "id" : pathlib.Path(self.filepath).as_uri(),
            "format" : self.mimetype,
            "type"   : "Model"
        }
        placement = Placement() # use the identity placement for the new import_scene
        configure_model(new_model, model_data,placement)
        
        LOOP_GUARD_MAX=8
        for depth, _obj in walk_object_tree(new_model):
            if depth > LOOP_GUARD_MAX:
                raise Exception("infinite (or too deep) object parent-child tree")
            move_object_into_collection(_obj, context.collection)
                    
        
        
        # properties 
        return {"FINISHED"}


