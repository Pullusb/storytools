import bpy
import blf
import gpu

from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_texture_2d
from bpy_extras import view3d_utils
from . import fn

## Draw utils

def lock_axis_draw_callback(self, context):
    # Draw lock lines
    if not self.final_lock:
        return
    if self.final_lock == 'X':
        coords = self.lock_x_coords
        color = (1, 0, 0, 0.15)
    elif self.final_lock == 'Y':
        coords = self.lock_y_coords
        color = (0, 1, 0, 0.15)
    else:
        return
    
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2)

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    batch = batch_for_shader(shader, 'LINES', {"pos": coords})
    shader.uniform_float("color", color)
    batch.draw(shader)

    gpu.state.line_width_set(1)
    gpu.state.blend_set('NONE')

def stop_callback(self, context):
    # Remove draw handler and text set
    context.area.header_text_set(None) # Reset header
    context.window.cursor_set("DEFAULT")

    possible_handles = [
        '_handle',
        '_pos_handle',
        '_line_handle',
        '_grid_handle',
        '_text_handle',
        '_pip_handle',
        # '_guide_handle',
        ]
    for handle_name in possible_handles:
        if handle := getattr(self, handle_name, None):
            bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')

    ## Free offscreen
    if hasattr(self, 'pip_offscreen'):
        self.pip_offscreen.free()

    context.area.tag_redraw()

def draw_callback_wall(self, context):
    '''Draw a color wall to filter what's behind position
    
    
    self.coords : coordinate of the wall. world behind appears tinted
    self.front_coords : coordinate of front wall. world in front appears tinted in another color
    if self.current_area exists, only draw in current area
    '''
    ## Restrict to current viewport
    if hasattr(self, 'current_area') and context.area != self.current_area:
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

def origin_position_callback(self, context):
    """Draw origin position and init position as ghost"""

    coords = [] # Origin coords
    ghost_coords = [] # Starting origin coords

    cross_coord = [
        Vector((-0.1, 0, 0)), Vector((0.1, 0, 0)),
        Vector((0, -0.1, 0)), Vector((0, 0.1, 0)),
        Vector((0, 0, -0.1)), Vector((0, 0, 0.1)),
    ]

    if hasattr(self, 'objects'):
        ## Multi object
        for ob in self.objects:
            coords += [ob.matrix_world @ v for v in cross_coord]
        
        # if hasattr(self, 'init_mats')
    elif hasattr(self, 'object'):
        ## Single object
        coords = [self.object.matrix_world @ v for v in cross_coord]
    elif hasattr(self, 'ob'):
        ## Single object
        coords = [self.ob.matrix_world @ v for v in cross_coord]
    else:
        return

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2)

    if bpy.app.version <= (3,6,0):
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    else:
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    

    origin_batch = batch_for_shader(shader, 'LINES', {"pos": coords})

    if hasattr(self, 'init_mats'):
        ## Multi object
        for mat in self.init_mats:
            ghost_coords += [mat @ v for v in cross_coord]
    elif hasattr(self, 'init_mat'):
        ## Single object
        ghost_coords = [self.init_mat @ v for v in cross_coord]

    if ghost_coords:
        ## Draw ghost
        ghost_batch = batch_for_shader(shader, 'LINES', {"pos": ghost_coords})
        ghost_color = (0.5, 0.5, 0.5, 0.3)
        shader.uniform_float("color", ghost_color)
        ghost_batch.draw(shader)
    
    
    ## Draw current origin AFTER ghost to display on top

    ## Dimmed version always visible (no depth test)
    shader.uniform_float("color", (1.0, 0.6, 0.3, 0.2))
    origin_batch.draw(shader)

    ## Redraw with more vivid color WITH depth test
    previous_depth_test_value = gpu.state.depth_test_get()
    gpu.state.depth_test_set('LESS')
    shader.uniform_float("color", (1.0, 0.6, 0.3, 0.8)) # orange bright
    origin_batch.draw(shader)
    
    gpu.state.depth_test_set(previous_depth_test_value)

    gpu.state.line_width_set(1)
    gpu.state.blend_set('NONE')

