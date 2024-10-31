# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty,
                        CollectionProperty)

from bpy.types import PropertyGroup

## Update on prop change
def change_edit_lines_opacity(self, context):
    for gp in bpy.data.grease_pencils:
        if not gp.is_annotation:
            gp.edit_line_color[3]=self.edit_lines_opacity

def apply_on_all_scene(self, context):
    '''Propagate settings on other scene from property update'''

    ## self seem not always good at loading time, use context.scene
    # print('context.scene: ', context.scene.name, '\n====') # Dbg
    
    current_settings = context.scene.storytools_gp_settings
    if current_settings.sync_mode == 'SYNC_LOCAL':
        # print(current_settings.sync_mode, 'SKIP (SYNC_LOCAL)') # Dbg
        return

    for scn in bpy.data.scenes:
        print(scn.name)
        if scn == context.scene:
            # print('> same scene, skip') # Dbg
            continue

        if scn.storytools_gp_settings.sync_mode == 'SYNC_LOCAL':
            # print(f'Skip {scn.name} (local mode)') # Dbg
            # Skip scene using isolate mode
            continue
        
        # print('Propagate properties on scene:', scn.name) # Dbg
        for prop_name in current_settings.bl_rna.properties.keys():
            if prop_name in ('name', 'rna_type', 'sync_mode'):
                continue

            # value = getattr(context.scene.storytools_gp_settings, prop_name)
            value = getattr(current_settings, prop_name)

            if prop_name == 'frame_target_layers':
                ## Set number from the enum (assignation using square bracket wait for an int !)
                value = {"ACTIVE" : 0, "ACCESSIBLE" : 1, "VISIBLE" : 2}[value]
            
            if prop_name == 'keyframe_type':
                value = {'ALL' : 0, 'CURRENT' : 1, 'KEYFRAME' : 2, 'BREAKDOWN' : 3, 'MOVING_HOLD' : 4, 'EXTREME' : 5, 'JITTER' : 6, 'GENERATED' : 7}[value]

            # print(f'--> Assign {prop_name} = {value}') # Dbg
            ## assign without triggering reload
            scn.storytools_gp_settings[prop_name] = value

        ## Is there a way to replicate only active properties ??!
        ## Selective replication
        # scn.storytools_gp_settings['frame_offset'] = self.frame_offset
        # scn.storytools_gp_settings['frame_target_layers'] = self.frame_target_layers
        # scn.storytools_gp_settings['keyframe_type'] = self.keyframe_type

display_choice_items = (
        ('AUTO', 'Automatic', 'Show entry only if there is enough space', 0),
        ('SHOW', 'Show', 'Always show entry in list', 1),
        ('HIDE', 'Hide', 'Never show entry in list', 2),
    )

