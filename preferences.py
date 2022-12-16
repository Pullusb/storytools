# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty)

def get_addon_prefs():
    return bpy.context.preferences.addons[__package__].preferences

class STORYTOOLS_prefs(bpy.types.AddonPreferences):
    bl_idname = __name__.split('.')[0] # or with: os.path.splitext(__name__)[0]

    # some_bool_prop to display in the addon pref
    default_edit_line_opacity : bpy.props.FloatProperty(
        name='Use super special option',
        description="Edit line opacity for newly created objects\
            \nSome users prefer to set it to 0 (show only selected line in edit mode)\
            \nBlender default is 0.5",
        default=0.2, min=0.0, max=1.0)

    def draw(self, context):
            layout = self.layout
            layout.use_property_split = True
            # flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
            # layout = flow.column()
            layout.prop(self, 'default_edit_line_opacity')

### --- REGISTER ---

classes=(
STORYTOOLS_prefs,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)