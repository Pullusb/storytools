# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import (
    Operator,
    GizmoGroup,
    Gizmo
    )

from mathutils import Matrix, Vector
from gpu_extras.batch import batch_for_shader
import numpy as np
from .. import fn

## /!\ Unused version of map overlay using gizmo instead of gpu draw

# Example of a gizmo that activates an operator
# using the predefined dial gizmo to change the camera roll.
#
# Usage: Run this script and select a camera in the 3D view.
#
import bpy
from bpy.types import (
    GizmoGroup,
)

## Blender example, showing gizmo on active camera
""" 
class MyCameraWidgetGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_test_camera"
    bl_label = "Object Camera Test Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (ob and ob.type == 'CAMERA')

    def setup(self, context):
        # Run an operator using the dial gizmo
        ob = context.object
        gz = self.gizmos.new("GIZMO_GT_dial_3d")
        props = gz.target_set_operator("transform.rotate")
        props.constraint_axis = False, False, True
        props.orient_type = 'LOCAL'
        props.release_confirm = True

        gz.matrix_basis = ob.matrix_world.normalized()
        gz.line_width = 3

        gz.color = 0.8, 0.8, 0.8
        gz.alpha = 0.5

        gz.color_highlight = 1.0, 1.0, 1.0
        gz.alpha_highlight = 1.0

        self.roll_gizmo = gz

    def refresh(self, context):
        ob = context.object
        gz = self.roll_gizmo
        gz.matrix_basis = ob.matrix_world.normalized()
"""

## Same logic, but on Grease pencil object
""" 
class STORYTOOLS_GGT_gp_gizmos(GizmoGroup):
    bl_label = "Grease Pencil Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE'}

    # @classmethod
    # def poll(cls, context):
    #     # ob = context.object
    #     # return ob and ob.type == 'GREASEPENCIL'
    #     return context.object.type == 'MESH'
    
    @classmethod
    def poll(cls, context):
        # if context.scene 
        return any(ob.type == 'GREASEPENCIL' for ob in context.scene.objects)

    def setup(self, context):
        ob = context.object
        # gz = self.gizmos.new("GIZMO_GT_button_2d")
        gz = self.gizmos.new("GIZMO_GT_dial_3d")
        # gz.draw_style = 'FILL'
        gz.draw_options = {'FILL'} # 'FILL_SELECT'
        props = gz.target_set_operator("transform.translate")
        props.constraint_axis = (True, True, False)
        props.orient_type = 'GLOBAL'
        props.release_confirm = True
        

        # gz.matrix_basis = ob.matrix_world.normalized()
        gz.matrix_basis = fn.replace_rotation_matrix(ob.matrix_world, context.space_data.region_3d.view_matrix.inverted() )

        # gz.scale_basis = 0.1  # Adjust the size of the circle

        gz.color = 0.8, 0.8, 0.8
        gz.alpha = 0.5

        gz.color_highlight = 1.0, 1.0, 1.0
        gz.alpha_highlight = 1.0

        self.circle_gizmo = gz

    def refresh(self, context):
        ob = context.object
        gz = self.circle_gizmo
        # gz.matrix_basis = ob.matrix_world.normalized()
        gz.matrix_basis = fn.replace_rotation_matrix(ob.matrix_world, context.space_data.region_3d.view_matrix.inverted())
        ## /!\ Not updated when view move, only when object does (maybe not a problem since view should keep same orientation)
"""

## Gizmo loop test:
## Effectively draw multiple circles but naturally target_operator affect only active object

class STORYTOOLS_GGT_gp_gizmos(GizmoGroup):
    bl_label = "Grease Pencil Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SHOW_MODAL_ALL', 'SCALE'} 

    @classmethod
    def poll(cls, context):
        # if context.scene 
        return any(ob.type == 'GREASEPENCIL' for ob in context.scene.objects)

    def setup(self, context):
        self.gizs = []
        view_mat = context.space_data.region_3d.view_matrix.inverted()
        for ob in [o for o in context.scene.objects if o.type == 'GREASEPENCIL' and o.visible_get()]:
            # gz = self.gizmos.new("GIZMO_GT_button_2d")
            gz = self.gizmos.new("GIZMO_GT_dial_3d")
            gz.draw_options = {'FILL'} # 'FILL_SELECT'
            props = gz.target_set_operator("transform.translate")
            # props.constraint_axis = (True, True, False)
            props.orient_type = 'GLOBAL'
            props.release_confirm = True

            # gz.matrix_basis = ob.matrix_world.normalized()
            gz.matrix_basis = fn.replace_rotation_matrix(ob.matrix_world, view_mat)

            gz.scale_basis = 0.25  # Adjust the size of the circle
            # gz.color = 0.8, 0.8, 0.8
            gz.color = 0.8, 0.8, 0.0
            gz.alpha = 0.5

            gz.color_highlight = 1.0, 1.0, 1.0
            gz.alpha_highlight = 1.0

            self.gizs += [(ob, gz)]

    def refresh(self, context):
        # pass
        view_mat = context.space_data.region_3d.view_matrix.inverted()
        for ob, gz in self.gizs:
            # gz.matrix_basis = ob.matrix_world.normalized()
            gz.matrix_basis = fn.replace_rotation_matrix(ob.matrix_world, view_mat)
        ## /!\ Not updated when view move, only when object does (maybe not a problem since view should keep same orientation)



