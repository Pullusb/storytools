import bpy

from math import pi
from mathutils import Vector, Matrix

from bpy.types import Operator

from .. import fn

# region asset loading

## Asset id_type -> matching bpy.data collection (same name is used by libraries.load)
ASSET_ID_TYPES = {
    'OBJECT': 'objects',
    'COLLECTION': 'collections',
    'ARMATURE': 'armatures',
    'CAMERA': 'cameras',
    'CURVE': 'curves',
    'CURVES': 'hair_curves',
    'FONT': 'fonts',
    'GREASEPENCIL': 'grease_pencils',
    'LATTICE': 'lattices',
    'LIGHT': 'lights',
    'LIGHT_PROBE': 'lightprobes',
    'MESH': 'meshes',
    'META': 'metaballs',
    'POINTCLOUD': 'pointclouds',
    'SPEAKER': 'speakers',
    'VOLUME': 'volumes',
}

def get_import_method(space) -> str:
    """Return the import method of the asset browser: 'LINK', 'APPEND' or 'APPEND_REUSE'
    ('FOLLOW_PREFS' is resolved using the library settings in the preferences)"""
    params = space.params
    method = getattr(params, 'import_method', 'APPEND')
    if method != 'FOLLOW_PREFS':
        return method

    library = bpy.context.preferences.filepaths.asset_libraries.get(params.asset_library_reference)
    return library.import_method if library else 'APPEND'

def load_asset_id(name, data_field, library_path, local_id, link=False):
    """Return the data-block to instantiate for an asset, None if it could not be loaded.
    Library assets are appended (or linked), assets of the current file are returned as is"""
    if local_id is not None:
        return local_id

    try:
        with bpy.data.libraries.load(library_path, assets_only=True, link=link) as (data_from, data_to):
            if name not in getattr(data_from, data_field):
                return None
            setattr(data_to, data_field, [name])
    except Exception as e:
        print(f'Storytools: Could not load asset "{name}" from "{library_path}": {e}')
        return None

    loaded = getattr(data_to, data_field)
    return loaded[0] if loaded else None

def clear_appended_asset_metadata(id_data):
    """Clear the asset metadata of an appended data-block and of the data it brought along
    (as blender's own append does): appending a collection asset also brings its objects,
    which would otherwise stay listed as assets of the current file"""
    fn.clear_asset_metadata(id_data)

    if isinstance(id_data, bpy.types.Collection):
        objects = id_data.all_objects
    elif isinstance(id_data, bpy.types.Object):
        objects = [id_data]
    else:
        return

    for ob in objects:
        fn.clear_asset_metadata(ob)
        if ob.data:
            fn.clear_asset_metadata(ob.data)

# endregion asset loading

# region viewport search

def get_view3d_spaces(screen):
    """Yield the (area, space_data) of the 3D viewports of a screen, skipping storytools minimaps"""
    for area in screen.areas:
        if area.type != 'VIEW_3D':
            continue
        space = area.spaces.active
        if not space.region_3d:
            ## Region data is not initialised yet (area never drawn)
            continue
        if fn.is_minimap_viewport(space_data=space):
            continue
        yield area, space

def area_center(area) -> Vector:
    return Vector((area.x + area.width / 2, area.y + area.height / 2))

def get_nearest_view3d(context):
    """Return the (window, area, space_data) of the 3D viewport adjacent to current area.
    Search in current screen first (nearest area), then in the other opened windows (biggest area)
    Return None if there is no usable viewport"""

    candidates = list(get_view3d_spaces(context.screen))
    if candidates:
        if context.area:
            center = area_center(context.area)
            candidates.sort(key=lambda c: (area_center(c[0]) - center).length)
        return (context.window, *candidates[0])

    ## Fallback: viewport in another window (asset browser used in its own window)
    for window in context.window_manager.windows:
        if window.screen == context.screen:
            continue
        others = sorted(get_view3d_spaces(window.screen),
                        key=lambda c: c[0].width * c[0].height, reverse=True)
        if others:
            return (window, *others[0])

    return None

def get_view_matrix(scene, rv3d) -> Matrix:
    """Return the world matrix of the viewport point of view
    (active camera matrix when the viewport is in camera view)"""
    if rv3d.view_perspective == 'CAMERA' and scene.camera:
        return scene.camera.matrix_world.copy()
    return rv3d.view_matrix.inverted()

# endregion viewport search