## guide on transform - [Not used yet]
def guide_callback(self, context):
    """Draw pseudo shadow to better see object, WIP TEST"""

    # coords = []
    ## only on active object
    bbox = context.object.bound_box

    ## TODO if bbox has 0 0 0, fall back on a fake 0.2, 0.2, 0.2 box

    ## TODO In the end, better to draw thin lines for positionning

    ## Get view orign and create a Z box according to event

    mat = context.object.matrix_world

    ## Bottom square
    square = [
              mat @ Vector(bbox[0]),
              mat @ Vector(bbox[4]),
              mat @ Vector(bbox[7]),
              mat @ Vector(bbox[3]),
              ]

    if bpy.app.version <= (3,6,0):
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    else:
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    coords = [
        square[0],  square[1], square[0] + Vector((0,0,-12)),
        square[1],  square[0] + Vector((0,0,-12)), square[1] + Vector((0,0,-12))
    ]

    coords += [
        square[2],  square[3], square[2] + Vector((0,0,-12)),
        square[3],  square[2] + Vector((0,0,-12)), square[3] + Vector((0,0,-12))
    ]

    previous_depth_test_value = gpu.state.depth_test_get()

    gpu.state.depth_test_set('LESS') # visible "in front" of other
    # gpu.state.depth_test_set('EQUAL') # ...
    # gpu.state.depth_test_set('GREATER') # visible in "behind" other
    gpu.state.face_culling_set('NONE') # NONE, FRONT or BACK.
    gpu.state.blend_set('ALPHA')
    
    shader.uniform_float("color", (0.0, 0.7, 0.4, 0.3))
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords})
    batch.draw(shader)

    gpu.state.depth_test_set(previous_depth_test_value)

    gpu.state.blend_set('NONE')


## shift callback
def line_draw_callback(self, context):
    """generic 3D line draw callback for line drawing
    need following variable in self:
    line_coords (flat list of vector3 pairs)
    line_color (vector4)
    line_width (float)
    line_blend (default NONE, str) choice in: 
        NONE No blending.
        ALPHA The original color channels are interpolated according to the alpha value.
        ALPHA_PREMULT The original color channels are interpolated according to the alpha value with the new colors pre-multiplied by this value.
        ADDITIVE The original color channels are added by the corresponding ones.
        ADDITIVE_PREMULT The original color channels are added by the corresponding ones that are pre-multiplied by the alpha value.
        MULTIPLY The original color channels are multiplied by the corresponding ones.
        SUBTRACT The original color channels are subtracted by the corresponding ones.
        INVERT The original color channels are replaced by its complementary color.
    line_ghost (default False) if True, add test for main lines and draw a dimmed line when occluded (override line_blend)
    """
    line_color = getattr(self, 'line_color', (0.0, 0.5, 1.0, 1.0)) # blue
    line_width = getattr(self, 'line_width', 1.0)
    line_ghost = getattr(self, 'line_ghost', False)
    line_blend = getattr(self, 'line_blend', 'NONE')
    
    if line_ghost:
        # Force blend to alpha to show ghost
        line_blend = 'ALPHA'

    gpu.state.blend_set(line_blend)
    gpu.state.line_width_set(line_width)
    previous_depth_test_value = gpu.state.depth_test_get()
    
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": self.line_coords})

    if line_ghost:
        ## Trace dimmed ghost lines (opacity at 25% of original alpha)
        shader.uniform_float("color", (line_color[0], line_color[1], line_color[2], line_color[3] * 0.25))
        batch.draw(shader)
        
        ## set depth test so next lines are occluded by geometry
        gpu.state.depth_test_set('LESS')

    ## Trace full opacity lines
    shader.uniform_float("color", line_color)
    batch.draw(shader)

    ## Restore default/previous
    gpu.state.line_width_set(1)
    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set(previous_depth_test_value)

