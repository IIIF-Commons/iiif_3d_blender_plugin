from bpy.props import StringProperty
from bpy.types import Panel, Scene

properties = {
    "iiif_manifest_id": StringProperty(
        name="Manifest ID",
        description="ID of the IIIF Manifest",
        default="https://example.org/iiif/3d/manifest.json"
    ),
    "iiif_manifest_label": StringProperty(
        name="Manifest Label",
        description="Label of the IIIF Manifest",
        default="Scene"
    ),
    "iiif_manifest_summary": StringProperty(
        name="Manifest Summary",
        description="Summary of the IIIF Manifest",
        default="Scene exported from Blender"
    )
}

def register_ui_properties():
    for prop_name, prop_value in properties.items():
        setattr(Scene, prop_name, prop_value)

def unregister_ui_properties():
    for prop_name in properties.keys():
        delattr(Scene, prop_name)

class IIIFManifestPanel(Panel):
    bl_label = "IIIF Manifest"
    bl_idname = "SCENE_PT_iiif_manifest"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        if not context:
            return

        layout = self.layout
        scene = context.scene
        if layout is not None and scene is not None:
            layout.prop(scene, "iiif_manifest_id")
            layout.prop(scene, "iiif_manifest_label")
            layout.prop(scene, "iiif_manifest_summary")
