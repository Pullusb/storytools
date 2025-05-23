import bpy
from bpy.props import (StringProperty,
                       IntProperty,
                        BoolProperty,
                        EnumProperty,)
from bpy.types import Context, OperatorProperties
from pathlib import Path
from . import fn

def get_blender_icons_as_enum():
    # return ((i.identifier, i.name, '', i.value) for i in bpy.types.UILayout.bl_rna.functions['prop'].parameters['icon'].enum_items)
    return tuple((i.identifier, i.name, '') for i in bpy.types.UILayout.bl_rna.functions['prop'].parameters['icon'].enum_items)

class STORYTOOLS_OT_set_draw_tool(bpy.types.Operator):
    bl_idname = "storytools.set_draw_tool"
    bl_label = "Set Draw Tool"
    bl_description = "Tool preset\
        \nChange tool / brush / layer / material to use"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    name : StringProperty(
        name="Name", description="Name that define this preset (Optional).\
            \nJust for personal organisation",
        default="", options={'SKIP_SAVE'})

    mode : EnumProperty(
        name="Mode", description="Using shortcut will change to this mode", 
        default='PAINT_GREASE_PENCIL', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('PAINT_GREASE_PENCIL', 'Draw', 'Switch to draw mode', 0),
            ('EDIT_GREASE_PENCIL', 'Edit', 'Switch to edit mode', 1),
            ('SCULPT_GREASE_PENCIL', 'Sculpt', 'Switch to Sculpt mode', 2),
            ('OBJECT', 'Object', 'Switch to Object mode', 3),
            ('NONE', 'Current', 'No change', 4),
            ))

    tool : StringProperty(
        name="Tool", description="Tool to set\
            \nEmpty field = no change",
        default="", # builtin.brush
        options={'SKIP_SAVE'})
    
    brush : StringProperty(
        name="Brush", description="Name of Brush to set\
            \nIf it's a User brush, need to enter the relative asset path\
            \nExample: 'Saved/Brushes/CustomFill.asset.blend/Brush/CustomFill'\
            \nEmpty field = no change",
        default="",
        options={'SKIP_SAVE'})

    layer : StringProperty(
        name="Layer", description="Layer to set (exact name, case sensitive)\
            \nEmpty field = no change",
        default="", # Sketch
        options={'SKIP_SAVE'})
    
    material : StringProperty(
        name="Material", description="Material to set (exact name, case sensitive)\
            \nEmpty field = No change or use layer-material synchronisation if enabled",
        default="", # line
        options={'SKIP_SAVE'})

    ## Interface options
    show : BoolProperty(
        name='Show in UI', description='Show in brushbar',
        default=True,
        )
    
    icon : EnumProperty(
        name="Icon", description="Icon to display in interface", 
        default='GREASEPENCIL',
        items=get_blender_icons_as_enum()
        )

    description : StringProperty(default='', options={'SKIP_SAVE'})
    
    ## Shortcut text : Internal use only for description
    shortcut : StringProperty(default='', 
                            description='For internal use only',
                            options={'SKIP_SAVE', 'HIDDEN'})

    order : IntProperty(default=0, step=1)

    @classmethod
    def description(cls, context, properties) -> str:
        ## User mande description is passed
        if properties.description:
            desc = properties.description
            if properties.name:
                desc = properties.name + '\n' + desc
            if properties.shortcut:
                desc = desc + '\n' + properties.shortcut
            return desc
        
        ## Auto build description from properties
        desc = []
        if properties.name:
            desc.append(properties.name) 
        else:
            desc.append("Tool Preset")

        desc.append("")

        ## List mode ?
        # if properties.mode != 'NONE':
        #     desc.append(f"Mode: {properties.mode.title().split('_')[0]}")
        
        tools = []
        if properties.tool:
            if 'builtin_brush.' in properties.tool:
                tools.append(f"Tool: {properties.tool.replace('builtin_brush.', '')}")
            else:
                tools.append(f'Tool: {properties.tool}')
        
        if properties.brush:
            if '/' in properties.brush:
                brush_name = properties.brush.split("/")[-1]
            else:
                brush_name = properties.brush
            tools.append(f'Brush: {brush_name}')

        if tools:
            desc.append(' > '.join(tools))
        
        gp_properties = []        
        if properties.layer:
            gp_properties.append(f'Layer: {properties.layer}')

        if properties.material:
            gp_properties.append(f'Material: {properties.material}')

        if gp_properties:
            desc.append(', '.join(gp_properties))

        if properties.shortcut:
            desc.append('')
            desc.append(f'Shortcut: {properties.shortcut}')

        return '\n'.join(desc)

    @staticmethod
    def get_brush_from_blend(brush_name, blend_file):
        '''Load brush from blend file by name, return brush object if found'''
        with bpy.data.libraries.load(str(blend_file), assets_only=True, link=False) as (data_from, data_to):
            if brush_name in data_from.brushes:
                print(f'Load brush {brush_name} from {blend_file}')
                data_to.brushes = [brush_name]
        if data_to.brushes:
            return data_to.brushes[0]

    def execute(self, context):
        ## Mode needs to add shortcut to generic Gpencil (would conflict with Selection mask)
        # if self.mode != 'NONE' and context.mode != self.mode:
        #     bpy.ops.object.mode_set(mode=self.mode)
        
        prop_names = ('tool', 'brush', 'layer', 'material')
        # if not self.tool and not self.brush and not self.layer and not self.material:
        if not any(getattr(self, prop_name) for prop_name in prop_names) and self.mode == 'NONE':
            message = [
                'This Storytools keymap has no settings yet',
                'Customize or disable the keymap in addon preferences',
                'Click on the following button to open:',
                ['storytools.open_addon_prefs', 'Open Storytools Preferences', 'PREFERENCES'],
                ]
            fn.show_message_box(message, 'Keymap not set', 'ERROR')
            return {"CANCELLED"}

        ob = context.object

        # Mode change (Need context aware shortcut protection to work well with other modes)...
        if self.mode != 'NONE':
            bpy.ops.object.mode_set(mode=self.mode)

        if self.tool:
            try:
                bpy.ops.wm.tool_set_by_id(name=self.tool)
                # self.report({'INFO'}, f'Tool {self.tool}')
            except:
                self.report({'ERROR'}, f'Cannot set tool {self.tool}, need identifier (ex: "builtin.brush")')
                return {"CANCELLED"}
        
        if '/' in self.brush:
            ## always Consider that this is a custom user brush to use with asset_activate
            ## But need a more robust solution
            try:
                bpy.ops.brush.asset_activate(asset_library_type='CUSTOM',
                asset_library_identifier="User Library",
                relative_asset_identifier=self.brush)
            except Exception as e:
                print('Error loading brush from asset', e)
                self.report({'ERROR'}, f'Cannot load {self.brush}, need to be an asset path, ex: "Saved/Brushes/CustomFill.asset.blend/Brush/CustomFill"')
                return {"CANCELLED"}

        elif self.brush:
            ## self.brush is brush name as str here
            br = bpy.data.brushes.get(self.brush)

            if not br:
                ## Try to load brush
                ## First search in brush from essential lib (Problem ! when used this way it does not)
                
                essential_brush_lib = Path(bpy.utils.resource_path('LOCAL')) / 'datafiles' / 'assets' / 'brushes' / 'essentials_brushes-gp_draw.blend'
                ## /!\ Loading directly duplicate the brush if then used from asset shelf ! (Using operator)
                # br = self.get_brush_from_blend(self.brush, essential_brush_lib)
                # if br:
                #     print('Essential brush found')

                ## Load using "asset_activate" operator
                with bpy.data.libraries.load(str(essential_brush_lib), assets_only=True, link=False) as (data_from, data_to):
                    if self.brush in data_from.brushes:
                        ## Just True to know brush exists in essential pack, activate and skip next search
                        br = True
                if br:
                    bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS', 
                    asset_library_identifier="", 
                    relative_asset_identifier=f"brushes/essentials_brushes-gp_draw.blend/Brush/{self.brush}")

            if not br:
                ## Search in user libs
                asset_libs = bpy.context.preferences.filepaths.asset_libraries
                for asset_library in asset_libs:
                    library_path = Path(asset_library.path)
                    blend_files = [fp for fp in library_path.glob("**/*.blend") if fp.is_file()]
                    print('blend_files: ', blend_files)
                    for blend_file in blend_files:
                        br = self.get_brush_from_blend(self.brush, blend_file)
                        if br:
                            print('Found brush in ', blend_file)
                            break
                    if br:
                        break
            
            if not isinstance(br, bool):
                # when found in blend (not a boolean value from checks above)
                if br:
                    # Use asset-activate operator, instead of deprecated : context.scene.tool_settings.gpencil_paint.brush = br

                    ## FIXME: brush source hardcoded to essential for now, but will miserably fail if user set brush name from another library
                    ## Need to find a way to get library type and relative_asset_identifier from brush object
                    bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS', 
                    asset_library_identifier="", 
                    relative_asset_identifier=f"brushes/essentials_brushes-gp_draw.blend/Brush/{self.brush}")

                else:
                    self.report({'WARNING'}, f'Could not find brush named {self.brush}')
                    # return {"CANCELLED"}

                    ## Using name, can directly try to load brush from essential library ?
                    # bpy.data.libraries['es`sentials_brushes-gp_draw.blend'].users_id[0]

        if self.layer:
            fn.set_layer_by_name(ob, self.layer)
        
        if self.material:
            # FIXME: Sync happen after material set... how to prevent
            fn.set_material_by_name(ob, self.material)

        return {"FINISHED"}