## Create a custom gizmo to display specific type
gp_plane = (
    Vector((-1, 0, 0)), Vector((1, 0, 0)),
            )


class VIEW3D_GT_show_GP_plane(Gizmo):
    bl_idname = "VIEW3D_GT_show_GP_plane"
    # bl_target_properties = (
    #     {"id": "offset", "type": 'FLOAT', "array_length": 1},
    # )

    __slots__ = (
        "custom_shape",
        # "gp_shape",
        "init_mouse_x",
        "init_mouse_y",
        "mx",
        "my",
    )

    def draw(self, context):
        # self._update_offset_matrix()
        self.color =  (0.2392, 0.2392, 0.2392) # non-gamma-corrected:(0.0466, 0.0466, 0.0466)
        self.color_highlight = (0.27, 0.27, 0.27)
        self.draw_custom_shape(self.custom_shape)

    ## WARN: select_id is probably not what I think it is...
    # def test_select(self, context, select_id):
    #     px_scale = context.preferences.system.ui_scale
    #     x_min = self.matrix_basis.to_translation().x + (x_l * px_scale)
    #     x_max = self.matrix_basis.to_translation().x + (x_r * px_scale)
    #     y_min = self.matrix_basis.to_translation().y + (y_d * px_scale)
    #     y_max = self.matrix_basis.to_translation().y + (y_u * px_scale)
    #     select = 1 if x_min < select_id[0] < x_max and y_min < select_id[1] < y_max else -1

    #     return select

    def setup(self):
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('LINES', gp_plane)
        ## Keep default full alpha
        # self.alpha = 1.0
        # self.alpha_highlight = 1.0

    def invoke(self, context, event):
        self.mx = self.init_mouse_x = event.mouse_x
        self.my = self.init_mouse_y = event.mouse_y
        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        print('exited')
        return 
        ## Just cancel if move above 10px
        # if abs(self.init_mouse_x - self.mx) > 10 or abs(self.init_mouse_y - self.my) > 10:
        #     return

        ## Refresh all 3D areas
        # for area in context.screen.areas:
        #     if area.type == 'VIEW_3D':
        #         area.tag_redraw()

    def modal(self, context, event, tweak):
        self.mx = event.mouse_x
        self.my = event.mouse_y
        ## Dragged opts
        # delta = (event.mouse_y - self.init_mouse_y) / 10.0
        # if 'SNAP' in tweak:
        #     delta = round(delta)
        # if 'PRECISE' in tweak:
        #     delta /= 10.0
        # value = self.init_value - delta
        # self.target_set_value("offset", value)
        # context.area.header_text_set("My Gizmo: %.4f" % value)
        return {'RUNNING_MODAL'}



## Try to map gizmo loop over GP and
class STORYTOOLS_GGT_map_gizmos(GizmoGroup):
    bl_label = "Map gizmos"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'} # SHOW_MODAL_ALL ? 
    # bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        return True

    def setup(self, context):
        visible_gp = [o for o in bpy.context.scene.objects if o.type == 'GREASEPENCIL' and o.visible_get()]
        # visible_gp = [bpy.context.object]
        # lines = [o.matrix_world @ vec for vec in gp_plane for o in visible_gp]
        
        self.gp_gz_list = []

        for gp in visible_gp:
            gz = self.gizmos.new("VIEW3D_GT_show_GP_plane")
            gz.scale_basis = 1
            self.gp_gz_list.append((gz, gp))

        """
        ## Simple Single button_2d
        self.gz_gp_objs = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_gp_objs, 'ADD', scale_basis=10, alpha=0.6) # PLUS
        props = self.gz_gp_objs.target_set_operator("storytools.toggle_bottom_bar")
        """

    def draw_prepare(self, context):
        # prefs = fn.get_addon_prefs()
        settings = context.scene.storytools_settings
        px_scale = context.preferences.system.ui_scale
        
        for gz, ob in self.gp_gz_list:
            gz.matrix_basis = ob.matrix_world

        # self.gz_gp_objs.matrix_basis = mat

    # def refresh(self, context):
    #     pass


classes=(
    # MyCameraWidgetGroup,
    STORYTOOLS_GGT_gp_gizmos,
    # VIEW3D_GT_show_GP_plane,
    # STORYTOOLS_GGT_map_gizmos,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)