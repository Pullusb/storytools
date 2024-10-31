import bpy

from bpy.types import Operator, Panel
from bpy.props import BoolProperty

from .. import fn


class STORYTOOLS_PT_gp_settings_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools"
    bl_label = "Grease pencil options"
    bl_options = {'INSTANCED'}

    def draw(self, context):
        layout = self.layout
        # layout.use_property_split = True
        layout.use_property_decorate = False
        # prefs = fn.get_addon_prefs()
        col = layout.column() # align=True
        ## Full display
        # col.prop(prefs, "nested_level", text='Nested Level')
        col.label(text='Grease Pencil')
        # col.prop(context.object.data, 'edit_line_color')
        col.prop(context.object.data.grid, 'color')
        
        col.separator()
        col.label(text='Frame Settings:')
        col.prop(context.scene.storytools_gp_settings, 'frame_offset', text='Frame Offset')

        col.separator()
        col.label(text='Target Layers:')
        col.prop(context.scene.storytools_gp_settings, 'frame_target_layers', text='')
        # row = col.row(align=True)
        # row.prop(context.scene.storytools_gp_settings, 'frame_target_layers', text='Layer', expand=True)
        
        col.separator()
        col.label(text='Keyframe Type:')
        col.prop(context.scene.storytools_gp_settings, 'keyframe_type', text='')
        
        col.separator()
        col.label(text='Sync Settings:')
        col.prop(context.scene.storytools_gp_settings, 'sync_mode', text='')
        ## TODO: add a sync button to propagate sync mode on all scene ?

        # col.separator()
        # col.operator("storytools.open_addon_prefs", text='Open Storytools Preferences', icon='PREFERENCES')


classes = (
    STORYTOOLS_PT_gp_settings_ui,
    )

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
