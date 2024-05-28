import bpy
from bpy.types import Panel
from ..fn import get_addon_prefs

class STORYTOOLS_PT_map_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Minimap"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        prefs = get_addon_prefs()
        if context.region.type == "HEADER":
            self.layout.operator("storytools.map_frame_objects", text="", icon="ZOOM_SELECTED")
            # self.layout.prop(prefs, "minimap_mode", text="", icon="ZOOM_SELECTED")
        else:
            self.layout.operator("storytools.map_frame_objects", text="")
            # self.layout.prop(prefs, "minimap_mode", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        prefs = get_addon_prefs()
        col = layout.column(align=True)
        ## Full display
        # col.prop(prefs, "nested_level", text='Nested Level')
        col.operator("storytools.setup_minimap_viewport", text='Setup Minimap Viewport')
        col.operator("storytools.disable_minimap_viewport", text='Disable Minimap Viewport')
        col.separator()
        col.label(text='Recenter Map:')
        col.operator("storytools.map_frame_objects", text='Frame GP Objects and Camera')
        col.operator("storytools.map_frame_objects", text='Frame GP Objects').target = 'GP'
        col.operator("view3d.view_all", text='Frame All')

def draw_header_button(self, context):
    self.layout.popover("STORYTOOLS_PT_map_ui", text="")

classes = (
    STORYTOOLS_PT_map_ui,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_HT_header.append(draw_header_button)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    bpy.types.VIEW3D_HT_header.remove(draw_header_button)