class STORYTOOLS_PGT_gp_settings(PropertyGroup):

    frame_offset : IntProperty(
        name='Grease Pencil Frame Offset',
        description="Frame offset to apply when creating new frame above an existing one\
            \nOr when applying offset to all subsequents frames",
        default=12,
        min=1, soft_max=300, max=16000,
        update=apply_on_all_scene
        )

    frame_target_layers : EnumProperty(
        name='Layer targets to keys',
        description='Define in wich layers keys should be added\
            \nand where to check for existing keys (offset if key already at current frame)',
        default='ACCESSIBLE',
        items=(
            ("ACTIVE", "Active", "Only on active layer ", 0),
            ("ACCESSIBLE", "Accessible", "On visible and unlocked layers", 1),
            ("VISIBLE", "Visible", "Only on all visible layers", 2),
            ),
        update=apply_on_all_scene
        )
    
    ## Check if need different target for checking and applying
    ## For now seem logical to have check and target destination on same layer scope.

    keyframe_type : EnumProperty(
        name='Frame Type Filter',
        default='ALL',
        items=(
            ('ALL', 'All', 'All Keyframe types', 'KEYFRAME', 0),
            ('CURRENT', 'Use Hovered Type', 'Currenly hovered type on active layers', 'ACTION_TWEAK', 1),
            ('KEYFRAME', 'Keyframe', '', 'KEYTYPE_KEYFRAME_VEC', 2),
            ('BREAKDOWN', 'Breakdown', '', 'KEYTYPE_BREAKDOWN_VEC', 3),
            ('MOVING_HOLD', 'Moving Hold', '', 'KEYTYPE_MOVING_HOLD_VEC', 4),
            ('EXTREME', 'Extreme', '', 'KEYTYPE_EXTREME_VEC', 5),
            ('JITTER', 'Jitter', '', 'KEYTYPE_JITTER_VEC', 6),
            ('GENERATED', 'Generated', '', 'KEYTYPE_GENERATED_VEC', 7),
            ),
        update=apply_on_all_scene
        )


    sync_mode : EnumProperty(
        name='GP Settings Sync',
        description="Control how scene storytools GP settings interact with global preferences and other scenes",
        items=(
            ('SYNC_GLOBAL', "Sync Preferences & Scenes", "Settings are restored from global preference when opening files and synchronized across scenes"),
            ('SYNC_SCENES', "Sync Only Between Scenes", "Synchronize settings with other scenes when changed, but ignore global preferences"),
            ('SYNC_LOCAL', "No Sync", "Maintain independent settings, isolated from global preferences and scene sync")
        ),
        default='SYNC_GLOBAL'
    )

    # sync_scene : BoolProperty(name='Sync Between Scenes',
    #                     description="Synchronise those settings with other scenes\
    #                         \nIf False, change won't be send to other scene and won't be affected by other scenes",
    #                     default=True)
    
    # sync_preferences : BoolProperty(name='Sync With Preferences',
    #                     description='Local scene storytools GP settings will be restore to values in preferences\
    #                         \nOtherwise local settings will be kept when opening file',
    #                     default=True)

class STORYTOOLS_PGT_main_settings(PropertyGroup):
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
        name="Material Sync", description="Define how to switch material when active layer is changed",
        default='INDIVIDUAL', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('INDIVIDUAL', 'Sync Materials', 'Sync material and layer per object', 0),
            ('GLOBAL', 'Sync Across Objects', 'Sync material and layer globally ', 1),
            ('DISABLED', 'No Sync', 'No material association when changing layer', 2),
            ))

    show_session_toolbar : BoolProperty(
        name='Show Toolbar',
        description="Show/Hide viewport Bottom Toolbar buttons on this session\
            \nTo completely disable, uncheck 'Active Toolbar' in addon Storytools preferences",
        default=True)
    
    show_cam_settings : EnumProperty(
        name='Show Camera Settings',
        description="Show Camera properties of every camera in list (when sidebar size allow)",
        default='AUTO',
        items=display_choice_items
        )

    ## Properties vbisibility toggles

    show_gp_visibility : EnumProperty(
        name='Show Visibility Toggle',
        description="Show object visibility toggle",
        default='SHOW',
        items=display_choice_items
        )

    show_gp_in_front : EnumProperty(
        name='Show In Front Toggle',
        description="Show object in front toggle",
        default='AUTO',
        items=display_choice_items
        )

    show_gp_parent : EnumProperty(
        name='Show Parent Info',
        description="Show When Object is parented",
        default='AUTO',
        items=display_choice_items
        )

    show_gp_users : EnumProperty(
        name='Show Linked Data Toggle',
        description="Show object user data when object has multiple user (when object have multiple users)",
        default='AUTO',
        items=display_choice_items
        )

    ## Storyboard Keymap items

    ## Add the presets... collection property or individual settings ?
    ## Collection is much cleaner, But incompatible with selective pref load...


classes=(
STORYTOOLS_PGT_main_settings,
STORYTOOLS_PGT_gp_settings,
# STORYTOOLS_PGT_km_preset, # old
# STORYTOOLS_PGT_keymap_presets, # old
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.storytools_settings = bpy.props.PointerProperty(type = STORYTOOLS_PGT_main_settings)
    bpy.types.Scene.storytools_gp_settings = bpy.props.PointerProperty(type = STORYTOOLS_PGT_gp_settings)
    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.storytools_settings
    del bpy.types.Scene.storytools_gp_settings