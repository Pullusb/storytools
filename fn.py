# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import json
import os
from pathlib import Path
from mathutils import Matrix, Vector, geometry
from bpy_extras import view3d_utils
from math import pi


## Vector

def location_to_region(worldcoords):
    ''' return 2d location '''
    return view3d_utils.location_3d_to_region_2d(
        bpy.context.region, bpy.context.space_data.region_3d, worldcoords)

def region_to_location(viewcoords, depthcoords):
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


def rotate_by_90_degrees(ob, axis='X', negative=True):
    angle = pi/2
    if negative:
        angle += -1
    mat_90 = Matrix.Rotation(angle, 4, axis)
    ob.matrix_world = ob.matrix_world @ mat_90

def get_scale_matrix(scale):
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
