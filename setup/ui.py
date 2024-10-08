import bpy
from .. import fn

class STORYTOOLS_PT_quick_setup(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER" # "UI"
    # bl_category = "View" # Gpencil
    bl_label = "Quick Setup"
    bl_options = {"INSTANCED"}

    # def draw_header_preset(self, context):
    #     layout = self.layout
    #     layout.operator("storytools.open_addon_prefs", text='', icon='PREFERENCES')
    
    # @classmethod
    # def poll(cls, context):
    #     return context.object and context.object.type == 'GPENCIL'

    def draw(self, context):
        col = self.layout.column()
        col.label(text='place holder')
        col.operator('storytools.setup_drawing', text='Quick UI Reset', icon='GREASEPENCIL')

        col.separator()
        col.label(text="Settings Presets")

        ## Export / Restore settings
        col.operator('storytools.save_load_settings_preset', text='View Settings Presets', icon='PRESET').category = 'view_settings'
        col.operator('storytools.save_load_settings_preset', text='Tool Settings Presets', icon='PRESET').category = 'tool_settings'


        ## -- Workspace setup
        show_workspace_switch = context.window.workspace.name != 'Storyboard'

        if show_workspace_switch:
            col.label(text='Workspace:')
            col.operator('storytools.set_storyboard_workspace', text='Storyboard Workspace', icon='WORKSPACE')

        col.separator()
        col.operator("storytools.open_addon_prefs", text='Open Storytools Preferences', icon='PREFERENCES')

        ## Minimap
        # col.separator()
        # if not fn.is_minimap_viewport(context):
        #     col.label(text='Minimap:')
        #     col.operator('storytools.setup_minimap_viewport', text='Viewport to minimap', icon='WORLD').split_viewport = False
        #     col.operator('storytools.setup_minimap_viewport', text='Split With Minimap', icon='SPLIT_HORIZONTAL').split_viewport = True


        # show_storypencil_setup = len(context.window_manager.windows) == 1 and context.preferences.addons.get('storypencil')
        # if show_workspace_switch or show_storypencil_setup:        
        #     col.separator()
        #     col.label(text='Workspace:')

        #     if show_workspace_switch:
        #         col.operator('storytools.set_storyboard_workspace', text='Storyboard Workspace', icon='WORKSPACE')

        #     if show_storypencil_setup: # Experimental Dual setup
        #         col.operator('storytools.setup_storypencil', text='Setup Storypencil (dual window)', icon='WORKSPACE')

def drawing_setup_ui(self, context):
    """Drawing Setup pop-up to set in header"""
    layout = self.layout
    # layout.operator('storytools.setup_drawing', text='', icon='GREASEPENCIL')
    layout.popover(panel='STORYTOOLS_PT_quick_setup', text='', icon='GREASEPENCIL')

def register():
    bpy.utils.register_class(STORYTOOLS_PT_quick_setup)
    bpy.types.VIEW3D_HT_header.append(drawing_setup_ui)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(drawing_setup_ui)
    bpy.utils.unregister_class(STORYTOOLS_PT_quick_setup)