'''
## Hardcoded shortcuts, Keymap only set preset number (behavior defined in ops)
class STORYTOOLS_OT_set_draw_tool(bpy.types.Operator):
    bl_idname = "storytools.set_draw_tool"
    bl_label = "Set Draw Tool"
    bl_description = "Set a draw tool, configuring brush / layer / material tool"
    bl_options = {"REGISTER", "INTERNAL"}

    # path_to_pal : bpy.props.StringProperty(name="paht to palette", description="path to the palette", default="")
    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    preset : bpy.props.IntProperty(name='Preset number', default=1, options={'SKIP_SAVE'})

    def execute(self, context):
        # if context.mode != 'OBJECT':
        #     bpy.ops.object.mode_set(mode='PAINT_GREASE_PENCIL')
        
        presets = {
            1: {'tool': 'builtin.brush', 'layer':'Sketch', 'mat': 'line'},
            2: {'tool': 'builtin_brush.Fill', 'layer':'Color', 'mat': 'fill_white'},
            3: {'tool': 'builtin.brush', 'layer':'Color', 'mat': 'fill_white'},
            4: {'tool': 'builtin_brush.Erase'},
        }

        preset_d = presets[self.preset]

        ob = context.object
        if 'tool' in preset_d.keys() and preset_d['tool']:
            bpy.ops.wm.tool_set_by_id(name=preset_d['tool'])
        if 'layer' in preset_d.keys() and preset_d['layer']:
            fn.set_layer_by_name(ob, preset_d['layer'])

        ## Material not forced for now, Already changed by layer synchro
        # if 'mat' in preset_d.keys() and preset_d['mat']:
        #     fn.set_material_by_name(ob, preset_d['mat']) 

        return {"FINISHED"}
'''


