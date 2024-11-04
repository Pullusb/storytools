import bpy
import gpu
import blf
import numpy as np
import hashlib

from math import pi, cos, sin
from gpu_extras.presets import draw_circle_2d
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils.geometry import intersect_line_plane
from mathutils import Vector, Color
from bpy_extras import view3d_utils
from time import time

from bpy.app.handlers import persistent
from .. import fn


## User view calculation from Swann Martinez's Multi-user addon
def project_to_viewport(region: bpy.types.Region, rv3d: bpy.types.RegionView3D, coords: list, distance: float = 1.0) -> Vector:
    """ Compute a projection from 2D to 3D viewport coordinate

        :param region: target windows region
        :type region:  bpy.types.Region
        :param rv3d: view 3D
        :type rv3d: bpy.types.RegionView3D
        :param coords: coordinate to project
        :type coords: list
        :param distance: distance offset into viewport
        :type distance: float
        :return: Vector() list of coordinates [x,y,z]
    """
    target = [0, 0, 0]

    if coords and region and rv3d:
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coords)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coords)
        target = ray_origin + view_vector * distance

    return Vector((target.x, target.y, target.z))

def generate_user_camera(area, region, rv3d) -> list:
    """ Generate a basic camera represention of the user point of view
    v1-4 first point represent the square
    v5: frame center point
    v6: view location (orbit point)
    v7: 

    :return: list of 7 points
    """

    # area, region, rv3d = view3d_find()

    v1 = v2 = v3 = v4 = v5 = v6 = v7 = [0, 0, 0]

    if area and region and rv3d:
        width = region.width
        height = region.height

        v1 = project_to_viewport(region, rv3d, (width, height))
        v2 = project_to_viewport(region, rv3d, (width, 0))
        v3 = project_to_viewport(region, rv3d, (0, 0))
        v4 = project_to_viewport(region, rv3d, (0, height))

        v5 = project_to_viewport(region, rv3d, (width/2, height/2))
        v6 = rv3d.view_location # list(rv3d.view_location)
        v7 = project_to_viewport(
            region, rv3d, (width/2, height/2), distance=-.8)

    coords = [v1, v2, v3, v4, v5, v6, v7]

    return coords

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


def name_to_hue(name):
    # Use MD5 hash for consistency across sessions
    hash_value = hashlib.md5(name.encode()).hexdigest()
    # Convert first 8 characters of hash to integer and scale to 0-1
    return int(hash_value[:8], 16) / 0xffffffff

shadow_offset = Vector((1,-1))

