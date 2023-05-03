import bpy

from . import fn


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

addon_keymaps = []

def register_keymap():
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name = "Grease Pencil Stroke Paint Mode", space_type = "EMPTY")

    # TODO: Shortcut to change Mat / Brushes / Layer
    numbers = ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR']
    for i, number in enumerate(numbers):
        if i == 0:
            continue
        kmi = km.keymap_items.new('storytools.set_draw_tool', type=number, value='PRESS')
        kmi.properties.preset=i
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
    bpy.utils.register_class(STORYTOOLS_OT_set_draw_tool)
