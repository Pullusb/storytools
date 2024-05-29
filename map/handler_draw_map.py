import bpy
import gpu
import blf
import numpy as np
from math import pi, cos, sin
from gpu_extras.presets import draw_circle_2d
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


## 2D minimap drawing
def draw_map_callback_2d():
    context = bpy.context
    if not fn.is_minimap_viewport(context):
        return

    # if context.region_data.view_perspective != 'CAMERA':
    #     return
   
    gpu.state.blend_set('ALPHA')
    shader_uniform = gpu.shader.from_builtin('UNIFORM_COLOR')
    font_id = 0
    
    ### Trace GP objects 
    color = (0.8, 0.8, 0.0, 0.9)
    gps = [o for o in bpy.context.scene.objects if o.type == 'GPENCIL' and o.visible_get()]    
    
    # scale = context.region_data.view_distance # TODO: define scaling
    radius = 10.0
    offset_vector = Vector((0, radius + radius * 0.1))
    # for gp in gps:
    #     draw_circle_2d(fn.location_to_region(gp.matrix_world.translation), color, scale)
    # active = context.object
    # if active and active.type == 'GPENCIL':
    #     draw_circle_2d(fn.location_to_region(active.matrix_world.translation), (0.9, 0.9, 0.0, 0.9), scale)

    for ob in [o for o in bpy.context.scene.objects if o.type == 'GPENCIL' and o.visible_get()]:
        if context.object and context.object == ob:
            color = (0.9, 0.9, 0.6, 0.9)
        else:
            color = (0.7, 0.7, 0.0, 0.85)
        
        ## Draw location
        ## On origin
        # loc = fn.location_to_region(ob.matrix_world.to_translation()) # On origin ?

        ## On BBox median point (feel probably better for user perspective)
        loc = fn.location_to_region(Vector(np.mean([ob.matrix_world @ Vector(corner) for corner in ob.bound_box], axis=0)))
        circle_co = fn.circle_2d(*loc, radius, 20) # Scaled to dist radius
        batch = batch_for_shader(shader_uniform, 'TRI_FAN', {"pos":  circle_co})
        shader_uniform.bind()
        shader_uniform.uniform_float("color", color)
        batch.draw(shader_uniform)

        ## Draw text 
        blf.position(font_id, *(loc + offset_vector), 0)
        blf.size(font_id, 20)
        blf.color(font_id, *color)
        display_name = ob.name if len(ob.name) <= 24 else ob.name[:24-3] + '...'
        blf.draw(font_id, display_name)

    cam = bpy.context.scene.camera
    if cam:
        ## ? Instead highlight camera basic Gizmo ?

        frame = [cam.matrix_world @ v for v in cam.data.view_frame(scene=context.scene)]
        mat = cam.matrix_world
        loc = mat.to_translation()
        gpu.state.line_width_set(1.0)

        right = (frame[0] + frame[1]) / 2
        left = (frame[2] + frame[3]) / 2
        # cam_tri = [loc, left, right]

        near_clip_point = mat @ Vector((0,0,-cam.data.clip_start))
        far_clip_point = mat @ Vector((0,0,-cam.data.clip_end))
        orient = Vector((0,0,1))
        orient.rotate(mat)

        ## Redefined left right (interchangeably) by taking most distants point to center in 2d space for the cone
        ## (/!\ Does not work when perfecly looking up/down...)
        # center_2d = fn.location_to_region(sum(frame, start=Vector()) / 4)
        # frame_region = [(fn.location_to_region(v), v) for v in frame]
        # frame_region.sort(key=lambda x: (x[0] - center_2d).length)
        # left, right = frame_region[-2][1], frame_region[-1][1] # Keep second element of the last two pair

        # View cone with clipping display
        if cam.data.type == 'ORTHO':
            cam_view = [
                # Left
                fn.location_to_region(intersect_line_plane(left, left + orient, near_clip_point, orient)),
                fn.location_to_region(intersect_line_plane(left, left + orient, far_clip_point, orient)),
                # Right
                fn.location_to_region(intersect_line_plane(right, right + orient, near_clip_point, orient)),
                fn.location_to_region(intersect_line_plane(right, right + orient, far_clip_point, orient)),
            ]
        else:            
            cam_view = [
                # Left
                fn.location_to_region(intersect_line_plane(loc, left, near_clip_point, orient)),
                fn.location_to_region(intersect_line_plane(loc, left, far_clip_point, orient)),
                # Right
                fn.location_to_region(intersect_line_plane(loc, right, near_clip_point, orient)),
                fn.location_to_region(intersect_line_plane(loc, right, far_clip_point, orient)),
            ]

        # Add perpenticular lines 
        cam_view.append(cam_view[0])
        cam_view.append(cam_view[2])
        cam_view.append(cam_view[1])
        cam_view.append(cam_view[3])

        ## TODO : Trace cam Tri         

        cam_lines = batch_for_shader(shader_uniform, 'LINES', {"pos": cam_view})
        shader_uniform.bind()
        shader_uniform.uniform_float("color", (0.5, 0.5, 1.0, 0.5))
        cam_lines.draw(shader_uniform)


