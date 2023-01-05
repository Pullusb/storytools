# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty)

# update on prop change
def change_edit_lines_opacity(self, context):
    for gp in bpy.data.grease_pencils:
        if not gp.is_annotation:
            gp.edit_line_color[3]=self.edit_lines_opacity
    
class STORYTOOLS_PGT_distances(bpy.types.PropertyGroup) :
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


    # IntProperty : IntProperty(
    #     name="int prop", description="", default=25, min=1, max=2**31-1, soft_min=1, soft_max=2**31-1, step=1, options={'HIDDEN'})#, subtype='PIXEL'


    # ## enum (with Icon)
    # keyframe_type : EnumProperty(
    #     name="Keyframe Filter", description="Only jump to defined keyframe type", 
    #     default='ALL', options={'HIDDEN', 'SKIP_SAVE'},
    #     items=(
    #         ('ALL', 'All', '', 0), # 'KEYFRAME'
    #         ('KEYFRAME', 'Keyframe', '', 'KEYTYPE_KEYFRAME_VEC', 1),
    #         ('BREAKDOWN', 'Breakdown', '', 'KEYTYPE_BREAKDOWN_VEC', 2),
    #         ('MOVING_HOLD', 'Moving Hold', '', 'KEYTYPE_MOVING_HOLD_VEC', 3),
    #         ('EXTREME', 'Extreme', '', 'KEYTYPE_EXTREME_VEC', 4),
    #         ('JITTER', 'Jitter', '', 'KEYTYPE_JITTER_VEC', 5),
    #         ))


# classes=(
# PROJ_PGT_settings,
# )

def register(): 
    # for cls in classes:
    #     bpy.utils.register_class(cls)
    bpy.utils.register_class(STORYTOOLS_PGT_distances)
    bpy.types.Scene.storytools_settings = bpy.props.PointerProperty(type = STORYTOOLS_PGT_distances)
    

def unregister():
    # for cls in reversed(classes):
    #     bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(STORYTOOLS_PGT_distances)
    del bpy.types.Scene.storytools_settings