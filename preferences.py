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
                        CollectionProperty,
                        FloatVectorProperty)

from bpy.app.handlers import persistent
from textwrap import dedent

from .constants import (DEFAULT_LAYER_STACK,
                        DEFAULT_MATERIAL_STACK,
                        DEFAULT_ACTIVE_LAYER)
from .fn import (get_addon_prefs, 
                 open_addon_prefs, 
                 draw_kmi_custom, 
                 get_tool_presets_keymap,
                 get_default_layer_stack_entries, 
                 get_default_material_stack_entries)
# from rna_keymap_ui import draw_km, draw_kmi
from .properties import STORYTOOLS_PGT_gp_settings # gp local settings


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
        unregister_panels,
        register_panels,
    )

    unregister_panels()

    if self.show_sidebar_ui:
        register_panels(self.category.strip())

# region layer/mat stacks

def set_active_update(self, _context):
    ## Only one entry can be flagged as active
    if not self.set_active:
        return
    prefs = get_addon_prefs()
    for entry in prefs.layer_stack:
        ## check all entry that are not the one currently clicked (set active to False on those)
        ## (same as entry != self and entry.set_active)
        if entry.as_pointer() != self.as_pointer() and entry.set_active:
            entry.set_active = False

class STORYTOOLS_PG_layer_stack_entry(bpy.types.PropertyGroup):
    name : StringProperty(
        name="Layer Name",
        description="Name of the layer to create on new grease pencil objects",
        default="Layer")

    material : StringProperty(
        name="Material",
        description="Material associated with this layer for default layer/material synchronisation\
            \nShould match a material from the default material stack (exact name, case sensitive)\
            \nEmpty field = no association",
        default="")

    brush : StringProperty(
        name="Brush",
        description="Brush associated with this layer for default layer/brush synchronisation\
            \nAsset name from the Essentials Grease Pencil draw brushes (ex: 'Pencil', 'Ink Pen', 'Fill')\" \
            \nFor user custom asset with path containing a '/': 'Saved/Brushes/MyBrush.asset.blend/Brush/MyBrush')\
            \nFor online brush of the asset essential , ex: 'ONLINE_ESSENTIALS::::brushes/grease_pencil/Graphite_Dense.blend/Brush/Graphite Dense'\
            \nEmpty field = no association",
        default="")
    # User custom brush is resolved as: CUSTOM::User Library::Saved/Brushes/turbo_brush.asset.blend/Brush/turbo_brush

    stroke_type : EnumProperty(
        name="Stroke Type",
        description="Brush stroke type associated with this layer (Blender 5.1+)\
            \nNo Change = keep the brush's own stroke type",
        default='NONE',
        items=(
            ('NONE', 'No Change', 'Do not set a stroke type on this layer', 0),
            ('STROKE', 'Stroke', 'Set brush to stroke-only', 1),
            ('FILL', 'Fill', 'Set brush to fill-only', 2),
            ('BOTH', 'Stroke And Fill', 'Set brush to both stroke and fill', 3),
            ))

    set_active : BoolProperty(
        name="Set As Active Layer",
        description="Set this layer as the active one on new grease pencil objects\
            \nWhen no layer is flagged, the top layer is used",
        default=False, update=set_active_update)

def same_color_update(self, _context):
    ## Keep stored fill in sync when enabling same color mode
    ## (so unchecking later starts editing fill from the stroke color)
    if self.same_color:
        self.fill_color = self.stroke_color

