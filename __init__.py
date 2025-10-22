from bpy.types import TOPBAR_MT_file_export, TOPBAR_MT_file_import,OUTLINER_MT_collection_new, OUTLINER_MT_collection , Menu
from bpy.utils import register_class, unregister_class

from .modules.test import RunUnitTests

from .modules.ExportManifest import ExportManifest
from .modules.ImportManifest import ImportManifest
from .modules.ImportLocalModel import ImportLocalModel
from .modules.ImportNetworkModel import ImportNetworkModel
from .modules.NewManifest import NewManifest
from .modules.NewCamera import NewCamera
from .modules.LoadLocalModel import LoadLocalModel
from .modules.LoadNetworkModel import LoadNetworkModel
from .modules.SceneBackground import SceneBackground

from .modules.custom_props import (
    AddIIIF3DObjProperties,
    AddIIIF3DCollProperties,
    IIIF3DObjMetadataPanel,
    IIIF3DCollMetadataPanel
)
from .modules.ui import (
    IIIFManifestPanel,
    register_ui_properties,
    unregister_ui_properties,
)

import logging
logger=logging.getLogger("iiif.init")


class OUTLINER_MT_edit_manifest_anno_page(Menu):
    """
    intent is that this menu will be added to the popup
    menu associated with any Blender bpy.type.Collection
    which has an iiif_type property value of AnnotationPage
    """
    bl_label="Add Painting Annotations"
    bl_idname="OUTLINER_MT_edit_manifest"
    
    def draw(self,context):
        layout = self.layout
        layout.operator(ImportLocalModel.bl_idname, text="Add Local Model")
        layout.operator(ImportNetworkModel.bl_idname, text="Add Network Model")
        layout.operator(NewCamera.bl_idname, text="Add Camera")
        
##class OUTLINER_MT_edit_manifest_scene(Menu):
##    """
##    intent is that this menu will be added to the popup
##    menu associated with any Blender bpy.type.Collection
##    which has an iiif_type property value of Scene
##    """
##    bl_label="Edit Background Color"
##    bl_idname="OUTLINER_MT_edit_manifest_scene"
##    
##    def draw(self,context):
##        layout = self.layout
##        layout.operator(NewCamera.bl_idname, text="Add Camera")

def menu_func_manifest_submenu(self,context):
    target_collection = context.collection
    layout = self.layout
    if target_collection.get("iiif_type","") == "AnnotationPage":
        layout.menu(OUTLINER_MT_edit_manifest_anno_page.bl_idname, text="Add Painting Annotation") 
    elif target_collection.get("iiif_type","") == "Scene":
        layout.operator(SceneBackground.bl_idname, text="Set Background Color")

classes = (
    RunUnitTests,
    ImportManifest,
    ExportManifest,
    ImportLocalModel,
    ImportNetworkModel,
    LoadLocalModel,
    LoadNetworkModel,
    SceneBackground,
    IIIFManifestPanel,
    AddIIIF3DObjProperties,
    AddIIIF3DCollProperties,
    IIIF3DObjMetadataPanel,
    IIIF3DCollMetadataPanel,
    NewManifest,
    NewCamera,
    OUTLINER_MT_edit_manifest_anno_page
)

def menu_func_import(self, context):
    self.layout.operator(
        ImportManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )

def menu_func_export(self, context):
    self.layout.operator(
        ExportManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )
    
    
def menu_func_new_manifest(self, context):
    self.layout.operator(
        NewManifest.bl_idname, text="New IIIF Manifest"
    )
    
def register():
    for cls in classes:
        register_class(cls)

    register_ui_properties()

    TOPBAR_MT_file_import.append(menu_func_import)
    TOPBAR_MT_file_export.append(menu_func_export)
    
    OUTLINER_MT_collection_new.append(menu_func_new_manifest)
    
    OUTLINER_MT_collection.append(menu_func_manifest_submenu)

def unregister():
    TOPBAR_MT_file_import.remove(menu_func_import)
    TOPBAR_MT_file_export.remove(menu_func_export)
    
    OUTLINER_MT_collection_new.remove(menu_func_new_manifest)
    
    OUTLINER_MT_collection.append(menu_func_manifest_submenu)

    unregister_ui_properties()

    for cls in classes:
        unregister_class(cls)

if __name__ == "__main__":
    try:
        register()
    except Exception as e:
        print(e)
        unregister()
        raise e