## 2D minimap drawing
def draw_map_callback_2d():
    context = bpy.context
    if not fn.is_minimap_viewport(context):
        return

    # if context.region_data.view_perspective != 'CAMERA':
    #     return
    
    settings = fn.get_addon_prefs()
    gpu.state.blend_set('ALPHA')
    shader_uniform = gpu.shader.from_builtin('UNIFORM_COLOR')
    font_id = 0

    cam = bpy.context.scene.camera
    ### Trace GP objects 
    color = (0.8, 0.8, 0.0, 0.9)
    # gps = [o for o in bpy.context.scene.objects if o.type == 'GREASEPENCIL' and o.visible_get()]

    # scale = context.region_data.view_distance # TODO: define scaling
    radius = settings.map_dot_size * context.preferences.system.ui_scale
    offset_vector = Vector((0, radius + radius * 0.1))
    # for gp in gps:
    #     draw_circle_2d(fn.location_to_region(gp.matrix_world.translation), color, scale)
    # active = context.object
    # if active and active.type == 'GREASEPENCIL':
    #     draw_circle_2d(fn.location_to_region(active.matrix_world.translation), (0.9, 0.9, 0.0, 0.9), scale)

    gp_list = [o for o in bpy.context.scene.objects if o.type == 'GREASEPENCIL' and o.visible_get()]

    ## Always recenter map (expensive! Need better object-frame function)
    # if settings.map_always_frame_objects:
    #     obj_list = gp_list
    #     if cam:
    #         obj_list = obj_list + [cam]
    #     fn.frame_objects(context, objects=obj_list)

    for ob in gp_list:
        if context.object and context.object == ob:
            # color = (0.9, 0.9, 0.6, 0.9) # All same color
            color = (0.9, 0.9, 0.6)
        else:
            # color = (0.7, 0.7, 0.0, 0.85) # All same color
            color = (0.7, 0.7, 0.0)
        color = Color(color)
        color.h = name_to_hue(ob.name) # Hue by name
        color = (*color, 1.0) # Add alpha

        loc = fn.location_to_region(Vector(np.mean([ob.matrix_world @ Vector(corner) for corner in ob.bound_box], axis=0)))
        if settings.use_map_dot:
            ## Draw location
            ## On origin
            # loc = fn.location_to_region(ob.matrix_world.to_translation()) # On origin ?

            ## On BBox median point (feel probably better for user perspective)
            ## note: can use "4" circle to mark another object type
            circle_co = fn.circle_2d(*loc, radius, 20) # Scaled to dist radius
            batch = batch_for_shader(shader_uniform, 'TRI_FAN', {"pos":  circle_co})
            shader_uniform.bind()
            shader_uniform.uniform_float("color", color)
            batch.draw(shader_uniform)

        ## Names
        if settings.use_map_name:
            display_name = ob.name if len(ob.name) <= 24 else ob.name[:21] + '...'
            ## Draw text shadow
            blf.position(font_id, *(loc + offset_vector + shadow_offset), 0)
            blf.size(font_id, settings.map_name_size)
            blf.color(font_id, 0,0,0, 0.8) # shadow color
            blf.draw(font_id, display_name)

            ## Draw text 
            blf.position(font_id, *(loc + offset_vector), 0)
            blf.size(font_id, settings.map_name_size)
            blf.color(font_id, *color)
            blf.draw(font_id, display_name)

    if cam:
        ## ? Instead highlight camera basic Gizmo ?

        frame = [cam.matrix_world @ v for v in cam.data.view_frame(scene=context.scene)]
        mat = cam.matrix_world
        loc = mat.to_translation()
        gpu.state.line_width_set(3.0) # Thick only on camera tri ?

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
        cam_view = get_frustum_lines(loc, left, right, orient, near_clip_point, far_clip_point, cam.data.type)

        cam_view = [fn.location_to_region(v) for v in cam_view]

        ## TODO : Trace cam Tri  

        cam_lines = batch_for_shader(shader_uniform, 'LINES', {"pos": cam_view})
        shader_uniform.bind()
        shader_uniform.uniform_float("color", (0.5, 0.5, 1.0, 0.5))
        cam_lines.draw(shader_uniform)

    return
    # FIXME: refresh view trace
    ## Iterate over non-minimap viewports
    # current_region = next((region for region in context.area.regions if region.type == 'WINDOW'), None)
    current_rv3d = context.space_data.region_3d
    
    # base_color = (0.6, 0.3, 0.08)
    base_color = (0.7, 0.4, 0.08)
    hue_offset = 0
    # print(f'{time()} Loop over 3D areas') #Dbg
    # minimap_areas = []
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active # area.spaces[0]
                if fn.is_minimap_viewport(context, space) or space.region_quadviews:
                    # minimap_areas.append((area, space.region_3d))
                    continue

                rv3d = space.region_3d
                # print(f'3D viewport') #Dbg
                if rv3d.view_perspective == 'CAMERA':
                    ## Same as camera view
                    continue

                region = next((region for region in area.regions if region.type == 'WINDOW'), None)
                if region is None:
                    continue
                ## Construct lines - naive method for now (consider view is always z-aligned)
                view_mat = rv3d.view_matrix.inverted()
                view_orient = Vector((0,0,1))
                view_orient.rotate(view_mat)
                
                user_cam = generate_user_camera(area, region, rv3d)
                # loc = rv3d.view_matrix.inverted().to_translation()
                loc = user_cam[6]
                left = (user_cam[2] + user_cam[3]) / 2
                right = (user_cam[0] + user_cam[1]) / 2
                near_clip_point = view_mat @ Vector((0, 0, -space.clip_start))
                far_clip_point = view_mat @ Vector((0, 0, -space.clip_end))
                
                view_lines = get_frustum_lines(loc, left, right, view_orient, near_clip_point, far_clip_point, rv3d.view_perspective)

                ## specify current region (no need, using current context is OK)
                # view_lines = [location_3d_to_region_2d(current_region, current_rv3d, v) for v in view_lines]
                view_lines = [fn.location_to_region(v) for v in view_lines]

                ## Add focal point (view-loc) Line
                # view_lines += [fn.location_to_region(v) for v in user_cam[5:7]]

                color = Color(base_color)
                color.h += hue_offset
                view_batch = batch_for_shader(shader_uniform, 'LINES', {"pos": view_lines})
                shader_uniform.bind()
                shader_uniform.uniform_float("color", (*tuple(color), 0.8))
                view_batch.draw(shader_uniform)
                
                # print(f'draw viewport {hue_offset}') #Dbg
                ## Do not work, probably detect no changes as viewport move is not considered one
                # context.area.tag_redraw()
                # area.tag_redraw()
                # rv3d.update()
                # current_rv3d.update()

                hue_offset += 0.25
    
    ## Redraw minimap areas
    # for a, r in minimap_areas:
    #     a.tag_redraw()
    #     r.update()
    
    # dps = bpy.context.evaluated_depsgraph_get()
    # dps.update()

    # current_rv3d.update()
    # context.area.tag_redraw()
    ## 
    # context.scene.cursor.location = context.scene.cursor.location # UGLY TEST to make it work