def text_draw_callback_px(self, context):
    """Generic Draw text callback
    Need those variable in text, else fallback to generic values
    text_body (str)
    text_position (vector2)
    text_size (float)
    text_color (vector3)
    """

    if hasattr(self, 'current_area') and context.area != self.current_area:
        return

    font_id = 0
    text_body = getattr(self, 'text_body', 'Running')
    text_size = getattr(self, 'text_size', 20.0)
    text_color = getattr(self, 'text_color', (0.0, 0.5, 1.0)) # red -> (0.8, 0.1, 0.2)
    text_position = getattr(self, 'text_position', (120, 120))

    blf.color(0, *text_color, 1) # fix alpha to 1
    blf.size(font_id, text_size)
    ## optional : Center X position accordinga to text dimension (may offset a lot on x when text is updating)
    # dimensions = blf.dimensions(font_id, text_body)
    # text_position = (text_position[0] - (dimensions[0] / 2), text_position[1])
    
    ## Shadow (no error but do not see anything)
    # blf.shadow(font_id, 5, 0.0, 0.0, 0.0, 1.0) # fontid, blur level (0, 3, 5) or outline (6)), r, g, b, a
    # blf.shadow_offset(fontid, 4, -4) # fontid, x, y
    
    if '\n' in text_body:
        ## a good ratio between lines is 50% of the height
        text_lines = text_body.split('\n')
        ## get the mean of the height
        # height_list = [blf.dimensions(font_id, line)[1] for line in text_lines]
        height_list = [h for line in text_lines if (h := blf.dimensions(font_id, line)[1])] # without 0 height lines
        height = sum([i for i in height_list]) / len(height_list)
        ## Snap on 0.5 value

        ## display line by line
        for i, line in enumerate(text_lines):
            ## Other method : Offset each line by the height of the previous
            # width, height = blf.dimensions(font_id, line)
            offset_down = i * (height + height / 2) # line + spacing
            blf.position(font_id, text_position[0], text_position[1] - offset_down, 0)
            blf.draw(font_id, line)

    else:
        ## Standard display
        blf.position(font_id, *text_position, 0) # Leave out z at 0
        blf.draw(font_id, text_body)


def gp_plane_callback(self, context):
    '''Draw a grid plane in 3D view'''
    if not self.drag_mode:
        return
    if not self.coords:
        return
    ## Restrict to current viewport
    if hasattr(self, 'current_area') and context.area != self.current_area:
        return

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(1) # should be at one already

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    
    # coords = [
    #     self.coords[0], self.coords[1], self.coords[2],
    #     self.coords[3], self.coords[0], self.coords[2]
    # ]

    shader.uniform_float("color", (0.0, 0.7, 0.4, 0.2)) # green
    # shader.uniform_float("color", (0.8, 0.5, 0.4, 0.2))

    batch = batch_for_shader(shader, 'LINES', {"pos": self.coords})
    batch.draw(shader)

    gpu.state.line_width_set(1)
    gpu.state.blend_set('NONE')

## Not used yet
def ob_lock_location_cam_draw_panel(self, context):
    '''Display object location settings'''
    layout = self.layout
    layout.use_property_split = True
    col = layout.column()
    row = col.row(align=True)
    row.prop(self.ob, "location")
    row.use_property_decorate = False
    row.prop(self.ob, "lock_location", text="", emboss=False, icon='DECORATE_UNLOCKED')



