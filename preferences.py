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

from bpy.app.handlers import persistent

from .fn import get_addon_prefs, open_addon_prefs, draw_kmi_custom, get_tool_presets_keymap
# from rna_keymap_ui import draw_km, draw_kmi
from .properties import STORYTOOLS_PGT_gp_settings # gp local settings
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
    """
    Update function called when sidebar UI settings are changed.
    Handles unregistering panels with the old category name and
    registering them with the new category name.
    """
    # Import at function level to avoid circular imports
    from .ui import (
        panel_classes,
        unregister_panels,
        register_panels,
    )
    
    unregister_panels()

    if self.show_sidebar_ui:
        register_panels(self.category.strip())

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
            ('GPSETTINGS', 'GP Settings', 'Grease Pencil settings', 1),
            ('TOOLPRESETS', 'Tool Presets', 'Manage tool presets and change their shortcuts', 2),
            ('RESETLIST', 'Reset List', 'Choose some UI and tools to restore in one click', 3),
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
        name="Move Object Use Visual Hint",
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

    use_top_view_map: BoolProperty(
        name="Minimap Corner During Transforms",
        description="Show a top view minimap in viewport corner during some transforms actions",
        default=True)

    top_view_map_size: FloatProperty(
        name="Top View Map Size, as percentage of viewport height",
        default=22, min=2, max=90, soft_min=5, soft_max=40, subtype='PERCENTAGE')
        # default=0.2, min=0.05, max=1.0, soft_min=0.1, soft_max=0.4)

    ### --- Grease pencil settings

    gp : PointerProperty(type=STORYTOOLS_PGT_gp_settings) # gp local settings

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

    ## Hint / Tips / Warning management

    use_warnings : BoolProperty(
        name='Enable Hints And Warnings',
        description="Show beginner friendly warnings and hints",
        default=True)

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
            col.prop(self, 'use_warnings')
            
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

            box = col.box()
            bcol = box.column()
            bcol.label(text='Tools Settings:', icon='MESH_CIRCLE')
            # bcol.label(text='Move In Depth', icon='EMPTY_SINGLE_ARROW')
            bcol.prop(self, 'use_visual_hint', text='Move Object Visual Hints')
            subcol = bcol.column(align=True)
            subcol.prop(self, 'visual_hint_start_color', text='Near Color')
            subcol.prop(self, 'visual_hint_end_color', text='Far Color')
            subcol.active = self.use_visual_hint

            bcol.separator()
            bcol.prop(self, 'use_top_view_map', text='Minimap View During Transforms')
            subcol = bcol.column(align=True)
            subcol.prop(self, 'top_view_map_size', text='Top View Size')
            subcol.active = self.use_top_view_map

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

            ## Git update code
            if self.is_git_repo:
                box = col.box()
                box.label(text='Addon Update')
                if self.is_git_repo and self.has_git:
                    box.operator('storytools.git_pull', text='Pull Last Update Using Git', icon='PLUGIN')
                else:
                    box.label(text='Addon can be updated using git')
                    row = box.row()
                    row.operator('wm.url_open', text='Download and install git here', icon='URL').url = 'https://git-scm.com/download/'
                    row.label(text='then restart blender')

        elif self.pref_tab == 'GPSETTINGS':
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
            
            ## gp local settings
            ## GP properties that are also in scene through property group
            ## single options
            # col.prop(self.gp, 'frame_offset')

            col.separator()
            col.label(text='GP control bar behavior:')
            col.label(text='Following settings are replicated in scene on new files', icon='INFO')
            ## All at once
            for prop_name in self.gp.bl_rna.properties.keys():
                if prop_name in ('name', 'rna_type'):
                    continue
                if prop_name.startswith('sync'):
                    continue
                col.prop(self.gp, prop_name)

        elif self.pref_tab == 'TOOLPRESETS':
            
            
            """ # Direct draw
            kc = bpy.context.window_manager.keyconfigs.user
            user_keymaps = kc.keymaps
            km = user_keymaps.get('Grease Pencil Paint Mode') # limit to paint mode
            for kmi in reversed(km.keymap_items):
                if kmi.idname == 'storytools.set_draw_tool':
                    ## native kmi draw not needed, using custom
                    # if kmi.is_user_defined:
                    #     # col.template_keymap_item_properties(kmi)
                    #     # draw_kmi(kc, kc.keymaps, km, kmi, col, 0) # native template do not allow removal
                    #     # continue
                    draw_kmi_custom(km, kmi, col)
                    # user_kms.append((km, kmi))

            # for km, kmi in sorted(user_kms, key=lambda x: x[1].type):
            #     draw_kmi_custom(km, kmi, col)
            """

            col.label(text='First number is for ordering (order based on shortcut when 0)', icon='INFO')
            for km, kmi in get_tool_presets_keymap():
                draw_kmi_custom(km, kmi, col)

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
        ## prefs have changed, set dirty flag
        context.preferences.is_dirty = True
        return {"FINISHED"}

