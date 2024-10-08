import bpy
import gpu

from bpy.types import Operator
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent

from .. import fn
from .. import draw

class STORYTOOLS_OT_camera_depth(Operator):
    bl_idname = "storytools.camera_depth"
    bl_label = 'Camera Depth Move'
    bl_description = "Move Camera Depth (forward and backward)\
        \n+ Alt : Lock Z axis movements"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        self.cam = context.scene.camera
        if any(self.cam.lock_location):
            self.report({'ERROR'}, 'Camera location is locked')
            return {'CANCELLED'}

        self.init_pos = self.cam.location.copy()
        self.init_mouse_x = event.mouse_x
        
        self.shift_pressed = event.shift
        self.current_delta = 0
        self.cumulated_delta = 0

        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        
        # camera forward vector
        self.cam_forward_vec = self.cam.matrix_world.to_quaternion() @ Vector((0,0,-1))
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        fac = 0.01 if event.shift else 0.1
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse_x = event.mouse_x

        self.current_delta = (event.mouse_x - self.init_mouse_x) * fac

        move_val = self.cumulated_delta + self.current_delta

        new_position = self.init_pos + self.cam_forward_vec * move_val
        if event.alt:
            new_position.z = self.init_pos.z

        self.cam.matrix_world.translation = new_position
        
        if event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")
            fn.key_object(self.cam, scale=False, use_autokey=True)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cam.location = self.init_pos
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

