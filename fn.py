# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import json
import math
import hashlib
import numpy as np

from fnmatch import fnmatch
from math import pi, cos, sin
from pathlib import Path

from bpy_extras import view3d_utils
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils.geometry import intersect_line_plane
from mathutils import (Matrix,
                       Vector,
                       Color,
                       geometry,
                       )

from .constants import LAYERMAT_PREFIX


### -- mapping --
## Mapping of keymap items to their id
KEYNUM_MAP = {
    # Top row numbers
    "ONE": "1",
    "TWO": "2",
    "THREE": "3",
    "FOUR": "4",
    "FIVE": "5",
    "SIX": "6",
    "SEVEN": "7",
    "EIGHT": "8",
    "NINE": "9",
    "ZERO": "0",
    
    # Numpad numbers
    "NUMPAD_1": "1",
    "NUMPAD_2": "2",
    "NUMPAD_3": "3",
    "NUMPAD_4": "4",
    "NUMPAD_5": "5",
    "NUMPAD_6": "6",
    "NUMPAD_7": "7",
    "NUMPAD_8": "8",
    "NUMPAD_9": "9",
    "NUMPAD_0": "0"
}

### -- prefs --

def get_addon_prefs():
    return bpy.context.preferences.addons[__package__].preferences

def open_addon_prefs():
    '''Open addon prefs windows with focus on current addon'''
    #TODO futureproof update: make if work with manifest as well
    from .__init__ import bl_info
    wm = bpy.context.window_manager
    wm.addon_filter = 'All'
    if not 'COMMUNITY' in  wm.addon_support: # reactivate community
        wm.addon_support = set([i for i in wm.addon_support] + ['COMMUNITY'])
    wm.addon_search = bl_info['name']
    bpy.context.preferences.active_section = 'ADDONS'
    bpy.ops.preferences.addon_expand(module=__package__)
    bpy.ops.screen.userpref_show('INVOKE_DEFAULT')


def snap_to_step(value, step):
    # return (value//step)*step # Also valid
    return round(value / step) * step

### -- Vector --

def location_to_region(worldcoords) -> Vector:
    '''return 2d location'''
    return view3d_utils.location_3d_to_region_2d(
        bpy.context.region, bpy.context.space_data.region_3d, worldcoords)

def region_to_location(viewcoords, depthcoords) -> Vector:
    '''return normalized 3d vector'''
    return view3d_utils.region_2d_to_location_3d(
        bpy.context.region, bpy.context.space_data.region_3d, viewcoords, depthcoords)

def reset_draw_settings(context=None):
    '''Reset placement and orientation settings according to addon preferences'''
    context = context or bpy.context
    settings = context.scene.tool_settings
    prefs = get_addon_prefs()

    # 'ORIGIN', 'CURSOR', 'SURFACE', 'STROKE'
    # settings.gpencil_stroke_placement_view3d = 'ORIGIN'
    if prefs.default_placement != 'NONE':
        settings.gpencil_stroke_placement_view3d = prefs.default_placement
    
    # 'VIEW', 'AXIS_Y', 'AXIS_X', 'AXIS_Z', 'CURSOR'
    # settings.gpencil_sculpt.lock_axis = 'AXIS_Y' # Front Axis
    if prefs.default_orientation != 'NONE':
        settings.gpencil_sculpt.lock_axis = prefs.default_orientation

def coord_distance_from_view(coord=None, context=None):
    '''Get distance between view origin and plane facing view at coordinate'''
    context = context or bpy.context
    coord = coord or context.scene.cursor.location

    rv3d = context.region_data
    view_mat = rv3d.view_matrix.inverted()
    view_point = view_mat @ Vector((0, 0, -1000))
    co = intersect_line_plane(view_mat.translation, view_point, coord, view_point)
    if co is None:
        return None
    return (co - view_mat.translation).length

def get_camera_view_vector():
    '''return active camera view vector (normalized direction)
    return None if no active camera
    '''
    view_vector = Vector((0,0,-1))
    if not bpy.context.scene.camera:
        return
    view_vector.rotate(bpy.context.scene.camera.matrix_world)
    return view_vector

def get_viewport_view_vector(context=None):
    '''return current viewport view vector (normalized direction)'''
    context = context or bpy.context
    view_vector = Vector((0,0,-1))
    view_vector.rotate(context.space_data.region_3d.view_rotation)
    return view_vector

def coord_distance_from_cam(coord=None, context=None):
    """Get the distance between the camera and a 3D point, parallel to view vector axis"""
    context = context or bpy.context
    coord = coord or context.scene.cursor.location

    view_mat = context.scene.camera.matrix_world
    view_point = view_mat @ Vector((0, 0, -1000))
    co = intersect_line_plane(view_mat.translation, view_point, coord, view_point)
    if co is None:
        return None
    return (co - view_mat.translation).length

def get_cam_frame_world(cam, scene=None):
    '''get camera frame center position in 3d space
    Need scene to get resolution ratio (default to active scene)
    ortho camera note: scale must be 1,1,1 (parent too)
    to fit right in cam-frame rectangle
    '''

    scene = scene or bpy.context.scene

    # Without scene passed, base on square
    frame = cam.data.view_frame(scene=scene)
    mat = cam.matrix_world
    frame = [mat @ v for v in frame]
    #-# Get center
    # import numpy as np
    # center = np.add.reduce(frame) / 4
    # center = np.sum(frame, axis=0) / 4
    return frame

def get_cam_frame_world_center(cam, scene=None):
    '''get camera frame center position in 3d space
    Need scene to get resolution ratio (default to active scene)
    ortho camera note: scale must be 1,1,1 (parent too)
    to fit right in cam-frame rectangle
    '''

    scene = scene or bpy.context.scene

    frame = get_cam_frame_world(cam, scene=scene)
    #-# Get center
    # return np.sum(frame, axis=0) / 4
    return np.add.reduce(frame) / 4

def calculate_dolly_zoom_position(old_position, target_position, old_focal_length, new_focal_length):
    """
    Calculates a new camera position for a dolly zoom effect based on focal length change.
    Designed to be used in a modal operator with a slider.
    
    Args:
        old_position: The previous/current camera position (mathutils.Vector)
        target_position: The target position (mathutils.Vector)
        old_focal_length: The previous/current focal length in mm
        new_focal_length: The new focal length in mm
    
    Returns:
        Vector: The new camera position
    """
    # Get direction vector from old camera position to target
    direction = (target_position - old_position).normalized()
    
    # Calculate current distance
    current_distance = (target_position - old_position).length
    
    # Calculate new distance to maintain same field of view for subject
    # The ratio of distances should equal the ratio of focal lengths
    new_distance = current_distance * (new_focal_length / old_focal_length)
    
    # Calculate new position
    return target_position - direction * new_distance    

def replace_rotation_matrix(M1, M2):
    '''Replace rotation component of matrix 1 with matrix 2
    return a new matrix
    '''
    # Convert Blender matrices to numpy arrays
    M1_np = np.array(M1)
    M2_np = np.array(M2)
    # Extract the rotation components (upper 3x3 part)
    R2 = M2_np[:3, :3]
    # Replace the rotation part of M1 with R2
    M1_np[:3, :3] = R2
    # Convert back to Blender Matrix
    M1_new = Matrix(M1_np.tolist())
    return M1_new

def rotate_by_90_degrees(ob, axis='X', negative=True):
    angle = pi/2
    if negative:
        angle += -1
    mat_90 = Matrix.Rotation(angle, 4, axis)
    ob.matrix_world = ob.matrix_world @ mat_90

def get_scale_matrix(scale) -> Matrix:
    '''Recreate a neutral mat scale'''
    matscale_x = Matrix.Scale(scale[0], 4,(1,0,0))
    matscale_y = Matrix.Scale(scale[1], 4,(0,1,0))
    matscale_z = Matrix.Scale(scale[2], 4,(0,0,1))
    matscale = matscale_x @ matscale_y @ matscale_z
    return matscale