def zenith_view_callback(self, context):
    """Draw a zenith view (perpendicular to current view) of the active object.
    Displays a picture-in-picture view in the corner of the viewport.
    
    Required properties in self:
    - pip_size (float): Size of the zenith view relative to viewport 
    - pip_quality (int): Quality percentage of the rendered view
    - pip_position (tuple): (x, y) offset position in the viewport
    - pip_border_color (tuple): (r, g, b, a) color of the border
    - pip_border_thickness (float): Thickness of the border
    - pip_distance (float): Distance from the object
    - pip_from_camera (bool): If True, use the camera's view instead of the current view
    - pip_object (bool): Object to track (if not set, use the active object or the operator's "self.object")

    Optional:
    - pip_offscreen: Will be created if not present
    - current_area: Restricts drawing to the operator's original area

    to free offscreen use:
    if hasattr(self, 'pip_offscreen'):
        self.pip_offscreen.free()
    """
    # Restrict to current viewport if specified
    if hasattr(self, 'current_area') and context.area != self.current_area:
        return

    # Get properties with fallback values
    size = getattr(self, 'pip_size', 0.25) # size as percentage of viewport
    quality = getattr(self, 'pip_quality', 75) # quality percentage
    position = getattr(self, 'pip_position', (40, 40)) # bottom-left corner
    border_color = getattr(self, 'pip_border_color', (0.0, 0.5, 1.0, 0.7)) # Blue outline
    border_thickness = getattr(self, 'pip_border_thickness', 1.0)
    distance = getattr(self, 'pip_distance', 15.0)
    from_camera = getattr(self, 'pip_from_camera', False)

    # Get or create offscreen
    if not hasattr(self, 'pip_offscreen'):
        width = int(context.region.width * size * quality / 100)
        height = int(context.region.height * size * quality / 100)
        self.pip_offscreen = gpu.types.GPUOffScreen(width, height)

    # Get object's location - use active object or operator's object if available
    if hasattr(self, 'pip_object'):
        obj = self.pip_object
    elif hasattr(self, 'object'):
        obj = self.object
    else:
        obj = context.object

    if not obj:
        return

    obj_loc = obj.matrix_world.translation
    
    # Calculate dimensions for the viewport
    region_width = context.region.width
    region_height = context.region.height
    width = int(region_width * size)
    height = int(region_height * size)
    
    # Get position from the offset or use default
    x_pos, y_pos = position
    
    # Calculate position based on region
    x = x_pos if x_pos >= 0 else region_width + x_pos - width
    y = y_pos if y_pos >= 0 else region_height + y_pos - height
    
    # Get vector from current view
    if from_camera and context.scene.camera:
        # use camera
        view_mat = context.scene.camera.matrix_world
        # cam_pos = context.scene.camera.matrix_world.translation
    else:
        # use current viewpoint
        view_mat = context.space_data.region_3d.view_matrix
        # cam_pos = context.space_data.region_3d.view_matrix.inverted().translation
    
    view_right = Vector((view_mat.col[0][0], view_mat.col[0][1], view_mat.col[0][2]))
    view_forward = Vector((-view_mat.col[2][0], -view_mat.col[2][1], -view_mat.col[2][2]))
    view_up = Vector((view_mat.col[1][0], view_mat.col[1][1], view_mat.col[1][2]))

    # Create a viewpoint that looks from the direction opposite to the camera
    pip_pos = obj_loc + Vector((0, 0, distance)) # Final position above object

    # view direction (always -Z)
    pip_forward = Vector((0, 0, -1))

    ## The "up" direction of the zenith view points opposite to the main camera
    ## This ensures the bottom of the image points toward the camera

    ## Calculate vector from object to camera (method solely based on object position)
    # obj_to_cam = cam_pos - obj_loc
    # obj_to_cam.z = 0  # Remove z component
    # obj_to_cam.normalize()
    # pip_up = -obj_to_cam  # Use the inverted object-to-camera vector as the "up" direction

    ## Following method always align with camera. Avoid the 180 turn of method above
    horizontal_view = view_forward.copy()
    horizontal_view.z = 0  # Supprimer la composante verticale
    if horizontal_view.length < 0.01:  # Si la vue est presque verticale
        # Utiliser view_up comme référence alternative
        horizontal_view = view_up.copy()
        horizontal_view.z = 0
        if horizontal_view.length < 0.01:
            # Dernier recours: utiliser l'axe Y mondial
            horizontal_view = Vector((0, -1, 0))

    # Normaliser le vecteur horizontal
    if horizontal_view.length > 0:
        horizontal_view.normalize()
    pip_up = horizontal_view

    # If pip_up and pip_forward are almost parallel, use an alternative reference
    if abs(pip_up.dot(pip_forward)) > 0.98:
        # Use view_right as an alternative reference
        pip_up = view_right

    # Calculate the "right" vector (perpendicular to the other two)
    pip_right = pip_forward.cross(pip_up).normalized()

    # Recalculate the "up" vector to ensure perfect orthogonality
    pip_up = pip_right.cross(pip_forward).normalized()

    # Create the rotation matrix
    rot_mat = Matrix.Identity(4)
    rot_mat.col[0][:3] = pip_right
    rot_mat.col[1][:3] = pip_up
    rot_mat.col[2][:3] = (-pip_forward[0], -pip_forward[1], -pip_forward[2])

    # Create view matrix
    pip_view_matrix = Matrix.Translation(pip_pos) @ rot_mat
    pip_view_matrix.invert()

    ## Reuse current view projection matrix
    # proj_matrix = context.space_data.region_3d.window_matrix.copy()
    ## custom matrix
    ## ortho
    # proj_matrix = Matrix.OrthoProjection(pip_forward, 4) ## 


    ## Generic Perspective proj matrix
    # Calculate aspect ratio based on our offscreen dimensions
    width = int(context.region.width * size)
    height = int(context.region.height * size)
    aspect_ratio = width / height
    
    
    # Set near and far clipping planes
    near_clip = 0.1
    far_clip = distance * 6
    
    ## Create perspective projection matrix manually
    # fov = radians(50.0) # field of view in radians
    # f = 1.0 / tan(fov / 2.0)
    # Hardcoded f value
    f = 2.14450692
    
    # Build the projection matrix
    proj_matrix = Matrix.Identity(4)
    proj_matrix[0][0] = f / aspect_ratio
    proj_matrix[1][1] = f
    proj_matrix[2][2] = (far_clip + near_clip) / (near_clip - far_clip)
    proj_matrix[2][3] = (2 * far_clip * near_clip) / (near_clip - far_clip)
    proj_matrix[3][2] = -1.0
    proj_matrix[3][3] = 0.0

    # Draw the 3D view to offscreen
    self.pip_offscreen.draw_view3d(
        context.scene,
        context.view_layer,
        context.space_data,
        context.region,
        pip_view_matrix,
        proj_matrix,
        do_color_management=False)

    gpu.state.blend_set('ALPHA')

    ## / Extra Visual hints in the offscreen buffer
    # Replace the section under "## / Extra Visual hints in the offscreen buffer" with this:

    with self.pip_offscreen.bind():
        width = self.pip_offscreen.width
        height = self.pip_offscreen.height
        
        # First draw the 2D overlay (yellow rectangle)
        shader_2d = gpu.shader.from_builtin('UNIFORM_COLOR')
        
        # Create a yellow rectangle in the bottom-left corner
        rect_width = width * 0.2
        rect_height = height * 0.2
        
        vertices_2d = [
            (10, 10),
            (10 + rect_width, 10),
            (10 + rect_width, 10 + rect_height),
            (10, 10 + rect_height),
        ]
        
        indices = [(0, 1, 2), (0, 2, 3)]
        
        batch_2d = batch_for_shader(shader_2d, 'TRIS', {"pos": vertices_2d}, indices=indices)
        shader_2d.bind()
        shader_2d.uniform_float("color", (1.0, 1.0, 0.0, 0.5))  # Yellow with 50% opacity
        batch_2d.draw(shader_2d)
        
        # Draw the axes differently - project the world points to screen space first
        try:
            # Define axes in world space
            world_points = [
                (0, 0, 0),        # Origin
                (100, 0, 0),      # X axis end
                (0, 100, 0),      # Y axis end
                (0, 0, 100)       # Z axis end
            ]
            
            # Convert to 2D screen coordinates
            screen_points = []
            for point in world_points:
                # Create a 4D vector (x, y, z, 1)
                p = Vector((point[0], point[1], point[2], 1.0))
                
                # Apply view matrix
                p_view = pip_view_matrix @ p
                
                # Apply projection matrix
                p_clip = proj_matrix @ p_view
                
                # Perspective division
                if abs(p_clip.w) > 0.0001:
                    p_ndc = Vector((p_clip.x / p_clip.w, p_clip.y / p_clip.w, p_clip.z / p_clip.w))
                else:
                    p_ndc = Vector((0, 0, 0))  # Fallback for invalid points
                
                # Convert NDC to screen coordinates
                p_screen = Vector(((p_ndc.x + 1.0) * 0.5 * width, 
                                (p_ndc.y + 1.0) * 0.5 * height))
                
                screen_points.append(p_screen)
            
            # Now draw 2D lines using the projected points
            # Draw X axis (red)
            batch = batch_for_shader(shader_2d, 'LINES', {"pos": [
                (screen_points[0].x, screen_points[0].y), 
                (screen_points[1].x, screen_points[1].y)
            ]})
            shader_2d.bind()
            shader_2d.uniform_float("color", (1.0, 0.0, 0.0, 1.0))  # Red
            gpu.state.line_width_set(3)
            batch.draw(shader_2d)
            
            # Draw Y axis (green)
            batch = batch_for_shader(shader_2d, 'LINES', {"pos": [
                (screen_points[0].x, screen_points[0].y), 
                (screen_points[2].x, screen_points[2].y)
            ]})
            shader_2d.bind()
            shader_2d.uniform_float("color", (0.0, 1.0, 0.0, 1.0))  # Green
            batch.draw(shader_2d)
            
            # Draw Z axis (blue)
            batch = batch_for_shader(shader_2d, 'LINES', {"pos": [
                (screen_points[0].x, screen_points[0].y), 
                (screen_points[3].x, screen_points[3].y)
            ]})
            shader_2d.bind()
            shader_2d.uniform_float("color", (0.0, 0.0, 1.0, 1.0))  # Blue
            batch.draw(shader_2d)
            
            # Draw a small crosshair at the origin
            origin_x = screen_points[0].x
            origin_y = screen_points[0].y
            size = 10
            
            crosshair_points = [
                [(origin_x - size, origin_y), (origin_x + size, origin_y)],
                [(origin_x, origin_y - size), (origin_x, origin_y + size)]
            ]
            
            for points in crosshair_points:
                batch = batch_for_shader(shader_2d, 'LINES', {"pos": points})
                shader_2d.bind()
                shader_2d.uniform_float("color", (1.0, 1.0, 1.0, 1.0))  # White
                batch.draw(shader_2d)
                
        except Exception as e:
            # If an error occurs, print to console for debugging
            print(f"Error in drawing: {e}")
            
            # Draw a red rectangle to indicate an error occurred
            error_rect = [
                (width - 50, height - 50),
                (width - 10, height - 50),
                (width - 10, height - 10),
                (width - 50, height - 10),
            ]
            
            indices = [(0, 1, 2), (0, 2, 3)]
            
            batch = batch_for_shader(shader_2d, 'TRIS', {"pos": error_rect}, indices=indices)
            shader_2d.bind()
            shader_2d.uniform_float("color", (1.0, 0.0, 0.0, 1.0))  # Red
            batch.draw(shader_2d)
    ## end of extra Visual hints in the offscreen buffer /

    # Draw the offscreen buffer to screen
    draw_texture_2d(self.pip_offscreen.texture_color, (x, y), width, height)    

    ## Draw border
    vertices = [
        (x, y),
        (x + width, y),
        (x + width, y + height),
        (x, y + height),
        (x, y),
    ]
    
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.line_width_set(border_thickness)
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": vertices})
    shader.bind()
    shader.uniform_float("color", border_color)
    batch.draw(shader)

    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')