class STORYTOOLS_OT_asset_add_to_view(Operator):
    bl_idname = "storytools.asset_add_to_view"
    bl_label = "Add Asset Aligned To View"
    bl_description = "Add active asset to the scene, aligned with adjacent 3D view\
        \nA camera is placed right at view point and becomes the active camera\
        \nOther assets are placed in front of the view"
    bl_options = {"REGISTER", "UNDO"}

    enter_camera : bpy.props.BoolProperty(
        name='Enter Camera',
        description="When the added asset is a camera, look through it once placed",
        default=True)

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if not space or space.type != 'FILE_BROWSER' or space.browse_mode != 'ASSETS':
            cls.poll_message_set('Only available in an asset browser')
            return False
        if not getattr(context, 'asset', None):
            cls.poll_message_set('No active asset')
            return False
        return True

    def execute(self, context):
        asset = getattr(context, 'asset', None)
        if not asset:
            self.report({'ERROR'}, 'No active asset')
            return {"CANCELLED"}

        ## Asset representation can be invalidated by the library load, read everything needed now
        asset_name = asset.name
        id_type = asset.id_type
        library_path = asset.full_library_path
        local_id = asset.local_id

        data_field = ASSET_ID_TYPES.get(id_type)
        if not data_field:
            self.report({'ERROR'}, f'Cannot add a "{id_type}" asset in the scene')
            return {"CANCELLED"}

        view = get_nearest_view3d(context)
        if not view:
            self.report({'ERROR'}, 'No 3D viewport found to align the asset with')
            return {"CANCELLED"}
        window, area, view_space = view

        ## Viewport can live in another window, using another scene
        scn = window.scene
        view_layer = window.view_layer
        rv3d = view_space.region_3d

        ## Only a collection can be linked: linked objects are not editable, so they would
        ## ignore the view placement (blender's own asset drop behaves the same way)
        link = id_type == 'COLLECTION' and get_import_method(context.space_data) == 'LINK'

        id_data = load_asset_id(asset_name, data_field, library_path, local_id, link=link)
        if id_data is None:
            source = library_path or 'current file'
            self.report({'ERROR'}, f'Could not load asset "{asset_name}" from {source}')
            return {"CANCELLED"}

        ## Only appended data is cleaned up: an asset of the current file must stay an asset
        ## (a copy is cleared instead, its source data is left untouched)
        if id_type == 'COLLECTION':
            ## Instanced through an empty: the collection itself has no transform
            if local_id is None:
                clear_appended_asset_metadata(id_data)
            ob = bpy.data.objects.new(id_data.name, None)
            ob.instance_type = 'COLLECTION'
            ob.instance_collection = id_data

        elif id_type == 'OBJECT':
            if local_id is None:
                ob = id_data
                clear_appended_asset_metadata(ob)
            else:
                ## Asset of the current file: instantiate a copy, sharing data as an Alt+D duplicate
                ob = id_data.copy()
                fn.clear_asset_metadata(ob)

        else:
            ## Object data asset (camera, mesh, grease pencil...): wrap it in a new object
            ob_data = id_data.copy() if local_id is not None else id_data
            fn.clear_asset_metadata(ob_data)
            ob = bpy.data.objects.new(ob_data.name, ob_data)

        is_camera = ob.type == 'CAMERA'

        ## Cameras are grouped in the camera collection of the scene, as storytools created ones
        if is_camera:
            collection = fn.get_camera_collection(scn)
        else:
            collection = view_layer.active_layer_collection.collection
        collection.objects.link(ob)

        ## Placement: camera goes right at the view point, other assets in front of the view
        view_matrix = get_view_matrix(scn, rv3d)
        _view_loc, view_rot, _view_scale = view_matrix.decompose()
        ## Keep the asset own scale, only location and rotation are defined by the view
        _loc, _rot, scale = ob.matrix_world.decompose()

        if is_camera:
            location = view_matrix.translation
        else:
            # TODO: opt: expose initial_distance distance value ?
            location = view_matrix @ Vector((0.0, 0.0, -scn.storytools_settings.initial_distance))
            if ob.type == 'GREASEPENCIL':
                ## Same correction as a new storytools drawing, so the canvas faces the view
                view_rot = (view_rot.to_matrix().to_4x4() @ Matrix.Rotation(-pi/2, 4, 'X')).to_quaternion()

        ob.matrix_world = Matrix.LocRotScale(location, view_rot, scale)

        ## Changing the active object while painting/drawing would break the mode
        active = view_layer.objects.active
        if ob.name in view_layer.objects and (active is None or active.mode == 'OBJECT'):
            for other in list(view_layer.objects.selected):
                other.select_set(False)
            ob.select_set(True)
            view_layer.objects.active = ob

        if is_camera:
            scn.camera = ob
            if self.enter_camera:
                rv3d.view_perspective = 'CAMERA'

        if scn == context.scene:
            fn.update_ui_prop_index(context)
        area.tag_redraw()

        self.report({'INFO'}, f'{ob.name} Added')
        return {"FINISHED"}


def asset_browser_header_button(self, context):
    """Storytools button added in the asset browser header, next to the editor menus.
    Appending to header would place right most of the header, less accessible"""
    layout = self.layout
    layout.separator()
    layout.operator('storytools.asset_add_to_view', text='Add To View', icon='ADD')


classes=(
STORYTOOLS_OT_asset_add_to_view,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(asset_browser_header_button)

def unregister():
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(asset_browser_header_button)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
