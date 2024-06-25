import bpy
import json
from pathlib import Path
from pprint import pprint as pp
import tempfile
# from bpy_extras.io_utils import ImportHelper, ExportHelper
from .. import fn


def get_session_settings(get_default=False, context=None, target='tool_settings'):
    if context is None:
        context = bpy.context

    prop_dic = {}

    ## -- Viewport settings

    if target == 'viewport_settings':    
        if context.area == 'VIEW_3D':
            space_data = context.space_data
        else:
            space_data = next((a.spaces.active for a in context.screen.areas if a.type == 'VIEW_3D'), None)
            if not space_data:
                return

        viewport_options = ('overlay', 'shading')
        for sub_setting in viewport_options:
            prop_dic[sub_setting] = fn.list_attr(getattr(space_data, sub_setting),
                                        f"bpy.context.space_data.{sub_setting}",
                                        recursion_limit=1,
                                        get_default=get_default)

        ## ins space_data
        inc = ['show_object_*', 'show_region_*', 'show_gizmo_*']
        prop_dic['space_data'] = fn.list_attr(space_data,
                                                'bpy.context.space_data',
                                                recursion_limit=2,
                                                get_default=get_default,
                                                includes=inc,
                                                excludes=['show_region_ui', 'region_toolbar'] # skip toolbar and sidebar
                                                )

    ## -- Tool settings

    if target == 'tool_settings':
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
            prop_dic[sub_setting] = fn.list_attr(getattr(context.scene.tool_settings, sub_setting),
                                                    f'bpy.context.scene.tool_settings.{sub_setting}',
                                                    recursion_limit=1,
                                                    get_default=get_default)

    return prop_dic


class STORYTOOLS_OT_save_load_settings_preset(bpy.types.Operator):
    bl_idname = "storytools.save_load_settings_preset"
    bl_label = "Presets"
    bl_description = "Load/Save settings presets"
    bl_options = {"REGISTER", "INTERNAL"}

    name : bpy.props.StringProperty(name='Preset Name', default='My Preset', description='Name of the new preset')

    category : bpy.props.StringProperty(default='', options={'SKIP_SAVE'})
    # preset_path : bpy.props.StringProperty(default='', options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self.preset_dir_obj = Path(bpy.utils.user_resource('SCRIPTS'), 'presets', self.category)
        self.preset_dir = str(self.preset_dir_obj)

        self.preset_list = []
        if self.preset_dir_obj.exists():
            self.preset_list = [f for f in self.preset_dir_obj.iterdir() if f.suffix == '.json']

        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        if self.preset_list:
            box = layout.box()
            col = box.column()
            for preset in self.preset_list:
                # col.label(text=preset)
                row = col.row()
                row.operator('storytools.load_setting_preset', text=preset.stem, emboss=False).preset_path = str(preset)
                row.operator('storytools.remove_setting_preset', text='', icon='REMOVE', emboss=False).preset_path = str(preset)

        ## Choice to restore default (TOOL_SETTINGS or VIEW_SETTINGS)
        layout.separator()
        layout.operator('storytools.restore_default_settings', text=f'Restore Default', emboss=False).target = self.category

        ## Save new settings
        ## use context.window_manager.preset_name ?
        row = layout.row(align=False)
        row.prop(self, 'name', text='')
        
        op = row.operator('storytools.export_setting_preset', text='', icon='ADD')
        op.preset_path = str((self.preset_dir_obj / self.name).with_suffix(".json"))
        op.target = self.category

        if self.name in self.preset_list:
            layout.label(text='Name already exists and will be overwriten', icon='ERROR')

    def execute(self, context):
        ## export when pressing ok (confusing ?)
        # bpy.ops.storytools.export_setting_preset(preset_path=str(self.preset_dir_obj / self.name), target=self.category)
        return {"FINISHED"}


### --- Load / Remove preset

def load_preset(preset_file): # , target='ALL'
    '''Receive a preset_file Path object and load contained preset'''
    # prop_dic = json.load(str(preset_file))
    with preset_file.open('r') as fd:
        prop_dic = json.load(fd)

    ## Load json
    for zone, dic in prop_dic.items():
        print(f'\n--{zone}--')

        ## Simple filter for tool_setting VS view_settings load (based on inclusion/exclusions)
        # if target == 'view_settings' and zone not in ('space_data', 'overlay', 'shading'):
        #     continue
        # if target == 'tool_settings' and zone in ('space_data', 'overlay', 'shading'):
        #     continue

        for k, v in dic.items():
            current_value = eval(k)

            data_path, prop = k.rsplit('.', 1)
            obj = eval(data_path)

            ## Enum with multiple choice (expect a set)
            if obj.bl_rna.properties[prop].is_enum_flag:
                ## Set are not json serializable, Set are stored as list
                ## if is_enum_flag, reconvert loaded value to set
                v = set(v)

            if current_value != v:
                print(f'>> {k}: {current_value}  (default {v})')
                ## Apply properties
                setattr(obj, prop, v)
            # else:
            #     print(k)

class STORYTOOLS_OT_load_setting_preset(bpy.types.Operator):
    bl_idname = "storytools.load_setting_preset"
    bl_label = "Load Setting Preset"
    bl_description = "Load preset"
    bl_options = {"REGISTER", "INTERNAL"}
    
    preset_path : bpy.props.StringProperty(default='', options={'SKIP_SAVE'})

    def execute(self, context):
        if not self.preset_path:
            return {'CANCELLED'}
        preset = Path(self.preset_path)
        if not preset.exists():
            return {'CANCELLED'}

        load_preset(preset)

        self.report({'INFO'}, f'Preset Loaded: {preset.stem}')
        return {"FINISHED"}

