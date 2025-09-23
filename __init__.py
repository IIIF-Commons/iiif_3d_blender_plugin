from bpy.types import TOPBAR_MT_file_export, TOPBAR_MT_file_import,OUTLINER_MT_collection_new, OUTLINER_MT_collection , Menu
from bpy.utils import register_class, unregister_class

from .modules.test import RunUnitTests

from .modules.exporter import ExportManifest
from .modules.importer import ImportManifest
from .modules.ImportLocalModel import ImportLocalModel
from .modules.ImportNetworkModel import ImportNetworkModel
from .modules.NewManifest import NewManifest
from .modules.NewCamera import NewCamera
from .modules.LoadLocalModel import LoadLocalModel

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


class OUTLINER_MT_edit_manifest(Menu):
    """
    intent is that this menu will be added to the popup
    menu associated with any Blender bpy.type.Collection
    which has an iiif_type property value of AnnotationPage
    """
    bl_label="Manifest Editing"
    bl_idname="OUTLINER_MT_edit_manifest"
    
    def draw(self,context):
        layout = self.layout
        layout.operator(ImportLocalModel.bl_idname, text="Add Local Model")
        layout.operator(ImportNetworkModel.bl_idname, text="Add Network Model")
        layout.operator(NewCamera.bl_idname, text="Add Camera")

def menu_func_manifest_submenu(self,context):
    target_collection = context.collection
    if target_collection.get("iiif_type","") == "AnnotationPage":
        self.layout.menu(OUTLINER_MT_edit_manifest.bl_idname, text="Edit Manifest") 

classes = (
    RunUnitTests,
    ImportManifest,
    ExportManifest,
    ImportLocalModel,
    ImportNetworkModel,
    LoadLocalModel,
    IIIFManifestPanel,
    AddIIIF3DObjProperties,
    AddIIIF3DCollProperties,
    IIIF3DObjMetadataPanel,
    IIIF3DCollMetadataPanel,
    NewManifest,
    NewCamera,
    OUTLINER_MT_edit_manifest
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
