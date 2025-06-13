import datetime
import os
import urllib.request
from typing import Set

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from .initialize_collections import initialize_annotation
import json
import logging

from ..utils.blender_naming import generate_name_from_id

logger = logging.getLogger("import-model")


class ImportModel(Operator, ImportHelper):
    """Import IIIF 3D Model"""

    bl_idname = "iiif.import_model"
    bl_label = "Import IIIF Model Resource"

    filename_ext = ""
    filter_glob: StringProperty(  # type: ignore
        default="*.glb;*.gltf", options={"HIDDEN"}
    )
    
    filepath: StringProperty(  # type: ignore
        name="File Path",
        description="Path to the input file",
        maxlen=0,
        subtype="FILE_PATH",
        options={'HIDDEN'}
    )

    model_url: StringProperty(  # type: ignore
        name="URL / IIIF id",
        description="URL to external 3D resource",
        maxlen=0,
        subtype="NONE",
    )

        
    def execute(self, context: Context) -> Set[str]:

        annotation_page_collection = context.collection
        if not annotation_page_collection.get("iiif_type","") == "AnnotationPage":
            logger.warning("invalid context.collection: %r" % (annotation_page_collection,))
            return {"CANCELLED"}
            
        if not self.filepath:
            logger.warning("ImportModel.execute : no filepath set" )
            return {"CANCELLED"}
        
        logger.info("call to import model at %s" % self.filepath)
        # logging.getLogger('glTFImporter')
        #storedLevel = logging.getLogger('glTFImporter').level
        #logging.getLogger('glTFImporter').setLevel(logger.level)
        try:
            retCode = bpy.ops.import_scene.gltf(filepath=self.filepath, loglevel=2)
            logger.info("gltf import returned %r" % (retCode,))
        except Exception as exc:
            logger.error("glTF import error", exc)
            return {"FINISHED"}
        #finally:
        #    logging.getLogger('glTFImporter').setLevel(storedLevel)
        
        new_model = bpy.context.active_object
        logger.info("new_model: %r" % (new_model,))
        
        if self.model_url:
            iiif_id = self.model_url
        else:
            import pathlib
            iiif_id = pathlib.Path(self.filepath).as_uri()
        new_model["iiif_id"] = iiif_id
        
        import os.path
        file_ext = os.path.splitext( self.filepath )[1].lower()
        
        ext_to_mime = {
            ".glb" : "model/gltf-binary",
            ".gltf": "model/gltf+json"
        }
        
        model_format = ext_to_mime.get(file_ext, None)
        
        new_model_data = {
            "id" : None,
            "type" : None
        }
        if model_format:
            new_model_data["format"] = model_format
        
        
        new_model["iiif_json"] = json.dumps(new_model_data)
        new_model["iiif_type"] = "Model"
        
        annotation_collection=bpy.data.collections.new("Annotation")
        initialize_annotation( annotation_collection )    
        annotation_page_collection.children.link(annotation_collection) 
        annotation_collection.name = generate_name_from_id( annotation_collection ) or annotation_collection.name

        if new_model.users_collection:
            for col in new_model.users_collection:
                col.objects.unlink(new_model)
        annotation_collection.objects.link(new_model)       
        
        
        return {"FINISHED"}

            
class ImportLocalModel(ImportModel, ImportHelper):
    bl_idname = "iiif.import_local_model"
    bl_label = "Import local file as model"    
    
    # developer note VM 2025-04-19 : just put this here as a reminder
    # of how UI works with the operator, Not needed for production
    def invoke(self, context, event):
        logger.info("ImportLocalModel.invoke entered")
        rv = ImportHelper.invoke(self, context,event)
        return rv


class ImportNetworkModel(ImportModel, ImportHelper):
    bl_idname = "iiif.import_network_model"
    bl_label = "Import remote resource as model"    
    
    
    def invoke(self, context, event):
        logger.info("ImportRemoteModel.invoke entered")
        rv = context.window_manager.invoke_props_dialog(self, width=640)
        logger.info("return from invoke_props_dialog %r : %r" % (rv, self.model_url) )
        return rv

    def execute(self, context: Context) -> Set[str]:
        logger.info("stub execution only with %r : %r" % (self.model_url, self.filepath))
        self.filepath = self.download_model(self.model_url)
        return ImportModel.execute(self, context)
        
    
     
    # developer note: following is copy of the method
    # from the importer Operator as developed by K Niebes
    # a TODO is to somehow share this function, perhaps by clever multiple
    # inheritance  
    def download_model(self, url: str) -> str:
        """Download the model file from the given URL"""
        temp_dir = bpy.app.tempdir
        time_string = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        model_name = os.path.basename(url)
        model_extension = os.path.splitext(model_name)[1]
        temp_file = os.path.join(
            temp_dir, f"temp_model_{time_string}_{model_name}{model_extension}"
        )

        try:
            #self.report({"DEBUG"}, f"Downloading model from {url} to {temp_file}")
            logger.info( f"Downloading model from {url} to {temp_file}" )
            urllib.request.urlretrieve(url, temp_file)
            logger.info( f"Successfully downloaded model to {temp_file}") 
            return temp_file
        except Exception as e:
            logger.exception( f"Error downloading model: {str(e)}" , e)
            self.report({"ERROR"}, f"Error downloading model: {str(e)}")
            raise