class STORYTOOLS_OT_camera_pan(Operator):
    bl_idname = "storytools.camera_pan"
    bl_label = 'Object Pan Translate'
    bl_description = "Pan Camera, X/Y to lock on axis\
                    \n+ Ctrl : autolock on major axis\
                    \n+ Shift :Precision mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        self.cam = context.scene.camera

        if any(self.cam.lock_location):
            # print('locked!')
            self.report({'ERROR'}, 'Camera location is locked')
            return {'CANCELLED'}

            ## redo panel changes crash (probably cause of the mix)
            self.ob = self.cam # need to assign 'ob' variable
            return context.window_manager.invoke_props_dialog(self)

        self.shift_pressed = event.shift
        self.cumulated_delta = Vector((0, 0))
        self.current_delta = Vector((0, 0))

        self.final_lock = self.lock = None
        self.init_pos = self.cam.location.copy() # to restore if cancelled
        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.lock_text = 'Camera Pan'
        self.local_x = self.cam.matrix_world.to_quaternion() @ Vector((1,0,0))
        self.local_y = self.cam.matrix_world.to_quaternion() @ Vector((0,1,0))
        context.window.cursor_set("SCROLL_XY")

        self.update_position(context, event)

        ## Draw handler
        center = fn.get_cam_frame_world_center(self.cam)
        self.lock_x_coords = [center + self.local_x * 10000, center + self.local_x * -10000]
        self.lock_y_coords = [center + self.local_y * 10000, center + self.local_y * -10000]
        wm = context.window_manager

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw.lock_axis_draw_callback, args, 'WINDOW', 'POST_VIEW')

        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def update_position(self, context, event):
        mouse_co = Vector((event.mouse_x, event.mouse_y))
        lock = self.lock
        
        ## Slower with shift
        fac = 0.01 if event.shift else 0.1
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse = mouse_co

        self.current_delta = (mouse_co - self.init_mouse) * fac
        move_2d = self.cumulated_delta + self.current_delta
        
        # Ctrl: override lock to "major" direction
        if event.ctrl:
            if abs(move_2d.x) >= abs(move_2d.y):
                lock = 'X'
            else:
                lock = 'Y'

        move_vec = Vector((0,0,0))
        if not lock or lock == 'X': 
            move_vec += self.local_x * (move_2d.x)
        if not lock or lock == 'Y': 
            move_vec += self.local_y * (move_2d.y)

        self.final_lock = lock
        # set location
        self.cam.location = self.init_pos + move_vec
        
        ## set header text (optional)
        self.lock_text = f'Camera Pan X: {move_2d.x:.3f}, Y: {move_2d.y:.3f}'
        self.lock_text += f' | Lock Axis {lock}' if lock else ''
        context.area.header_text_set(self.lock_text)

    def modal(self, context, event):
        self.update_position(context, event)
        
        if event.type in ('X','Y') and event.value == 'PRESS':
            self.lock = event.type if self.lock != event.type else None
        
        elif event.type == 'LEFTMOUSE': # and event.value == 'RELEASE'
            context.window.cursor_set("DEFAULT")
            
            fn.key_object(self.cam, scale=False, use_autokey=True)

            draw.stop_callback(self, context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cam.location = self.init_pos
            draw.stop_callback(self, context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}


class STORYTOOLS_OT_lock_camera_to_view_toggle(Operator):
    bl_idname = "storytools.lock_camera_to_view_toggle"
    bl_label = 'Toggle Lock Camera To View'
    bl_description = "In Camera view: Toggle 'lock camera to view' (active viewport)\
        \nIn free view: Go to camera\
        \n+ Ctrl : Center and resize view to fit camera bounds\
        \n+ Shift : Match view zoom to render resolution"
    bl_options = {'REGISTER', 'INTERNAL'}


    # Ctrl : Fit viewport to camera frame bounds

    def invoke(self, context, event):
        self.fit_viewport = event.ctrl
        self.zoom_full_res = event.shift
        
        return self.execute(context)

    def execute(self, context):
        go_to_cam = False
        
        if context.space_data.region_3d.view_perspective != 'CAMERA':
            context.space_data.region_3d.view_perspective = 'CAMERA'
            go_to_cam = True

        r3d = context.space_data.region_3d
        is_rotation_locked = r3d.lock_rotation

        if is_rotation_locked and (self.fit_viewport or self.zoom_full_res):
            ## If lock rotation is enabled zoom ops will raise errors
            ## Unlock temporarily
            r3d.lock_rotation = False

        if self.fit_viewport:
            ## TODO: Custom view_fit that consider all regions width
            # fn.fit_view(context)
            # return {"FINISHED"}

            bpy.ops.view3d.view_center_camera()
            ## Dezoom slightly to let frame enter view

            r3d.view_camera_zoom += r3d.view_camera_zoom * -0.1

            if is_rotation_locked:
                r3d.lock_rotation = True
            return {"FINISHED"}

        if self.zoom_full_res:
            bpy.ops.view3d.zoom_camera_1_to_1()
            if is_rotation_locked:
                r3d.lock_rotation = True
            return {"FINISHED"}


        if go_to_cam:
            return {"FINISHED"}

        ## Toggle lock only if in camera view 
        sd = context.space_data
        sd.lock_camera = not sd.lock_camera
        return {"FINISHED"}

class STORYTOOLS_OT_camera_key_transform(Operator):
    bl_idname = "storytools.camera_key_transform"
    bl_label = 'Key Camera Transforms'
    bl_description = "Key current camera location and rotation"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def execute(self, context):
        ret = fn.key_object(context.scene.camera, scale=False)
        if ret:
            self.report({'INFO'}, ret)
        return {"FINISHED"}
 
class STORYTOOLS_OT_lock_view(Operator):
    bl_idname = "storytools.lock_view"
    bl_label = 'Lock Current View'
    bl_description = "Lock current viewport orbit navigation"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        r3d = context.space_data.region_3d
        r3d.lock_rotation = not r3d.lock_rotation
        return {"FINISHED"}

class VIEW3D_OT_locked_pan(bpy.types.Operator):
    bl_idname = "view3d.locked_pan"
    bl_label = "Locked Pan"
    bl_description = "Locked Pan, a wrapper for pan operation\
                    \nOnly valid when viewport has locked rotation (region_3d.lock_rotation)"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        # context.area.type == 'VIEW_3D'
        return context.space_data.region_3d.lock_rotation

    def execute(self, context):
        # print("Locked rotation - Pan wrapper") # Dbg
        bpy.ops.view3d.move("INVOKE_DEFAULT")
        return {'FINISHED'}

## --- KEYMAPS

addon_keymaps = []
def register_keymaps():
    addon = bpy.context.window_manager.keyconfigs.addon

    # active
    # compare
    # idname
    # name
    # repeat
    # map_type

    key_props = [
    'type',
    'value',
    'ctrl',
    'alt',
    'shift',
    'oskey',
    'any',
    'key_modifier',
    ]

    user_km = bpy.context.window_manager.keyconfigs.user.keymaps.get('3D View')
    if not user_km:
        print('-- Storytools could not reach user keymap')
        return

    for skmi in user_km.keymap_items:
        # Only replicate orbit shortcut
        if skmi.idname != 'view3d.rotate':
            continue

        # skmi.show_expanded = True #Dbg

        ## FIXME : Trackball shortcut skip ?
        ## by default 3 shortcut exists : MOUSEROTATE, MIDDLEMOUSE, TRACKPADPAN
        if skmi.type == 'MOUSEROTATE':
            continue

        ## Check if duplicates exists 
        km_dup = next((k for k in user_km.keymap_items 
                        if k.idname == VIEW3D_OT_locked_pan.bl_idname
                        and all(getattr(skmi, x) == getattr(k, x) for x in key_props)), None)
        if km_dup:
            # print(f'--> "{skmi.name} > {skmi.type} > {skmi.value}" shortcut already have a lock pan equivalent') # Dbg
            continue
        
        # print(f'>-> Create {skmi.name} > {skmi.type} > {skmi.value}" shortcut to lock pan') # Dbg
        ## Create duplicate
        km = addon.keymaps.new(name = "3D View", space_type = "VIEW_3D")
        kmi = km.keymap_items.new(
            idname=VIEW3D_OT_locked_pan.bl_idname,
            type=skmi.type,
            value=skmi.value,
            ctrl=skmi.ctrl,
            alt=skmi.alt,
            shift=skmi.shift,
            oskey=skmi.oskey,
            any=skmi.any,
            key_modifier=skmi.key_modifier,
            )

        addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

@persistent
def set_lockpan_km(dummy):
    register_keymaps()

classes=(
    STORYTOOLS_OT_camera_pan,
    STORYTOOLS_OT_camera_depth,
    STORYTOOLS_OT_camera_key_transform,
    STORYTOOLS_OT_lock_camera_to_view_toggle,
    STORYTOOLS_OT_lock_view,
    VIEW3D_OT_locked_pan,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(set_lockpan_km)
    # register_keymaps()

def unregister():
    unregister_keymaps()
    bpy.app.handlers.load_post.remove(set_lockpan_km)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    