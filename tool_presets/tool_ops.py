# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import re
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty,
                        CollectionProperty)

from .. import fn

## Operator to use in shortcut to trigger tool presets

class STORYTOOLS_OT_select_tool_preset(bpy.types.Operator):
    bl_idname = "storytools.select_tool_preset"
    bl_label = "Select Tool Preset"
    bl_description = "Select a tool preset"
    bl_options = {'REGISTER', 'INTERNAL'}

    identifier : StringProperty(default='', options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self.button = event.type
        self.ctrl = event.ctrl
        self.shift = event.shift
        self.alt = event.alt
        return self.execute(context)

    def execute(self, context):
        pg = fn.get_addon_prefs().tool_presets

        index = pg.index
        tools = pg.tools

        ## note: Name is used as identifier in toolpreset

        ## if a correct identifier passed, trigger the associated tool
        if self.identifier:
            tool = next((t for t in tools if t.name == self.identifier), None)
            if tool is None:
                
                message = [
                    f"Name {self.identifier} not found in storytools preset",
                    'Available name:',
                    ', '.join([t.name for t in tools if t.name]),
                ]

                fn.show_message_box(_message=message, _title='Not found', _icon='ERROR')
                return {'CANCELLED'}


        number_dict = {
            'ONE' : 1,
            'NUMPAD_ONE': 1,
            'TWO' : 2,
            # ... Need to complete
        }

        ## If no identifier passed and button is a number

        # if self.button in number_dict.keys():

        if num := number_dict.get(self.button):
            if num > len(tools):
                message = [f'Number {num} is out of toolpreset range',
                           'Set another number key as shortcut input',
                           'Or set the name of the tool preset to use']
                fn.show_message_box(_message=message, _title='Not found', _icon='ERROR')
                return {'CANCELLED'}
                
            tool = tools[num]

        else:
            message = [
                "Storytools preset need to specify a name",
                'Or use a number as shortcut input',
                'Available name:',
                ', '.join([t.name for t in tools if t.name]),
            ]
            fn.show_message_box(_message=message, _title='Not found', _icon='ERROR')
            return {'CANCELLED'}
        
        ## Now apply the tool preset:
        # print('applying tool.name')
        # ...

        # refresh_areas() # ?
        return {'FINISHED'}
    