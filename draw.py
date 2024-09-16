import bpy
import blf
import gpu

from mathutils import Vector
from gpu_extras.batch import batch_for_shader
# from .preferences import get_addon_prefs

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

    if bpy.app.version <= (3,6,0):
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    else:
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
    if hasattr(self, '_handle'):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
    if hasattr(self, '_pos_handle'):
        bpy.types.SpaceView3D.draw_handler_remove(self._pos_handle, 'WINDOW')
    if hasattr(self, '_guide_handle'):
        bpy.types.SpaceView3D.draw_handler_remove(self._guide_handle, 'WINDOW')
    context.area.tag_redraw()

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


## Not used yet
def text_draw_callback_px(self, context):
    font_id = 0
    color = [0.8, 0.1, 0.2]
    blf.color(0, *color, 1)
    blf.position(font_id, 15, 100, 0)
    blf.size(font_id, 25, 72)
    # blf.draw(font_id, self.message)
    blf.draw(font_id, 'Test draw')


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