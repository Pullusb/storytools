import bpy
import gpu
import math

from time import time
from math import pi, radians, degrees
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_plane

from bpy.types import Operator
from gpu_extras.batch import batch_for_shader

from .. import fn
from .. import draw

## Bonus
# - load guides if there are any

## possible modal cursor set
# ('DEFAULT', 'NONE', 'WAIT', 'CROSSHAIR', 'MOVE_X', 'MOVE_Y', 'KNIFE', 'TEXT', 
# 'PAINT_BRUSH', 'PAINT_CROSS', 'DOT', 'ERASER', 'HAND', 
# 'SCROLL_X', 'SCROLL_Y', 'SCROLL_XY', 'EYEDROPPER', 'PICK_AREA', 
# 'STOP', 'COPY', 'CROSS', 'MUTE', 'ZOOM_IN', 'ZOOM_OUT')

## Object transform

    # on_cam : bpy.props.BoolProperty(
    #     default=False, options={'SKIP_SAVE'})
        # if self.on_cam:
        #     self.ob = context.scene.camera
        #     if not self.ob:
        #         return {'CANCELLED'}

        #     ## Take view center when in viewcam
        #     if context.space_data.region_3d.view_perspective == 'CAMERA':
        #         self.init_world_loc = fn.get_cam_frame_world_center(self.ob)
        #     else:
        #         self.init_world_loc = self.ob.matrix_world.to_translation()

        # else:
        #     self.ob = context.object
        #     self.init_world_loc = self.ob.matrix_world.to_translation()

def draw_callback_wall(self, context):
    ## Restrict to current viewport
    if context.area != self.current_area:
        return

    prefs = fn.get_addon_prefs()
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    shader.bind()

    previous_depth_test_value = gpu.state.depth_test_get()
    # gpu.state.depth_mask_set(True)
    gpu.state.blend_set('ALPHA')

    ## Draw behind zone
    gpu.state.depth_test_set('LESS')
    shader.uniform_float("color", prefs.visual_hint_end_color)
    batch = batch_for_shader(shader, 'TRIS', {"pos": self.coords})
    batch.draw(shader)

    if context.space_data.region_3d.view_perspective == 'CAMERA':
        ## Draw front zone (only in camera view to avoid flicking)
        gpu.state.depth_test_set('GREATER')
        shader.uniform_float("color", prefs.visual_hint_start_color)
        batch = batch_for_shader(shader, 'TRIS', {"pos": self.front_coords})
        batch.draw(shader)


    # Restore values
    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set(previous_depth_test_value)
    # gpu.state.depth_mask_set(False)