def circle_3d(x, y, radius, segments):
    coords = []
    m = (1.0 / (segments - 1)) * (pi * 2)
    for p in range(segments):
        p1 = x + cos(m * p) * radius
        p2 = y + sin(m * p) * radius
        coords.append(Vector((p1, p2, 0)))
    return coords

def draw_map_callback():
    context = bpy.context
    if not fn.is_minimap_viewport(context):
        return

    # if context.region_data.view_perspective != 'CAMERA':
    #     return
   
    gpu.state.blend_set('ALPHA')
    font_id = 0
    
    ### Trace GP objects 
    
    shader_uniform = gpu.shader.from_builtin('UNIFORM_COLOR')
    
    ## As lines:
    """
    gpu.state.line_width_set(3.0)
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
    
    gp_lines = batch_for_shader(shader_uniform, 'LINES', {"pos": lines})
    shader_uniform.bind()
    shader_uniform.uniform_float("color", (1.0, 1.0, 0.0, 0.8))
    gp_lines.draw(shader_uniform)
    """

    ## as Circles
    radius = 0.02 * context.region_data.view_distance

    ## Text need to be on a 2D draw_callback
    # text_offset_vec = Vector((0, radius + 0.04, 0))
    # text_offset_vec.rotate(context.region_data.view_rotation)

    # lines = [o.matrix_world @ v for o in bpy.context.scene.objects if o.type == 'GPENCIL' and o.visible_get() for v in line_vecs]
    for ob in [o for o in bpy.context.scene.objects if o.type == 'GPENCIL' and o.visible_get()]:
        if context.object and context.object == ob:
            color = (0.9, 0.9, 0.6, 0.9)
        else:
            color = (0.7, 0.7, 0.0, 0.85)
        
        ## On origin
        # loc = ob.matrix_world.to_translation()
        ## On BBox median point

        loc = Vector(np.mean([ob.matrix_world @ Vector(corner) for corner in ob.bound_box], axis=0))
        circle_co = circle_3d(*loc.xy, radius, 24) # Scaled to dist radius
        batch = batch_for_shader(shader_uniform, 'TRI_FAN', {"pos":  circle_co})
        shader_uniform.bind()
        shader_uniform.uniform_float("color", color)
        batch.draw(shader_uniform)

        ## Draw text 
        # blf.position(font_id, *(loc + text_offset_vec))
        # blf.size(font_id, 20)
        # blf.color(font_id, *color)
        # display_name = ob.name if len(ob.name) <= 24 else ob.name[:24-3] + '...'
        # blf.draw(font_id, display_name)
    

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

        cam_lines = batch_for_shader(shader_uniform, 'LINES', {"pos": cam_view})
        shader_uniform.bind()
        shader_uniform.uniform_float("color", (0.5, 0.5, 1.0, 0.5))
        cam_lines.draw(shader_uniform)


draw_handle = None

def register():
    if bpy.app.background:
        return

    global draw_handle
    draw_handle = bpy.types.SpaceView3D.draw_handler_add(
        draw_map_callback_2d, (), "WINDOW", "POST_PIXEL")
        # draw_map_callback, (), "WINDOW", "POST_VIEW")

def unregister():
    if bpy.app.background:
        return

    global draw_handle
    if draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handle, 'WINDOW')

if __name__ == "__main__":
    register()
