# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from pathlib import Path
from shutil import which
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty,
                        FloatVectorProperty)

from .fn import get_addon_prefs, open_addon_prefs, draw_kmi_custom, refresh_areas
# from .tool_presets.properties import STORYTOOLS_PG_tool_presets

def toggle_gizmo_buttons(self, _):
    from . import gizmo_toolbar
    if self.active_toolbar:
        bpy.utils.register_class(gizmo_toolbar.STORYTOOLS_GGT_toolbar)
        bpy.utils.register_class(gizmo_toolbar.STORYTOOLS_GGT_toolbar_switch)
        # Force active when user tick the box
        bpy.context.scene.storytools_settings.show_session_toolbar = True 
    else:
        bpy.utils.unregister_class(gizmo_toolbar.STORYTOOLS_GGT_toolbar)
        bpy.utils.unregister_class(gizmo_toolbar.STORYTOOLS_GGT_toolbar_switch)

def toggle_toolpreset_buttons(self, _):
    from . import gizmo_toolpreset_bar
    if self.active_presetbar:
        bpy.utils.register_class(gizmo_toolpreset_bar.STORYTOOLS_GGT_toolpreset_bar)
    else:
        bpy.utils.unregister_class(gizmo_toolpreset_bar.STORYTOOLS_GGT_toolpreset_bar)

def reload_toolpreset_buttons():
    from . import gizmo_toolpreset_bar
    bpy.utils.unregister_class(gizmo_toolpreset_bar.STORYTOOLS_GGT_toolpreset_bar)
    bpy.utils.register_class(gizmo_toolpreset_bar.STORYTOOLS_GGT_toolpreset_bar)

class STORYTOOLS_OT_reload_toolpreset_ui(bpy.types.Operator):
    bl_idname = "storytools.reload_toolpreset_ui"
    bl_label = "Reload UI Presets"
    bl_description = "Reload the toolpreset topbar gizmos in viewport\
        \nNecessary if 'set draw tool' shortcuts have just been customized"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        reload_toolpreset_buttons()
        return {'FINISHED'}

def ui_in_sidebar_update(self, _):
    from .ui import (
        STORYTOOLS_PT_storytools_ui,
        STORYTOOLS_PT_camera_ui,
        STORYTOOLS_PT_drawings_ui,
        STORYTOOLS_PT_layers_ui,
        STORYTOOLS_PT_materials_ui,
        STORYTOOLS_PT_brushes_ui,
        STORYTOOLS_PT_colors_ui,
        STORYTOOLS_PT_palette_ui,
        STORYTOOLS_PT_tool_ui,
                     )
    
    cls_and_id = (
        (STORYTOOLS_PT_storytools_ui, 'STORYTOOLS_PT_storytools_ui'),
        (STORYTOOLS_PT_camera_ui, 'STORYTOOLS_PT_camera_ui'),
        (STORYTOOLS_PT_drawings_ui, 'STORYTOOLS_PT_drawings_ui'),
        (STORYTOOLS_PT_layers_ui, 'STORYTOOLS_PT_layers_ui'),
        (STORYTOOLS_PT_materials_ui, 'STORYTOOLS_PT_materials_ui'),
        (STORYTOOLS_PT_brushes_ui, 'STORYTOOLS_PT_brushes_ui'),
        (STORYTOOLS_PT_colors_ui, 'STORYTOOLS_PT_colors_ui'),
        (STORYTOOLS_PT_palette_ui, 'STORYTOOLS_PT_palette_ui'),
        (STORYTOOLS_PT_tool_ui, 'STORYTOOLS_PT_tool_ui'),
    )

    ## loop to register
    for cls, idname in cls_and_id: 
        has_panel = hasattr(bpy.types, idname)
        if has_panel:
            try:
                bpy.utils.unregister_class(cls)
            except:
                pass

        if self.show_sidebar_ui:
            # STORYTOOLS_PT_storytools_ui.bl_space_type = self.panel_space_type
            cls.bl_category = self.category.strip()
            bpy.utils.register_class(cls)

    ## Old with single panel
    # has_panel = hasattr(bpy.types, 'STORYTOOLS_PT_storytools_ui')
    # if has_panel:
    #     try:
    #         bpy.utils.unregister_class(STORYTOOLS_PT_storytools_ui)
    #     except:
    #         pass

    # if self.show_sidebar_ui:
    #     # STORYTOOLS_PT_storytools_ui.bl_space_type = self.panel_space_type
    #     STORYTOOLS_PT_storytools_ui.bl_category = self.category.strip()
    #     bpy.utils.register_class(STORYTOOLS_PT_storytools_ui)

