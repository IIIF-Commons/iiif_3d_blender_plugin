
from bpy.props import ( BoolProperty,
                        FloatVectorProperty,
                        PointerProperty,)
from bpy.utils import register_class, unregister_class
from bpy.types import  Panel, PropertyGroup, Collection
from .utils.blender_setup import set_scene_background_color

import logging
logger = logging.getLogger("iiif.scene_background")


def background_color_changed( sender, context ):
    set_scene_background_color( sender.color )
    
def background_export_changed( sender, context ):
    pass
    
class IIIFBackgroundProperties( PropertyGroup ):

    color : FloatVectorProperty( # type: ignore
             name = "Background Color",
             subtype = "COLOR",
             default = (1.0,1.0,1.0,1.0),
             size = 4,
             update=background_color_changed
    )
             
    export : BoolProperty(   # type: ignore  
        name = "Export to Manifest",
        default = False,
        update=background_export_changed
    )
    
class IIIBackgroundPanel(Panel):
    bl_label = "IIIF Background"
    bl_idname = "COLLECTION_PT_iiif_background"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "collection"

    
    @classmethod
    def poll(cls, context):
        """
        This implementation of poll will disable drawing of the 
        Panel unless the active collection  (instance of Collection)
        is one that organizes a IIIF Scene resource
        """
        if context.collection.get("iiif_type","") == "Scene":
            return True
        return None
        
    def draw(self, context):
        if not context:
            return

        layout = self.layout
        collection = context.collection
        
        layout.prop(collection.background, "export") # type: ignore
        layout.prop(collection.background, "color")  # type: ignore

classes = (
    IIIBackgroundPanel,
    IIIFBackgroundProperties
)


def register_background_properties():
    for cls in classes:
        register_class(cls)

    # his assignment will add these custom properties to the 
    # Collection class. Those properties are defined for all Collection instances
    # but will only be used for those Collection isntances that organize
    # a IIIF Scene resource
    Collection.background = PointerProperty(type=IIIFBackgroundProperties) # type: ignore

    
def unregister_background_properties():
    for cls in classes:
        unregister_class(cls)


