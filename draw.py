import bpy
import blf
import gpu

from mathutils import Vector
from gpu_extras.batch import batch_for_shader
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
    if handle := getattr(self, '_handle', None):
        bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
    if handle := getattr(self, '_pos_handle', None):
        bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
    # if handle := getattr(self, '_guide_handle', None):
    #     bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
    if handle := getattr(self, '_line_handle', None):
        bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
    if handle := getattr(self, '_grid_handle', None):
        bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
    if handle := getattr(self, '_text_handle', None):
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

    
    """

    line_color = getattr(self, 'line_color', (0.0, 0.5, 1.0, 1.0)) # blue
    line_width = getattr(self, 'line_width', 1.0)
    line_blend = getattr(self, 'line_blend', 'NONE')

    gpu.state.blend_set(line_blend)
    gpu.state.line_width_set(line_width)

    ## old compatibility (kept for reference)
    # if bpy.app.version <= (3,6,0):
    #     shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    # else:
    #     shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.uniform_float("color", line_color)
    batch = batch_for_shader(shader, 'LINES', {"pos": self.line_coords})
    batch.draw(shader)

    ## restore default
    gpu.state.line_width_set(1)
    gpu.state.blend_set('NONE')


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
        ## display line by line
        for i, line in enumerate(text_body.split('\n')):
            ## Offset each line by the height of the previous
            width, height = blf.dimensions(font_id, line)
            ## a good ratio is 50% of the height
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