addon_keymaps = []

def register_keymap():
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Grease Pencil Paint Mode", space_type="EMPTY")

    '''
    ## Hardcoded
    numbers = ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR']
    for i, number in enumerate(numbers):
        if i == 0:
            continue
        kmi = km.keymap_items.new('storytools.set_draw_tool', type=number, value='PRESS')
        kmi.properties.preset=i
        addon_keymaps.append((km, kmi))
    '''

    kmi = km.keymap_items.new('storytools.set_draw_tool', type='ONE', value='PRESS')
    kmi.properties.name = 'Sketch Draw'
    kmi.properties.mode = 'PAINT_GREASE_PENCIL'
    kmi.properties.tool = 'builtin.brush'
    kmi.properties.brush = 'Pencil'
    kmi.properties.layer = 'Sketch'
    # kmi.properties.material = '' # line
    # kmi.properties.icon = 'GPBRUSH_PEN'
    kmi.properties.icon = 'GREASEPENCIL'
    kmi.properties.order = 10
    # kmi.properties.description = 'Set Pencil brush on "Sketch" layer'
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new('storytools.set_draw_tool', type='TWO', value='PRESS')
    kmi.properties.name = 'Line Draw'
    kmi.properties.mode = 'PAINT_GREASE_PENCIL'
    kmi.properties.tool = 'builtin.brush'
    kmi.properties.brush = 'Ink Pen'
    kmi.properties.layer = 'Line'
    kmi.properties.icon = 'LINE_DATA'
    kmi.properties.order = 20
    # kmi.properties.description = 'Set Ink Brush on "Line" layer'
    # kmi.properties.material = '' # line
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('storytools.set_draw_tool', type='THREE', value='PRESS')
    kmi.properties.name = 'Bucket Fill'
    kmi.properties.mode = 'PAINT_GREASE_PENCIL'
    kmi.properties.tool = 'builtin_brush.Fill'
    kmi.properties.brush = 'Fill'
    kmi.properties.layer = 'Color'
    # kmi.properties.material = '' # fill_white
    kmi.properties.icon = 'SHADING_SOLID'
    kmi.properties.order = 30
    # kmi.properties.description = 'Set Fill tool on "Color" layer'
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('storytools.set_draw_tool', type='FOUR', value='PRESS')
    kmi.properties.name = 'Fill Draw'
    kmi.properties.mode = 'PAINT_GREASE_PENCIL'
    kmi.properties.tool = 'builtin.brush'
    kmi.properties.layer = 'Color'
    kmi.properties.icon = 'NODE_MATERIAL'
    kmi.properties.order = 40
    # kmi.properties.description = 'Set draw tool "Color" layer'
    # kmi.properties.material = '' # fill_white
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('storytools.set_draw_tool', type='FIVE', value='PRESS')
    kmi.properties.name = 'Eraser by points'
    kmi.properties.mode = 'PAINT_GREASE_PENCIL'
    kmi.properties.tool = 'builtin_brush.Erase'
    kmi.properties.brush = 'Eraser Point'
    kmi.properties.icon = 'CLIPUV_DEHLT'
    kmi.properties.order = 50
    # kmi.properties.description = 'Set Point Eraser'
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('storytools.set_draw_tool', type='SIX', value='PRESS')
    kmi.properties.name = 'Eraser by strokes'
    kmi.properties.mode = 'PAINT_GREASE_PENCIL'
    kmi.properties.tool = 'builtin_brush.Erase'
    kmi.properties.brush = 'Eraser Stroke'
    kmi.properties.icon = 'CON_TRACKTO'
    kmi.properties.order = 60
    # kmi.properties.description = 'Set Stroke Eraser'
    addon_keymaps.append((km, kmi))

    # kmi = km.keymap_items.new('storytools.set_draw_tool', type='SEVEN', value='PRESS')
    # addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new('storytools.set_draw_tool', type='SEVEN', value='PRESS')
    kmi.properties.name = 'Annotate'
    kmi.properties.tool = 'builtin.brush'
    kmi.properties.layer = 'Annotate'
    kmi.properties.material = 'line_red' # Sync override material
    kmi.properties.order = 70
    kmi.properties.icon = 'SYNTAX_ON' # CURRENT_FILE, TEXT
    addon_keymaps.append((km, kmi))

def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)    
    addon_keymaps.clear()

def register():
    bpy.utils.register_class(STORYTOOLS_OT_set_draw_tool)
    register_keymap()

def unregister():
    unregister_keymap()
    bpy.utils.unregister_class(STORYTOOLS_OT_set_draw_tool)
