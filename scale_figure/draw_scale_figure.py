import bpy
import gpu

from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent
from mathutils import Vector, Matrix
from math import radians

from .. import fn
from .. import draw
from .figure_shapes import build_scale_figure_shape

## -- Size references (/guides)
## Show lines and circles on GP object origins to aprehend sizes in space

## show a default cross shape at origin

draw_handle = None

def get_canvas_scale_figure_matrix(context=None):
    context = context or bpy.context
    settings = context.scene.tool_settings
    orient = settings.gpencil_sculpt.lock_axis # 'VIEW', 'AXIS_Y', 'AXIS_X', 'AXIS_Z', 'CURSOR

    ## Rocation
    if context.scene.tool_settings.gpencil_stroke_placement_view3d == 'CURSOR':
        loc = context.scene.cursor.location
    else:
        loc = context.object.matrix_world.translation

    ## Rotation
    orient_matrix = Matrix()

    if orient == 'VIEW':
        orient_matrix = context.space_data.region_3d.view_matrix.inverted() @ Matrix.Rotation(radians(-90), 4, 'X')

    elif orient == 'AXIS_Y': # front (X-Z)
        orient_matrix = context.object.matrix_world.copy()

    elif orient == 'AXIS_X': # side (Y-Z)
        orient_matrix = context.object.matrix_world @ Matrix.Rotation(radians(90), 4, 'Z')
   
    elif orient == 'AXIS_Z': # top (X-Y)
        orient_matrix = context.object.matrix_world @ Matrix.Rotation(radians(-90), 4, 'X')

    elif orient == 'CURSOR':
        ## When used on surface, plain Z up is ok. But when placed aligned with view, Y up (rotated) may be better
        orient_matrix = context.scene.cursor.matrix.copy() # @ Matrix.Rotation(radians(-90), 4, 'X')
    
    # remove_translation component
    orient_matrix = orient_matrix.to_3x3() 
    orient_matrix.resize_4x4() # Convert back to 4x4 (keeping only rotation and scale)
    # Reset scale (we always want to show world scale)
    orient_matrix.normalize()

    ## Assemble final canvasmatrix (scale a 1)
    canvas_matrix = Matrix.Translation(loc) @ orient_matrix # @ Matrix.Scale(1,4)

    return canvas_matrix

def draw_scale_figure_callback():
    context = bpy.context
    
    settings = context.scene.storytools_settings
    if not settings.use_scale_figure:
        return

    if fn.is_minimap_viewport(context):
        return

    obj = context.object
    if not obj or obj.type != 'GREASEPENCIL':
        return
    
    # if context.region_data.view_perspective != 'CAMERA':
    #     return

    previous_depth_test_value = gpu.state.depth_test_get()
    if settings.use_scale_figure_xray:
        gpu.state.depth_test_set('NONE') # 'ALWAYS' also look same
    else:
        gpu.state.depth_test_set('LESS')

    gpu.state.blend_set('ALPHA')    
    shader_uniform = gpu.shader.from_builtin('UNIFORM_COLOR')
    ## As lines:
    gpu.state.line_width_set(1.0)

    ## TODO Bonus: get customization on object custom prop (if any)
    ## can also have an option to show or not
    
    # co, no = fn.get_gp_draw_plane(bpy.context)
    # canvas_matrix = fn.get_gp_draw_plane_matrix(context) # Truly follow canvas
    canvas_matrix = get_canvas_scale_figure_matrix(bpy.context) # Custom function

    ## Local shape
    ## TODO: separate local figure builing in a function for external usage
    lines = build_scale_figure_shape()

    ## Apply canvas matrix
    lines = [canvas_matrix @ v for v in lines]
    
    ## Draw
    line_batch = batch_for_shader(shader_uniform, 'LINES', {"pos": lines})
    shader_uniform.bind()
    shader_uniform.uniform_float("color", (*settings.scale_figure_color, settings.scale_figure_opacity))
    # shader_uniform.uniform_float("color", (1.0, 0, 0, 0.0))
    line_batch.draw(shader_uniform)

    ## Restore values
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set(previous_depth_test_value)


def register():
    if bpy.app.background:
        return

    global draw_handle
    draw_handle = bpy.types.SpaceView3D.draw_handler_add(
        # draw_map_callback_2d, (), "WINDOW", "POST_PIXEL")
        draw_scale_figure_callback, (), "WINDOW", "POST_VIEW")

def unregister():
    if bpy.app.background:
        return

    global draw_handle
    if draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handle, 'WINDOW')

if __name__ == "__main__":
    register()