def toolset_edit_ui(col):
    col.use_property_split = True
    tools = get_addon_prefs().tool_presets.tools
    idx = get_addon_prefs().tool_presets.index
    item = tools[idx]
    # layout.label(text='Name:', icon='INFO') # Tell that it's used by shortcut (better than order)
    col.prop(item, 'preset_name')
    if dupe := next((i for i, tool in enumerate(tools) if i != idx and tool.preset_name == item.preset_name), None):
        col.label(text=f'Name is already used by tool {dupe}')

    col.prop(item, 'mode')
    col.prop(item, 'tool')
    col.prop(item, 'layer')
    col.prop(item, 'material')
    col.prop(item, 'brush')
    col.prop(item, 'icon')
    col.prop(item, 'show')

    # if not item.valid:
    #     col.label(text='Invalid Path', icon='ERROR')

class STORYTOOLS_prefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    category : StringProperty(
            name="Category",
            description="Choose a name for the sidebar category tab",
            default="Storytools",
            update=ui_in_sidebar_update)

    pref_tab : EnumProperty(
        name="Preference Tool Tab", description="Choose preferences to display",
        default='SETTINGS',
        items=(
            ('SETTINGS', 'Settings', 'Customize interface elements and settings', 0),
            ('TOOLPRESETS', 'Tool Presets', 'Manage tool presets and change their shortcuts', 1),
            ('RESETLIST', 'Reset List', 'Choose some UI and tools to restore in one click', 2),
            ),
        )

    ## UI settings

    show_sidebar_ui: BoolProperty(
        name="Enable Sidebar Panel",
        description="Show Storytools Sidebar UI",
        default=True,
        update=ui_in_sidebar_update,
    )

    active_toolbar : BoolProperty(
        name='Enable Bottom Control bar',
        description="Show viewport bottom bar with control gizmo buttons",
        default=True, update=toggle_gizmo_buttons)

    active_presetbar : BoolProperty(
        name='Enable Top Tool Presets Bar',
        description="Show viewport top tool-presets bar",
        default=True, update=toggle_toolpreset_buttons)

    ## Toolbar settings (Control bar)
    toolbar_margin : IntProperty(
        name='Control Bar Margin',
        description="Space margin between viewport and bottom tool bar Gizmo buttons",
        default=36,
        soft_min=-100, soft_max=500,
        min=-1000, max=1000)
    
    # toolbar_icon_bounds : IntProperty(
    #     name='Icon bounds',
    #     description="Bounds of the toolbar icons",
    #     default=34,
    #     min=0, max=100)
    
    toolbar_backdrop_size : IntProperty(
        name='Icon Backdrop Size',
        description="Backdrop size of the control icons (Blender gizmo buttons are around 14)",
        default=18,
        min=12, max=30)

    toolbar_gap_size : IntProperty(
        name='Button Distance',
        description="Gap size between buttons in control bar",
        default=40,
        min=20, max=60)

    ## Toolpreset settings
    presetbar_margin : IntProperty(
        name='Preset Bar Margin',
        description="Space margin between viewport border and tool preset buttons",
        default=18,
        soft_min=-100, soft_max=500,
        min=-1000, max=1000)
    
    presetbar_gap_size : IntProperty(
        name='Preset Bar Button Distance',
        description="Gap size between buttons in tool presets bar",
        default=44,
        min=20, max=200)

    presetbar_backdrop_size : IntProperty(
        name='Icon Backdrop Size',
        description="Backdrop size of the preset bar icons (Blender gizmo buttons are around 14)",
        default=18,
        min=12, max=40)

    ## Minimap settings

    map_always_frame_objects : BoolProperty(
        name='Always Frame Objects',
        description="Constantly set pan and zoom to frame GP objects and camera",
        default=False)

    use_map_name : BoolProperty(
        name='Show Map names',
        description="Show objects name on map",
        default=True)
    
    map_name_size : IntProperty(
        name='Name Size',
        description="Size of the names displayed on minimap",
        default=18,
        min=4, soft_max=100, max=500)
    
    use_map_dot : BoolProperty(
        name='Show Map Dots',
        description="Show colored marker on objects",
        default=True)
    
    map_dot_size : IntProperty(
        name='Object Dot Size',
        description="Size of dots marking objects on map",
        default=10,
        min=1, soft_max=100, max=500)

    ## UI settings
    object_gz_color : FloatVectorProperty(
        name="Object Buttons Color",
        description="Object viewport buttons backdrop color",
        default=(0.3, 0.3, 0.3), min=0, max=1.0, step=3, precision=2,
        subtype='COLOR_GAMMA', size=3)

    camera_gz_color : FloatVectorProperty(
        name="Camera Buttons Color",
        description="Camera viewport buttons backdrop color",
        default=(0.1, 0.1, 0.1), min=0, max=1.0, step=3, precision=2,
        subtype='COLOR_GAMMA', size=3)

    gp_gz_color : FloatVectorProperty(
        name="Grease Pencil Buttons Color",
        description="Grease Pencil viewport buttons backdrop color",
        default=(0.2, 0.2, 0.2), min=0, max=1.0, step=3, precision=2,
        subtype='COLOR_GAMMA', size=3)

    active_gz_color : FloatVectorProperty(
        name="Active Buttons Color",
        description="Color when state of the button is active",
        default=(0.25, 0.43, 0.7), min=0, max=1.0, step=3, precision=2,
        subtype='COLOR_GAMMA', size=3)

    ## Distance overlay color
    use_visual_hint: BoolProperty(
        name="Depth Move Use Visual Hint",
        description="Show colored visual hint when using depth move",
        default=True)

    # (0.2, 0.2, 0.8, 0.1) # Blue
    visual_hint_start_color : FloatVectorProperty(
        name="Visual Hint Start Color", subtype='COLOR_GAMMA', size=4,
        default=(0.2, 0.2, 0.8, 0.15), min=0.0, max=1.0,
        description="Color of the near plane visual hint when using Depth move")
    
    # (0.88, 0.8, 0.35, 0.2) # Yellow
    # (0.7, 0.2, 0.2, 0.22) # Red
    visual_hint_end_color : FloatVectorProperty(
        name="Visual Hint End Color", subtype='COLOR_GAMMA', size=4,
        default=(0.7, 0.2, 0.2, 0.22), min=0.0, max=1.0,
        description="Color of the far plane visual hint when using Depth move")

    ### --- Grease pencil settings

    default_edit_line_opacity : FloatProperty(
        name='Default Edit Line Opacity',
        description="Edit line opacity for newly created objects\
            \nSome users prefer to set it to 0 (show only selected line in edit mode)\
            \nBlender default is 0.5",
        default=0.2, min=0.0, max=1.0)

    use_autolock_layers : BoolProperty(
        name='Default Autolock Layers',
        description="Choose if layer autolock is enabled when creating a grease pencil object using popup",
        default=True)
    
    use_lights : BoolProperty(
        name='Default Layer Use Light',
        description="Choose if layers should have use light on when creating a grease pencil object using popup",
        default=False)

    gp_frame_offset : IntProperty(
        name='Grease Pencil Frame Offset',
        description="Frame offset to apply when creating new frame above an existing one\
            \nOr when applying offset to all subsequents frames",
        default=12,
        min=1, soft_max=300, max=16000)

    default_placement : EnumProperty(
        name='Placement',
        default='ORIGIN',
        description='Set Grease pencil stroke placement settings when creating new object',
        items=(
            ('ORIGIN', 'Origin', 'Draw stroke at Object origin', 'OBJECT_ORIGIN', 0),
            ('CURSOR', '3D Cursor', 'Draw stroke at 3D cursor location', 'PIVOT_CURSOR', 1),
            ('SURFACE', 'Surface', 'Stick stroke to surfaces', 'SNAP_FACE', 2),
            ('STROKE', 'Stroke', 'Stick stroke to other strokes', 'STROKE', 3),
            ('NONE', 'Keep Placement', 'Do not change placement setting', 'BLANK1', 4)
            ),
        )

    default_orientation : EnumProperty(
        name='Orientation',
        description="Set Grease pencil Orientation when creating new objects",
        default='AXIS_Y',
        items=(
            ('VIEW', 'View', 'Align strokes to current view plane', 'RESTRICT_VIEW_ON', 0),
            ('AXIS_Y', 'Front (X-Z)', 'Project strokes to plane locked to Y', 'AXIS_FRONT', 1),
            ('AXIS_X', 'Side (Y-Z)', 'Project strokes to plane locked to X', 'AXIS_SIDE', 2),
            ('AXIS_Z', 'Top (X-Y)', 'Project strokes to plane locked to Z', 'AXIS_TOP', 3),
            ('CURSOR', 'Cursor', 'Align strokes to current 3D cursor orientation', 'PIVOT_CURSOR', 4),
            ('NONE', 'Keep Orientation', 'Do not change orientation setting', 'BLANK1', 5)
            )
        )

    ### --- Preferences for reset screen

    show_sidebar : EnumProperty(
        name='Show Sidebar',
        description="Choose to show/hide sidebar or leave it as it is",
        default='SHOW',
        items=(
            ('SHOW', 'Show Sidebar', 'Customize interface elements and settings', 0),
            ('HIDE', 'Hide Sidebar', 'Manage tool presets and change their shortcuts', 1),
            ('NONE', 'Do Nothing', 'Manage tool presets and change their shortcuts', 2),
            ),
        )

    set_sidebar_tab : BoolProperty(
        name='Set Tab In Sidebar',
        description="Set tab in sidebar",
        default=True)

    sidebar_tab_target : StringProperty(
        name='Set Storytools Tab',
        description="Name of the Tab to set (respect case)",
        default='Storytools')


    set_edit_line_opacity : BoolProperty(
        name='Set Edit Line Opacity',
        description="Set edit line opacity",
        default=True)

    set_selection_tool : EnumProperty(
        name='Set Selection Tool (in edit mode)',
        description="Set the selection tool if in grease pencil edit mode",
        default='builtin.select_lasso',
        items=(
            ('builtin.select_lasso', 'Select Lasso', '', 0),
            ('builtin.select_box', 'Select Box', '', 1),
            ('builtin.select_circle', 'Select Circle', '', 2),
            ('builtin.select', 'Tweak', '', 3),
            ('NONE', 'Do Nothing', 'Do not set any tools', 4),
            ),
        )

    ## Tool presets (Old tool presets)
    # tool_presets : PointerProperty(type=STORYTOOLS_PG_tool_presets)

    # Update variables
    is_git_repo : BoolProperty(default=False)
    has_git : BoolProperty(default=False)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        row = layout.row(align=True)
        row.use_property_split = False
        row.prop(self, "pref_tab", expand=True)

        col = layout.column()

        if self.pref_tab == 'SETTINGS':
            # Tool Presets
            box = col.box()
            bcol = box.column()
            bcol.label(text='Tool Preset Bar Settings:', icon='NODE_TOP')
            bcol.prop(self, 'active_presetbar')
            bcol.prop(self, 'presetbar_margin')
            bcol.prop(self, 'presetbar_gap_size', text='Buttons Spread')
            bcol.prop(self, 'presetbar_backdrop_size')

            # col.separator()

            # Sidebar
            box = col.box()
            bcol = box.column()
            bcol.label(text='Sidebar Settings:', icon='NODE_SIDE')
            bcol.prop(self, 'show_sidebar_ui')
            subcol = bcol.column()
            subcol.prop(self, 'category')
            subcol.active = self.show_sidebar_ui
            if not self.show_sidebar_ui:
                bcol.label(text='Layer/Material Sync is disabled when sidebar panel is off', icon='INFO')

            # col.separator()

            # Controls
            box = col.box()
            bcol = box.column()
            bcol.label(text='Control Bar Settings:', icon='STATUSBAR')
            bcol.prop(self, 'active_toolbar')
            tool_col = bcol.column()
            tool_col.prop(self, 'toolbar_margin')
            tool_col.prop(self, 'toolbar_gap_size', text='Buttons Spread')
            tool_col.prop(self, 'toolbar_backdrop_size')
            # tool_col.prop(self, 'toolbar_icon_bounds')
            
            tool_col.separator()
            
            tool_col.prop(self, 'object_gz_color')
            tool_col.prop(self, 'gp_gz_color')
            tool_col.prop(self, 'camera_gz_color')
            tool_col.prop(self, 'active_gz_color')

            tool_col.active = self.active_toolbar

            col.separator()

            col.label(text='Tools Settings:', icon='MESH_CIRCLE')
            # col.label(text='Move In Depth', icon='EMPTY_SINGLE_ARROW')
            col.prop(self, 'use_visual_hint', text='Move Object Visual Hints')
            subcol = col.column(align=True)
            subcol.prop(self, 'visual_hint_start_color', text='Near Color')
            subcol.prop(self, 'visual_hint_end_color', text='Far Color')
            subcol.active = self.use_visual_hint

            col.separator()
            ## GP setttings
            col.label(text='Grease Pencil Settings:', icon='GREASEPENCIL')
            row = col.row(align=True)
            row.prop(self, 'default_placement', text='Set Placement / Orientation')
            row.prop(self, 'default_orientation', text='')
            ## placement and orientation on two lines
            # col.prop(self, 'default_placement')
            # col.prop(self, 'default_orientation')
            col.prop(self, 'use_autolock_layers')
            col.prop(self, 'use_lights')
            col.prop(self, 'default_edit_line_opacity')
            col.prop(self, 'gp_frame_offset')

            box = col.box()
            bcol = box.column()
            bcol.label(text='Minimap Settings', icon='WORLD_DATA')
            # bcol.prop(self, 'active_map_toolbar')
            tool_col = bcol.column()
            tool_col.prop(self, 'use_map_name')
            tool_col.prop(self, 'map_name_size')
            tool_col.prop(self, 'use_map_dot')
            tool_col.prop(self, 'map_dot_size')
            # tool_col.prop(self, 'map_always_frame_objects')

            ## Potential future Customization
            # tool_col.prop(self, 'map_toolbar_margin')
            # tool_col.prop(self, 'map_toolbar_gap_size', text='Buttons Spread')
            # tool_col.prop(self, 'map_toolbar_backdrop_size')


        elif self.pref_tab == 'TOOLPRESETS':

            user_keymaps = bpy.context.window_manager.keyconfigs.user.keymaps
            ## Note: list only in 'Grease Pencil Stroke Paint Mode' as other modes are not supported yet
            km = user_keymaps.get('Grease Pencil Stroke Paint Mode')

            ## search only based on addon keymaps
            # from . keymaps import addon_keymaps
            # # user_kms = []
            # for akm in set([kms[0] for kms in addon_keymaps]):
            #     km = user_keymaps.get(akm.name)
            #     if not km:
            #         continue
            ## Search on all keymaps
            
            ## TODO: list and reoder based on order (or use dynamic UI list)

            for kmi in reversed(km.keymap_items):
                if kmi.idname == 'storytools.set_draw_tool':
                    draw_kmi_custom(km, kmi, col)
                    # user_kms.append((km, kmi))

            col.separator()
            row = col.row()
            row.operator('storytools.add_tool_preset_shortcut', text="Add New Tool Preset", icon='ADD')
            row.operator('storytools.reload_toolpreset_ui', icon='FILE_REFRESH')

            col.separator()
            box = col.box()
            bcol = box.column()
            bcol.label(text='After any "Tool Presets" is added or changed', icon='INFO')
            bcol.label(text='a click on "Reload UI Presets" button above is needed', icon='BLANK1')
            bcol.label(text='for the modification to take effect in viewport buttons', icon='BLANK1')
            # for km, kmi in sorted(user_kms, key=lambda x: x[1].type):
            #     draw_kmi_custom(km, kmi, col)
        
        elif self.pref_tab == 'RESETLIST':
            box = col.box()
            bcol = box.column()
            bcol.label(text='Following settings are related to "Reset Drawing Setup" operator', icon='INFO')
            bcol.label(text='Used to quickly reset prefered drawing settings', icon='BLANK1')
            bcol.label(text='This operator is located in menu at top right corner in header', icon='GREASEPENCIL')
            # bcol.label(text='Customize to your convenience', icon='BLANK1')

            bcol = box.column()
            
            bcol.prop(self, 'show_sidebar', text='Sidebar State')
            
            row = bcol.row()
            row.prop(self, 'set_sidebar_tab')
            subrow = row.row()
            subrow.prop(self, 'sidebar_tab_target', text='')
            subrow.active = self.set_sidebar_tab
            
            row = bcol.row()
            row.prop(self, 'set_edit_line_opacity')
            row.label(text=f'{self.default_edit_line_opacity:.1f} (located in "Settings" Tab)')

            bcol.prop(self, 'set_selection_tool')


        """
        elif self.pref_tab == 'TOOLS':
            col.label(text='Draw Topbar:', icon='NODE_TOP')
            ## show 
            tool_presets = self.tool_presets
            
            ## Tool UI list
            row = col.row()
            minimum_row = 6 # default number of displayed lines
            row.template_list("STORYTOOLS_UL_toolpreset_list", "", tool_presets, "tools", tool_presets, "index", 
                rows=minimum_row)

            idx = tool_presets.index
            tools = tool_presets.tools

            # UI list right side
            subcol = row.column(align=True)
            ## Add / remove
            subcol.operator('storytools.add_toolpreset', text='', icon='ADD')
            subcol.operator('storytools.duplicate_toolpreset', text='', icon='DUPLICATE')
            subcol.operator('storytools.remove_toolpreset', text='', icon='REMOVE')

            subcol.separator()

            ## move up / down
            move_op = subcol.operator('storytools.move_collection_item', text='', icon='TRIA_UP')
            move_op.direction = 'UP'
            move_op.prop_name = 'tool_presets'
            move_op.items_name = 'tools'

            move_op = subcol.operator('storytools.move_collection_item', text='', icon='TRIA_DOWN')
            move_op.direction = 'DOWN'
            move_op.prop_name = 'tool_presets'
            move_op.items_name = 'tools'

            if idx == -1 or not len(tools):
                col.label(text='No Brush toolpreset selected above', icon='ERROR')
                col.label(text='Use "+" button to add brush')
            else:                
                toolset_edit_ui(col)
        """

        ## Git update code
        if self.is_git_repo:
            box = layout.box()
            box.label(text='Addon Update')
            if self.is_git_repo and self.has_git:
                box.operator('storytools.git_pull', text='Pull Last Update Using Git', icon='PLUGIN')
            else:
                box.label(text='Addon can be updated using git')
                row = box.row()
                row.operator('wm.url_open', text='Download and install git here', icon='URL').url = 'https://git-scm.com/download/'
                row.label(text='then restart blender')