class STORYTOOLS_OT_remove_keymap_item(bpy.types.Operator):
    bl_idname = "storytools.remove_keymap_item"
    bl_label = "Remove keymap item"
    bl_description = "Remove keymap item"
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
        
        # kmi = km.keymap_items.from_id(self.item_id)
        km.keymap_items.remove(kmi)
        context.preferences.is_dirty = True
        return {"FINISHED"}

class STORYTOOLS_OT_add_tool_preset_shortcut(bpy.types.Operator):
    bl_idname = "storytools.add_tool_preset_shortcut"
    bl_label = "Add Tool Preset Shortcut"
    bl_description = "Add a tool preset shortcut in user keymap\
        \nAdd new keymap entry: Grease pencil > Grease Pencil Paint Mode\
        \nWith operator idname 'storytools.set_draw_tool' and default value"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        ## Add keymap entry to USER keymap (not ADDON), treated differently in preference display 
        user_km = bpy.context.window_manager.keyconfigs.user
        # km = user_km.keymaps.get('Grease Pencil Paint Mode') 
        km = user_km.keymaps.new(name="Grease Pencil Paint Mode", space_type="EMPTY")
        # km.keymap_items
        existing_presets = [kmi for kmi in km.keymap_items if kmi.idname == 'storytools.set_draw_tool']
        
        name = f'Preset {len(existing_presets)}'
        kmi = km.keymap_items.new('storytools.set_draw_tool', type='F6', value='PRESS')
        ## Set default values 
        kmi.properties.name = name
        kmi.properties.mode = 'PAINT_GREASE_PENCIL'
        kmi.properties.tool = 'builtin.brush'
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


### Handler for prefs to scene properties replications
@persistent
def replicate_preference_settings(dummy):
    ## only on new file ?
    # if bpy.data.filepath != "":
    #     return

    ## Instead of doing only on new file, use local scene sync user choice
    prefs = get_addon_prefs()

    ## On register, overwrite scene gp settings property with preferences ones (only on new files)
    for scene in bpy.data.scenes:
        if scene.storytools_gp_settings.sync_mode != 'SYNC_GLOBAL':
            # print('Skip setting replication on scene:', scene.name) #dbg
            continue

        for prop_name in prefs.gp.bl_rna.properties.keys():
            if prop_name in ('name', 'rna_type', 'sync_mode'):
                continue

            # print(f'scene {scene.name} -> replicating {prop_name}') #dbg

            # setattr(scene.storytools_gp_settings, prop_name, getattr(prefs.gp, prop_name)) # Setattr Trigger update !
            
            scene.storytools_gp_settings[prop_name] = getattr(prefs.gp, prop_name) # Do not trigger update !

### --- REGISTER ---

classes = (
    STORYTOOLS_prefs,
    STORYTOOLS_OT_open_addon_prefs,
    STORYTOOLS_OT_restore_keymap_item,
    STORYTOOLS_OT_remove_keymap_item,
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

    if not 'replicate_preference_settings' in [hand.__name__ for hand in bpy.app.handlers.load_post]:
        bpy.app.handlers.load_post.append(replicate_preference_settings)

def unregister():
    if not 'replicate_preference_settings' in [hand.__name__ for hand in bpy.app.handlers.load_post]:
        bpy.app.handlers.load_post.remove(replicate_preference_settings)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
