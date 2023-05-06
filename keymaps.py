import bpy
from bpy.props import (StringProperty,
                       FloatProperty,
                        BoolProperty,
                        EnumProperty,)
from . import fn

class STORYTOOLS_OT_set_draw_tool(bpy.types.Operator):
    bl_idname = "storytools.set_draw_tool"
    bl_label = "Set Draw Tool"
    bl_description = "Set a draw tool\
        \nSet tool / brush / layer / material to use"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    # mode : EnumProperty(
    #     name="Mode", description="Using shortcut will change to this mode", 
    #     default='PAINT_GPENCIL', options={'HIDDEN', 'SKIP_SAVE'},
    #     items=(
    #         ('PAINT_GPENCIL', 'Draw', 'Switch to draw mode', 0),
    #         ('EDIT_GPENCIL', 'Edit', 'Switch to edit mode', 1),
    #         ('SCULPT_GPENCIL', 'Sculpt', 'Switch to Sculpt mode', 2),
    #         ('OBJECT', 'Object', 'Switch to Object mode', 3),
    #         ('NONE', 'Current', 'No mode switch', 4),
    #         ))

    tool : StringProperty(
        name="Tool", description="Tool to set\
            \nEmpty field = no change",
        default="", # builtin_brush.Draw
        options={'SKIP_SAVE'})
    
    brush : StringProperty(
        name="Brush", description="Brush to set\
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

    # name : StringProperty(
    #     name="Preset Name (optional)", description="Name that define this preset.\
    #         \nJust for personal organisation",
    #     default="", options={'SKIP_SAVE'})

    def execute(self, context):
        ## Mode needs to add shortcut to generic Gpencil (would conflict with Selection mask)
        # if self.mode != 'NONE' and context.mode != self.mode:
        #     bpy.ops.object.mode_set(mode=self.mode)
        if not self.tool and not self.brush and not self.layer and not self.material:
            message = [
                'This Storytools keymap has no settings yet',
                'Customize or disable the keymap in addon preferences',
                'Click on the following button to open:',
                ['storytools.open_addon_prefs', 'Open Storytools Preferences', 'PREFERENCES'],
                ]
            fn.show_message_box(message, 'Keymap not set', 'ERROR')
            return {"CANCELLED"}
        
        ob = context.object
        if self.tool:
            try:
                bpy.ops.wm.tool_set_by_id(name=self.tool)
                self.report({'INFO'}, f'tool {self.tool}')
            except:
                self.report({'ERROR'}, f'Cannot set tool {self.tool}, need identifier (ex: "builtin_brush.Draw")')
                return {"CANCELLED"}
        
        if self.brush:
                br = bpy.data.brushes.get(self.brush)
                if br:
                    context.scene.tool_settings.gpencil_paint.brush = br
                else:
                    self.report({'WARNING'}, f'Could not find brush named {self.brush}')
                    # return {"CANCELLED"}

        if self.layer:
            fn.set_layer_by_name(ob, self.layer)
        
        if self.material:
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
        return context.object and context.object.type == 'GPENCIL'

    preset : bpy.props.IntProperty(name='Preset number', default=1, options={'SKIP_SAVE'})

    def execute(self, context):
        # if context.mode != 'OBJECT':
        #     bpy.ops.object.mode_set(mode='PAINT_GPENCIL')
        
        presets = {
            1: {'tool': 'builtin_brush.Draw', 'layer':'Sketch', 'mat': 'line'},
            2: {'tool': 'builtin_brush.Fill', 'layer':'Color', 'mat': 'fill_white'},
            3: {'tool': 'builtin_brush.Draw', 'layer':'Color', 'mat': 'fill_white'},
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
    km = addon.keymaps.new(name = "Grease Pencil Stroke Paint Mode", space_type = "EMPTY")

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
    kmi.properties.tool='builtin_brush.Draw'
    kmi.properties.layer='Sketch'
    kmi.properties.material='' # line
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new('storytools.set_draw_tool', type='TWO', value='PRESS')
    kmi.properties.tool='builtin_brush.Draw'
    kmi.properties.layer='Line'
    kmi.properties.material='' # line
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('storytools.set_draw_tool', type='THREE', value='PRESS')
    kmi.properties.tool='builtin_brush.Fill'
    kmi.properties.layer='Color'
    kmi.properties.material='' # fill_white
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('storytools.set_draw_tool', type='FOUR', value='PRESS')
    kmi.properties.tool='builtin_brush.Draw'
    kmi.properties.layer='Color'
    kmi.properties.material='' # fill_white
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('storytools.set_draw_tool', type='FIVE', value='PRESS')
    kmi.properties.tool='builtin_brush.Erase'
    kmi.properties.brush='Eraser Point'
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('storytools.set_draw_tool', type='SIX', value='PRESS')
    kmi.properties.tool='builtin_brush.Erase'
    kmi.properties.brush='Eraser Stroke'
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new('storytools.set_draw_tool', type='SEVEN', value='PRESS')
    kmi.properties.tool=''
    kmi.properties.brush=''
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