class STORYTOOLS_OT_restore_keymap_item(bpy.types.Operator):
    bl_idname = "storytools.restore_keymap_item"
    bl_label = "Restore keymap item"
    bl_description = "Reset keymap item to default"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return True
    
    km_name : StringProperty()
    # kmi_name : StringProperty()
    kmi_id : IntProperty()

    def execute(self, context):
        km = bpy.context.window_manager.keyconfigs.user.keymaps.get(self.km_name)
        if not km:
            self.report({'ERROR'}, f'No keymap {self.km_name} found')
            return {"CANCELLED"}
        
        kmi = next((i for i in km.keymap_items if i.id == self.kmi_id), None)
        if not kmi:
            self.report({'ERROR'}, f'Keymap item not found')
            return {"CANCELLED"}
        
        # kmi = c.get(self.kmi_name)
        # if not kmi:
        #     self.report({'ERROR'}, f'No key item {self.kmi_name} found')
        #     return {"CANCELLED"}
        km.restore_item_to_default(kmi)

        return {"FINISHED"}

class STORYTOOLS_OT_add_tool_preset_shortcut(bpy.types.Operator):
    bl_idname = "storytools.add_tool_preset_shortcut"
    bl_label = "Add Tool Preset Shortcut"
    bl_description = "Add a tool preset shortcut\
        \nAdd new keymap entry: Grease pencil > Grease Pencil Stroke Paint Mode\
        \nWith opertor id storytools.set_draw_tool and default value"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        user_km = bpy.context.window_manager.keyconfigs.addon
        # km = user_km.keymaps.get('Grease Pencil Stroke Paint Mode') 
        km = user_km.keymaps.new(name = "Grease Pencil Stroke Paint Mode", space_type = "EMPTY")
        # km.keymap_items
        existing_presets = [kmi for kmi in km.keymap_items if kmi.idname == 'storytools.set_draw_tool']
        
        name = f'Preset {len(existing_presets)}'
        kmi = km.keymap_items.new('storytools.set_draw_tool', type='F6', value='PRESS')
        ## Set default values 
        kmi.properties.name = name
        kmi.properties.mode = 'PAINT_GPENCIL'
        kmi.properties.tool = 'builtin_brush.Draw'
        return {'FINISHED'}


class STORYTOOLS_OT_open_addon_prefs(bpy.types.Operator):
    bl_idname = "storytools.open_addon_prefs"
    bl_label = "Open Storytools Prefs"
    bl_description = "Open Storytools addon preferences window in addon tab\
        \nprefill the search with addon name"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        open_addon_prefs()
        return {'FINISHED'}


### --- REGISTER ---

classes = (
    STORYTOOLS_prefs,
    STORYTOOLS_OT_open_addon_prefs,
    STORYTOOLS_OT_restore_keymap_item,
    STORYTOOLS_OT_reload_toolpreset_ui,
    STORYTOOLS_OT_add_tool_preset_shortcut,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

    ## Update section
    prefs = get_addon_prefs()
    ## Change a variable in prefs if a '.git is detected'
    prefs.is_git_repo = (Path(__file__).parent / '.git').exists()
    prefs.has_git = bool(which('git'))

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
