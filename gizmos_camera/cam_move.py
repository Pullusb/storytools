import bpy

from bpy.types import Operator
from mathutils import Vector
from mathutils.geometry import intersect_line_plane

from .. import fn
from .. import draw

def setup_top_view_map(self, context, distance=15.0):
    prefs = fn.get_addon_prefs()
    args = (self, context)
    if not prefs.use_top_view_map:
        return 
    ## Setup pip view properties
    ## Upper left corner
    self.pip_size = prefs.top_view_map_size / 100  # Size relative to viewport
    # self.pip_quality = 100  # Render quality percentage
    self.pip_from_camera = True

    top_margin = fn.get_header_margin(context, bottom=False)
    left_margin = next((r.width for r in context.area.regions if r.type == 'TOOLS'), 0)
    offset_from_corner = 10
    bottom_pos = context.region.height * self.pip_size + top_margin + offset_from_corner
    self.pip_position = (left_margin + offset_from_corner, context.region.height - bottom_pos)

    self.pip_object = self.cam

    self.pip_distance = distance
    self._pip_handle = bpy.types.SpaceView3D.draw_handler_add(draw.zenith_view_callback, args, 'WINDOW', 'POST_PIXEL')

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

    dolly_mode : bpy.props.BoolProperty(name="Dolly Mode", default=False)

    def invoke(self, context, event):
        self.current_area = context.area
        self.cam = context.scene.camera
        # Store the initial ctrl state
        self.is_focal_mode = event.ctrl
        if not self.is_focal_mode and any(self.cam.lock_location):
            self.report({'ERROR'}, 'Camera location is locked')
            return {'CANCELLED'}

        self.init_pos = self.cam.matrix_world.translation.copy()
        self.init_mouse_x = event.mouse_x
        
        # Store initial camera values
        self.init_lens = self.cam.data.lens
        self.init_ortho_scale = self.cam.data.ortho_scale
        
        self.shift_pressed = event.shift
        self.current_delta = 0
        self.cumulated_delta = 0

        if context.active_object and context.active_object != self.cam:
            self.focal_target = context.active_object.matrix_world.translation.copy()
        else:
            ## either use current focal point (could be used with view too ! so maybe more logic)
            ## or 3d cursor
            self.focal_target = context.scene.cursor.location.copy()

        self.cam_forward_vec = Vector((0,0,-1))
        self.cam_forward_vec.rotate(self.cam.matrix_world)

        ## If point is behind camera, use camera focus distance in front of camera.
        if (self.cam.matrix_world.inverted() @ self.focal_target).z > 0:
            distance = self.cam.data.dof.focus_distance
            if not distance:
                distance = 10
            self.focal_target = distance * self.cam_forward_vec + self.init_pos

        ## Stay centered on camera
        self.focal_target = intersect_line_plane(self.init_pos, self.init_pos + self.cam_forward_vec * 100000, self.focal_target, self.cam_forward_vec)

        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)

        args = (self, context) 
        if self.is_focal_mode:
            self.text_body = "Focal Length" if self.cam.data.type == 'PERSP' else "Orthographic Scale"
            # ui_scale = context.preferences.system.ui_scale
            # self.text_position = (context.area.width / 2 - (120 * ui_scale), event.mouse_region_y + (80 * ui_scale)) # mid area x
            self.text_position = (context.area.width / 2 - 120, event.mouse_region_y + 80) # mid area x
            # self.text_position = (event.mouse_region_x - 100, event.mouse_region_y + 80) # place x relative to mouse
            self.text_size = 18.0
            self._text_handle = bpy.types.SpaceView3D.draw_handler_add(draw.text_draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        
        # Setup camera top view map if enabled
        dist = 6.0 if self.is_focal_mode else 15.0
        setup_top_view_map(self, context, dist)

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
                self.text_body = f"Orthographic Scale: {self.init_ortho_scale:.{decimals}f} -> {self.cam.data.ortho_scale:.{decimals}f}"
                context.area.header_text_set(f'Orthographic Scale Offset: {move_val:.2f}')
            else:
                # For perspective camera, adjust focal length
                # lens = self.init_lens * (1 + move_val)
                lens = self.init_lens + move_val
                self.cam.data.lens = lens

                if event.type == 'D' and event.value == 'PRESS':
                    # Toggle dolly mode
                    self.dolly_mode = not self.dolly_mode
                    if not self.dolly_mode:
                        # Reset position
                        self.cam.matrix_world.translation = self.init_pos

                if self.dolly_mode:
                    # Calculate and update camera position
                    self.cam.matrix_world.translation = fn.calculate_dolly_zoom_position(
                        self.init_pos,
                        self.focal_target,
                        self.init_lens,
                        lens
                    )

                dolly_text = 'On' if self.dolly_mode else 'Off'

                body = f"Focal Length: {self.init_lens:.{decimals}f} -> {lens:.{decimals}f}"
                self.text_body = body
                offset_text = f"(Offset: +{move_val:.2f})" if move_val >= 0 else f"(Offset: {move_val:.2f})"
                context.area.header_text_set(f'{body} {offset_text} | Dolly Toggle (D): {dolly_text}')

        else:
            # Position-based behavior
            new_position = self.init_pos + self.cam_forward_vec * move_val
            if event.alt:
                new_position.z = self.init_pos.z
            self.cam.matrix_world.translation = new_position
            context.area.header_text_set(f'Camera Offset: {move_val:.2f}')

        if event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")
            draw.stop_callback(self, context)

            if self.is_focal_mode:
                # Keyframe camera parameters
                data_path = 'lens' if self.cam.data.type == 'PERSP' else 'ortho_scale'
                # TODO: pass active keying set ? # options={'INSERTKEY_AVAILABLE'}
                fn.key_data_path(self.cam.data, data_path=data_path, use_autokey=True)
            else:
                fn.key_object(self.cam, scale=False, use_autokey=True)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.is_focal_mode:
                # Restore initial camera parameters
                self.cam.data.lens = self.init_lens
                self.cam.data.ortho_scale = self.init_ortho_scale
            else:
                self.cam.matrix_world.translation = self.init_pos
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

        # if not self.shift_mode:
        dist = 5.0 if self.shift_mode else 15.0
        setup_top_view_map(self, context, dist)

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
 

classes=(
    STORYTOOLS_OT_camera_pan,
    STORYTOOLS_OT_camera_depth,
    STORYTOOLS_OT_camera_key_transform,
    STORYTOOLS_OT_lock_camera_to_view_toggle,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
