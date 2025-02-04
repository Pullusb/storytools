import bpy
from .. import fn

class STORYTOOLS_PT_viewport_setup(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    # bl_region_type = "HEADER"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Viewport Setup"
    bl_options = {"INSTANCED"}

    # @classmethod
    # def poll(cls, context):
    #     return not fn.is_minimap_viewport(context)

    def draw_header(self, context):
        layout = self.layout
        if fn.is_minimap_viewport(context):
            layout.operator("storytools.map_frame_objects", text="", icon="ZOOM_SELECTED")
        else:
            layout.operator("storytools.setup_drawing", text='', icon='GREASEPENCIL')

        # if fn.is_minimap_viewport(context):
        #     if context.region.type == "HEADER":
        #         self.layout.operator("storytools.map_frame_objects", text="", icon="ZOOM_SELECTED")
        #         # self.layout.prop(prefs, "minimap_mode", text="", icon="ZOOM_SELECTED")
        #     else:
        #         self.layout.operator("storytools.map_frame_objects", text="")
        #         # self.layout.prop(prefs, "minimap_mode", text="")
        # else:
        #     if context.region.type == "HEADER":
        #         self.layout.operator("storytools.setup_drawing", text='', icon='GREASEPENCIL')
        #     else:
        #         self.layout.operator("storytools.setup_drawing", text='')

    def draw(self, context):
        col = self.layout.column()

        if fn.is_minimap_viewport(context):
            ## Minimap view operators
            col.label(text='Recenter Map:')
            col.operator("storytools.map_frame_objects", text='Frame GP Objects and Camera')
            col.operator("storytools.map_frame_objects", text='Frame GP Objects').target = 'GP'
            col.operator("view3d.view_all", text='Frame All')

            ## TODO restrict selection to current active type / restore selection
            col.separator()
            col.operator("storytools.disable_minimap_viewport", text='Disable Minimap Viewport')

        else:
            ## setttgings 
            # col.label(text='Draw settings')
            # col.operator('storytools.setup_drawing', text='Quick UI Reset', icon='GREASEPENCIL')

            col.label(text="Settings Presets")

            ## Export / Restore settings
            col.operator('storytools.save_load_settings_preset', text='View Settings Presets', icon='PRESET').category = 'view_settings'
            col.operator('storytools.save_load_settings_preset', text='Tool Settings Presets', icon='PRESET').category = 'tool_settings'

            col.separator()
            ## -- Workspace load
            # show_workspace_switch = context.window.workspace.name != 'Storyboard'
            # if show_workspace_switch:
            col.label(text='Workspace:')
            col.operator('storytools.set_storyboard_workspace', text='Storyboard Workspace', icon='WORKSPACE')

            ## -- Open addon preferences
            col.separator()
            col.operator("storytools.open_addon_prefs", text='Open Storytools Preferences', icon='PREFERENCES')

            ## Minimap
            col.separator()
            if not fn.is_minimap_viewport(context):
                col.label(text='Minimap: (Work in progress)')
                col.operator('storytools.setup_minimap_viewport', text='Viewport to minimap', icon='WORLD').split_viewport = False
                col.operator('storytools.setup_minimap_viewport', text='Split With Minimap', icon='SPLIT_HORIZONTAL').split_viewport = True


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
    self.layout.popover('STORYTOOLS_PT_viewport_setup', text='') # icon='GREASEPENCIL'

def register():
    bpy.utils.register_class(STORYTOOLS_PT_viewport_setup)
    bpy.types.VIEW3D_HT_header.append(drawing_setup_ui)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(drawing_setup_ui)
    bpy.utils.unregister_class(STORYTOOLS_PT_viewport_setup)
