# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty,
                        CollectionProperty)

from bpy.types import PropertyGroup

# update on prop change
def change_edit_lines_opacity(self, context):
    for gp in bpy.data.grease_pencils:
        if not gp.is_annotation:
            gp.edit_line_color[3]=self.edit_lines_opacity

""" 
class STORYTOOLS_PGT_km_preset(PropertyGroup):
    mode : EnumProperty(
        name="Mode", description="Using shortcut will change to this mode", 
        default='PAINT_GPENCIL', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('PAINT_GPENCIL', 'Draw', 'Switch to draw mode', 0),
            ('EDIT_GPENCIL', 'Edit', 'Switch to edit mode', 1),
            ('SCULPT_GPENCIL', 'Sculpt', 'Switch to Sculpt mode', 2),
            ('OBJECT', 'Object', 'Switch to Object mode', 3),
            ))

    tool : StringProperty(
        name="Tool", description="Tool to set",
        default="builtin_brush.Draw")
    
    layer : StringProperty(
        name="Layer", description="Layer to set (exact name, case sensitive)\
            \nEmpty field = no change",
        default="Sketch")
    
    material : StringProperty(
        name="Material", description="Material to set (exact name, case sensitive)\
            \nEmpty field = No change or use layer-material synchronisation if enabled",
        default="line")

    name : StringProperty(
        name="Preset Name (optional)", description="Name that define this preset.\
            \nJust for personal organisation",
        default="")

class STORYTOOLS_PGT_keymap_presets(PropertyGroup):
    preset_0 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
    preset_1 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
    preset_2 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
    preset_3 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
    preset_4 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
    preset_5 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
    preset_6 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
    preset_7 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
    preset_8 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
    preset_9 : CollectionProperty(type=STORYTOOLS_PGT_km_preset)
 """
class STORYTOOLS_PGT_distances(PropertyGroup) :
    ## HIDDEN to hide the animatable dot thing

    initial_distance : FloatProperty(
        name="Distance", description="Initial distance when creating a new grease pencil object", 
        default=8.0, min=0.0, max=600, step=3, precision=1)
    
    ## property with update on change
    edit_lines_opacity : FloatProperty(
        name="Edit Lines Opacity", description="Change edit lines opacity for all grease pencils in scene", 
        default=0.5, min=0.0, max=1.0, step=3, precision=2, update=change_edit_lines_opacity)
    
    # stringprop : StringProperty(
    #     name="str prop",
    #     description="",
    #     default="")# update=None, get=None, set=None
    
    initial_parented : BoolProperty(
        name="Attached To Camera",
        description="When Creating the object, Attach it to the camera",
        default=False) # options={'ANIMATABLE'},subtype='NONE', update=None, get=None, set=None

    select_active_only : BoolProperty(
        name="Select Active Only",
        description="When changing object, deselect other objects if not in 'Object mode'",
        default=True)
    
    ## enum (with Icon)
    material_sync : EnumProperty(
        name="Material Sync", description="Only jump to defined keyframe type", 
        default='INDIVIDUAL', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('INDIVIDUAL', 'Sync Materials', 'Sync material and layer per object', 0),
            ('GLOBAL', 'Sync Across Objects', 'Sync material and layer globally ', 1),
            ('DISABLED', 'No Sync', 'No material association when changing layer', 2),
            ))

    show_session_toolbar : bpy.props.BoolProperty(
        name='Show Toolbar',
        description="Show/Hide viewport Bottom Toolbar buttons on this session\
            \nTo completely disable, uncheck 'Active Toolbar' in addon Storytools preferences",
        default=True)
    
    show_focal : bpy.props.BoolProperty(
        name='Show Focal',
        description="Show the focal length properties of every camera",
        default=True)

    show_camera_panel : bpy.props.BoolProperty(
        name='Cameras',
        description="Show the camera panel",
        default=True)
    
    ## GP Object properties
    show_gp_users : bpy.props.BoolProperty(
        name='Show Linked Data Toggle',
        description="Show object user data when object has multiple user (when object have multiple users)",
        default=True)
    
    show_gp_parent : bpy.props.BoolProperty(
        name='Show Parent Info',
        description="Show When Object is parented",
        default=True)

    show_gp_in_front : bpy.props.BoolProperty(
        name='Show In Front Toggle',
        description="Show object in front toggle",
        default=True)

    ## Storyboard Keymap items
    
    ## Add the presets... collection property or individual settings ?
    ## Collection is much cleaner, But incompatible with selective pref load...
    
    

classes=(
# STORYTOOLS_PGT_km_preset,
# STORYTOOLS_PGT_keymap_presets,
STORYTOOLS_PGT_distances,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.storytools_settings = bpy.props.PointerProperty(type = STORYTOOLS_PGT_distances)
    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.storytools_settings