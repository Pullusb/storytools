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
            if context.region.type != "HEADER":
                ## Hack: Disabled col property to avoid clicking on propertie
                sub = col.row()
                op = sub.operator('storytools.info_note', text='Minimap Options', emboss=False)
                op.text = ''
                op.title = ''
                sub.enabled = False
            col.label(text='Recenter Map:')
            col.operator("storytools.map_frame_objects", text='Frame GP Objects and Camera').target = 'ALL' # default
            col.operator("storytools.map_frame_objects", text='Frame GP Objects').target = 'GP'
            col.operator("storytools.map_frame_objects", text='Frame Active Object').target = 'ACTIVE'
            col.separator()
            col.operator("view3d.view_all", text='Frame All')

            if context.region.type == "HEADER":
                col.separator()
                col.operator("storytools.disable_minimap_viewport", text='Disable Minimap Viewport', icon='LOOP_BACK')

        else:
            ## settings 
            # col.label(text='Draw settings')
            # col.operator('storytools.setup_drawing', text='Quick UI Reset', icon='GREASEPENCIL')

            ## -- Open addon preferences
            col.operator("storytools.open_addon_prefs", text='Open Storytools Preferences', icon='PREFERENCES')

            col.separator()
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
            col.operator('storytools.set_storyboard_dual_window_workspace', text='Storyboard Dual Workspace', icon='WORKSPACE')
            # col.operator('storytools.setup_spark', text='Storyboard Spark Workspace', icon='WORKSPACE')

            ## Minimap
            col.separator()
            if not fn.is_minimap_viewport(context):
                col.label(text='Minimap Setup:')
                col.operator('storytools.setup_minimap_viewport', text='Viewport To Minimap', icon='WORLD').split_viewport = False
                col.operator('storytools.setup_minimap_viewport', text='Split With Minimap', icon='SPLIT_HORIZONTAL').split_viewport = True
                col.operator('storytools.setup_minimap_on_pointed_editor', text='Pick Editor To Minimap', icon='RESTRICT_SELECT_OFF').split_editor = False
                ## point and split is bugged
                # col.operator('storytools.setup_minimap_on_pointed_editor', text='Pick And Split Editor', icon='SPLIT_HORIZONTAL').split_editor = True

            ## Static storyboard layout generator
            col.separator()
            col.label(text='Static Storyboard:')
            col = col.column(align=True)
            row = col.row(align=True)
            row.operator("storytools.create_static_storyboard_pages", text='Create Storyboard Pages', icon='GRID')
            # row.menu("STORYTOOLS_MT_storyboard_presets_management", text="", icon='TOOL_SETTINGS') # menu for presets management
            row.menu("STORYTOOLS_MT_static_storyboard_options", text="", icon='TOOL_SETTINGS') # menu for presets management and animatic creation
            if context.object and context.object.type == 'GREASEPENCIL' and context.object.get('stb_settings'):
                subcol = col.column(align=True)
                subcol.label(text='Panel Management:')
                subcol.operator("storytools.storyboard_offset_panel_modal", text='Insert A Panel', icon='ADD').mode = 'INSERT'
                subcol.operator("storytools.storyboard_offset_panel_modal", text='Remove A Panel', icon='REMOVE').mode = 'DELETE'
                col.separator()
            col.operator("storytools.render_storyboard_images", text='Render StoryBoard', icon='RESTRICT_RENDER_OFF')
            col.menu("STORYTOOLS_MT_export_storyboard_to_pdf", icon='DOCUMENTS', text='Create PDF')

            # show_storypencil_setup = len(context.window_manager.windows) == 1 and context.preferences.addons.get('storypencil')
            # if show_workspace_switch or show_storypencil_setup:        
            #     col.separator()
            #     col.label(text='Workspace:')

            #     if show_workspace_switch:
            #         col.operator('storytools.set_storyboard_workspace', text='Storyboard Workspace', icon='WORKSPACE')

            #     if show_storypencil_setup: # Experimental Dual setup
            #         col.operator('storytools.setup_storypencil', text='Setup Storypencil (dual window)', icon='WORKSPACE')


## --- Marker management in Timeline

class STORYTOOLS_PT_marker_management(bpy.types.Panel):
    bl_space_type = "DOPESHEET_EDITOR"
    # bl_region_type = "HEADER"
    bl_region_type = "UI"
    bl_label = "Marker Management"
    bl_options = {"INSTANCED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Scale markers:")
        row = layout.row(align=True)
        row.operator("storytools.time_compression", text="Compress", icon="TRIA_LEFT").direction = 'COMPRESS'
        row.operator("storytools.time_compression", text="Dilate", icon="TRIA_RIGHT").direction = 'DILATE'

def marker_management_ui(self, context):
    """Add a panel to the marker management UI"""

    if not context.scene.storytools_settings.show_marker_management:
        return

    layout = self.layout
    layout.label(text="Markers:")
    row = layout.row(align=True)
    row.operator("storytools.push_markers", text="", icon="TRIA_LEFT").direction = 'LEFT'
    row.operator("storytools.push_markers", text="", icon="TRIA_RIGHT").direction = 'RIGHT'
    row.operator("wm.call_panel", text="", icon='DOWNARROW_HLT').name = "STORYTOOLS_PT_marker_management"

## Options related to static storyboard
class STORYTOOLS_MT_static_storyboard_options(bpy.types.Menu):
    bl_label = "Static Storyboard Options"

    def draw(self, context):
        layout = self.layout
        layout.menu("STORYTOOLS_MT_storyboard_presets_management", icon='FILE_LARGE', text='Manage Storyboard Presets')
            
        layout.label(text='Animatic:')
        layout.operator("storytools.create_animatic_from_board", text='Create Animatic Scene', icon='SCENE_DATA') # SCENE_DATA, MARKER_HLT ## idea of animatic
        layout.prop(context.scene.storytools_settings, "show_marker_management", text="Show Marker Management In Timeline")
        ## TODO: add a quick way to change frame radius size (to avoid getting in animatic frame)
        # frame_material = bpy.data.materials.get('Frames')

## Options related to static storyboard
def drawing_setup_ui(self, context):
    """Drawing Setup pop-up to set in viewport header"""
    self.layout.popover('STORYTOOLS_PT_viewport_setup', text='') # icon='GREASEPENCIL'


classes = (
    STORYTOOLS_PT_marker_management,
    STORYTOOLS_MT_static_storyboard_options,
    STORYTOOLS_PT_viewport_setup,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_HT_header.append(drawing_setup_ui)
    bpy.types.DOPESHEET_HT_header.append(marker_management_ui)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(drawing_setup_ui)
    bpy.types.DOPESHEET_HT_header.remove(marker_management_ui)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