class STORYTOOLS_OT_remove_setting_preset(bpy.types.Operator):
    bl_idname = "storytools.remove_setting_preset"
    bl_label = "Remove Setting Preset"
    bl_description = "Remove preset"
    bl_options = {"REGISTER", "INTERNAL"}
    
    preset_path : bpy.props.StringProperty(default='', options={'SKIP_SAVE'})

    def execute(self, context):
        if not self.preset_path:
            return {'CANCELLED'}
        fp = Path(self.preset_path)
        if not fp.exists():
            return {'CANCELLED'}
        fp.unlink()
        self.report({'INFO'}, f'Preset removed: {fp.stem}')
        return {"FINISHED"}
    
### ---- Save preset

class STORYTOOLS_OT_export_setting_preset(bpy.types.Operator):
    bl_idname = "storytools.export_setting_preset"
    bl_label = "Export Setting Preset"
    bl_description = "Export setting preset"
    bl_options = {"REGISTER", "INTERNAL"}

    name : bpy.props.StringProperty(name='Preset Name', default='')
    
    preset_path : bpy.props.StringProperty(default='', options={'SKIP_SAVE'})

    target : bpy.props.EnumProperty(items=(
        ('tool_settings', 'Tool Settings', ''),
        ('view_settings', 'View Settings', ''),
        ('all', 'All', ''),
        ),
        default='tool_settings'
    )

    def execute(self, context):
        prop_dic = get_session_settings(get_default=False, context=None, target=self.target)

        if self.preset_path:
            preset = Path(self.preset_path)
        else:
            script_path = Path(bpy.utils.user_resource('SCRIPTS'))

            if not script_path.exists():
                self.report({'ERROR'}, 'Script folder not found')
                return ({'CANCELLED'})

            if not self.name:
                self.report({'ERROR'}, 'Need to specify a name')
                return ({'CANCELLED'})

            preset_dir = script_path / 'presets' / self.target
            
            preset = (preset_dir / self.name).with_suffix('.json')

        if not preset_dir.exists():
            preset_dir.mkdir(exist_ok=True, parents=True)

        ## Debug prints
        for zone, dic in prop_dic.items():
            print(f'\n--{zone}--')
            for k, v in dic.items():
                print(k, v)
        
        ## export
        with preset.open('w') as fd:
            json.dump(prop_dic, fd, indent='\t')
        
        self.report({'INFO'}, f'Preset saved at: {preset}')
        return {"FINISHED"}


### --- Export/Load default Settings

## /!\ Default viewport settings properties are completely messed up !
## Need to store a "Good enough" default-like settings somewhere (but version-dependant...)
## or : Launch blender with default settings in background and dump settings

def export_default_settings(filepath='', target='tool_settings'):
    '''Launch another factory default instance with a python an expression to launch an export settings
    note: launching on a full python script would allow to exec on any blender exec.
    '''

    import subprocess

    name = f'{fn.get_version_name()}-{target}.json'
    
    if not filepath:
        # Default to temp dir
        dump = Path(tempfile.gettempdir(), name)
    else:
        # Parent folder of used path
        dump = Path(filepath)
        if dump.exists() and dump.is_dir():
            dump = dump / name

    cmd = [
        bpy.app.binary_path,
        '--background',
        '--factory-startup', # factory default
        '--addons', f'{__package__}',
        '--python-expr', f'import bpy;bpy.ops.storytools.export_setting_preset(preset_path="{dump.as_posix()}", target="{target}")' # ;exit()
        ## addon_utils method
        # '--python-expr', f'import bpy;import addon_utils;addon_utils.enable("{__package__}");bpy.ops.prefload.export_settings(dump_path="{dump.as_posix()}", to_console={to_console}, to_clipboard={to_clipboard})'
    ]

    print(cmd)
    # subprocess.Popen(cmd)
    subprocess.call(cmd)
    print(f'Exported at: {dump}')

class STORYTOOLS_OT_restore_default_settings(bpy.types.Operator):
    bl_idname = "storytools.restore_default_settings"
    bl_label = "Restore Default Viewport Settings"
    bl_description = "Restore Default Viewport Setting\
        \n+Ctrl: Overwrite cached deffautl settings (needed if addon version has changed)"
    bl_options = {"REGISTER", "INTERNAL"}

    target : bpy.props.EnumProperty(items=(
        ('tool_settings', 'Tool Settings', ''),
        ('view_settings', 'View Settings', ''),
        ('all', 'All', ''),
        ),
        default='tool_settings'
    )

    def invoke(self, context, event):
        self.ctrl = event.ctrl
        return self.execute(context)

    def execute(self, context):
        ## Default properties settings are wrong !!
        # prop_dic = get_session_settings(get_default=True, context=None)


        ## Export json from default blender in subprocess
        name = f'{fn.get_version_name()}-{self.target}.json'
        preset_file = Path(tempfile.gettempdir(), name)

        ## Delete previous if forced
        if self.ctrl and preset_file.exists():
            preset_file.unlink()

        if not preset_file.exists():
            export_default_settings(target=self.target)

        if not preset_file.exists():
            self.report({'ERROR'}, f'Could not find: "{preset_file}"')
            return {'CANCELLED'}

        load_preset(preset_file)

        return {"FINISHED"}


classes=(
    STORYTOOLS_OT_save_load_settings_preset,
    STORYTOOLS_OT_export_setting_preset,
    STORYTOOLS_OT_load_setting_preset,
    STORYTOOLS_OT_remove_setting_preset,
    STORYTOOLS_OT_restore_default_settings,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)