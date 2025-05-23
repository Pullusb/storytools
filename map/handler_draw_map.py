import bpy
import gpu
import blf
import numpy as np

from gpu_extras.presets import draw_circle_2d
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector, Color
from time import time

from bpy.app.handlers import persistent
from .. import fn


## 2D minimap drawing
def draw_map_callback_2d():
    context = bpy.context
    if not fn.is_minimap_viewport(context):
        return

    # if context.region_data.view_perspective != 'CAMERA':
    #     return
    
    shadow_offset = Vector((1,-1))
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
        color.h = fn.name_to_hue(ob.name) # Hue by name
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

        cam_view = fn.get_camera_frustum(cam, context=context) # get in 3D space
        cam_view = [fn.location_to_region(v) for v in cam_view] # convert to 2D space

        ## TODO : Trace cam Tri  
        gpu.state.line_width_set(3.0) # Thick only on camera tri ?
        cam_lines = batch_for_shader(shader_uniform, 'LINES', {"pos": cam_view})
        shader_uniform.bind()
        shader_uniform.uniform_float("color", (0.5, 0.5, 1.0, 0.5))
        cam_lines.draw(shader_uniform)

    ## return here to skip viewport frustum display
    gpu.state.line_width_set(1.0) # reset line width
    return

    # FIXME: Can Works by setting a property in loop. Need a proper method to refresh view trace, or activate only in specific cases

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
                
                # Get viewport frustum lines in 3D
                view_lines_3d = fn.get_viewport_frustum(area, region, rv3d, space)

                ## Specify current region (Here no need, using current context is OK)
                # view_lines = [location_3d_to_region_2d(current_region, current_rv3d, v) for v in view_lines]

                view_lines = [fn.location_to_region(v) for v in view_lines_3d]

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

                ## Dirty : Change a property to force refresh current minimap window
                # rv3d.view_perspective = rv3d.view_perspective


    ## Dirty refresh method: Change a property to force refresh windows...
    # current_rv3d.view_perspective = current_rv3d.view_perspective

    ## /!\ Following refresh tests are not working:
    '''
    ## Redraw minimap areas
    # for a, r in minimap_areas:
    #     a.tag_redraw()
    #     r.update()
    
    # dps = bpy.context.evaluated_depsgraph_get()
    # dps.update()

    # current_rv3d.update()
    # context.area.tag_redraw()
    '''



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
