import bpy
import gpu
import blf
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils.geometry import intersect_line_plane
from mathutils import Vector
from bpy.app.handlers import persistent
from .. import fn

def extrapolate_points_by_length(a, b, length):
    '''
    Return a third point C from by continuing in AB direction
    Length define BC distance. both vector2 and vector3
    '''
    # return b + ((b - a).normalized() * length)# one shot
    ab = b - a
    if not ab:
        return None
    return b + (ab.normalized() * length)

def view3d_camera_border_2d(context, cam):
    # based on https://blender.stackexchange.com/questions/6377/coordinates-of-corners-of-camera-view-border
    # cam = context.scene.camera
    frame = cam.data.view_frame(scene=context.scene)
    # to world-space
    frame = [cam.matrix_world @ v for v in frame]
    # to pixelspace
    region, rv3d = context.region, context.space_data.region_3d
    frame_px = [location_3d_to_region_2d(region, rv3d, v) for v in frame]
    return frame_px

def vertices_to_line_loop(v_list, closed=True) -> list:
    '''Take a sequence of vertices
    return a position lists of segments to create a line loop passing in all points
    the result is usable with gpu_shader 'LINES'
    ex: vlist = [a,b,c] -> closed=True return [a,b,b,c,c,a], closed=False return [a,b,b,c]
    '''
    loop = []
    for i in range(len(v_list) - 1):
        loop += [v_list[i], v_list[i + 1]]
    if closed:
        # Add segment between last and first to close loop
        loop += [v_list[-1], v_list[0]]
    return loop

def draw_map_callback():
    context = bpy.context
    if not fn.is_minimap_viewport(context):
        return

    # if context.region_data.view_perspective != 'CAMERA':
    #     return
   
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(3.0)

    shader_lines = gpu.shader.from_builtin('UNIFORM_COLOR')

    # line_vecs = [Vector((-0.5,0,0)), Vector((0.5,0,0))]
    line_vecs = [Vector((-1,0,0)), Vector((1,0,0))]

    ## TODO add orientation matrix (according to draw prefs)
    ## Reorient to top view ?

    ## Should be the same but give wrong order
    lines = [o.matrix_world @ v for o in bpy.context.scene.objects if o.type == 'GPENCIL' and o.visible_get() for v in line_vecs]
    ## Equivalent to:
    # lines = []
    # for o in [o for o in bpy.context.scene.objects if o.type == 'GPENCIL' and o.visible_get()]:
    #     lines += [o.matrix_world @ v for v in line_vecs]
    
    gp_lines = batch_for_shader(shader_lines, 'LINES', {"pos": lines})
    shader_lines.bind()
    shader_lines.uniform_float("color", (1.0, 1.0, 0.0, 0.8))
    gp_lines.draw(shader_lines)

    cam = bpy.context.scene.camera
    if cam:
        ## ? Instead highlight camera basic Gizmo ?

        frame = [cam.matrix_world @ v for v in cam.data.view_frame(scene=context.scene)]
        mat = cam.matrix_world
        loc = mat.to_translation()
        gpu.state.line_width_set(1.0)


        right = (frame[0] + frame[1]) / 2
        left = (frame[2] + frame[3]) / 2
        cam_tri = [loc, left, right]

        near_clip_point = mat @ Vector((0,0,-cam.data.clip_start))
        far_clip_point = mat @ Vector((0,0,-cam.data.clip_end))
        orient = Vector((0,0,1))
        orient.rotate(mat)

        if cam.data.type == 'ORTHO':
            cam_view = [
                # Left
                intersect_line_plane(left, left + orient, near_clip_point, orient),
                intersect_line_plane(left, left + orient, far_clip_point, orient),
                # Right
                intersect_line_plane(right, right + orient, near_clip_point, orient),
                intersect_line_plane(right, right + orient, far_clip_point, orient),
            ]
        else:
            ###  Cone Coors

            ## Basic view cone
            # cam_view = [
            #     loc, extrapolate_points_by_length(loc, right, 2000),
            #     loc, extrapolate_points_by_length(loc, left, 2000)
            # ]
            
            # View cone with clipping display
            cam_view = [
                # Left
                intersect_line_plane(loc, left, near_clip_point, orient),
                intersect_line_plane(loc, left, far_clip_point, orient),
                # Right
                intersect_line_plane(loc, right, near_clip_point, orient),
                intersect_line_plane(loc, right, far_clip_point, orient),
            ]
            # TODO : rotate or project on world z orientation, (at least get get largest cone from view if rotated)

        # Add perpenticular lines 
        cam_view.append(cam_view[0])
        cam_view.append(cam_view[2])
        cam_view.append(cam_view[1])
        cam_view.append(cam_view[3])

        cam_lines = batch_for_shader(shader_lines, 'LINES', {"pos": cam_view})
        shader_lines.bind()
        shader_lines.uniform_float("color", (0.5, 0.5, 1.0, 0.5))
        cam_lines.draw(shader_lines)


draw_handle = None

def register():
    if bpy.app.background:
        return

    global draw_handle
    draw_handle = bpy.types.SpaceView3D.draw_handler_add(
        # draw_map_callback, (), "WINDOW", "POST_PIXEL")
        draw_map_callback, (), "WINDOW", "POST_VIEW")

def unregister():
    if bpy.app.background:
        return

    global draw_handle
    if draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handle, 'WINDOW')

if __name__ == "__main__":
    register()
