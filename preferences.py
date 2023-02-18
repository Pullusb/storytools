# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from pathlib import Path
from shutil import which
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty)

def get_addon_prefs():
    return bpy.context.preferences.addons[__package__].preferences

def toggle_gizmo_buttons(context, scene):
    from . import GZ_toolbar
    if get_addon_prefs().active_toolbar:
        bpy.utils.register_class(GZ_toolbar.STORYTOOLS_GGT_toolbar)
        # Force active when user tick the box
        bpy.context.scene.storytools_settings.show_session_toolbar = True 
    else:
        bpy.utils.unregister_class(GZ_toolbar.STORYTOOLS_GGT_toolbar)

class STORYTOOLS_prefs(bpy.types.AddonPreferences):
    bl_idname = __name__.split('.')[0] # or __package__

    default_edit_line_opacity : bpy.props.FloatProperty(
        name='Default Edit Line Opacity',
        description="Edit line opacity for newly created objects\
            \nSome users prefer to set it to 0 (show only selected line in edit mode)\
            \nBlender default is 0.5",
        default=0.2, min=0.0, max=1.0)

    active_toolbar : bpy.props.BoolProperty(
        name='Active Toolbar',
        description="Show viewport Bottom Toolbar with gizmo buttons",
        default=True, update=toggle_gizmo_buttons)

    toolbar_margin : bpy.props.IntProperty(
        name='Toolbar margin',
        description="Space margin between viewport and bottom tool bar Gizmo buttons",
        default=36,
        soft_min=-100, soft_max=500,
        min=-1000, max=1000)
    
    # toolbar_icon_bounds : bpy.props.IntProperty(
    #     name='Icon bounds',
    #     description="Bounds of the toolbar icons",
    #     default=34,
    #     min=0, max=100)
    
    toolbar_backdrop_size : bpy.props.IntProperty(
        name='Icon Backdrop Size',
        description="Backdrop size of the toolbar icons (Blender gizmo buttons are around 14)",
        default=24,
        min=12, max=40)

    toolbar_gap_size : bpy.props.IntProperty(
        name='Button Distance',
        description="Gap size between buttons in toolbar icons",
        default=62,
        min=20, max=200)

    object_gz_color : bpy.props.FloatVectorProperty(
        name="Object Buttons Color",
        description="Object buttons gizmo backdrop color",
        default=(0.3, 0.3, 0.3), min=0, max=1.0, step=3, precision=2,
        subtype='COLOR_GAMMA', size=3)

    camera_gz_color : bpy.props.FloatVectorProperty(
        name="Camera Buttons Color",
        description="Camera buttons gizmo backdrop color",
        default=(0.1, 0.1, 0.1), min=0, max=1.0, step=3, precision=2,
        subtype='COLOR_GAMMA', size=3)

    # Update variables
    is_git_repo : BoolProperty(default=False)
    has_git : BoolProperty(default=False)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        col = layout.column()
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
        
        tool_col.active = self.active_toolbar

        col.separator()
        col.label(text='Object Settings:', icon='GREASEPENCIL')
        col.prop(self, 'default_edit_line_opacity')

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

### --- REGISTER ---

classes=(
STORYTOOLS_prefs,
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