class STORYTOOLS_OT_object_depth_move(Operator):
    bl_idname = "storytools.object_depth_move"
    bl_label = "Object Depth Move"
    bl_description = "Move object Forward/backward (Slide left-right)\
                    \n+ Ctrl : Adjust Scale (Retain same size in camera framing)\
                    \n+ Shift : Precision mode\
                    \n+ Alt : Constraint on horizontal plane"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not context.object:
            cls.poll_message_set("No active object")
            return False
        if context.object.type == 'CAMERA' and len(context.selected_objects) < 2:
            cls.poll_message_set("Cannot move camera object")
            return False
        return True
        # return context.object and context.object.type != 'CAMERA'

    def invoke(self, context, event):
        self.cam = bpy.context.scene.camera
        if not self.cam:
            self.report({'ERROR'}, 'No active camera')
            return {"CANCELLED"}
        if any(context.object.lock_location):
            self.report({'ERROR'}, "Active object's location is locked")
            return {'CANCELLED'}
        
        self.init_mouse_x = event.mouse_x
        self.shift_pressed = event.shift
        self.delta = 0
        self.cumulated_delta = 0

        self.coords = []
        self.front_coords = []
        self.cam_pos = self.cam.matrix_world.translation
        self.view_vector = Vector((0,0,-1))
        self.view_vector.rotate(self.cam.matrix_world)
        self.mode = 'distance'

        ## Consider all selected only in object mode
        if context.mode == 'OBJECT':
            self.objects = [o for o in context.selected_objects if o.type != 'CAMERA']
            if context.object.type != 'CAMERA' and context.object not in self.objects:
                self.objects.append(context.object)
        else:
            self.objects = [context.object]

        # Filter locked objects
        self.objects = [o for o in self.objects if not any(o.lock_location)] 
        if not self.objects:
            self.report({'ERROR'}, "Object is locked")
            return {'CANCELLED'}

        self.init_mats = [o.matrix_world.copy() for o in self.objects]
        
        if self.cam.data.type == 'ORTHO':
            context.area.header_text_set(f'Move factor: 0.00')
            # distance is view vector based
        else:
            self.init_vecs = [o.matrix_world.translation - self.cam_pos for o in self.objects]
            self.init_dists = [v.length for v in self.init_vecs]
            context.area.header_text_set(
                f'Move factor: 0.00 | Mode: {self.mode} (M to switch) | Ctrl: Adjust Scale | Shift: Precision')
        
        context.window.cursor_set("SCROLL_X")
        
        self.current_area = context.area # gpuDraw
        if fn.get_addon_prefs().use_visual_hint:
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_wall, (self, context), 'WINDOW', 'POST_VIEW') # gpuDraw
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def stop(self, context):
        context.area.header_text_set(None)
        context.window.cursor_set("DEFAULT")
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW') # gpuDraw
        context.area.tag_redraw()
        ## refresh all view if in all viewport

    def modal(self, context, event):
        if self.mode == 'distance':
            factor = 0.1 if not event.shift else 0.01
        else:
            # Smaller factor for proportional dist
            factor = 0.01 if not event.shift else 0.001

        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.delta
            self.init_mouse_x = event.mouse_x

        if event.type in {'MOUSEMOVE'}:
            # diff = (event.mouse_x - self.init_mouse_x) * factor

            self.delta = (event.mouse_x - self.init_mouse_x) * factor
            diff = self.cumulated_delta + self.delta

            if self.cam.data.type == 'ORTHO':
                # just push in view vector direction
                context.area.header_text_set(f'Move factor: {diff:.2f}')
                for i, obj in enumerate(self.objects):
                    new_vec = self.init_mats[i].translation + (self.view_vector * diff)
                    obj.matrix_world.translation = new_vec
            else:
                # Push from camera point and scale accordingly
                context.area.header_text_set(
                    f'Move factor: {diff:.2f} | Mode: {self.mode} (M to switch) | Ctrl: Adjust scale | Shift: Slow')

                for i, obj in enumerate(self.objects):
                    if self.mode == 'distance':
                        ## move with the same length for everyone 
                        new_vec = self.init_vecs[i] + (self.init_vecs[i].normalized() * diff)
                    
                    else:
                        ## move with proportional factor from individual distance vector to camera
                        new_vec = self.init_vecs[i] + (self.init_vecs[i] * diff)

                    if event.alt: # Lock Z position 
                        new_pos = self.cam_pos + new_vec
                        new_pos.z = self.init_mats[i].to_translation().z
                        new_vec = new_pos - self.cam_pos

                    obj.matrix_world.translation = self.cam_pos + new_vec
                    
                    if event.ctrl: # Adjust scale only if Ctrl is pressed
                        dist_percentage = new_vec.length / self.init_dists[i]
                        obj.scale = self.init_mats[i].to_scale() * dist_percentage
                    else:
                        obj.scale = self.init_mats[i].to_scale() # reset to initial size

            ## Prepare coordinate for GPU draw
            d = 1000
            z_offset = 0.006
            self.coords = [
                Vector((-d,-d, -z_offset)),
                Vector((d,-d, -z_offset)),
                Vector((0, d, -z_offset)),
            ]
            for v in self.coords:
                v.rotate(self.cam.matrix_world)
                v += context.object.matrix_world.to_translation()
            
            self.front_coords = [
                Vector((-d,-d, z_offset)),
                Vector((d,-d, z_offset)),
                Vector((0, d, z_offset)),
            ]
            for v in self.front_coords:
                v.rotate(self.cam.matrix_world)
                v += context.object.matrix_world.to_translation()


        if event.type in {'M'} and event.value == 'PRESS':
            # Switch mode
            self.mode = 'distance' if self.mode == 'proportional' else 'proportional'

        # cancel on release
        if event.type in {'LEFTMOUSE'}: # and event.value == 'PRESS'
            draw.stop_callback(self, context)
            ## Key objects
            for o in self.objects:
                fn.key_object(o, use_autokey=True)
            return {"FINISHED"}
        
        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            for i, obj in enumerate(self.objects):
                obj.matrix_world = self.init_mats[i]
            draw.stop_callback(self, context)
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}


