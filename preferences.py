# SPDX-License-Identifier: GPL-2.0-or-later

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
from .properties import STORYTOOLS_PG_tool_presets

def toggle_gizmo_buttons(self, _):
    from . import gizmo_toolbar
    if self.active_toolbar:
        bpy.utils.register_class(gizmo_toolbar.STORYTOOLS_GGT_toolbar)
        # Force active when user tick the box
        bpy.context.scene.storytools_settings.show_session_toolbar = True 
    else:
        bpy.utils.unregister_class(gizmo_toolbar.STORYTOOLS_GGT_toolbar)

def ui_in_sidebar_update(self, _):
    from .panels import (STORYTOOLS_PT_storytools_ui,
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
    col.prop(item, 'name')
    if dupe := next((i for i, tool in enumerate(tools) if i != idx and tool.name == item.name), None):
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
            ('SHORTCUTS', 'Shortcuts', 'Change shortcuts affectation', 1),
            ('TOOLS', 'Tools', 'Add or reorganize tools', 2),
            ),
        )
    # items=(
    #     ('UI', 'Interface', 'Customize interface elements', 0),
    #     ('SHORTCUTS', 'Shortcuts', 'Change shortcuts affectation', 1),
    #     ('SETTINGS', 'Settings', 'Various settings', 2),
    #     ),

    ## UI settings

    show_sidebar_ui: BoolProperty(
        name="Enable Sidebar Panel",
        description="Show Storytools Sidebar UI",
        default=True,
        update=ui_in_sidebar_update,
    )

    default_edit_line_opacity : FloatProperty(
        name='Default Edit Line Opacity',
        description="Edit line opacity for newly created objects\
            \nSome users prefer to set it to 0 (show only selected line in edit mode)\
            \nBlender default is 0.5",
        default=0.2, min=0.0, max=1.0)

    active_toolbar : BoolProperty(
        name='Enable Bottom Toolbar',
        description="Show viewport bottom toolbar with gizmo buttons",
        default=True, update=toggle_gizmo_buttons)

    toolbar_margin : IntProperty(
        name='Toolbar margin',
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
        description="Backdrop size of the toolbar icons (Blender gizmo buttons are around 14)",
        default=20,
        min=12, max=40)

    toolbar_gap_size : IntProperty(
        name='Button Distance',
        description="Gap size between buttons in toolbar icons",
        default=46,
        min=20, max=200)

    object_gz_color : FloatVectorProperty(
        name="Object Buttons Color",
        description="Object buttons gizmo backdrop color",
        default=(0.3, 0.3, 0.3), min=0, max=1.0, step=3, precision=2,
        subtype='COLOR_GAMMA', size=3)

    camera_gz_color : FloatVectorProperty(
        name="Camera Buttons Color",
        description="Camera buttons gizmo backdrop color",
        default=(0.1, 0.1, 0.1), min=0, max=1.0, step=3, precision=2,
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

    ## Tool presets
    tool_presets : PointerProperty(type=STORYTOOLS_PG_tool_presets)


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
            col.label(text='Sidebar Settings:', icon='NODE_SIDE')
            col.prop(self, 'show_sidebar_ui')
            subcol = col.column()
            subcol.prop(self, 'category')
            subcol.active = self.show_sidebar_ui
            if not self.show_sidebar_ui:
                col.label(text='Layer/Material Sync is disabled when sidebar panel is off', icon='INFO')

            col.separator()
            col.label(text='Toolbar Settings:', icon='STATUSBAR')
            col.prop(self, 'active_toolbar')
            tool_col = col.column()
            tool_col.prop(self, 'toolbar_margin')
            tool_col.prop(self, 'toolbar_gap_size')
            tool_col.prop(self, 'toolbar_backdrop_size')
            # tool_col.prop(self, 'toolbar_icon_bounds')
            
            tool_col.separator()
            tool_col.prop(self, 'object_gz_color')
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
            col.label(text='Object Settings:', icon='GREASEPENCIL')
            col.prop(self, 'default_edit_line_opacity')

        elif self.pref_tab == 'SHORTCUTS':

            user_keymaps = bpy.context.window_manager.keyconfigs.user.keymaps
            # km = user_keymaps['Grease Pencil Stroke Paint Mode']

            from . keymaps import addon_keymaps
            # user_kms = []
            for akm in set([kms[0] for kms in addon_keymaps]):
                km = user_keymaps.get(akm.name)
                if not km:
                    continue
                for kmi in reversed(km.keymap_items):
                    if kmi.idname == 'storytools.set_draw_tool':
                        draw_kmi_custom(km, kmi, col)
                        # user_kms.append((km, kmi))
                
            # for km, kmi in sorted(user_kms, key=lambda x: x[1].type):
            #     draw_kmi_custom(km, kmi, col)
        
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

class STORYTOOLS_OT_open_addon_prefs(bpy.types.Operator):
    bl_idname = "storytools.open_addon_prefs"
    bl_label = "Open Storytools Prefs"
    bl_description = "Open Storytools addon preferences window in addon tab\
        \nprefill the search with addon name"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        open_addon_prefs()
        return {'FINISHED'}

## UIlists

class STORYTOOLS_OT_move_collection_item(bpy.types.Operator):
    bl_idname = "storytools.move_collection_item"
    bl_label = "Move Item"
    bl_description = "Move item in list up or down"
    bl_options = {'REGISTER', 'INTERNAL'}

    # direction : bpy.props.IntProperty(default=1)
    direction : bpy.props.EnumProperty(
        items=(
            ('UP', 'Move Up', 'Move up'),
            ('DOWN', 'Move down', 'Move down'),
        ),
        default='UP',
    )

    prop_name : bpy.props.StringProperty()
    items_name : bpy.props.StringProperty()

    def execute(self, context):
        pg = getattr(get_addon_prefs(), self.prop_name)
        uilist = getattr(pg, self.items_name)
        index = pg.index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        uilist.move(neighbor, index)
        list_length = len(uilist) - 1 # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)
        list_index = max(0, min(new_index, list_length))

        setattr(pg, 'index', list_index)
        refresh_areas()
        return {'FINISHED'}
    
## Manage tools presets
class STORYTOOLS_OT_add_toolpreset(bpy.types.Operator):
    '''Add '''
    bl_idname = "storytools.add_toolpreset"
    bl_label = "Edit Source"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        tools = get_addon_prefs().tool_presets.tools
        tools.add()
        context.area.tag_redraw()
        return {'FINISHED'}

class STORYTOOLS_OT_remove_toolpreset(bpy.types.Operator):
    '''Remove storytools Tool preset'''
    bl_idname = "storytools.remove_toolpreset"
    bl_label = "Remove toolpreset"
    bl_options = {'REGISTER', 'INTERNAL'}

    # index : bpy.props.IntProperty()

    def execute(self, context):
        pg = get_addon_prefs().tool_presets
        self.report({'INFO'}, f'Removed {pg.tools[pg.index].name}')
        pg.tools.remove(pg.index)
        context.area.tag_redraw()
        return {'FINISHED'}

class STORYTOOLS_UL_toolpreset_list(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, active_property, index):

        self.use_filter_show = False # force closed search
        layout.label(text=f'{active_property}')
        layout.label(text=item.name)
        ## display icon if using blender icons with gizmos

        # layout.operator('storytools.edit_toolpreset', text='', icon='PRESET')

    # def draw_filter(self, context, layout):
    #     row = layout.row()
    #     subrow = row.row(align=True)
    #     subrow.prop(self, "filter_name", text="") # Only show items matching this name (use ‘*’ as wildcard)

    #     # reverse order
    #     icon = 'SORT_DESC' if self.use_filter_sort_reverse else 'SORT_ASC'
    #     subrow.prop(self, "use_filter_sort_reverse", text="", icon=icon) # built-in reverse

    # def filter_items(self, context, data, propname):
    #     collec = getattr(data, propname)
    #     helper_funcs = bpy.types.UI_UL_list

    #     flt_flags = []
    #     flt_neworder = []
    #     if self.filter_name:
    #         flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, collec, "name",
    #                                                       reverse=self.use_filter_sort_reverse)#self.use_filter_name_reverse)
    #     return flt_flags, flt_neworder

### --- REGISTER ---

classes = (
    ## UI list
    STORYTOOLS_OT_move_collection_item,
    STORYTOOLS_OT_add_toolpreset,
    STORYTOOLS_OT_remove_toolpreset,
    STORYTOOLS_UL_toolpreset_list,

    ## prefs
    STORYTOOLS_prefs,
    STORYTOOLS_OT_open_addon_prefs,
    STORYTOOLS_OT_restore_keymap_item,
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
