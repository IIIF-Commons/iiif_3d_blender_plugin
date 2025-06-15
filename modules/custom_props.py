from typing import Set
import bpy
from bpy.types import Collection, Context, Object, Operator, Panel

### Metadata Operators ###

class AddIIIF3DObjProperties(Operator):
    """Add IIIF3D manifest required object properties"""

    bl_idname = "add_obj_properties.iiif_manifest"
    bl_label = "Add IIIF 3D Properties"

    def execute(self, context: Context) -> Set[str]:
        try:
            obj = context.view_layer.objects.active
            if obj is not None:
                if "iiif_annotation_id" not in obj:
                    obj["iiif_annotation_id"] = obj.name
                if "iiif_source_url" not in obj:
                    obj["iiif_source_url"] = "https://example.org/iiif/3d/manifest.json"

            return {"FINISHED"}
        except Exception as e:
            import traceback

            self.report({"ERROR"}, f"Error adding IIIF properties: {str(e)}")
            traceback.print_exc()
            return {"CANCELLED"}

class AddIIIF3DCollProperties(Operator):
    """Add IIIF3D manifest required collection properties"""

    bl_idname = "add_coll_properties.iiif_manifest"
    bl_label = "Add IIIF 3D Properties"

    def execute(self, context: Context) -> Set[str]:
        try:
            coll = context.collection
            if "iiif_annotation_id" not in coll:
                coll["iiif_annotation_id"] = coll.name
            if "iiif_source_url" not in coll:
                coll["iiif_source_url"] = "https://example.org/iiif/3d/manifest.json"

            return {"FINISHED"}
        except Exception as e:
            import traceback

            self.report({"ERROR"}, f"Error adding IIIF properties: {str(e)}")
            traceback.print_exc()
            return {"CANCELLED"}

### Metadata Panels ###

def rna_idprop_quote_path(prop):
    return "[\"{:s}\"]".format(bpy.utils.escape_identifier(prop))

def draw(self, context, context_member, prop_type):
        
    layout = self.layout

    operator = "add_obj_properties.iiif_manifest" if context_member == "object" else "add_coll_properties.iiif_manifest"
    obj = context.object if context_member == "object" else context.collection

    row = layout.row()
    props = row.operator(operator, text="Add Required", icon='ADD')
    #props.data_path = context_member
    del row
    layout.separator()
  
    for key in obj.keys():
        if not key.startswith("iiif_"):
            continue
        
        split = layout.split(factor=0.4, align=True)
        label_row = split.row()
        label_row.alignment = 'RIGHT'
        label_row.label(text=key, translate=False)

        value_row = split.row(align=True)
        value_column = value_row.column(align=True)
        value_column.prop(obj, rna_idprop_quote_path(key), text="")

        operator_row = value_row.row(align=True)
        operator_row.alignment = 'RIGHT'
        props = operator_row.operator("wm.properties_remove", text="", icon='X', emboss=False)
        props.data_path = self._context_path
        props.property_name = key

class IIIF3DObjMetadataPanel(Panel):
    """Add custom panel for manifest properties"""

    bl_idname = "OBJECT_PT_iiif_obj_props"
    bl_label = "IIIF Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 999

    _context_path = "object"
    _property_type = Object

    def draw(self, context):
        draw(self, context, self._context_path, self._property_type)

class IIIF3DCollMetadataPanel(Panel):
    """Add custom panel for manifest properties"""

    bl_idname = "OBJECT_PT_iiif_coll_props"
    bl_label = "IIIF Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "collection"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 999

    _context_path = "collection"
    _property_type = Collection

    def draw(self, context):
        draw(self, context, self._context_path, self._property_type)
    
