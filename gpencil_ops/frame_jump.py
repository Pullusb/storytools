import bpy

from mathutils import Vector, Matrix

from bpy.types import Operator

from .. import fn

def check_for_frames(ob, active_only=True):
    if ob.type != 'GPENCIL':
        return 'Not a Grease Pencil object'

    if not (layer := ob.data.lauers.active):
        return "No active layer on grease pencil object"

    if not len(layer.frames):
        return f'No frames on active layer {layer.info}'

    return False


## Duplicate code from GPtoolbox ?

"""
class STORYTOOLS_OT_gp_frame_jump(Operator):
    bl_idname = "screen.gp_frame_jump"
    bl_label = 'Jump to GPencil Keyframe'
    bl_description = "Jump to prev/next keyframe on active and selected layers of active grease pencil object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'
    
    def execute(self, context):
        if error_message := check_for_frames(context.object):
            self.report({'ERROR'}, error_message)
            return {'CANCELLED'}
"""


""" # WIP flip frame ops, modal copeid from object pan
class STORYTOOLS_OT_flip_frames(Operator):
    bl_idname = "storytools.flip_frames"
    bl_label = 'Flip Frames'
    bl_description = "Flip in frames by dragging left-right"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    def invoke(self, context, event):
        self.ob = context.object
        self.layer = context.object.data.layers.active
        if not self.layer:
            self.report({'ERROR'}, "No active layer on Grease pencil object")
            return {'CANCELLED'}

        if not len(self.layer.frames):
            self.report({'ERROR'}, f'No frames on active layer {self.layer.info}')
            return {'CANCELLED'}

        self.shift_pressed = event.shift
        self.cumulated_translate = Vector((0, 0, 0))
        self.current_translate = Vector((0, 0, 0))

        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.init_vector = fn.region_to_location(self.init_mouse, self.init_world_loc)

        self.update_position(context, event)

        ## Placement helpers
        # self._guide_handle = bpy.types.SpaceView3D.draw_handler_add(draw.guide_callback, args, 'WINDOW', 'POST_VIEW')
        context.window.cursor_set("SCROLL_XY")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def update_position(self, context, event):
        mouse_co = Vector((event.mouse_x, event.mouse_y))

        ## Handle precision mode
        multiplier = 1 if not event.shift else 0.1
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_translate += self.current_translate
            self.init_vector = fn.region_to_location(mouse_co, self.init_world_loc)

        current_loc = fn.region_to_location(mouse_co, self.init_world_loc)

        self.current_translate = (current_loc - self.init_vector) * multiplier

        move_vec = self.current_translate + self.cumulated_translate

        # new_loc = self.init_world_loc + move_vec


    def modal(self, context, event):    
        self.update_position(context, event)

        if event.type == 'LEFTMOUSE': # and event.value == 'RELEASE'
            # draw.stop_callback(self, context)
            ## just quit
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.ob.matrix_world = self.init_mat
            # draw.stop_callback(self, context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        return {"FINISHED"}
"""