class STORYTOOLS_OT_object_pan(Operator):
    bl_idname = "storytools.object_pan"
    bl_label = 'Object Pan Translate'
    bl_description = "Translate active object, X/Y to lock on axis\
                    \n+ Ctrl : autolock on major axis\
                    \n+ Shift : Precision mode\
                    \n+ Alt : Constraint on horizontal plane"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object

    def invoke(self, context, event):
        # TODO bonus : add multiselection support like depth move (only on object mode)
        self.ob = context.object
        if any(context.object.lock_location):
            self.report({'ERROR'}, "Active object's location is locked")
            return {'CANCELLED'}

        self.final_lock = self.lock = None
        self.shift_pressed = event.shift
        self.cumulated_translate = Vector((0, 0, 0))
        self.current_translate = Vector((0, 0, 0))
        self.init_world_loc = self.ob.matrix_world.to_translation()

        self.init_mat = self.ob.matrix_world.copy() # to restore if cancelled

        ## Axis Lock
        # view_matrix = context.space_data.region_3d.view_matrix
        # self.local_x = view_matrix.to_quaternion() @ Vector((1,0,0))
        # self.local_y = view_matrix.to_quaternion() @ Vector((0,1,0))
        self.view_rotation = context.space_data.region_3d.view_rotation.copy()
        self.view_no = Vector((0,0,-1))
        self.view_no.rotate(self.view_rotation)
        self.local_x = self.view_rotation @ Vector((1,0,0))
        self.local_y = self.view_rotation @ Vector((0,1,0))
        self.lock_x_coords = [self.init_world_loc + self.local_x * 10000, 
                              self.init_world_loc + self.local_x * -10000]
        self.lock_y_coords = [self.init_world_loc + self.local_y * 10000, 
                              self.init_world_loc + self.local_y * -10000]

        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.init_vector = fn.region_to_location(self.init_mouse, self.init_world_loc)

        self.update_position(context, event)

        args = (self, context)
        ## Handler for lock axis
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw.lock_axis_draw_callback, args, 'WINDOW', 'POST_VIEW')
        ## Handler for origin positions and ghost
        self._pos_handle = bpy.types.SpaceView3D.draw_handler_add(draw.origin_position_callback, args, 'WINDOW', 'POST_VIEW')
        
        ## placement helpers
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
            ## Broken with track to target
            # mouse_co_world = fn.region_to_location(mouse_co, self.init_world_loc)
            # origin = context.space_data.region_3d.view_matrix.inverted().to_translation()
            # self.init_vector = intersect_line_plane(origin, mouse_co_world, self.init_world_loc, self.view_no)

        current_loc = fn.region_to_location(mouse_co, self.init_world_loc)
        ## TODO Need a method for moving track to target
        # mouse_co_world = fn.region_to_location(mouse_co, self.init_world_loc)
        # origin = context.space_data.region_3d.view_matrix.inverted().to_translation()
        # current_loc = intersect_line_plane(origin, mouse_co_world, self.init_world_loc, self.view_no)

        self.current_translate = (current_loc - self.init_vector) * multiplier

        move_vec = self.current_translate + self.cumulated_translate

        lock = self.lock
        ## Override lock with ctrl auto-axis lock if pressed
        if event.ctrl:
            move_2d = mouse_co - self.init_mouse
            if abs(move_2d.x) >= abs(move_2d.y):
                lock = 'X'
            else:
                lock = 'Y'

        new_loc = self.init_world_loc + move_vec
        
        if lock:
            ## Use intersect line plane on object origin and cam X-Z plane
            if lock == 'X':
                plane_no = self.view_rotation @ Vector((0,1,0))
            if lock == 'Y':
                plane_no = self.view_rotation @ Vector((1,0,0))
            locked_pos = intersect_line_plane(new_loc, new_loc + plane_no, self.init_world_loc, plane_no)
            if locked_pos is not None:
                new_loc = locked_pos

        self.final_lock = lock

        if event.alt: # Lock initial Z position 
            new_loc.z = self.init_world_loc.z

        ## Set new position
        self.ob.matrix_world.translation = new_loc

    def modal(self, context, event):    
        self.update_position(context, event)

        if event.type in ('X','Y') and event.value == 'PRESS':
            self.lock = event.type if self.lock != event.type else None

        if event.type == 'LEFTMOUSE': # and event.value == 'RELEASE'
            draw.stop_callback(self, context)
            fn.key_object(self.ob, use_autokey=True)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.ob.matrix_world = self.init_mat
            draw.stop_callback(self, context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        return {"FINISHED"}

class STORYTOOLS_OT_object_rotate(Operator):
    bl_idname = "storytools.object_rotate"
    bl_label = 'Object Rotate'
    bl_description = "Rotate active object on camera axis\
                    \n+ Ctrl : Snap on 15 degrees angles\
                    \n+ Shift : Precision mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    camera : bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})

    # @classmethod
    # def poll(cls, context):
    #     return context.object
    
    @classmethod
    def description(self, context, properties):
        if properties.camera:
            return "Rotate Camera\
                    \n+ Ctrl : Snap on 15 degrees angles\
                    \n+ Shift : Precision mode\
                    \nDouble click : reset rotation"

        return "Rotate active object on camera axis\
                    \n+ Ctrl : Snap on 15 degrees angles\
                    \n+ Shift : Precision mode"

    def reset_rotation(self, context):
        r3d = context.space_data.region_3d
        aim = r3d.view_rotation @ Vector((0.0, 0.0, 1.0)) # view vector
        # aim = self.ob.matrix_world.to_quaternion() @ Vector((0.0, 0.0, 1.0)) # view vector
        z_up_quat = aim.to_track_quat('Z','Y') # track Z, up Y
        if r3d.view_perspective != 'CAMERA':
            r3d.view_rotation = z_up_quat
            return

        q = self.ob.matrix_world.to_quaternion() # store current rotation

        if self.ob.parent:
            q = self.ob.parent.matrix_world.inverted().to_quaternion() @ q
            cam_quat = self.ob.parent.matrix_world.inverted().to_quaternion() @ z_up_quat
        else:
            cam_quat = z_up_quat
        self.ob.rotation_euler = cam_quat.to_euler('XYZ')

        ## Set view position in cam as in GP tools rotate canvas ?
        # diff_angle = q.rotation_difference(cam_quat).to_euler('ZXY').z        
        # # self.set_cam_view_offset_from_angle(context, diff_angle)

    def invoke(self, context, event):
        if self.camera:
            ## Need a custom implementation
            # if context.region_data.view_perspective != 'CAMERA':
            #     # bpy.ops.view3d.rotate_canvas('INVOKE_DEFAULT')
            #     bpy.ops.view3d.view_roll('INVOKE_DEFAULT')
            #     return {"FINISHED"}
            self.ob = context.scene.camera
        else:
            self.ob = context.object
        
        if not self.ob:
            mess = "No active object"
            self.report({'ERROR'}, mess)
            return {'CANCELLED'}
            
        if any(self.ob.lock_rotation):
            self.report({'ERROR'}, "Rotation is locked !")
            return {'CANCELLED'}
    
        self.shift_pressed = event.shift
        self.cumulated_delta = 0
        self.current_delta = 0

        self.init_mat = self.ob.matrix_world.copy()

        self.view_vector = Vector((0,0,-1))
        r3d = context.space_data.region_3d
        self.view_vector.rotate(r3d.view_rotation) # r3d.view_matrix

        ## Snap on 15 degrees
        self.snap_step = radians(15)
        self.init_mouse_x = event.mouse_x
        
        ## Check previous time to detect double click
        # if event.alt: # Alt not accessible

        if self.camera and (last_rotate_call_time := context.window_manager.get('last_rotate_call_time')):
            if time() - last_rotate_call_time < 0.25:
                self.reset_rotation(context)
                fn.key_object(self.ob, use_autokey=True)
                return {'FINISHED'}

        ## Optional handler to show origin and ghost
        args = (self, context) # Dcb
        self._pos_handle = bpy.types.SpaceView3D.draw_handler_add(draw.origin_position_callback, args, 'WINDOW', 'POST_VIEW') # Dcb

        context.window.cursor_set("SCROLL_XY")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    # def draw(self, context):
    #     return

    def update_rotation(self, context, event):
        ## Adjust rotation speed according to precision mode
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse_x = event.mouse_x

        ## Calcualte rotation from last reference point
        multiplier = 0.01 if not event.shift else 0.001
        self.current_delta = (event.mouse_x - self.init_mouse_x) * multiplier

        ## Get final rotation
        final_rotation = self.cumulated_delta + self.current_delta
        
        ## Angle snap
        if event.ctrl:
            final_rotation = fn.snap_to_step(final_rotation, self.snap_step)

        context.area.header_text_set(f'Rotation: {degrees(final_rotation):.2f}')

        ## Rotate on view vector
        rot_matrix = Matrix.Rotation(final_rotation, 4, self.view_vector)

        mat = self.init_mat.copy()
        mat.translation = Vector((0,0,0))
        mat = rot_matrix @ mat
        mat.translation = self.init_mat.translation
        self.ob.matrix_world = mat

    def modal(self, context, event): 
        self.update_rotation(context, event)
        if event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")
            fn.key_object(self.ob, use_autokey=True)
            draw.stop_callback(self, context) # Dcb
            if self.camera:
                context.window_manager['last_rotate_call_time'] = time()
                if self.init_mat == self.ob.matrix_world:
                    ## Avoid undo stack push if there was on moves
                    return {'CANCELLED'}

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.ob.matrix_world = self.init_mat
            context.area.header_text_set(None)
            context.window.cursor_set("DEFAULT")
            draw.stop_callback(self, context) # Dcb
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        return {"FINISHED"}


class STORYTOOLS_OT_object_scale(Operator):
    bl_idname = "storytools.object_scale"
    bl_label = 'Object Scale'
    bl_description = "Scale object by going left-right\
                    \n+ Shift : Precision mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object

    def invoke(self, context, event):
        if any(context.object.lock_scale):
            self.report({'ERROR'}, "Active object's scale is locked")
            return {'CANCELLED'}
        self.init_scale = context.object.scale.copy()
        self.init_mouse_x = event.mouse_x

        self.shift_pressed = event.shift
        self.current_delta = 0
        self.cumulated_delta = 0

        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        multiplier = 0.01 if not event.shift else 0.001
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse_x = event.mouse_x

        self.current_delta = (event.mouse_x - self.init_mouse_x) * multiplier

        scale_offset = self.cumulated_delta + self.current_delta

        ## Mutliply by initial scale
        context.object.scale = self.init_scale * (1 + scale_offset)

        ## Add to initial scale (Less usable with bigger scales)
        # context.object.scale = self.init_scale + Vector([scale_offset]*3)

        if event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")

            ## Key all transforms
            fn.key_object(context.object, use_autokey=True)

            ## Key only scale
            # fn.key_object(context.object, loc=False, rot=False, use_autokey=True)

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.object.scale = self.init_scale
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

class STORYTOOLS_OT_object_key_transform(Operator):
    bl_idname = "storytools.object_key_transform"
    bl_label = 'Key Object Transforms'
    bl_description = "Key active object Loc / Rot / Scale"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object

    def execute(self, context):
        ret = fn.key_object(context.object)
        if ret:
            self.report({'INFO'}, ret)
        return {"FINISHED"}

## Cannot append to GPencil 'Add' menu, being an operator_menu_enum "object.gpencil_add"
# def menu_add_storytools_gp(self, context):
#     """Storyboard GP object entries in the Add Object > Gpencil Menu"""
#     if context.mode == 'OBJECT':
#         self.layout.operator('storytools.create_object', text="Storyboard Drawing")

## to test -> bl_options = {'HIDE_HEADER'}

classes=(
STORYTOOLS_OT_object_pan,
STORYTOOLS_OT_object_rotate,
STORYTOOLS_OT_object_scale,
STORYTOOLS_OT_object_depth_move,
STORYTOOLS_OT_object_key_transform,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)