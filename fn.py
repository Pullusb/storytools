# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import json
import math
import numpy as np
from fnmatch import fnmatch
from math import pi, cos, sin
from pathlib import Path

from bpy_extras import view3d_utils
import mathutils
from mathutils import Matrix, Vector, geometry

from .constants import LAYERMAT_PREFIX


def get_addon_prefs():
    return bpy.context.preferences.addons[__package__].preferences

def open_addon_prefs():
    '''Open addon prefs windows with focus on current addon'''
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

## Vector

def location_to_region(worldcoords) -> Vector:
    '''return 2d location'''
    return view3d_utils.location_3d_to_region_2d(
        bpy.context.region, bpy.context.space_data.region_3d, worldcoords)

def region_to_location(viewcoords, depthcoords) -> Vector:
    '''return normalized 3d vector'''
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
    '''Get distance between view origin and plane facing view at coordinate'''
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

## Object

def empty_at(pos, name='Empty', type='PLAIN_AXES', size=1.0, link=True):
    '''
    Create an empty at given Vector3 position.
    pos (Vector3): position 
    name (str, default Empty): name of the empty object
    type (str, default 'PLAIN_AXES'): options in 'PLAIN_AXES','ARROWS','SINGLE_ARROW','CIRCLE','CUBE','SPHERE','CONE','IMAGE'
    size (int, default 1.0): Size of the empty
    link (Bool,default True): Link to active collection
    i.e : empty_at((0,0,1), 'ARROWS', 2) creates "Empty" at Z+1, of type gyzmo and size 2
    '''

    mire = bpy.data.objects.new(name, None)
    if link:
        bpy.context.collection.objects.link(mire)
    mire.empty_display_type = type
    mire.empty_display_size = size
    mire.location = pos
    return mire

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

## ---
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


## UI

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


def is_minimap_viewport(context=None):

    ## check if in quad view
    # if context.space_data.region_quadviews:
    #     return False

    ## specific combination to identify as map viewport (Arbitrary)
    if context.space_data.show_object_viewport_lattice or context.space_data.show_object_viewport_light_probe:
        return False

    ## check if locked
    if not context.region_data.lock_rotation:
        return False

    ## check if looking down
    euler_view = context.region_data.view_matrix.to_euler()
    if euler_view[1] != 0.0 or euler_view[1] != 0.0:
        return False
    
    ## Check if ortho view
    if context.region_data.view_perspective != 'ORTHO':
        return False
    
    ## TODO : additional check with view settings combination to identify map viewport

    return True

def get_headers_bottom_width(context, overlap=False) -> int:
    '''Return margin of bottom aligned headers
    (Possible regions: HEADER, TOOL_HEADER, ASSET_SHELF, ASSET_SHELF_HEADER)
    '''
    if not context.preferences.system.use_region_overlap:
        return 0

    bottom_margin = 0
    ## asset shelf header should be only added only if shelf deployed
    regions = context.area.regions
    header = next((r for r in regions if r.type == 'HEADER'), None)
    tool_header = next((r for r in regions if r.type == 'TOOL_HEADER'), None)
    asset_shelf = next((r for r in regions if r.type == 'ASSET_SHELF'), None)

    if header.alignment == 'BOTTOM':
        bottom_margin += header.height
    if tool_header.alignment == 'BOTTOM':
        bottom_margin += tool_header.height
    
    if asset_shelf.height > 1:
        
        if not overlap:
            ## Header of asset shelf should only be added if shelf open
            asset_shelf_header = next((r for r in regions if r.type == 'ASSET_SHELF_HEADER'), None)
            bottom_margin += asset_shelf.height + asset_shelf_header.height
        else:
            ## Only if toggle icon is centered
            bottom_margin += asset_shelf.height

    # for r in context.area.regions:
    #     ## 'ASSET_SHELF_HEADER' is counted even when not visible
    #     if r.alignment == 'BOTTOM' and r.type != 'ASSET_SHELF_HEADER':
    #         bottom_margin += r.height
    
    return bottom_margin

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

    gp_index = next((i for i, o in enumerate(scn.objects) if o.type == 'GPENCIL' and context.object == o), None)
    if gp_index is not None:
        scn.gp_object_props['index'] = gp_index

## keymap UI

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
    col = _indented_layout(layout, 0)
    # col = layout.column()
    if kmi.show_expanded:
        col = col.column(align=True)
        box = col.box()
    else:
        box = col.column()

    split = box.split()

    row = split.row(align=True)
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
        ops = row.operator("storytools.restore_keymap_item", text="", icon='BACK') # modified
        ops.km_name = km.name
        ops.kmi_id = kmi.id
        # ops.kmi_name = kmi.idname

        ## keyitem_restore is not accessible in addon prefs
        # row.operator('preferences.keyitem_restore', text="", icon='BACK').item_id = kmi.id
    else:
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


## Property dump

def convert_attr(Attr):
    '''Convert given value to a Json serializable format'''
    if isinstance(Attr, (mathutils.Vector, mathutils.Color)):
        return Attr[:]
    elif isinstance(Attr, mathutils.Matrix):
        return [v[:] for v in Attr]
    elif isinstance(Attr,bpy.types.bpy_prop_array):
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

known_types = (int, float, bool, str, set, mathutils.Vector, mathutils.Color, mathutils.Matrix)


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
    zoom_value = max(min(zoom_value, 30.0), -30.0) # clamp between -30 and 30
    r3d.view_camera_zoom = zoom_value
    print('zoom after', r3d.view_camera_zoom) # Dbg