def circle_3d(x, y, radius, segments):
    coords = []
    m = (1.0 / (segments - 1)) * (pi * 2)
    for p in range(segments):
        p1 = x + cos(m * p) * radius
        p2 = y + sin(m * p) * radius
        coords.append(Vector((p1, p2, 0)))
    return coords

def get_frustum_lines(loc, left, right, orient, near_clip_point, far_clip_point, view_type):
    """return points of quad representing view frustum
    sequence reresent following pairs to be used draw batch LINES
    # Left and Right lines:
    left near -> left far
    right near -> right far
    
    ## near clip and far clip perpendicular lines:
    left near -> right near
    left far -> right far

    """

    if view_type == 'ORTHO':
        view_list = [
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
        # view_list = [
        #     loc, extrapolate_points_by_length(loc, right, 2000),
        #     loc, extrapolate_points_by_length(loc, left, 2000)
        # ]
        
        # View cone with clipping display
        view_list = [
            # Left
            intersect_line_plane(loc, left, near_clip_point, orient),
            intersect_line_plane(loc, left, far_clip_point, orient),
            # Right
            intersect_line_plane(loc, right, near_clip_point, orient),
            intersect_line_plane(loc, right, far_clip_point, orient),
        ]

    # if post_pixel:
    #     view_list = [fn.location_to_region(v) for v in view_list]

    # Add perpenticular lines 
    view_list.append(view_list[0])
    view_list.append(view_list[2])
    view_list.append(view_list[1])
    view_list.append(view_list[3])
    
    return view_list
'''
## Not used: used 2D POST_PIXEL version
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
    lines = [o.matrix_world @ v for o in bpy.context.scene.objects if o.type == 'GREASEPENCIL' and o.visible_get() for v in line_vecs]
    ## Equivalent to:
    # lines = []
    # for o in [o for o in bpy.context.scene.objects if o.type == 'GREASEPENCIL' and o.visible_get()]:
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

    # lines = [o.matrix_world @ v for o in bpy.context.scene.objects if o.type == 'GREASEPENCIL' and o.visible_get() for v in line_vecs]
    for ob in [o for o in bpy.context.scene.objects if o.type == 'GREASEPENCIL' and o.visible_get()]:
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
        # cam_tri = [loc, left, right]

        near_clip_point = mat @ Vector((0,0,-cam.data.clip_start))
        far_clip_point = mat @ Vector((0,0,-cam.data.clip_end))
        orient = Vector((0,0,1))
        orient.rotate(mat)

        cam_view = get_frustum_lines(
            loc, left, right, orient, near_clip_point, far_clip_point, cam.data.type)

        cam_lines = batch_for_shader(shader_uniform, 'LINES', {"pos": cam_view})
        shader_uniform.bind()
        shader_uniform.uniform_float("color", (0.5, 0.5, 1.0, 0.5))
        cam_lines.draw(shader_uniform)
'''
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
