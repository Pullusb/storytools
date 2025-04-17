import bpy
import blf
import gpu

from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_texture_2d
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

    Optional:
    - pip_offscreen: Will be created if not present
    - current_area: Restricts drawing to the operator's original area
    """
    # Restrict to current viewport if specified
    if hasattr(self, 'current_area') and context.area != self.current_area:
        return

    # Get properties with fallback values
    size = getattr(self, 'pip_size', 0.25)
    quality = getattr(self, 'pip_quality', 75)
    position = getattr(self, 'pip_position', (40, 40)) # bottom-left corner
    border_color = getattr(self, 'pip_border_color', (0.0, 0.5, 1.0, 0.7)) # Blue outline
    border_thickness = getattr(self, 'pip_border_thickness', 1.0)

    # Get or create offscreen
    if not hasattr(self, 'pip_offscreen'):
        width = int(context.region.width * size * quality / 100)
        height = int(context.region.height * size * quality / 100)
        self.pip_offscreen = gpu.types.GPUOffScreen(width, height)

    # Get object's location - use active object or operator's object if available
    if hasattr(self, 'ob'):
        obj = self.ob
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
    
    # Get the current view's vectors
    view_mat = context.space_data.region_3d.view_matrix

    view_forward = -Vector((view_mat.col[2][0], view_mat.col[2][1], view_mat.col[2][2]))
    # view_forward = Vector((0, 0, -1))
    # view_forward.rotate(view_mat)

    view_up = Vector((view_mat.col[1][0], view_mat.col[1][1], view_mat.col[1][2]))
    # view_up = Vector((0, 1, 0))
    # view_up.rotate(view_mat)
    
    # Create pip view position (above the object)
    distance = 20.0  # Distance above object
    pip_pos = obj_loc + Vector((0, 0, distance)) # Zenith view
    # pip_pos = obj_loc + (view_up * distance) # Perpendicular to view

    # The view direction is down (-Z)
    forward = Vector((0, 0, -1))
    
    # Use the current view's forward as our up direction
    up = view_forward
    
    # If forward and up are nearly parallel, use a different up vector
    if abs(forward.dot(up)) > 0.99:
        print('forward and up nearly parallel, using view_up')
        up = view_up
    
    # Calculate the right direction
    right = forward.cross(up).normalized()
    
    # Recalculate up for perfect orthogonality
    up = right.cross(forward).normalized()
    
    ## Create the rotation matrix
    ## World global Z view
    rot_mat = Matrix.Identity(4)
    rot_mat.col[0][:3] = -right
    rot_mat.col[1][:3] = -up
    rot_mat.col[2][:3] = (-forward[0], -forward[1], -forward[2])  # Negated for camera direction
    pip_view_matrix = Matrix.Translation(pip_pos) @ rot_mat

    # _, rot_mat, _ = view_mat.decompose()
    # rot_90 = Matrix.Rotation(1.570796, 4, 'X') # -pi/2 = -1.570796 (90 degrees)
    # rot_mat.rotate(rot_90)
    # pip_view_matrix = Matrix.LocRotScale(pip_pos, rot_mat, Vector((1, 1, 1)))
    
    # Create view matrix
    pip_view_matrix.invert()  # Convert to view matrix
    
    # Get a projection matrix that ensures the object is in view
    # Start with the current projection
    proj_matrix = context.space_data.region_3d.window_matrix.copy()
    
    # Draw the 3D view to offscreen
    self.pip_offscreen.draw_view3d(
        context.scene,
        context.view_layer,
        context.space_data,
        context.region,
        pip_view_matrix,
        proj_matrix,
        do_color_management=True)
    
    # Draw the offscreen buffer to screen
    gpu.state.blend_set('ALPHA')
    draw_texture_2d(self.pip_offscreen.texture_color, (x, y), width, height)
    
    # Draw border
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