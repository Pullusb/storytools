# SPDX-License-Identifier: GPL-2.0-or-later

import json
from math import pi
from pathlib import Path

import bpy
import numpy as np
from bpy_extras import view3d_utils
from mathutils import Matrix, Vector, geometry

from .constants import LAYERMAT_PREFIX


def get_addon_prefs():
    return bpy.context.preferences.addons[__package__].preferences

## Vector

def location_to_region(worldcoords) -> Vector:
    ''' return 2d location '''
    return view3d_utils.location_3d_to_region_2d(
        bpy.context.region, bpy.context.space_data.region_3d, worldcoords)

def region_to_location(viewcoords, depthcoords) -> Vector:
    ''' return normalized 3d vector '''
    return view3d_utils.region_2d_to_location_3d(
        bpy.context.region, bpy.context.space_data.region_3d, viewcoords, depthcoords)

def reset_draw_settings(context=None):
    ## set drawing plane to origin - Front Axis
    context = context or bpy.context
    settings = context.scene.tool_settings
    # 'VIEW', 'AXIS_Y', 'AXIS_X', 'AXIS_Z', 'CURSOR'
    settings.gpencil_sculpt.lock_axis = 'AXIS_Y'
    # 'ORIGIN', 'CURSOR', 'SURFACE', 'STROKE'
    settings.gpencil_stroke_placement_view3d = 'ORIGIN'


def coord_distance_from_view(coord=None, context=None):
    context = context or bpy.context
    coord = coord or context.scene.cursor.location

    rv3d = context.region_data
    view_mat = rv3d.view_matrix.inverted()
    view_point = view_mat @ Vector((0, 0, -1000))
    co = geometry.intersect_line_plane(view_mat.translation, view_point, coord, view_point)
    if co is None:
        return None
    return (co - view_mat.translation).length

def coord_distance_from_cam(coord=None, context=None):
    context = context or bpy.context
    coord = coord or context.scene.cursor.location

    view_mat = context.scene.camera.matrix_world
    view_point = view_mat @ Vector((0, 0, -1000))
    co = geometry.intersect_line_plane(view_mat.translation, view_point, coord, view_point)
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

def compose_matrix(loc, rot, scale):
    loc_mat = Matrix.Translation(loc)
    rot_mat = rot.to_matrix().to_4x4()
    scale_mat = get_scale_matrix(scale)
    return loc_mat @ rot_mat @ scale_mat

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


## GP

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

## -- Palette --

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
    '''Return a tuple for '''
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
        print(f'/!\ material "{mat_name}" not found (for association with layer "{layer.info}")')
        return
    # create custom prop at object level
    ob[LAYERMAT_PREFIX + layer.info] = mat_name

def set_material_by_name(ob, mat_name):
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
    for i, layer in enumerate(ob.data.layers):
        if layer.info == name:
            # print(f':{i}:', m.name, ob.active_material_index)
            ob.data.layers.active_index = i
            return

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


## Animation

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