def assign_rotation_from_ref_matrix(obj, ref_mat, rot_90=True):
    '''Get an object, a reference matrix and assign
    :obj: Object to modify
    :ref_mat: Matrix to get rotation from
    :rot_90: Add and extra 90 degree negative rotation on X axis
    Usefull when aligning with camera view so object keep facing front
    '''
    
    _ref_loc, ref_rot, _ref_scale = ref_mat.decompose()
    
    if obj.parent:
        mat = obj.matrix_world
    else:
        mat = obj.matrix_basis

    o_loc, _o_rot, o_scale = mat.decompose()

    loc_mat = Matrix.Translation(o_loc)
    
    if rot_90:
        mat_90 = Matrix.Rotation(-pi/2, 4, 'X')
        rot_mat = ref_rot.to_matrix().to_4x4() @ mat_90
    else:
        rot_mat = ref_rot.to_matrix().to_4x4()

    scale_mat = get_scale_matrix(o_scale)

    new_mat = loc_mat @ rot_mat @ scale_mat

    if obj.parent:
        obj.matrix_world = new_mat
    else:
        obj.matrix_basis = new_mat

    return new_mat


def get_view_orientation_from_matrix(view_matrix):
    '''Get orientation from view_matrix'''
    r = lambda x: round(x, 2)
    view_rot = view_matrix.to_euler()

    orientation_dict = {(0.0, 0.0, 0.0) : 'TOP',
                        (r(math.pi), 0.0, 0.0) : 'BOTTOM',
                        (r(-math.pi/2), 0.0, 0.0) : 'FRONT',
                        (r(math.pi/2), 0.0, r(-math.pi)) : 'BACK',
                        (r(-math.pi/2), r(math.pi/2), 0.0) : 'LEFT',
                        (r(-math.pi/2), r(-math.pi/2), 0.0) : 'RIGHT'}

    return orientation_dict.get(tuple(map(r, view_rot)), 'UNDEFINED')


### -- Camera/View Frustum --

## User view calculation from Swann Martinez's Multi-user addon
def project_to_viewport(region: bpy.types.Region, rv3d: bpy.types.RegionView3D, coords: tuple, distance: float = 1.0) -> Vector:
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

def get_camera_frustum(cam, context=None):
    """
    Get camera frustum coordinates in 3D space
    
    cam (Object): Camera object
    context (Context, optional): Blender context for scene information
    
    Returns:
    list: 3D coordinates of camera frustum lines, or empty list if camera is invalid
    """
    if not cam or cam.type != 'CAMERA':
        return []
        
    if context is None:
        context = bpy.context
        
    scene = context.scene
    
    # Get camera frame
    frame = [cam.matrix_world @ v for v in cam.data.view_frame(scene=scene)]
    mat = cam.matrix_world
    loc = mat.to_translation()
    
    # Calculate midpoints for left and right sides
    right = (frame[0] + frame[1]) / 2
    left = (frame[2] + frame[3]) / 2
    
    # Calculate near and far clip points
    near_clip_point = mat @ Vector((0,0,-cam.data.clip_start))
    far_clip_point = mat @ Vector((0,0,-cam.data.clip_end))
    
    # Get orientation vector
    orient = Vector((0,0,1))
    orient.rotate(mat)
    
    # Get frustum lines using the existing function
    return get_frustum_lines(loc, left, right, orient, near_clip_point, far_clip_point, cam.data.type)

def get_viewport_frustum(area, region, rv3d, space):
    """
    Get viewport frustum coordinates in 3D space
    
    area (Area): Viewport area
    region (Region): Region of the viewport
    rv3d (RegionView3D): 3D region view
    space (SpaceView3D): View space for clip distances
    
    Returns:
    list: 3D coordinates of viewport frustum lines
    """

    ## Return camrera frustum if un camera view (supposed to be the same)
    # if rv3d.view_perspective == 'CAMERA':
    #     return get_camera_frustum(space.active.camera, context=bpy.context)
        
    # Construct view orientation
    view_mat = rv3d.view_matrix.inverted()
    view_orient = Vector((0, 0, 1))
    view_orient.rotate(view_mat)
    
    # Get user camera coordinates
    user_cam = generate_user_camera(area, region, rv3d)
    
    # Extract location and view frame points
    loc = user_cam[6]  # View location point
    left = (user_cam[2] + user_cam[3]) / 2  # Left midpoint
    right = (user_cam[0] + user_cam[1]) / 2  # Right midpoint
    
    # Calculate near and far clip points
    near_clip_point = view_mat @ Vector((0, 0, -space.clip_start))
    far_clip_point = view_mat @ Vector((0, 0, -space.clip_end))
    
    # Get frustum lines using the existing function
    return get_frustum_lines(loc, left, right, view_orient, near_clip_point, 
                            far_clip_point, rv3d.view_perspective)


### -- Collection management --

def get_view_layer_collection(col, vl_col=None, view_layer=None):
    '''return viewlayer collection from collection
    col: the collection to get viewlayer collection from
    view_layer (viewlayer, optional) : viewlayer to search in, if not passed, use active viewlayer
    
    '''
    if vl_col is None:
        if view_layer:
            vl_col = view_layer.layer_collection
        else:
            vl_col = bpy.context.view_layer.layer_collection
    for sub in vl_col.children:
        if sub.collection == col:
            return sub
        if len(sub.children):
            c = get_view_layer_collection(col, sub)
            if c is not None:
                return c

def get_parents_cols(col, root=None, scene=None, cols=None):
    '''Return a list of parents collections of passed col
    root : Pass a collection to search in (recursive)
        Else search in master collection
    scene: scene to search in (active scene if not passed)
    cols: used internally by the function to collect results
    '''
    if cols is None:
        cols = []
        
    if root == None:
        scn = scene or bpy.context.scene
        root=scn.collection

    for sub in root.children:
        if sub == col:
            cols.append(root)

        if len(sub.children):
            cols = get_parents_cols(col, root=sub, cols=cols)
    return cols

### -- Object --

def empty_at(pos, name='Empty', type='PLAIN_AXES', size=1.0, show_name=False, link=True):
    '''
    Create an empty at given Vector3 position.
    pos (Vector3): position 
    name (str, default Empty): name of the empty object
    type (str, default 'PLAIN_AXES'): options in 'PLAIN_AXES','ARROWS','SINGLE_ARROW','CIRCLE','CUBE','SPHERE','CONE','IMAGE'
    size (int, default 1.0): Size of the empty
    link (Bool,default True): Link to active collection
    i.e : empty_at((0,0,1), 'ARROWS', 2) creates "Empty" at Z+1, of type gyzmo and size 2
    '''
    
    mire = bpy.data.objects.get(name)
    if not mire:
        mire = bpy.data.objects.new(name, None)
        if link:
            bpy.context.collection.objects.link(mire)
    mire.empty_display_type = type
    mire.empty_display_size = size
    mire.location = pos
    mire.show_name = show_name
    return mire

def pack_images_in_object(obj, verbose=False):
    '''Pack all image textures used by object into the blend file.
    obj (Object): object containing materials with image textures.
    '''
    # Ensure the object has materials
    if not obj.data.materials:
        return

    # print(f"Packing images for object: {obj.name}")
    for mat in obj.data.materials:
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    node.image.pack()
                    if verbose:
                        print(f"Packed image: {node.image.name}")

### -- GP --

def get_gp_draw_plane(context):
    ''' return tuple with plane coordinate and normal
    of the curent drawing according to geometry'''

    settings = context.scene.tool_settings
    orient = settings.gpencil_sculpt.lock_axis # 'VIEW', 'AXIS_Y', 'AXIS_X', 'AXIS_Z', 'CURSOR'
    loc = settings.gpencil_stroke_placement_view3d # 'ORIGIN', 'CURSOR', 'SURFACE', 'STROKE'
    mat = context.object.matrix_world if context.object else None

    # -> placement
    if loc == "CURSOR":
        plane_co = context.scene.cursor.location
    else: # ORIGIN (also on origin if set to 'SURFACE', 'STROKE')
        if not context.object:
            plane_co = None
        else:
            plane_co = context.object.matrix_world.to_translation()# context.object.location

    # -> orientation
    if orient == 'VIEW':
        plane_no = context.space_data.region_3d.view_rotation @ Vector((0,0,1))
        ## create vector, then rotate by view quaternion
        # plane_no = Vector((0,0,1))
        # plane_no.rotate(context.space_data.region_3d.view_rotation)

        ## only depth is important, can return None so region to location use same depth
        # plane_no = None

    elif orient == 'AXIS_Y': # front (X-Z)
        plane_no = Vector((0,1,0))
        plane_no.rotate(mat)

    elif orient == 'AXIS_X': # side (Y-Z)
        plane_no = Vector((1,0,0))
        plane_no.rotate(mat)

    elif orient == 'AXIS_Z': # top (X-Y)
        plane_no = Vector((0,0,1))
        plane_no.rotate(mat)

    elif orient == 'CURSOR':
        plane_no = Vector((0,0,1))
        plane_no.rotate(context.scene.cursor.matrix)

    return plane_co, plane_no

