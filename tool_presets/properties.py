# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import re
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty,
                        CollectionProperty)

from bpy.types import PropertyGroup
from ..fn import get_addon_prefs

def get_blender_icons_as_enum():
    # return ((i.identifier, i.name, '', i.value) for i in bpy.types.UILayout.bl_rna.functions['prop'].parameters['icon'].enum_items)
    return tuple((i.identifier, i.name, '') for i in bpy.types.UILayout.bl_rna.functions['prop'].parameters['icon'].enum_items)

def increment_name(name):
    if re.search(r'.*\d+$', name):
        ## Increment rightmost number
        return re.sub(r'(\d+)(?!.*\d)', lambda x: str(int(x.group(1))+1).zfill(len(x.group(1))), name)
    ## Add an increment
    return name + '01'

def ensure_preset_tool_unique_name(self, context):
    '''Ensure name is unique'''
    tool_presets = get_addon_prefs().tool_presets
    name = self.preset_name
    while name in [i.preset_name for i in tool_presets.tools if i != self]:
        name = increment_name(name)
    if self.preset_name != name:
        self['preset_name'] = name

class STORYTOOLS_PGT_tool_preset(PropertyGroup):

    preset_name : StringProperty(
        name="Preset Name", description="Name that define the toolsetting\
            \nMust be unique",
        default="",
        update=ensure_preset_tool_unique_name
        )

    mode : EnumProperty(
        name="Mode", description="Using shortcut will change to this mode", 
        default='PAINT_GPENCIL', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('PAINT_GPENCIL', 'Draw', 'Switch to draw mode', 0),
            ('EDIT_GPENCIL', 'Edit', 'Switch to edit mode', 1),
            ('SCULPT_GPENCIL', 'Sculpt', 'Switch to Sculpt mode', 2),
            ('OBJECT', 'Object', 'Switch to Object mode', 3),
            ('NONE', 'Current', 'No mode switch', 4),
            ))

    brush : StringProperty(
        name="Brush", description="Brush to set\
            \nex: Eraser Stroke (with tool builtin_brush.Erase)\
            \nEmpty field = no change",
        default="")

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
    
    icon : EnumProperty(
        name="Icon", description="Icon to display in interface", 
        default='GPBRUSH_PEN',
        items=get_blender_icons_as_enum()
        )

    ## "Active" separated from show
    show : BoolProperty(
        name='Show in UI', description='Show in brushbar (Need an icon/image)',
        default=True,
        )

class STORYTOOLS_PG_tool_presets(PropertyGroup):
    index : IntProperty(default=-1)
    tools : bpy.props.CollectionProperty(type=STORYTOOLS_PGT_tool_preset)


""" ## Old - first iteration of the tool preset
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


classes=(
    STORYTOOLS_PGT_tool_preset,
    STORYTOOLS_PG_tool_presets,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
