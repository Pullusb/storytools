import bpy
import json
from pathlib import Path
from pprint import pprint as pp
# from bpy_extras.io_utils import ImportHelper, ExportHelper
from .. import fn


def get_session_settings(get_default=False, context=None):
    if context is None:
        context = bpy.context

    prop_dic = {}

    """## old_method passing data_path as string
    viewport_options = ('overlay', 'shading')
    for part in viewport_options:
        prop_dic[part] = fn.list_attr(f"bpy.context.space_data.{part}")

    inc = ['show_object_*', 'show_region_*', 'show_gizmo_*']
    prop_dic['space_data'] = fn.list_attr(f"bpy.context.space_data",
                                                recursion_limit=1,
                                                includes=inc)
    
    excl = ['annotation_stroke_placement_view*', 'gpencil_interpolate', 'use_lock_relative']
    prop_dic['tool_settings'] = fn.list_attr(f"bpy.context.scene.tool_settings",
                                                recursion_limit=2,
                                                # includes=[],
                                                excludes=excl)
    """

    ## -- Viewport settings
    inc = ['show_object_*', 'show_region_*', 'show_gizmo_*']
    prop_dic['space_data'] = fn.list_attr(context.space_data,
                                            'bpy.context.space_data',
                                            recursion_limit=1,
                                            get_default=get_default,
                                            includes=inc)

    ## -- Tool settings

    ## Root settings
    excl = [
            'annotation_stroke_placement_view*', # do not touch annotation settings ?
            'gpencil_interpolate', # return nothing
            'use_lock_relative', # don't know what that is yet
            'use_keyframe_insert_auto', # leave user autokey state
            ]

    prop_dic['tool_settings'] = fn.list_attr(context.scene.tool_settings,
                                                'bpy.context.scene.tool_settings',
                                                recursion_limit=1,
                                                get_default=get_default,
                                                excludes=excl)

    ## Sub-categories
    subsettings = [
        'gpencil_sculpt',
        'gpencil_paint',
        'gpencil_vertex_paint',
        'gpencil_sculpt_paint',
        'gpencil_weight_paint',
    ]
    
    ## Eventually add some of following sub_settings:
    # sculpt
    # statvis
    # curve_paint_settings
    # custom_bevel_profile_preset
    # sequencer_tool_settings
    # curve_paint_settings
    # particle_edit
    # unified_paint_settings

    for sub_setting in subsettings:
        prop_dic['tool_settings'] = fn.list_attr(getattr(context.scene.tool_settings, sub_setting),
                                                f'bpy.context.scene.tool_settings.{sub_setting}',
                                                recursion_limit=1,
                                                get_default=get_default)

    return prop_dic

class STORYTOOLS_OT_export_viewport_options(bpy.types.Operator):
    bl_idname = "storytools.export_viewport_options"
    bl_label = "Save Viewport options"
    bl_description = "Save viewport options"
    bl_options = {"REGISTER"} # , "INTERNAL"

    name : bpy.props.StringProperty(name='Preset Name', default='')

    def invoke(self, context, event):
        tool_settings_preset = Path(bpy.utils.user_resource('SCRIPTS'), 'presets', 'tool_settings')
        
        # TODO: list existing presets to avoid creating new ?
        self.preset_list = []
        if tool_settings_preset.exists():
            self.preset_list = [f.stem for f in tool_settings_preset.iterdir() if f.suffix == '.json']
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, 'name')
        if self.name in self.preset_list:
            layout.label(text='Name already exists and will be overwriten', icon='ERROR')

    def execute(self, context):
        script_path = Path(bpy.utils.user_resource('SCRIPTS'))

        if not script_path.exists():
            self.report({'ERROR'}, 'Script folder not found')
            return ({'CANCELLED'})

        if not self.name:
            self.report({'ERROR'}, 'Need to specify a name')
            return ({'CANCELLED'})
    

        preset_dir = script_path / 'presets' / 'tool_settings'
        prop_dic = get_session_settings(get_default=False, context=None)

        if not preset_dir.exists():
            preset_dir.mkdir(exist_ok=True, parents=True)
        
        preset = preset_dir / self.name

        ## Debug prints
        # for zone, dic in prop_dic.items():
        #     print(f'\n--{zone}--')
        #     for k, v in dic.items():
        #         print(k, v)
        
        ## export
    
        with preset.open('w') as fd:
            json.dump(prop_dic, fd, indent='\t')
        self.report({'INFO'}, f'Preset saved at: {preset}')
        return {"FINISHED"}


## Conclusion : Default viewport settings properties are completely messed up !
## Need to store a "Good enough" default-like settings somewhere (but version-dependant...).
""" class STORYTOOLS_OT_restore_default_settings(bpy.types.Operator):
    bl_idname = "storytools.restore_default_settings"
    bl_label = "Restore Default Viewport Settings"
    bl_description = "Restore Default Viewport Settings"
    bl_options = {"REGISTER"}

    def execute(self, context):
        prop_dic = get_session_settings(get_default=True, context=None)
        for zone, dic in prop_dic.items():
            print(f'\n--{zone}--')
            for k, v in dic.items():
                current_value = eval(k)
                if current_value != v:
                    print(f'{k}: {current_value}  (default {v})')

                    ## Apply properties
                    # data_path, prop = k.rsplit('.', 1)
                    # setattr(eval(data_path), prop, v)
        return {"FINISHED"}

 """

## TODO: loader
## TODO: Sane default load (No local view, no local cam, etc...)


classes=(
    STORYTOOLS_OT_export_viewport_options,
    # STORYTOOLS_OT_export_viewport_options,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)