def get_gp_draw_plane_matrix(context):
    '''return matrix representing the drawing plane of the grease pencil object'''

    settings = context.scene.tool_settings
    orient = settings.gpencil_sculpt.lock_axis # 'VIEW', 'AXIS_Y', 'AXIS_X', 'AXIS_Z', 'CURSOR'
    loc = settings.gpencil_stroke_placement_view3d # 'ORIGIN', 'CURSOR', 'SURFACE', 'STROKE'
    mat = context.object.matrix_world if context.object else None

    draw_plane_mat = Matrix().to_3x3()

    # -> placement
    if loc == "CURSOR":
        plane_co = context.scene.cursor.location
    else: # ORIGIN (also on origin if set to 'SURFACE', 'STROKE')
        if not context.object:
            plane_co = None
        else:
            plane_co = context.object.matrix_world.to_translation() # context.object.location

    if not plane_co:
        return

    # -> orientation
    if orient == 'VIEW':
        draw_plane_mat.rotate(context.space_data.region_3d.view_rotation)
        # draw_plane_mat = context.space_data.region_3d.view_matrix.inverted() @ draw_plane_mat # multiply mat

    elif orient == 'AXIS_Y': # front (X-Z) - Vector((0,1,0))
        draw_plane_mat = Matrix.Rotation(math.radians(90), 3, 'X')
        draw_plane_mat.rotate(mat)
        ## Can apply and nomalize matrix to reset scale ?
        # draw_plane_mat = mat @ draw_plane_mat # multiply mat

    elif orient == 'AXIS_X': # side (Y-Z) - Vector((1,0,0))
        draw_plane_mat = Matrix.Rotation(math.radians(-90), 3, 'Y')
        draw_plane_mat.rotate(mat)
        # draw_plane_mat = mat @ draw_plane_mat # multiply mat

    elif orient == 'AXIS_Z': # top (X-Y) - Vector((0,0,1))
        draw_plane_mat.rotate(mat)
        # draw_plane_mat = mat @ draw_plane_mat # multiply mat

    elif orient == 'CURSOR':
        draw_plane_mat.rotate(context.scene.cursor.matrix)
        # draw_plane_mat = context.scene.cursor.matrix @ draw_plane_mat # multiply mat

    draw_plane_mat = draw_plane_mat.to_4x4()
    draw_plane_mat.translation = plane_co

    return draw_plane_mat


def create_default_layers(object, frame=None, use_lights=False, set_material_sync=True):
    gp = object.data
    if frame is None:
        frame = bpy.context.scene.frame_current
    # Create default layers
    for l_name in ['Color', 'Line', 'Sketch', 'Annotate']:
        layer = gp.layers.new(l_name)
        layer.frames.new(frame)
        layer.use_lights = use_lights

        if set_material_sync:
            # Set default material association
            if l_name in ['Line', 'Sketch']:
                set_material_association(object, layer, 'line')
            elif l_name == 'Color':
                set_material_association(object, layer, 'fill_white')
            elif l_name == 'Annotate':
                set_material_association(object, layer, 'line_red')

def create_gp_object(
        name="",
        parented=False,
        at_cursor=False,
        init_dist=8.0,
        face_camera=True,
        track_to_cam=False,
        enter_draw_mode=True,
        location=None,
        material_from_obj=None,
        layer_from_obj=None,
        context=None):
    """
    Create a new grease pencil object with specified parameters.
    
    Args:
        name: Name of the Grease pencil object
        parented: Whether to parent the object to the camera
        at_cursor: Create at cursor location instead of facing view
        init_dist: Initial distance from view
        face_camera: Create facing camera instead of current view
        track_to_cam: Add a track-to constraint pointing at active camera
        enter_draw_mode: Whether to enter draw mode after creation
        location: Explicit location to use instead of cursor or view (override other if provided)
        context: Blender context, optional
        
    Returns:
        The created Grease Pencil object
    """
    # Get context if not provided
    if context is None:
        context = bpy.context
    
    # Get references
    prefs = get_addon_prefs()
    scn = context.scene
    
    # Ensure we're in object mode
    if context.object and context.object.visible_get() and context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    if context.mode == 'OBJECT':
        bpy.ops.object.select_all(action='DESELECT')

    # Get view matrix
    r3d = context.space_data.region_3d
    if r3d.view_perspective != 'CAMERA' and face_camera:
        view_matrix = scn.camera.matrix_world
    else:    
        view_matrix = r3d.view_matrix.inverted()

    # Set location - prioritize explicit location if provided
    if location is not None:
        # Use the provided location directly
        loc = location
    elif at_cursor:
        loc = scn.cursor.location
    else:
        loc = view_matrix @ Vector((0.0, 0.0, -init_dist))
    
    # Clean name or generate default name if empty
    name = name.strip()
    if name == "":
        # Create default numbered name
        name_counter = len([o for o in bpy.data.objects if o.type == 'GREASEPENCIL']) + 1
        name = f"Drawing_{name_counter:03d}"
    
    # TODO bonus : maybe check if want to use same data as another drawing ?

    # Create Grease Pencil object
    gp = bpy.data.grease_pencils_v3.new(name)
    ob = bpy.data.objects.new(name, gp)

    # Find appropriate collection
    draw_col = next((c for c in scn.collection.children_recursive if c.name.startswith('Drawings')), None)
    if not draw_col:
        draw_col = next((c for c in scn.collection.children_recursive if c.name.startswith('GP')), None)
    if not draw_col:
        draw_col = context.collection  # auto-fallback on active collection

    # Link to collection
    draw_col.objects.link(ob)

    # Set parent if needed
    if parented:
        ob.parent = scn.camera

    # Set transform
    _ref_loc, ref_rot, _ref_scale = view_matrix.decompose()
    rot_mat = ref_rot.to_matrix().to_4x4() @ Matrix.Rotation(-pi/2, 4, 'X')
    ## Old matrix creation method
    # loc_mat = Matrix.Translation(loc)
    # new_mat = loc_mat @ rot_mat @ get_scale_matrix((1, 1, 1))
    ## Using Blender matrix compose method
    new_mat = Matrix.LocRotScale(loc, rot_mat.to_3x3(), Vector((1, 1, 1)))

    ob.matrix_world = new_mat

    # Make active and selected
    context.view_layer.objects.active = ob
    ob.select_set(True)

    # Add constraint if needed
    if track_to_cam:
        constraint = ob.constraints.new('TRACK_TO')
        constraint.target = scn.camera
        constraint.track_axis = 'TRACK_Y'
        constraint.up_axis = 'UP_Z'

    ## Configure default settings
    # TODO: Set Active palette (Need a selectable loader)
    if material_from_obj and len(material_from_obj.data.materials):
        ## load material from reference object
        for mat in material_from_obj.data.materials:
            gp.materials.append(mat)
    else:
        load_default_palette(ob=ob)

    ## No edit line color in GPv3 (wire is displayed using curve theme)
    # gp.edit_line_color[3] = prefs.default_edit_line_opacity # Bl default is 0.5
    gp.use_autolock_layers = prefs.use_autolock_layers
    
    ## Create layers
    if layer_from_obj and len(layer_from_obj.data.layers):
        for ref_layer in layer_from_obj.data.layers:
            layer = gp.layers.new(ref_layer.name)
            layer.frames.new(scn.frame_current)
            ## get same use light and opacity settings
            layer.use_lights = ref_layer.use_lights
            layer.opacity = ref_layer.opacity
        
        ## Copy custom properties for layer-material sync
        for k, v in layer_from_obj.items():
            if k.startswith(LAYERMAT_PREFIX):
                ob[k] = v

    else:
        # Create default layers
        create_default_layers(ob, use_lights=prefs.use_lights)
    
    # Set default active layer (Could also be a preference but may be too much)
    target_active = gp.layers.get('Sketch')
    if not target_active and len(gp.layers):
        target_active = gp.layers[-1]
    gp.layers.active = target_active

    # Update UI
    update_ui_prop_index(context)

    # Enter draw mode if requested
    if enter_draw_mode:
        bpy.ops.object.mode_set(mode='PAINT_GREASE_PENCIL')
        reset_draw_settings(context=context)

    # Show canvas if first GP created on scene (or always enable at creation) ?
    if len([o for o in context.scene.objects if o.type == 'GREASEPENCIL']) == 1:
        context.space_data.overlay.use_gpencil_grid = True

    return ob

