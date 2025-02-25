import bpy
import gpu

from bpy.types import Operator
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent
from mathutils.geometry import intersect_line_plane

from .. import fn
from .. import draw

class STORYTOOLS_OT_camera_depth(Operator):
    bl_idname = "storytools.camera_depth"
    bl_label = 'Camera Depth Move'
    bl_description = "Move Camera Depth (forward and backward)\
        \n+ Alt : Lock Z axis movements (After call)\
        \n+ Ctrl : Adjust focal length / orthographic scale"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        self.current_area = context.area
        self.cam = context.scene.camera
        # Store the initial ctrl state
        self.is_focal_mode = event.ctrl
        
        if not self.is_focal_mode and any(self.cam.lock_location):
            self.report({'ERROR'}, 'Camera location is locked')
            return {'CANCELLED'}

        self.init_pos = self.cam.location.copy()
        self.init_mouse_x = event.mouse_x
        
        # Store initial camera values
        self.init_lens = self.cam.data.lens
        self.init_ortho_scale = self.cam.data.ortho_scale
        
        self.shift_pressed = event.shift
        self.current_delta = 0
        self.cumulated_delta = 0

        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        
        # camera forward vector
        self.cam_forward_vec = self.cam.matrix_world.to_quaternion() @ Vector((0,0,-1))
        if self.is_focal_mode:
            self.text_body = "Focal Length" if self.cam.data.type == 'PERSP' else "Orthographic Scale"
            # ui_scale = context.preferences.system.ui_scale
            # self.text_position = (context.area.width / 2 - (120 * ui_scale), event.mouse_region_y + (80 * ui_scale)) # mid area x
            self.text_position = (context.area.width / 2 - 120, event.mouse_region_y + 80) # mid area x
            # self.text_position = (event.mouse_region_x - 100, event.mouse_region_y + 80) # place x relative to mouse
            self.text_size = 18.0
            args = (self, context)    
            self._text_handle = bpy.types.SpaceView3D.draw_handler_add(draw.text_draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.is_focal_mode and self.cam.data.type == 'ORTHO':
            fac = 0.001 if event.shift else 0.01
        else:
            fac = 0.01 if event.shift else 0.1


        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse_x = event.mouse_x

        self.current_delta = (event.mouse_x - self.init_mouse_x) * fac
        move_val = self.cumulated_delta + self.current_delta
        
        if self.is_focal_mode:
            # Adjust camera parameters
            decimals = 2 if event.shift else 1
            if self.cam.data.type == 'ORTHO':
                # For orthographic camera, adjust ortho_scale
                # new_scale = self.init_ortho_scale * (1 - move_val)
                new_scale = self.init_ortho_scale - move_val
                self.cam.data.ortho_scale = new_scale

                # self.text_body = f"Orthographic Scale: {self.cam.data.ortho_scale:.2f}"
                self.text_body = f"Orthographic Scale: {self.init_ortho_scale:.1f} -> {self.cam.data.ortho_scale:.{decimals}f}"
                context.area.header_text_set(f'Orthographic Scale Offset: {move_val:.2f}')
            else:
                # For perspective camera, adjust focal length
                # new_focal = self.init_lens * (1 + move_val)
                new_focal = self.init_lens + move_val
                self.cam.data.lens = new_focal

                # self.text_body = f"Focal Length: {self.cam.data.lens:.1f}"
                self.text_body = f"Focal Length: {self.init_lens:.1f} -> {self.cam.data.lens:.{decimals}f}"
                context.area.header_text_set(f'Focal Length Offset: {move_val:.2f}')
        else:
            # Position-based behavior
            new_position = self.init_pos + self.cam_forward_vec * move_val
            if event.alt:
                new_position.z = self.init_pos.z
            self.cam.matrix_world.translation = new_position
            context.area.header_text_set(f'Camera Offset: {move_val:.2f}')

        if event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")
            if self.is_focal_mode:
                # Keyframe camera parameters
                data_path = 'lens' if self.cam.data.type == 'PERSP' else 'ortho_scale'
                # TODO: pass active keying set ? # options={'INSERTKEY_AVAILABLE'}
                fn.key_data_path(self.cam.data, data_path=data_path, use_autokey=True)
                draw.stop_callback(self, context)
            else:
                fn.key_object(self.cam, scale=False, use_autokey=True)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.is_focal_mode:
                # Restore initial camera parameters
                self.cam.data.lens = self.init_lens
                self.cam.data.ortho_scale = self.init_ortho_scale
            else:
                self.cam.location = self.init_pos
            context.window.cursor_set("DEFAULT")
            draw.stop_callback(self, context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

def shift_lines(context):
    """Return lines to display camera frame shift"""
    scene= context.scene
    camera = context.scene.camera

    shift_x, shift_y = camera.data.shift_x, camera.data.shift_y
    if shift_x == 0 and shift_y == 0:
        return []

    # Shift camera to center of frame
    # center = fn.get_cam_frame_world_center(camera, scene)

    frame = fn.get_cam_frame_world(camera, scene)
    center = sum(frame, Vector()) / 4
    # center = fn.get_cam_frame_world_center(camera, scene)
    if view_vec := fn.get_camera_view_vector():
        view_vec *=100
    else:
        return
    
    ## Get translation vector to return frame in unshifted position 
    unshifted_center = intersect_line_plane(camera.matrix_world.translation, camera.matrix_world.translation + view_vec, frame[0], view_vec)
    translation_vector = unshifted_center - center

    unshifted_frame = [v + translation_vector for v in frame]
    
    ## cam frame
    # 3-0
    # 2-1

    ## Add lines from out corners to non-shifted corners
    index_to_show = set()
    ## Choose index or corner to display (display corner outside of frame)
    if shift_x > 0:
        index_to_show.update([2, 3])
    elif shift_x < 0:
        index_to_show.update([0, 1])

    if shift_y > 0:
        index_to_show.update([1, 2])
    elif shift_y < 0:
        index_to_show.update([0, 3])

    index_to_show = sorted(index_to_show) # implicit convert to list
    # index_to_show = list(index_to_show) # implicit convert to list

    lines = []
    for idx in index_to_show:
        lines.extend([unshifted_frame[idx], frame[idx]])

    ## Fully trace non-shifted frame
    # lines.extend([unshifted_frame[0], unshifted_frame[1], 
    #               unshifted_frame[1], unshifted_frame[2], 
    #               unshifted_frame[2], unshifted_frame[3], 
    #               unshifted_frame[3], unshifted_frame[0]])

    ## Add non-shifted frame border lines
    ## move index accordingly to avoid diagonals
    if shift_y < 0:
        index_to_show.insert(0, index_to_show.pop())
        if shift_x > 0:
            index_to_show.insert(0, index_to_show.pop())

    for i in range(len(index_to_show)-1):
        lines.extend([unshifted_frame[index_to_show[i]], unshifted_frame[index_to_show[i+1]]])

    return lines

class STORYTOOLS_OT_camera_pan(Operator):
    bl_idname = "storytools.camera_pan"
    bl_label = 'Camera Pan/Shift'
    bl_description = "Pan Camera, X/Y to lock on axis\
                    \n+ Shift : Precision mode\
                    \n+ Ctrl (During) : Autolock on moved axis\
                    \n+ Ctrl (Start) : Camera Shift instead of Pan\
                    \n+ Alt  (During Shift): Snap to half-frame offset"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        self.cam = context.scene.camera

        if any(self.cam.lock_location):
            self.report({'ERROR'}, 'Camera location is locked')
            return {'CANCELLED'}

        # Set mode based on initial Ctrl state
        self.shift_mode = event.ctrl
        if self.shift_mode and self.cam.data.type != 'PERSP':
            self.shift_mode = False  # Force pan mode for ortho cameras
            
        self.shift_pressed = event.shift
        self.ctrl_released = False  # Track if Ctrl was released after start
        self.cumulated_delta = Vector((0, 0))
        self.current_delta = Vector((0, 0))

        self.final_lock = self.lock = None
        
        # Store initial values based on mode
        if self.shift_mode:
            self.init_shift_x = self.cam.data.shift_x
            self.init_shift_y = self.cam.data.shift_y
            self.lock_text = 'Camera Shift'
            
            ## Poka-yoke : Add text so used know immediately know he's not in default mode
            self.text_body = "Shift X/Y"
            self.text_position = (context.area.width / 2 - 60, event.mouse_region_y + 80)
            # self.text_position = (event.mouse_region_x - 100, event.mouse_region_y + 80) # place x relative to mouse
            self.text_size = 18.0
            args = (self, context)    
            self._text_handle = bpy.types.SpaceView3D.draw_handler_add(draw.text_draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            ## Show no-shifted frame hint lines
            self.line_coords = shift_lines(context)
            self.line_color = (0.5, 0.5, 0.5, 0.5)
            self._line_handle = bpy.types.SpaceView3D.draw_handler_add(draw.line_draw_callback, (self, context), 'WINDOW', 'POST_VIEW')

        else:
            self.init_pos = self.cam.location.copy()
            self.lock_text = 'Camera Pan'

        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.local_x = self.cam.matrix_world.to_quaternion() @ Vector((1,0,0))
        self.local_y = self.cam.matrix_world.to_quaternion() @ Vector((0,1,0))
        context.window.cursor_set("SCROLL_XY")

        # Setup draw handler
        center = fn.get_cam_frame_world_center(self.cam)
        self.lock_x_coords = [center + self.local_x * 10000, center + self.local_x * -10000]
        self.lock_y_coords = [center + self.local_y * 10000, center + self.local_y * -10000]
        
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw.lock_axis_draw_callback, args, 'WINDOW', 'POST_VIEW')

        self.update_transform(context, event)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def snap_shift(self, context, snap_threshold=0.12):
        '''Snap camera shift to nearest half-frame
        snap_threshold: float, proximity threshold to trigger snapping to half frame'''
        # Get render resolution
        render = context.scene.render
        res_x = render.resolution_x
        res_y = render.resolution_y
        aspect_ratio = res_x / res_y

        # Calculate frame dimensions based on sensor fit
        if self.cam.data.sensor_fit == 'AUTO':
            # In AUTO: If res_x > res_y, behaves like HORIZONTAL, else like VERTICAL
            if res_x >= res_y:
                frame_width = 1.0
                frame_height = 1.0 / aspect_ratio
            else:
                frame_height = 1.0
                frame_width = aspect_ratio
        elif self.cam.data.sensor_fit == 'HORIZONTAL':
            frame_width = 1.0
            frame_height = 1.0 / aspect_ratio
        else:  # VERTICAL
            frame_height = 1.0
            frame_width = aspect_ratio

        # Convert current shift to frame space
        shift_x_frames = self.cam.data.shift_x / frame_width
        shift_y_frames = self.cam.data.shift_y / frame_height

        # Calculate nearest half frame position
        half_x = round(shift_x_frames * 2) / 2
        half_y = round(shift_y_frames * 2) / 2
        
        # Check if we're close enough to snap
        if abs(shift_x_frames - half_x) < snap_threshold:
            self.cam.data.shift_x = half_x * frame_width
        if abs(shift_y_frames - half_y) < snap_threshold:
            self.cam.data.shift_y = half_y * frame_height        

    def update_transform(self, context, event):
        mouse_co = Vector((event.mouse_x, event.mouse_y))
        lock = self.lock
        
        ## Adjust factor based on mode and shift key (precision) state
        if self.shift_mode:
            fac = 0.001 if event.shift else 0.01
        else:
            fac = 0.01 if event.shift else 0.1

        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse = mouse_co

        self.current_delta = (mouse_co - self.init_mouse) * fac
        move_2d = self.cumulated_delta + self.current_delta
        
        ## Handle Ctrl for axis locking
        if event.ctrl:
            if not self.ctrl_released and self.shift_mode:
                # Don't apply autolock until Ctrl has been released and pressed again
                # Only for shift mode
                lock = self.lock
            else:
                if abs(move_2d.x) >= abs(move_2d.y):
                    lock = 'X'
                else:
                    lock = 'Y'
        elif not self.ctrl_released:
            ## Detected released once, kept as flag for next Ctrl press
            self.ctrl_released = True

        # Apply transformation based on mode
        if self.shift_mode:
            move_vec = Vector((0, 0))
            if not lock or lock == 'X': 
                move_vec.x = move_2d.x
            if not lock or lock == 'Y': 
                move_vec.y = move_2d.y

            self.cam.data.shift_x = self.init_shift_x + move_vec.x
            self.cam.data.shift_y = self.init_shift_y + move_vec.y

            if event.alt:
                ## Snap when closed to half-frame offest
                self.snap_shift(context, snap_threshold=0.15)

            decimals = 3 if event.shift else 2
            self.text_body = f"Shift X: {self.cam.data.shift_x:.{decimals}f}\nShift Y: {self.cam.data.shift_y:.{decimals}f}"
            ## update unshifted line hint coordinates
            self.line_coords = shift_lines(context)
        else:
            move_vec = Vector((0,0,0))
            if not lock or lock == 'X': 
                move_vec += self.local_x * (move_2d.x)
            if not lock or lock == 'Y': 
                move_vec += self.local_y * (move_2d.y)

            self.cam.location = self.init_pos + move_vec

        self.final_lock = lock
        mode_text = 'Camera Shift' if self.shift_mode else 'Camera Pan'
        self.lock_text = f'{mode_text} X: {move_2d.x:.3f}, Y: {move_2d.y:.3f}'
        self.lock_text += f' | Lock Axis {lock}' if lock else ''
        context.area.header_text_set(self.lock_text)

    def modal(self, context, event):
        self.update_transform(context, event)
        
        if event.type in ('X','Y') and event.value == 'PRESS':
            self.lock = event.type if self.lock != event.type else None
        
        elif event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")
            draw.stop_callback(self, context)
            
            if self.shift_mode:
                fn.key_data_path(self.cam.data, data_path=['shift_x', 'shift_y'], use_autokey=True)
            else:
                fn.key_object(self.cam, scale=False, use_autokey=True)
            
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.shift_mode:
                self.cam.data.shift_x = self.init_shift_x
                self.cam.data.shift_y = self.init_shift_y
            else:
                self.cam.location = self.init_pos
            
            draw.stop_callback(self, context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}


def fit_camera_view_to_regions(context):
    """
    Fit camera view to viewport while considering all UI regions.
    Returns True if fitting was performed, False otherwise.
    """
    region = context.region
    area = context.area
    r3d = context.space_data.region_3d
    
    # First use Blender's built-in operator to center the camera
    bpy.ops.view3d.view_center_camera()

    # Define margin in pixels
    margin = 20  # Margin around camera frame
    
    # Initialize UI element dimensions
    toolbar_width = 0
    sidebar_width = 0
    header_height = 0
    footer_height = 0
    asset_shelf_height = 0
    
    # Iterate through regions to find UI elements
    for r in area.regions:
        if r.type == 'TOOLS' and r.width > 1:  # Left toolbar
            toolbar_width = r.width
        elif r.type == 'UI' and r.width > 1:  # Right sidebar
            sidebar_width = r.width
        elif r.type == 'HEADER' and r.height > 1:  # Header
            # Check alignment (top or bottom)
            if hasattr(area, 'header_alignment') and area.header_alignment == 'BOTTOM':
                footer_height = r.height
            else:
                header_height = r.height
        elif r.type == 'ASSET_SHELF' and r.height > 1:  # Asset shelf (at bottom)
            asset_shelf_height = r.height
    
    # Calculate available space
    available_width = region.width - (toolbar_width + sidebar_width + 2 * margin)
    available_height = region.height - (header_height + footer_height + asset_shelf_height + 2 * margin)
    
    # Calculate proportion of available space
    width_prop = available_width / region.width
    height_prop = available_height / region.height
    
    # Apply zoom adjustment based on available space
    # We need to make the view smaller to fit within the available area
    current_zoom = r3d.view_camera_zoom
    scale_factor = min(width_prop, height_prop)
    new_zoom = current_zoom * scale_factor - 10  # Extra safety margin
    new_zoom = min(new_zoom, current_zoom)  # Don't zoom in
    r3d.view_camera_zoom = new_zoom
    
    # Calculate offset to center within available space
    # The offset values are normalized from -1 to 1
    # X-axis: positive moves view right, negative moves view left
    # Y-axis: positive moves view up, negative moves view down
    
    # Calculate the UI imbalance (difference between left and right UI elements)
    ui_imbalance_x = toolbar_width - sidebar_width
    
    # Calculate vertical imbalance (consider header, footer and asset shelf)
    ui_imbalance_y = (footer_height + asset_shelf_height) - header_height
    
    # Convert to normalized coordinates (-1 to 1) and handle axis direction
    offset_x = -1.0 * (ui_imbalance_x / (2.0 * region.width))
    offset_y = (ui_imbalance_y / (2.0 * region.height))
    
    # Apply offset
    r3d.view_camera_offset[0] = offset_x
    r3d.view_camera_offset[1] = offset_y
    
    return True


class STORYTOOLS_OT_lock_camera_to_view_toggle(Operator):
    bl_idname = "storytools.lock_camera_to_view_toggle"
    bl_label = 'Toggle Lock Camera To View'
    bl_description = "In Camera view: Toggle 'lock camera to view' (active viewport)\
        \nIn free view: Go to camera\
        \n+ Ctrl : Center and resize view to fit camera bounds\
        \n+ Shift : Match view zoom to render resolution"
    bl_options = {'REGISTER', 'INTERNAL'}

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
            ## Simple method (do not consider regions)
            # bpy.ops.view3d.view_center_camera()
            # ## Dezoom slightly to let frame enter view
            # r3d.view_camera_zoom += r3d.view_camera_zoom * -0.1
            
            ## Use the standalone function for custom view fitting
            fit_camera_view_to_regions(context)
            
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
    