import os  
import tempfile 
import urllib.parse
import urllib.request
import shutil

from typing import Set, Callable
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
    
    

    def execute(self, context: Context) -> Set[str]:
        
        scheme = urllib.parse.urlparse(self.model_url).scheme        
        if scheme not in {"http", "https"}:
            message = "unsupport url scheme %s for network retrieve" % (scheme,)
            logger.warn(message)
            return {"CANCELLED"}

        with tempfile.TemporaryDirectory(dir=bpy.app.tempdir) as tempdirname:
            model_basename = os.path.basename( self.model_url)
            local_filepath = os.path.join(tempdirname,model_basename)
           
            with urllib.request.urlopen( self.model_url ) as http_open_context:
                if http_open_context.status not in {200}:
                    message = "HTTP status returned as %s : retrieval cancelled" \
                                 % http_open_context.status
                    logger.warn(message)
                    return {"CANCELLED"}
                 
                try:
                    http_mimetype = http_open_context.headers["Content-Type"]
                    logger.debug(f"http header shows Content-Type {http_mimetype}")
                except KeyError:
                    http_mimetype = ""
                    
                    
                with open(local_filepath, 'wb') as out_file:
                    shutil.copyfileobj(http_open_context, out_file)
                # closing out of urlopen Context Manager, with 
                # URL data downloaded to local_filepath and 
                # http_mimetype set to the Content-Type (or to "")
    
                    
            mimetype = self.mimetype or http_mimetype
            
            # call the ImportLocalModel Operator to import the contents
            # of the local_filepath file into Blender as a Blender Object
            _op : Callable[...,Set[str]] = \
            bpy.ops.iiif.import_local_model # pyright:ignore[reportAttributeAccessIssue]
            res = _op(filepath=local_filepath, mimetype=mimetype)
            
            # Closing out of the TemporaryDirectory context manager. The directory
            # and the local_filepath will be deleted.
            # the res value is FINISHED or CANCELLED from the import of the local_filepath
            # and active_object should be set to the new Blender object. As well, the
            # IIIF_TEMP_FORMAT custom property will identify the mime-type that guided the
            # Blender import of the file.
        
        if "CANCELLED" in res:
            return res
            
        # including this just as a sanity-check
        if context.active_object is None:
            message = "context.active object is None after iiif.import_local_model"
            logger.warn(message)
        return {"FINISHED"}