def mean_vector(vec_list):
    '''Get mean vector from a list of vectors
    e.g: mean_vector([self.ob.matrix_world @ co for co in self.init_pos])
    '''
    return Vector(np.mean(vec_list, axis=0))

def get_coplanar_stroke_vector(obj, s, ensure_colplanar=True, tol=0.0003):
    '''Get a GP stroke object and return plane normal vector.
    
    ensure_coplanar: return None if points in stroke are not coplanar
    tol: tolerance value for coplanar points check

    return normal vector, None if points are not coplanar and ensure_colplanar is True
    '''

    if len(s.points) < 4:
        return

    # obj = bpy.context.object
    mat = obj.matrix_world
    pct = len(s.points)
    a = mat @ s.points[0].position
    b = mat @ s.points[pct//3].position
    c = mat @ s.points[pct//3*2].position
    ab = b-a
    ac = c-a
    
    # Get normal
    plane_no = ab.cross(ac)#.normalized()

    if ensure_colplanar:
        for p in s.points:
            if abs(geometry.distance_point_to_plane(mat @ p.position, a, plane_no)) > tol:
                return
    return plane_no

def get_normal(obj, frame, tol=0.0003):
    ct =  len(frame.drawing.strokes)
    if ct == 0:
        return
    if ct < 3:
        return get_coplanar_stroke_vector(obj, frame.drawing.strokes[0], ensure_colplanar=False)
    
    ## Use first point of 3 first strokes
    mat = obj.matrix_world
    a = mat @ frame.drawing.strokes[0].points[0].position
    b = mat @ frame.drawing.strokes[1].points[0].position
    c = mat @ frame.drawing.strokes[-1].points[0].position
    ab = b-a
    ac = c-a

    plane_no = ab.cross(ac)
    ## Verify coplanar ? # want to return even if it's not...
    # for p in s.points:
    #     if abs(geometry.distance_point_to_plane(mat @ p.position, a, plane_no)) > tol:
    #         return
    return plane_no

def get_coord(obj, frame):
    coords = [p.position for s in frame.drawing.strokes for p in s.points]
    mean_coord = sum(coords, Vector()) / len(coords)
    return obj.matrix_world @ mean_coord

def get_frame_coord_and_normal(obj, frame, tol=0.0003):
    '''Get a GP frame object return normal plane if strokes are coplanar (with a tolerance).
    return normal vector if coplanar else None
    '''

    ## get plane_co
    plane_co = get_coord(obj, frame)

    plane_no = get_normal(obj, frame, tol=tol)

    # if plane_no:
    #     ## Get bbox center
    #     bbox_center = sum([obj.matrix_world @ Vector(corner[:]) for corner in obj.bound_box], Vector()) / 8
    #     ## Project on plane found plane normal
    #     plane_co = intersect_line_plane(bbox_center, bbox_center + plane_no, obj.matrix_world @ frame.drawing.strokes[0].position, plane_no)
    #     plane_co = plane_co or bbox_center

    return plane_co, plane_no
        

def reset_gp_toolsettings():
    '''hardcoded and arbitrary set of changes to get better settings for a storyboard session'''
    
    context = bpy.context

    ## Set opacity at 1.0 and disable pressure on current pen
    # br = context.tool_settings.gpencil_paint.brush
    # br.gpencil_settings.use_strength_pressure = False
    # br.gpencil_settings.pen_strength = 1.0

    ## Affect pen
    if pencil := bpy.data.brushes.get("Pencil"):
        pencil.gpencil_settings.pen_strength = 0.7
        # pencil.gpencil_settings.pen_strength = 1.0
        pencil.gpencil_settings.use_strength_pressure = False
    
    if pencil := bpy.data.brushes.get("Ink Pen"):
        pencil.gpencil_settings.pen_strength = 1.0
        # pencil.gpencil_settings.pen_strength = 1.0
        pencil.gpencil_settings.use_strength_pressure = False

    ## Disable use guide
    context.tool_settings.gpencil_sculpt.guide.use_guide = False


### -- Palette --

def name_to_hue(name):
    # Use MD5 hash for consistency across sessions
    hash_value = hashlib.md5(name.encode()).hexdigest()
    # Convert first 8 characters of hash to integer and scale to 0-1
    return int(hash_value[:8], 16) / 0xffffffff

def load_palette(filepath, ob=None):
    with open(filepath, 'r') as fd:
        mat_dic = json.load(fd)
    # from pprint import pprint
    # pprint(mat_dic)
    
    if ob is None:
        ob = bpy.context.object

    for mat_name, attrs in mat_dic.items():
        curmat = bpy.data.materials.get(mat_name)
        if curmat:
            # exists
            if curmat.is_grease_pencil:
                if curmat not in ob.data.materials[:]: # add only if it's not already there
                    ob.data.materials.append(curmat)
                continue
            else:
                mat_name = mat_name + '.01' # rename to avoid conflict

        ## Create a GP mat
        mat = bpy.data.materials.new(name=mat_name)
        bpy.data.materials.create_gpencil_data(mat)
        
        ob.data.materials.append(mat)
        for attr, value in attrs.items():
            setattr(mat.grease_pencil, attr, value)


def load_default_palette(ob=None):
    '''Return a tuple compatible with Blender operator return values'''
    ob = ob or bpy.context.object
    pfp = Path(__file__).parent / 'palettes'
    
    if not pfp.exists():
        return ('ERROR', f'Palette path not found')

    base = pfp / 'base.json'
    if not base.exists():
        return ('ERROR', f'base.json palette not found in {pfp.as_posix()}')
    
    load_palette(base, ob=ob)
    return ('FINISHED', f'Loaded base Palette')

def set_material_association(ob, layer, mat_name):
    '''Take an object, a gp layer and a material name
    Create custom prop for layer material association if possible
    '''
    if not ob.data.materials.get(mat_name):
        print(f'/!\ material "{mat_name}" not found (for association with layer "{layer.name}")')
        return
    # create custom prop at object level
    ob[LAYERMAT_PREFIX + layer.name] = mat_name

def set_material_by_name(ob, mat_name) -> None:
    """
    Sets the active material of an object by its name.
    Parameters:
    ob (Object): The object whose material is to be set.
    mat_name (str): The name of the material to set as active. If None or an empty string, the function returns without making any changes.
    """

    if mat_name is None or mat_name == '':
        return
    for i, ms in enumerate(ob.material_slots):
        if not ms.material:
            continue
        m = ms.material
        if m.name == mat_name:
            # print(f':{i}:', m.name, ob.active_material_index)
            ob.active_material_index = i
            return

def set_layer_by_name(ob, name):
    if name is None or name == '':
        return
    if target_layer := ob.data.layers.get(name):
        ob.data.layers.active = target_layer

## ---
## Brushes
## ---

def create_brush(name, context=None):
    context = context or bpy.context
    brush = bpy.data.grease_pencil.brushes.new(name)
    bpy.data.brushes.create_gpencil_data(brush)

    # need to create preview
    # how to add to brush list
    # how to define brush type

    ## maybe better to append brush from a provided blend file or targeted brushlib
    ## (Better for customization)

    # context.scene.tool_settings.gpencil_paint.brush = brush

### -- Animation --

def key_object(ob, loc=True, rot=True, scale=True, use_autokey=False, mode=None, options=set(), context=None):
    '''Keyframe object location, rotation, scale 
    :ob: Object to key
    :loc: key location
    :rot: key rotation
    :scale: key scale
    :use_autokey: Respect auto_key (if enabled, key only if autokey is activated)
    :mode: in None (default), 'AVAILABLE' (add INSERTKEY_AVAILABLE), 'KEYING_SET' (respect keying set, not implemented)

    :options: Set in keyframe insert options:
    - ``INSERTKEY_NEEDED`` Only insert keyframes where they're needed in the relevant F-Curves.
    - ``INSERTKEY_VISUAL`` Insert keyframes based on 'visual transforms'.
    - ``INSERTKEY_XYZ_TO_RGB`` Color for newly added transformation F-Curves (Location, Rotation, Scale) is based on the transform axis.
    - ``INSERTKEY_REPLACE`` Only replace already existing keyframes.
    - ``INSERTKEY_AVAILABLE`` Only insert into already existing F-Curves.
    - ``INSERTKEY_CYCLE_AWARE`` Take cyclic extrapolation into account (Cycle-Aware Keying option).
    '''

    context = context or bpy.context

    ## Return if not autokeying
    if use_autokey and not context.scene.tool_settings.use_keyframe_insert_auto:
        return False
    if mode == 'AVAILABLE' and not options:
        options={'INSERTKEY_AVAILABLE',}

    act = None
    animation_data = ob.animation_data
    if animation_data:
        act = animation_data.action
    
    key_loc = False
    key_rot = False
    key_scale = False

    if mode is None:
        if loc: key_loc = True
        if rot: key_rot = True
        if scale: key_scale = True

    elif mode == 'AVAILABLE':
        if not act:
            return
        if loc: key_loc = next((fc for fc in act.fcurves if fc.data_path == 'location'), None)
        if rot: key_rot = next((fc for fc in act.fcurves if fc.data_path == 'rotation_euler'), None)
        if scale: key_scale = next((fc for fc in act.fcurves if fc.data_path == 'scale'), None)
    
    # if not act:
    #     if loc: key_loc = True
    #     if rot: key_rot = True
    #     if scale: key_scale = Truew

    text=[]
    if key_loc:
        ob.keyframe_insert('location', group='Object Transforms', options=options)
        text += ['location']
    if key_rot:
        ob.keyframe_insert('rotation_euler', group='Object Transforms', options=options)
        text += ['rotation']
    if key_scale:
        ob.keyframe_insert('scale', group='Object Transforms', options=options)
        text += ['scale']


    if text:
        return f'{ob.name}: Insert {", ".join(text)} keyframes'
    return

def key_data_path(ob, data_path, use_autokey=False, options=set(), context=None):
    '''Keyframe object location, rotation, scale 
    ob: Object to key
    data_path (str or list): data path to key, can be multiple data_path for the same object
    use_autokey: Respect auto_key (if enabled, key only if autokey is activated)

    :options: Set in keyframe insert options:
    - ``INSERTKEY_NEEDED`` Only insert keyframes where they're needed in the relevant F-Curves.
    - ``INSERTKEY_VISUAL`` Insert keyframes based on 'visual transforms'.
    - ``INSERTKEY_XYZ_TO_RGB`` Color for newly added transformation F-Curves (Location, Rotation, Scale) is based on the transform axis.
    - ``INSERTKEY_REPLACE`` Only replace already existing keyframes.
    - ``INSERTKEY_AVAILABLE`` Only insert into already existing F-Curves.
    - ``INSERTKEY_CYCLE_AWARE`` Take cyclic extrapolation into account (Cycle-Aware Keying option).
    '''

    context = context or bpy.context
    ## Return if not autokeying
    if use_autokey and not context.scene.tool_settings.use_keyframe_insert_auto:
        return False
    
    text = []
    if isinstance(data_path, str):
        data_path = [data_path]
    for dp in data_path:
        res = ob.keyframe_insert(dp, options=options)
        if res:
            text += [dp]
        
    if text:
        return f'{ob.name}: Insert {", ".join(text)} keyframes'
    return

### -- UI --

def refresh_areas():
    for area in bpy.context.screen.areas:
        area.tag_redraw()

def show_message_box(_message = "", _title = "Message Box", _icon = 'INFO'):
    '''Show message box with element passed as string or list
    if _message if a list of lists:
        if sublist have 2 element:
            considered a label [text, icon]
        if sublist have 3 element:
            considered as an operator [ops_id_name, text, icon]
        if sublist have 4 element:
            considered as a property [object, propname, text, icon]
    '''

    def draw(self, context):
        layout = self.layout
        for l in _message:
            if isinstance(l, str):
                layout.label(text=l)
            elif len(l) == 2: # label with icon
                layout.label(text=l[0], icon=l[1])
            elif len(l) == 3: # ops
                layout.operator_context = "INVOKE_DEFAULT"
                layout.operator(l[0], text=l[1], icon=l[2], emboss=False) # <- highligh the entry
            elif len(l) == 4: # prop
                row = layout.row(align=True)
                row.label(text=l[2], icon=l[3])
                row.prop(l[0], l[1], text='') 
    
    if isinstance(_message, str):
        _message = [_message]
    bpy.context.window_manager.popup_menu(draw, title = _title, icon = _icon)


def is_minimap_viewport(context=None, space_data=None):
    
    # space_data = context.space_data # Error when checking from header
    # region_data = context.region_data
    space_data = space_data or context.area.spaces.active
    region_data = space_data.region_3d

    ## check if in quad view
    if space_data.region_quadviews:
        return False

    # specific combination to identify as map viewport (Arbitrary)
    if space_data.show_object_viewport_lattice or space_data.show_object_viewport_light_probe:
        return False

    ## check if locked
    if not region_data.lock_rotation:
        return False

    ## check if looking down
    euler_view = region_data.view_matrix.to_euler()
    if euler_view[1] != 0.0 or euler_view[1] != 0.0:
        return False
    
    ## Check if ortho view
    if region_data.view_perspective != 'ORTHO':
        return False
    
    ## TODO : additional check with view settings combination to identify map viewport

    return True

def get_header_margin(context, bottom=True, overlap=False) -> int:
    '''Return margin of bottom aligned headers
    (Possible regions: HEADER, TOOL_HEADER, ASSET_SHELF, ASSET_SHELF_HEADER)
    '''
    if not context.preferences.system.use_region_overlap:
        return 0
    
    if bottom:
        side_name = 'BOTTOM'
    else:
        side_name = 'TOP'

    margin = 0
    ## asset shelf header should be only added only if shelf deployed
    regions = context.area.regions
    header = next((r for r in regions if r.type == 'HEADER'), None)
    tool_header = next((r for r in regions if r.type == 'TOOL_HEADER'), None)
    asset_shelf = next((r for r in regions if r.type == 'ASSET_SHELF'), None)

    if header.alignment == side_name : 
        margin += header.height

    if tool_header.alignment == side_name : 
        margin += tool_header.height
    
    ## calculate asset height only if checking bottom width
    if bottom and asset_shelf.height > 1:
        
        if not overlap:
            ## Header of asset shelf should only be added if shelf open
            asset_shelf_header = next((r for r in regions if r.type == 'ASSET_SHELF_HEADER'), None)
            margin += asset_shelf.height + asset_shelf_header.height
        else:
            ## Only if toggle icon is centered
            margin += asset_shelf.height

    # for r in context.area.regions:
    #     ## 'ASSET_SHELF_HEADER' is counted even when not visible
    #     if r.alignment == 'BOTTOM' and r.type != 'ASSET_SHELF_HEADER':
    #         margin += r.height
    
    return margin

def set_gizmo_settings(gz, icon,
        color=(0.0, 0.0, 0.0),
        color_highlight=(0.5, 0.5, 0.5),
        alpha=0.7,
        alpha_highlight=0.7, # 0.1
        show_drag=False,
        draw_options={'BACKDROP', 'OUTLINE'},
        scale_basis=24): # scale_basis default: 14
    gz.icon = icon
    # default 0.0
    gz.color = color
    # default 0.5
    gz.color_highlight = color_highlight
    gz.alpha = alpha
    gz.alpha_highlight = alpha_highlight
    gz.show_drag = show_drag
    gz.draw_options = draw_options
    gz.scale_basis = scale_basis
    gz.use_draw_offset_scale = True
    # gz.line_width = 1.0 # no affect on 2D gizmo ?

def circle_2d(x, y, radius, segments):
    coords = []
    m = (1.0 / (segments - 1)) * (pi * 2)
    for p in range(segments):
        p1 = x + cos(m * p) * radius
        p2 = y + sin(m * p) * radius
        coords.append((p1, p2))
    return coords

def update_ui_prop_index(context):
    '''Update storytools UI prop index after object addition or deletion'''
    scn = context.scene
    if scn.camera:
        scn.st_camera_props['index'] = next((i for i, c in enumerate(scn.objects) if scn.camera == c), 1)

    gp_index = next((i for i, o in enumerate(scn.objects) if o.type == 'GREASEPENCIL' and context.object == o), None)
    if gp_index is not None:
        scn.gp_object_props['index'] = gp_index

### -- keymap UI --

def get_tool_presets_keymap():
    '''Return ordered list of tool_presets operator keymap
    list of tuple (keymap, keymap_item)'''
    kc = bpy.context.window_manager.keyconfigs.user
    user_keymaps = kc.keymaps
    
    ## limit to  paint mode kms ? (List only in 'Grease Pencil Paint Mode' as other modes are not supported yet ?)
    # km = user_keymaps.get('Grease Pencil Paint Mode')
    # tool_preset_kmis = [(km, kmi) for kmi in km.keymap_items if kmi.idname == 'storytools.set_draw_tool']
    
    ## On the whole keymap
    tool_preset_kmis = [(km, kmi) for km in user_keymaps for kmi in km.keymap_items if kmi.idname == 'storytools.set_draw_tool']
    
    ## Sort depending on order prop (when order is specified, put first)
    ordered_kmis = [k for k in tool_preset_kmis if k[1].properties.order != 0]
    undordered_kmis = [k for k in tool_preset_kmis if k[1].properties.order == 0]

    ordered_kmis.sort(key=lambda x: x[1].properties.order)
    
    ## Sort unordered (number, then letters)
    ## Note: Can't order "ONE" "TWO" etc, So map them to "1", "2", etc
    undordered_kmis.sort(key=lambda x: KEYNUM_MAP.get(x[1].type, x[1].type))

    tool_preset_kmis = ordered_kmis + undordered_kmis
    return tool_preset_kmis


def _indented_layout(layout, level):
    indentpx = 16
    if level == 0:
        level = 0.0001   # Tweak so that a percentage of 0 won't split by half
    indent = level * indentpx / bpy.context.region.width

    split = layout.split(factor=indent)
    col = split.column()
    col = split.column()
    return col

def draw_kmi_custom(km, kmi, layout):
    ## modified from rna_keymap_ui import draw_km, draw_kmi
    col = _indented_layout(layout, 0)
    # col = layout.column()
    if kmi.show_expanded:
        col = col.column(align=True)
        box = col.box()
    else:
        box = col.column()

    split = box.split()

    row = split.row(align=True)

    ## / Specific to Storytools keymap show order prop
    if hasattr(kmi.properties, "order"):
        subrow = row.row(align=True)
        subrow.prop(kmi.properties, "order", text="")
        subrow.scale_x = 0.2
    ## end keymap order /
    row.prop(kmi, "show_expanded", text="", emboss=False)
    row.prop(kmi, "active", text="", emboss=False)

    # if km.is_modal:
    #     row.separator()
    #     row.prop(kmi, "propvalue", text="")
    # else:
    #     row.label(text=kmi.name)
    row.label(text=kmi.name)

    row = split.row()
    map_type = kmi.map_type
    row.prop(kmi, "map_type", text="")
    if map_type == 'KEYBOARD':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'MOUSE':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'NDOF':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'TWEAK':
        subrow = row.row()
        subrow.prop(kmi, "type", text="")
        subrow.prop(kmi, "value", text="")
    elif map_type == 'TIMER':
        row.prop(kmi, "type", text="")
    else:
        row.label()

    # mod_list = [m for m in ('ctrl','shift','alt', 'oskey') if getattr(kmi, m)]
    # if mod_list:
    #     mods = ' + '.join(mod_list)
    #     row.label(text=f'{mods} + ')
    # else:
    #     row.label(text='Key:')
    # row.prop(kmi, "key_modifier", text="", event=True)
    # row.separator()
    # row.label(text='+ Click')

    if (not kmi.is_user_defined) and kmi.is_user_modified:
        ## Not defined by user and has been modified : allow revert to initial state
        
        ## User 
        ## Native keyitem_restore is not accessible in addon prefs
        # row.operator('preferences.keyitem_restore', text="", icon='BACK').item_id = kmi.id

        ops = row.operator("storytools.restore_keymap_item", text="", icon='BACK') # modified
        ops.km_name = km.name
        ops.kmi_id = kmi.id

    elif kmi.is_user_defined:
        ## Defined by user : allow removal
        
        ## Native remove operator do not allow to remove when diplayed out of keymap window
        # row.operator(
        #     "preferences.keyitem_remove",
        #     text="",
        #     # Abusing the tracking icon, but it works pretty well here.
        #     icon=('TRACKING_CLEAR_BACKWARDS' if kmi.is_user_defined else 'X')
        # ).item_id = kmi.id

        ## Use a custom one
        ops = row.operator("storytools.remove_keymap_item", text="", icon='X') # modified
        ops.km_name = km.name
        ops.kmi_id = kmi.id

    else:
        # Not defined by user and not modified : no action (do not expose remove on addon listing it's own keymaps)
        row.label(text='', icon='BLANK1')

    # Expanded, additional event settings
    if kmi.show_expanded:
        col = col.column()
        box = col.box()

        split = box.column()
        # split = box.split(factor=0.4)

        ## Don't show idname (no place to change ops)
        # sub = split.row()
        # if km.is_modal:
        #     sub.prop(kmi, "propvalue", text="")
        # else:
        #     sub.prop(kmi, "idname", text="")

        if map_type not in {'TEXTINPUT', 'TIMER'}:
            sub = split.column()
            subrow = sub.row(align=True)

            if map_type == 'KEYBOARD':
                subrow.prop(kmi, "type", text="", event=True)
                subrow.prop(kmi, "value", text="")
                subrow_repeat = subrow.row(align=True)
                subrow_repeat.active = kmi.value in {'ANY', 'PRESS'}
                subrow_repeat.prop(kmi, "repeat", text="Repeat")
            elif map_type in {'MOUSE', 'NDOF'}:
                subrow.prop(kmi, "type", text="")
                subrow.prop(kmi, "value", text="")

            if map_type in {'KEYBOARD', 'MOUSE'} and kmi.value == 'CLICK_DRAG':
                subrow = sub.row()
                subrow.prop(kmi, "direction")
            
            # sub = split.column()
            sub = box.column()
            # sub.label(text='Modifiers:')
            subrow = sub.row()
            subrow.scale_x = 0.75
            subrow.prop(kmi, "any", toggle=True)
            if bpy.app.version >= (3,0,0):
                subrow.prop(kmi, "shift_ui", toggle=True)
                subrow.prop(kmi, "ctrl_ui", toggle=True)
                subrow.prop(kmi, "alt_ui", toggle=True)
                subrow.prop(kmi, "oskey_ui", text="Cmd", toggle=True)
            else:
                subrow.prop(kmi, "shift", toggle=True)
                subrow.prop(kmi, "ctrl", toggle=True)
                subrow.prop(kmi, "alt", toggle=True)
                subrow.prop(kmi, "oskey", text="Cmd", toggle=True)
            
            subrow.prop(kmi, "key_modifier", text="", event=True)
        
        # Operator properties
        box.template_keymap_item_properties(kmi)


### -- Property dump --

def convert_attr(Attr):
    '''Convert given value to a Json serializable format'''
    if isinstance(Attr, (Vector, Color)):
        return Attr[:]
    elif isinstance(Attr, Matrix):
        return [v[:] for v in Attr]
    elif isinstance(Attr, bpy.types.bpy_prop_array):
        return [Attr[i] for i in range(0,len(Attr))]
    elif isinstance(Attr, set):
        return(list(Attr))
    else:
        return(Attr)

basic_exclusions = (
### add lines here to exclude specific attribute
## Basics
'bl_rna', 'identifier', 'name_property', 'rna_type', 'properties', 'id_data', 'children', 'children_recursive', 

## To avoid recursion/crash on direct object call (comment for API check on deeper props)
'data', 'edges', 'faces', 'edge_keys', 'polygons', 'loops', 'face_maps', 'original',
'bl_idname',

##  Avoid some specific objects properties
#'matrix_local', 'matrix_parent_inverse', 'matrix_basis','location','rotation_euler', 'rotation_quaternion', 'rotation_axis_angle', 'scale', 'translation',
)

## root exclusions to add
root_exclusions = ('active_section', 'is_dirty', 'studio_lights', 'solid_lights')

known_types = (int, float, bool, str, set, Vector, Color, Matrix)


def list_attr(obj, rna_path_step, ct=0, data=None, recursion_limit=0, get_default=False, skip_readonly=True, includes=None, excludes=None):
    '''
    List recursively attribute and their value at passed data_path and return a serializable dict

    path (str): data_path to get 
    recursion_limit (int, default: 0): 0 no limit, 1 mean
    get_default (bool, default: False): get default property value intead of current value
    skip_readonly (bool, default: True): Do not list readonly
    includes (list, str) : String or list of strings fnmatch pattern, include attribute if match
    excludes (list, str) : String or list of strings fnmatch pattern, exclude attribute if match
    '''

    if includes:
        if not isinstance(includes, list):
            includes = [includes]
    if excludes:
        if not isinstance(excludes, list):
            excludes = [excludes]

    if data is None:
        data = {}

    ## TODO: use objects instead of strings
    for prop in obj.bl_rna.properties:
        if prop.identifier in basic_exclusions:
            continue

        ## Filters
        if includes:
            if not any(fnmatch(prop.identifier, pattern) for pattern in includes):
                continue
        if excludes:
            if any(fnmatch(prop.identifier, pattern) for pattern in excludes):
                continue

        try:
            value = getattr(obj, prop.identifier)
        except AttributeError:
            value = None
        
        if value is None:
            continue

        ## -> in the end, same condition as else below...
        # if isinstance(value, bpy.types.bpy_struct):
        #     ## test inspect sub struct, 
        #     # print(prop, value) # Show struct name
        #     if recursion_limit and ct+1 >= recursion_limit:
        #         continue
        #     list_attr(f'{path}.{prop}', ct+1, data=data,
        #               recursion_limit=recursion_limit, get_default=get_default, skip_readonly=skip_readonly)
        #     continue

        ## No support for collection yet
        if isinstance(value, (bpy.types.bpy_prop_collection, bpy.types.bpy_prop_array)): # , bpy.types.bpy_struct
            continue
        
        if skip_readonly and prop.is_readonly:
            if not isinstance(value, bpy.types.bpy_struct):
                # struct container are always readonly, do not in those cases
                # print('readonly:', path, prop)
                continue

        if isinstance(value, known_types):
            if get_default:
                # data[repr(obj.path_resolve(prop.identifier, False))] = convert_attr(prop.default)
                data[f'{rna_path_step}.{prop.identifier}']= convert_attr(prop.default)
            else:
                ## "Repr" is truncating data_path ! Need to pass a rna_path_step 
                # data[f'{repr(obj)}.{prop.identifier}'] = convert_attr(value)
                # data[repr(obj.path_resolve(prop.identifier, False))] = convert_attr(value)
                data[f'{rna_path_step}.{prop.identifier}'] = convert_attr(value)

        else:
            if recursion_limit and ct+1 >= recursion_limit:
                continue

            # print('>>', [f'{path}.{prop}', convert_attr(value), type(value)])
            list_attr(value,
                      f'{rna_path_step}.{prop.identifier}',
                      ct+1,
                      data=data,
                      recursion_limit=recursion_limit, get_default=get_default, skip_readonly=skip_readonly, includes=includes, excludes=excludes)

    return data

def get_version_name():
    version = bpy.app.version
    return f'bl-{version[0]}_{version[1]}'


""" def list_attr(path, ct=0, l=None, recursion_limit=0, get_default=False, skip_readonly=True, includes=None, excludes=None):
    '''
    List recursively attribute and their value at passed data_path and return a serializable dict

    path (str): data_path to get 
    recursion_limit (int, default: 0): 0 no limit, 1 mean
    get_default (bool, default: False): get default property value intead of current value
    skip_readonly (bool, default: True): Do not list readonly
    includes (list, str) : String or list of strings fnmatch pattern, include attribute if match
    excludes (list, str) : String or list of strings fnmatch pattern, exclude attribute if match
    '''

    if includes:
        if not isinstance(includes, list):
            includes = [includes]
    if excludes:
        if not isinstance(excludes, list):
            excludes = [excludes]

    if l is None:
        l = {}

    ## TODO: use objects instead of strings
    path_obj = eval(path)
    for attr in dir(path_obj):
        print('>', path, attr)
        if attr.startswith('__') or attr in basic_exclusions:
            continue

        # if path.endswith('context.preferences') and attr in root_exclusions:
        #     continue
        
        ## Filters
        if includes:
            if not any(fnmatch(attr, pattern) for pattern in includes):
                continue
        if excludes:
            if any(fnmatch(attr, pattern) for pattern in excludes):
                continue

        try:
            value = getattr(path_obj, attr)
        except AttributeError:
            value = None
        
        if value is None:
            continue

        if callable(value):
            continue

        ## -> in the end, same condition as else below...
        # if isinstance(value, bpy.types.bpy_struct):
        #     ## test inspect sub struct, 
        #     # print(attr, value) # Show struct name
        #     if recursion_limit and ct+1 >= recursion_limit:
        #         continue
        #     list_attr(f'{path}.{attr}', ct+1, l=l,
        #               recursion_limit=recursion_limit, get_default=get_default, skip_readonly=skip_readonly)
        #     continue

        ## No support for collection yet
        if isinstance(value, (bpy.types.bpy_prop_collection, bpy.types.bpy_prop_array)): # , bpy.types.bpy_struct
            continue
        
        if skip_readonly and path_obj.bl_rna.properties[attr].is_readonly:
            if not isinstance(value, bpy.types.bpy_struct):
                # struct container are readonly
                print('readonly:', path, attr)
                continue
            print('struct:', path, attr)

        if isinstance(value, known_types):
            if get_default:
                # print(attr, value, path_obj.bl_rna.properties[attr].default)
                l[f'{path}.{attr}'] = convert_attr(path_obj.bl_rna.properties[attr].default)
            else:
                l[f'{path}.{attr}'] = convert_attr(value)

        else:
            if recursion_limit and ct+1 >= recursion_limit:
                continue

            # print('>>', [f'{path}.{attr}', convert_attr(value), type(value)])
            # Comment this call to kill recursion
            list_attr(f'{path}.{attr}', ct+1, l=l,
                      recursion_limit=recursion_limit, get_default=get_default, skip_readonly=skip_readonly, includes=includes, excludes=excludes)

    return l """

""" ## old_method passing data_path as string
    viewport_options = ('overlay', 'shading')
    for part in viewport_options:
        prop_dic[part] = fn.list_attr(f"bpy.context.space_data.{part}")

    inc = ['show_object_*', 'show_region_*', 'show_gizmo_*']
    prop_dic['space_data'] = fn.list_attr(f"bpy.context.space_data",
                                                recursion_limit=1,
                                                includes=inc)
    
    excl = ['annotation_stroke_placement_view*', 'gpencil_interpolate', 'use_lock_relative']
    prop_dic['tool_settings'] = fn.list_attr(f"bpy.context.scene.tool_settings",
                                                recursion_limit=2,
                                                # includes=[],
                                                excludes=excl)
"""

## -- Fit view with sidebars (Unused yet)

class Rect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def top_left(self):
        return Vector((self.x, self.y))

    @property
    def bottom_left(self):
        return Vector((self.x, self.y - self.height))

    @property
    def bottom_right(self):
        return Vector((self.x + self.width, self.y - self.height))

    @property
    def top_right(self):
        return Vector((self.x + self.width, self.y))
    
    @property
    def center(self):
        return Vector((self.x + self.width / 2, self.y + self.height / 2))

    
    def __str__(self):
        return f'Rect(x={self.x}, y={self.y}, width={self.width}, height={self.height})'

def get_reduced_rect(context):
    '''return a Rect instance representing region coordinate of the frame'''
    area = context.area
    w, h = area.width, area.height
    # if not bpy.context.preferences.system.use_region_overlap:
    #     return w, h

    regions = area.regions
    header = next((r for r in regions if r.type == 'HEADER'), None)
    tool_header = next((r for r in regions if r.type == 'TOOL_HEADER'), None)
    asset_shelf = next((r for r in regions if r.type == 'ASSET_SHELF'), None)
    toolbar = next((r for r in regions if r.type == 'TOOLS'), None)
    sidebar = next((r for r in regions if r.type == 'UI'), None)

    bottom_margin = 0
    up_margin = 0
    if header.alignment == 'BOTTOM':
        bottom_margin += header.height
    else:
        up_margin += header.height

    if tool_header.alignment == 'BOTTOM':
        bottom_margin += tool_header.height
    else:
        up_margin += tool_header.height

    if asset_shelf.height > 1:
        bottom_margin += asset_shelf.height
        ## Header of asset shelf should only be added if shelf open
        # asset_shelf_header = next((r for r in regions if r.type == 'ASSET_SHELF_HEADER'), None)
        # bottom_margin += asset_shelf.height + asset_shelf_header.height

    reduced_x = 0
    reduced_y = 0

    reduced_width = w - sidebar.width - toolbar.width
    reduced_height = h - tool_header.height - 1

    return Rect(toolbar.width, h - reduced_y - 1, reduced_width, reduced_height)
    # return Rect(self.toolbar.width, h - reduced_y - 1, right_down, left_down)


def get_camera_frame_2d(scene=None, camera=None):
    '''return a Rect instance representing camera 2d frame region coordinate'''
    if scene is None:
        scene = bpy.context.scene

    frame_3d = get_cam_frame_world(scene.camera, scene=scene)

    frame_2d = [location_to_region(v) for v in frame_3d]

    rd = scene.render
    resolution_x = rd.resolution_x * rd.pixel_aspect_x
    resolution_y = rd.resolution_y * rd.pixel_aspect_y
    ratio_x = min(resolution_x / resolution_y, 1.0)
    ratio_y = min(resolution_y / resolution_x, 1.0)

    ## Top right - CW
    frame_width = (frame_2d[1].x - frame_2d[2].x) # same size (square)
    frame_height = (frame_2d[0].y - frame_2d[1].y) # same size (square)
    
    cam_width = (frame_2d[1].x - frame_2d[2].x) * ratio_x
    cam_height = (frame_2d[0].y - frame_2d[1].y) * ratio_y
    
    cam_x = frame_2d[3].x - ((frame_width - cam_width) / 2)
    cam_y = frame_2d[3].y - ((frame_height - cam_height) / 2)
    
    return Rect(cam_x, cam_y, cam_width, cam_height)


def fit_view(context=None):
    context = context or bpy.context

    def zoom_from_fac(zoomfac):
        from math import sqrt
        ## sqrt(2) = 1.41421356237309504880
        return (sqrt(4 * zoomfac) - 1.41421356237309504880) * 50.0

    r3d = context.space_data.region_3d
    
    view_frame = get_reduced_rect(context)
    cam_frame = get_camera_frame_2d()
    print('view_frame: ', view_frame)
    print('cam_frame: ', cam_frame)

    ## CENTER
    r3d.view_camera_offset = (0,0) # Center as if always using region overlap

    print('view_frame.width: ', view_frame.width)
    print('cam_frame.width: ', cam_frame.width)
    xfac = view_frame.width / (cam_frame.width + 4.0)
    yfac = view_frame.height / (cam_frame.height + 4.0)

    # xfac = view_frame.width / cam_frame.width
    # yfac = view_frame.height / cam_frame.height

    ## ZOOM
    print('zoom before', r3d.view_camera_zoom) # Dbg
    zoom_value = zoom_from_fac(min(xfac, yfac))
    zoom_value = max(min(zoom_value, 300.0), -30.0) # clamp between -30 and 30
    r3d.view_camera_zoom = zoom_value
    print('zoom after', r3d.view_camera_zoom) # Dbg

def frame_objects(context, target='NONE', objects=None, apply=True):
    '''frame objects in view using BBox
    target (str): string to define what to frame (ALL: GP object + Camera, GP: GP object, ACTIVE: active object)
    objects (list, default:None): alternatively, a list of object to frame can be passed
    apply (bool, default:True): apply the view distance and location, else only return the values

    return: rv3d's (view_distance, view_location)
    '''
    if objects is None:
        if target == 'ACTIVE':
            objects = [context.object]
        else:
            # case of GP or ALL
            objects = [o for o in context.scene.objects if o.type in ('GREASEPENCIL',) and o.visible_get()]

        if target == 'ALL' and context.scene.camera:
            objects.append(context.scene.camera)

        # objects = [o for o in context.view_layer.objects if o.type in ('GREASEPENCIL',) and o.visible_get()]
    if not objects:
        return {'CANCELLED'}

    # with context.temp_override(active=objects[0], selected_objects=objects, selected_editable_objects=objects, selected_ids=objects):
    #     # bpy.ops.view3d.view_selected('INVOKE_DEFAULT', use_all_regions=False)
    #     bpy.ops.view3d.view_selected()

    ## as of 4.1.1 override do not works with view3d.view_selected : https://projects.blender.org/blender/blender/issues/112141
    ## Trying a full homemade method

    # calculate x/y Bbox
    global_bbox = [ob.matrix_world @ Vector(v) for ob in objects for v in ob.bound_box]
    # global_bbox_center = Vector(np.mean(global_bbox, axis=0))
    sorted_x = sorted(global_bbox,key = lambda x : x.x)
    sorted_y = sorted(global_bbox,key = lambda x : x.y)
    sorted_z = sorted(global_bbox,key = lambda x : x.z)

    down_left = Vector((sorted_x[0].x, sorted_y[0].y, sorted_z[0].z))
    top_right = Vector((sorted_x[-1].x, sorted_y[-1].y, sorted_z[-1].z))
    
    global_bbox_center = (down_left + top_right) / 2
    # bbox_2d = [sorted_x[0].x, sorted_x[-1].x, sorted_y[0].y, sorted_y[-1].y]

    ## Debug
    # context.scene.cursor.location = down_left
    # fn.empty_at(down_left, name='DL', size=0.2)
    # fn.empty_at(top_right, name='TR', size=0.2)

    width = sorted_x[-1].x - sorted_x[0].x
    height = sorted_y[-1].y - sorted_y[0].y
    val = width if width > height else height
    
    if target == 'ACTIVE':
        ## Specifically for active object, dezoom a little
        val *= 1.2 # Add 20% margin

    # if (down_left.xy - top_right.xy).length < 1.0:
    val = max(val, 2.0) # Clamp to 2.0 as minimum value

    z_loc = context.region_data.view_location.z
    if context.region_data.view_location.z < top_right.z:
        z_loc = top_right.z + 0.2

    if apply:
        ## Set center and view distance 
        context.region_data.view_location.xy = global_bbox_center.xy
        context.region_data.view_distance = val

        context.region_data.view_location.z = z_loc
    
    return val, Vector((global_bbox_center.x, global_bbox_center.y, z_loc))