class STORYTOOLS_PG_material_stack_entry(bpy.types.PropertyGroup):
    name : StringProperty(
        name="Material Name",
        description="Name of the material to create on new grease pencil objects\
            \nIf a material with this name already exists in blend, it is reused as is",
        default="Material")

    stroke_color : FloatVectorProperty(
        name="Stroke Color",
        description="Stroke color of the material",
        subtype='COLOR', size=4, min=0.0, max=1.0,
        default=(0.0, 0.0, 0.0, 1.0))

    fill_color : FloatVectorProperty(
        name="Fill Color",
        description="Fill color of the material",
        subtype='COLOR', size=4, min=0.0, max=1.0,
        default=(0.0, 0.0, 0.0, 1.0))

    same_color : BoolProperty(
        name="Same Stroke And Fill Color",
        description="Use stroke color for both stroke and fill",
        default=True, update=same_color_update)

    holdout : BoolProperty(
        name="Holdout",
        description="Material masks underlying strokes and objects\
            \n(enable stroke and fill holdout on created material)",
        default=False)

class STORYTOOLS_UL_layer_stack_entries(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        row = layout.row(align=True)
        row.label(text='', icon='BLANK1')
        row.prop(item, 'name', text='', emboss=True, icon='OUTLINER_DATA_GP_LAYER')
        ## data is the addon prefs (collection owner), search associated material in material stack
        row.prop_search(item, 'material', data, 'material_stack', text='', icon='MATERIAL')
        row.prop(item, 'brush', text='', icon='BRUSH_DATA')
        row.prop(item, 'stroke_type', text='')
        row.prop(item, 'set_active', text='', icon='RADIOBUT_ON' if item.set_active else 'RADIOBUT_OFF', emboss=False)

class STORYTOOLS_UL_material_stack_entries(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        split = layout.row(align=True)
        split.label(text='', icon='BLANK1')
        split.prop(item, 'name', text='', emboss=True, icon='MATERIAL')
        row = split.row(align=True)
        color_row = row.row(align=True)
        color_row.prop(item, 'stroke_color', text='')
        if not item.same_color:
            color_row.prop(item, 'fill_color', text='')
        else:
            color_row.label(text='')
        row.prop(item, 'same_color', text='', icon='LINKED' if item.same_color else 'UNLINKED', emboss=False)
        row.prop(item, 'holdout', text='', icon='HOLDOUT_ON' if item.holdout else 'HOLDOUT_OFF', emboss=False)

# region Preferences
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
    
    ## edit_line_opacity not available anymore, kept in case feature is re-implemented in the future
    # default_edit_line_opacity : FloatProperty(
    #     name='Default Edit Line Opacity',
    #     description="Edit line opacity for newly created objects\
    #         \nSome users prefer to set it to 0 (show only selected line in edit mode)\
    #         \nBlender default is 0.5",
    #     default=0.2, min=0.0, max=1.0)

    use_autolock_layers : BoolProperty(
        name='Default Autolock Layers',
        description="Choose if layer autolock is enabled when creating a grease pencil object using popup",
        default=True)
    
    use_lights : BoolProperty(
        name='Default Layer Use Light',
        description="Choose if layers should have use light on when creating a grease pencil object using popup",
        default=False)

    ## Default modifiers and effects on new GP objects

    ## HSV modifier
    use_hsv_modifier : BoolProperty(
        name='Add Hue/Saturation Modifier',
        description="Add a Hue/Saturation modifier on new grease pencil objects",
        default=False)

    # hsv_hue : FloatProperty(
    #     name='Hue',
    #     description="Hue of the Hue/Saturation modifier added on new grease pencil objects",
    #     default=0.5, min=0.0, max=1.0)

    # hsv_saturation : FloatProperty(
    #     name='Saturation',
    #     description="Saturation of the Hue/Saturation modifier added on new grease pencil objects",
    #     default=1.0, min=0.0, soft_max=2.0)

    # hsv_value : FloatProperty(
    #     name='Value',
    #     description="Value of the Hue/Saturation modifier added on new grease pencil objects",
    #     default=1.0, min=0.0, soft_max=2.0)

    ## Blur FX:
    use_blur_effect : BoolProperty(
        name='Add Blur Effect',
        description="Add a Blur FX on newly created grease pencil objects",
        default=False)
    
    # blur_use_dof_mode : BoolProperty(
    #     name='Use Depth Of Field',
    #     description="Blur intensity is driven by the active camera depth of field settings\
    #         \n(camera DoF must be enabled)",
    #     default=True)

    # blur_samples : IntProperty(
    #     name='Samples',
    #     description="Number of blur samples of the Blur effect added on new grease pencil objects\
    #         \n(zero disables the blur)",
    #     default=32, min=0, max=32)

    ## Default layer and material stacks
    ## Filled with default values at first registration (when empty -> using seed_default_stacks)
    layer_stack : CollectionProperty(type=STORYTOOLS_PG_layer_stack_entry)

    layer_stack_index : IntProperty(default=0, options={'HIDDEN'})

    material_stack : CollectionProperty(type=STORYTOOLS_PG_material_stack_entry)

    material_stack_index : IntProperty(default=0, options={'HIDDEN'})

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

    ## Hint / Tips / Warning management

    use_warnings : BoolProperty(
        name='Enable Hints And Warnings',
        description="Show beginner friendly warnings and hints",
        default=True)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        row = layout.row(align=True)
        row.use_property_split = False
        row.prop(self, "pref_tab", expand=True)

        col = layout.column()

        if self.pref_tab == 'SETTINGS':
            # region Global settings
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

        elif self.pref_tab == 'GPSETTINGS':
            # region GP settings
            col.label(text='Grease Pencil Settings:', icon='GREASEPENCIL')
            row = col.row(align=True)
            row.prop(self, 'default_placement', text='Set Placement / Orientation')
            row.prop(self, 'default_orientation', text='')
            ## placement and orientation on two lines
            # col.prop(self, 'default_placement')
            # col.prop(self, 'default_orientation')
            col.prop(self, 'use_autolock_layers')
            col.prop(self, 'use_lights')
            # col.prop(self, 'default_edit_line_opacity')

            ## Layers and material stacks list

            layer_names = [entry[0] for entry in get_default_layer_stack_entries(prefs=self)]
            material_names = [m['name'] for m in get_default_material_stack_entries(prefs=self)]
            ## Active tool presets, to check name pairing with stacks (skip inactive keymaps)
            preset_kmis = [kmi for _km, kmi in get_tool_presets_keymap() if kmi.active]

            ## Default layer stack
            box = col.box()
            bcol = box.column()
            bcol.use_property_split = False
            bcol.label(text='Layer Stack:', icon='GREASEPENCIL_LAYER_GROUP')

            row = bcol.row()
            row.template_list("STORYTOOLS_UL_layer_stack_entries", "", self, "layer_stack", self, "layer_stack_index", rows=4)
            side = row.column(align=True)
            side.operator('storytools.stack_entry_add', text='', icon='ADD').stack = 'layer_stack'
            subside = side.column(align=True)
            subside.enabled = len(self.layer_stack) > 1
            subside.operator('storytools.stack_entry_remove', text='', icon='REMOVE').stack = 'layer_stack'
            side.separator()
            ops = side.operator('storytools.stack_entry_move', text='', icon='TRIA_UP')
            ops.stack, ops.direction = 'layer_stack', 'UP'
            ops = side.operator('storytools.stack_entry_move', text='', icon='TRIA_DOWN')
            ops.stack, ops.direction = 'layer_stack', 'DOWN'
            bcol.operator('storytools.stack_reset', text='Reset To Default Layers', icon='LOOP_BACK').stack = 'layer_stack'

            ## Warn on tool preset layer targets with no match in stack
            wcol = bcol.column(align=True)
            for kmi in preset_kmis:
                props = kmi.properties
                if not props.layer or props.layer in layer_names:
                    continue
                ## incorrect target, show warning
                preset_name = props.name if props.name else kmi.to_string()
                row = wcol.row()
                row.label(text=f'Layer "{props.layer}" targeted by tool preset "{preset_name}" is not in stack', icon='ERROR')
                op_hint = row.operator('storytools.info_note', text='', icon='INFO')
                op_hint.title = 'Missing Tool preset target'
                op_hint.text = f'Toolpreset shortcut "{preset_name}" is targeting layer name "{props.layer}"\
                               \nThis name does not appear in current layer stack.\
                               \nAdd this name in layer stack or change/remove the tool preset target (in Tool Presets Tab)'

            ## Default material stack
            box = col.box()
            bcol = box.column()
            bcol.use_property_split = False
            bcol.label(text='Material Stack:', icon='MATERIAL')

            row = bcol.row()
            row.template_list("STORYTOOLS_UL_material_stack_entries", "", self, "material_stack", self, "material_stack_index", rows=5)
            side = row.column(align=True)
            side.operator('storytools.stack_entry_add', text='', icon='ADD').stack = 'material_stack'
            subside = side.column(align=True)
            subside.enabled = len(self.material_stack) > 1
            subside.operator('storytools.stack_entry_remove', text='', icon='REMOVE').stack = 'material_stack'
            side.separator()
            ops = side.operator('storytools.stack_entry_move', text='', icon='TRIA_UP')
            ops.stack, ops.direction = 'material_stack', 'UP'
            ops = side.operator('storytools.stack_entry_move', text='', icon='TRIA_DOWN')
            ops.stack, ops.direction = 'material_stack', 'DOWN'
            bcol.operator('storytools.stack_reset', text='Reset To Default Materials', icon='LOOP_BACK').stack = 'material_stack'

            ## Warn on material references with no match in stack (layer associations and tool preset targets)
            wcol = bcol.column(align=True)
            for l_name, mat_name, *_ in get_default_layer_stack_entries(prefs=self):
                if not mat_name or mat_name in material_names:
                    continue
                wcol.label(text=f'Material "{mat_name}" associated to layer "{l_name}" is not in stack', icon='ERROR')
            for kmi in preset_kmis:
                props = kmi.properties
                if not props.material or props.material in material_names:
                    continue
                preset_name = props.name if props.name else kmi.to_string()
                row = wcol.row()
                row.label(text=f'Material "{props.material}" targeted by tool preset "{preset_name}" is not in stack', icon='ERROR')
                op_hint = row.operator('storytools.info_note', text='', icon='INFO')
                op_hint.title = 'Missing Tool preset material target'
                op_hint.text = f'Toolpreset shortcut "{preset_name}" is targeting material name "{props.layer}"\
                               \nThis name is not in material stack.\
                               \nAdd this name in material stack or change/remove the material tool preset target (in Tool Presets Tab)'

            ## Default modifiers and effects on new objects
            box = col.box()
            bcol = box.column()
            bcol.label(text='Modifiers And Effects', icon='MODIFIER')

            # mod_box = box.box()
            bcol.prop(self, 'use_hsv_modifier')
            # if self.use_hsv_modifier:
            #     subcol = mod_box.column(align=True)
            #     subcol.prop(self, 'hsv_hue')
            #     subcol.prop(self, 'hsv_saturation')
            #     subcol.prop(self, 'hsv_value')

            # mod_box = box.box()
            bcol.prop(self, 'use_blur_effect', text='Add Blur Effect (With DOF enabled)')
            # if self.use_blur_effect:
            #     subcol = mod_box.column(align=True)
            #     subcol.prop(self, 'blur_samples')
            #     subcol.prop(self, 'blur_use_dof_mode')

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
            # region Tool presets
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
            # region Reset list
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
            

            bcol.prop(self, 'set_selection_tool')

            ## Set edit line opacity (not available anymore, kept in case feature is re-implemented in the future)
            # row = bcol.row()
            # row.prop(self, 'set_edit_line_opacity')
            # row.label(text=f'{self.default_edit_line_opacity:.1f} (located in "Settings" Tab)')


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
        \nAdd new keymap entry: Grease pencil > Grease Pencil Draw Mode\
        \nWith operator idname 'storytools.set_draw_tool' and default value"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        ## Add keymap entry to USER keymap (not ADDON), treated differently in preference display 
        user_km = bpy.context.window_manager.keyconfigs.user
        if bpy.app.version >= (5, 1, 0):
            draw_mode_name = 'Grease Pencil Draw Mode'
        else:
            draw_mode_name = 'Grease Pencil Paint Mode'
        km = user_km.keymaps.new(name=draw_mode_name, space_type="EMPTY")
        # km.keymap_items
        existing_presets = [kmi for kmi in km.keymap_items if kmi.idname == 'storytools.set_draw_tool']
        
        name = f'Preset {len(existing_presets)}'
        kmi = km.keymap_items.new('storytools.set_draw_tool', type='F6', value='PRESS')
        ## Set default values 
        kmi.properties.name = name
        kmi.properties.mode = 'PAINT_GREASE_PENCIL'
        kmi.properties.tool = 'builtin.brush'
        return {'FINISHED'}


# region stack management

def fill_stack_with_defaults(prefs, stack):
    '''Fill given stack collection ('layer_stack' or 'material_stack') with default values'''
    collection = getattr(prefs, stack)
    collection.clear()
    if stack == 'layer_stack':
        for l_name, mat_name, brush, stroke_type in DEFAULT_LAYER_STACK:
            item = collection.add()
            item.name = l_name
            item.material = mat_name
            item.brush = brush
            item.stroke_type = stroke_type
            item.set_active = l_name == DEFAULT_ACTIVE_LAYER
    else:
        for mat_def in DEFAULT_MATERIAL_STACK:
            item = collection.add()
            for attr, value in mat_def.items():
                setattr(item, attr, value)
    setattr(prefs, stack + '_index', 0)

def seed_default_stacks(prefs=None):
    '''Fill layer and material stacks with default values when empty
    Called on register (deferred) and on file load'''
    prefs = prefs or get_addon_prefs()
    for stack in ('layer_stack', 'material_stack'):
        if not len(getattr(prefs, stack)):
            fill_stack_with_defaults(prefs, stack)

## Count int need to be global to be preserved between each timer call (rescheduled until None is returned)
_filling_attempts = 0

def _seed_default_stacks_timer():
    global _filling_attempts
    try:
        seed_default_stacks()
    except Exception:
        ## Preferences may not be available yet, retry a few times
        ## Just an additional security (usually not needed)
        _filling_attempts += 1
        if _filling_attempts < 4:
            print(f"Failed to seed default stacks, {_filling_attempts} retry ") # Dbg
            return 0.2
    return None

## Stack option to choose target UIlist in operators reset, add, remove, move.
_stack_prop = EnumProperty(
    name="Stack",
    items=(
        ('layer_stack', 'Layer Stack', ''),
        ('material_stack', 'Material Stack', ''),
        ),
    default='layer_stack', options={'SKIP_SAVE'})

class STORYTOOLS_OT_stack_reset(bpy.types.Operator):
    bl_idname = "storytools.stack_reset"
    bl_label = "Reset To Default Stack"
    bl_description = "Discard customization and restore the default stack content"
    bl_options = {"REGISTER", "INTERNAL"}

    stack : _stack_prop

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        prefs = get_addon_prefs()
        fill_stack_with_defaults(prefs, self.stack)
        context.preferences.is_dirty = True
        return {'FINISHED'}

class STORYTOOLS_OT_stack_entry_add(bpy.types.Operator):
    bl_idname = "storytools.stack_entry_add"
    bl_label = "Add Stack Entry"
    bl_description = "Add an entry below the selected one"
    bl_options = {"REGISTER", "INTERNAL"}

    stack : _stack_prop

    def execute(self, context):
        prefs = get_addon_prefs()
        collection = getattr(prefs, self.stack)
        collection.add() # new item gets property defaults ('Layer' / 'Material' name)
        ## Place new entry below active one (add() appends at the end)
        target_index = min(getattr(prefs, self.stack + '_index') + 1, len(collection) - 1)
        collection.move(len(collection) - 1, target_index)
        setattr(prefs, self.stack + '_index', target_index)
        context.preferences.is_dirty = True
        return {'FINISHED'}

class STORYTOOLS_OT_stack_entry_remove(bpy.types.Operator):
    bl_idname = "storytools.stack_entry_remove"
    bl_label = "Remove Stack Entry"
    bl_description = "Remove selected entry\
        \nStack always keeps at least one entry"
    bl_options = {"REGISTER", "INTERNAL"}

    stack : _stack_prop

    def execute(self, context):
        prefs = get_addon_prefs()
        collection = getattr(prefs, self.stack)
        if len(collection) <= 1:
            ## Keep at least one entry (empty stack would be re-seeded with defaults)
            self.report({'WARNING'}, 'Stack must keep at least one entry')
            return {'CANCELLED'}
        index = getattr(prefs, self.stack + '_index')
        collection.remove(index)
        setattr(prefs, self.stack + '_index', min(index, len(collection) - 1))
        context.preferences.is_dirty = True
        return {'FINISHED'}

class STORYTOOLS_OT_stack_entry_move(bpy.types.Operator):
    bl_idname = "storytools.stack_entry_move"
    bl_label = "Move Stack Entry"
    bl_description = "Move selected entry in the stack"
    bl_options = {"REGISTER", "INTERNAL"}

    stack : _stack_prop

    direction : EnumProperty(
        items=(('UP', 'Up', ''), ('DOWN', 'Down', '')),
        default='UP', options={'SKIP_SAVE'})

    def execute(self, context):
        prefs = get_addon_prefs()
        collection = getattr(prefs, self.stack)
        index = getattr(prefs, self.stack + '_index')
        target_index = index - 1 if self.direction == 'UP' else index + 1
        if target_index < 0 or target_index >= len(collection):
            return {'CANCELLED'}
        collection.move(index, target_index)
        setattr(prefs, self.stack + '_index', target_index)
        context.preferences.is_dirty = True
        return {'FINISHED'}


class STORYTOOLS_OT_open_addon_prefs(bpy.types.Operator):
    bl_idname = "storytools.open_addon_prefs"
    bl_label = "Open Storytools Prefs"
    bl_description = "Open Storytools addon preferences window in addon tab\
        \nPrefill the search with addon name"
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

    ## Ensure default layer/material stacks are filled (no-op when already populated)
    # seed_default_stacks(prefs)

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

# region register

classes = (
    STORYTOOLS_PG_layer_stack_entry,
    STORYTOOLS_PG_material_stack_entry,
    STORYTOOLS_UL_layer_stack_entries,
    STORYTOOLS_UL_material_stack_entries,
    STORYTOOLS_prefs,
    STORYTOOLS_OT_open_addon_prefs,
    STORYTOOLS_OT_restore_keymap_item,
    STORYTOOLS_OT_remove_keymap_item,
    STORYTOOLS_OT_reload_toolpreset_ui,
    STORYTOOLS_OT_add_tool_preset_shortcut,

    ## 
    STORYTOOLS_OT_stack_reset,
    STORYTOOLS_OT_stack_entry_add,
    STORYTOOLS_OT_stack_entry_remove,
    STORYTOOLS_OT_stack_entry_move,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    ## Deferred stack seeding (preferences not accessible during registration at startup)
    bpy.app.timers.register(_seed_default_stacks_timer, first_interval=0.0)

    if not 'replicate_preference_settings' in [hand.__name__ for hand in bpy.app.handlers.load_post]:
        bpy.app.handlers.load_post.append(replicate_preference_settings)

def unregister():
    if bpy.app.timers.is_registered(_seed_default_stacks_timer):
        bpy.app.timers.unregister(_seed_default_stacks_timer)

    if not 'replicate_preference_settings' in [hand.__name__ for hand in bpy.app.handlers.load_post]:
        bpy.app.handlers.load_post.remove(replicate_preference_settings)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
