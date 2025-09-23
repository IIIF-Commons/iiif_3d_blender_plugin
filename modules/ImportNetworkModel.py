
from typing import Set

from .editing.models import configure_model, walk_object_tree
from .editing.collections import move_object_into_collection, new_annotation
from .editing.transforms import Placement


import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

import logging
logger = logging.getLogger("iiif.import_network_model")



class ImportNetworkModel(Operator):
    """ 
    This network retrieval does not implement the CORS security protocol
    for clients, that is it will happily download resources from any HTTP
    server that the local computer can access.
    """
    
    bl_idname = "iiif.import_network_model"
    bl_label = "Import remote resource as model"    

    """
    mimetype property can be set by clients if there's already
    knowledge of what the mime-type of a resource is, this would
    typically be in the format property of a resource being imported
    as part of importing a manifest. If not specified by the client, then
    the mimetype will be taken from the Content-Type of the response HTTP headers
    """
    mimetype: StringProperty(  # type: ignore
        name="MIMETYPE",
        description="MIMETYPE as returned from fetch headers",
        maxlen=0,
        subtype="NONE",
        options={'HIDDEN'}
    )

    """
    This operator only supports http or https schema urls.
    A file schema should be handled by the client by redirecting to
    the ImportLocalModel
    """
    model_url: StringProperty(  # type: ignore
        name="URL / IIIF id",
        description="URL to external 3D resource",
        maxlen=0,
        subtype="NONE",
    )
    
    def invoke(self, context, event):
        logger.info("ImportRemoteModel.invoke entered")
        self.model_url=""
        rv = context.window_manager.invoke_props_dialog(self, width=640)
        logger.info("return from invoke_props_dialog %r : %r" % (rv, self.model_url) )
        return rv


    def execute(self, context: Context) -> Set[str]:

            
        # the key string is a mimetype
        # the value is callable object compatible with
        # the Operator.execute method; it will accept a filepath argument
        # and return set of result values
        
        local_loader = bpy.ops.iiif.load_network_model # pyright: ignore[reportAttributeAccessIssue]
        load_result = local_loader(model_url = self.model_url)
        if 'FINISHED' not in load_result:
            return load_result
            
        new_model = context.active_object
        if new_model is None:
            logger.warn("context.active_object is None")
            return {"CANCELLED"}
            
        model_data = {
            "id" : self.model_url,
            "format" : self.mimetype,
            "type"   : "Model"
        }
        placement = Placement() # use the identity placement for the new import_scene
        configure_model(new_model, model_data,placement)
        
        annotation_collection=new_annotation()
        context.collection.children.link(annotation_collection) 

        
        LOOP_GUARD_MAX=8
        for depth, _obj in walk_object_tree(new_model):
            if depth > LOOP_GUARD_MAX:
                raise Exception("infinite (or too deep) object parent-child tree")
            move_object_into_collection(_obj, annotation_collection)
        
        
                    
        
        
        # properties 
        return {"FINISHED"}
       
