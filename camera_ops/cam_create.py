import bpy
import os
from pathlib import Path
from bpy.types import Operator

from .. import fn

## region scan camera as asset
def recursive_scan_ext(fp, ext=('.blend',), depth=-1, skip_hidden=False, files=None) -> list:
    """Recursively collect files matching an extension.

    Args:
        fp (str | Path): Directory to scan.
        ext (str | tuple[str]): Lowercase extension(s), dot included.
        depth (int): 0=no recursion, 1=one sublevel, -1=unlimited.
        skip_hidden (bool): Do not descend into directories starting with a dot.
        files (list | None): Accumulator, created if None.

    Returns:
        list[Path]: Matching files.
    """
    files = [] if files is None else files
    append = files.append
    subdirs = []

    try:
        with os.scandir(fp) as it:
            for f in it:
                try:
                    if f.is_dir(follow_symlinks=False):
                        if skip_hidden and f.name.startswith('.'):
                            continue
                        subdirs.append(f.path)
                    elif f.name.lower().endswith(ext):
                        append(Path(f))
                except OSError:
                    continue
    except OSError:
        return files

    if depth != 0:
        for d in subdirs:
            recursive_scan_ext(d, ext=ext, depth=depth - 1, skip_hidden=skip_hidden, files=files)

    return files


def get_library_blends() -> list:
    '''Return a list of (library_name, library_root, blend_path) for every blend of the enabled asset libraries'''
    blends = []
    for lib in bpy.context.preferences.filepaths.asset_libraries:
        if not lib.enabled or not lib.path:
            continue
        root = Path(bpy.path.abspath(lib.path))
        if not root.is_dir():
            continue
        blends += [(lib.name, root, b) for b in sorted(recursive_scan_ext(root, ext='.blend', skip_hidden=True))]
    return blends

## scan cams from blend path
def read_blend_camera_assets(blend) -> list:
    '''Return the names of the camera data marked as asset in blend, None if unreadable'''
    if bpy.data.filepath and Path(bpy.data.filepath) == blend:
        ## Current file: use local data (the version on disk may be outdated)
        return sorted(cam.name for cam in bpy.data.cameras if cam.asset_data)

    try:
        with bpy.data.libraries.load(str(blend), assets_only=True, link=False) as (data_from, _data_to):
            return sorted(data_from.cameras)
    except Exception as e:
        print(f'Storytools: Could not read camera assets in "{blend}": {e}')
        return None


## Result of the last scan: list of entries as
## {'id': str, 'name': str, 'blend': str, 'library': str, 'relative': str}
_ASSET_ENTRIES = []

## Items returned by the EnumProperty callback (must be kept alive on the python side)
_ENUM_ITEMS = []

## True once a scan ran in this session (avoid re-walking libraries on every dialog opening)
_IS_SCANNED = False

def invalidate_cache():
    """Force the next get_camera_assets() call to rescan the libraries.
    Called when the asset list of the current file changed (mark/clear camera data asset)"""
    global _IS_SCANNED
    _IS_SCANNED = False

def get_camera_assets():
    """Fill _ASSET_ENTRIES global variable (once per session) to be read by enum update"""
    global _ASSET_ENTRIES, _IS_SCANNED
    if _IS_SCANNED:
        return

    _IS_SCANNED = True
    # current_file = Path(bpy.data.filepath) if bpy.data.filepath else None
    seen = set()
    entries = []
    for lib_name, root, blend in get_library_blends():
        key = str(blend)
        if key in seen:
            ## same blend reachable from two (nested) libraries
            continue
        seen.add(key)
        names = read_blend_camera_assets(blend)
        if not names:
            ## Unreadable blend (returned None) or no camera asset in it
            continue
        for name in names:
            entries.append({
                'id': f'{key}::{name}',
                'name': name,
                'blend': key,
                'library': lib_name,
                'relative': blend.relative_to(root).as_posix(),
                })

    entries.sort(key=lambda e: (e['library'], e['relative'], e['name']))
    _ASSET_ENTRIES = entries

def load_camera_asset_data(blend_path, data_name):
    '''Append a local copy of the camera data named data_name from blend_path.
    Return the new camera data, None if it could not be loaded'''
    blend = Path(blend_path)

    if bpy.data.filepath and Path(bpy.data.filepath) == blend:
        ## Asset lives in the current file, just duplicate it
        source = bpy.data.cameras.get(data_name)
        return source.copy() if source else None

    try:
        with bpy.data.libraries.load(str(blend), assets_only=True, link=False) as (data_from, data_to):
            if data_name not in data_from.cameras:
                return None
            data_to.cameras = [data_name]
    except Exception as e:
        print(f'Storytools: Could not append camera asset "{data_name}" from "{blend}": {e}')
        return None

    if not data_to.cameras:
        return None

    cam_data = data_to.cameras[0]
    ## An appended asset keeps its asset metadata and gets a fake user.
    ## Clear both (as blender's own asset append does): this local copy is a plain camera data
    if cam_data.asset_data:
        cam_data.asset_clear()
    cam_data.use_fake_user = False
    return cam_data

def get_camera_asset_entry(identifier) -> dict:
    '''Return the camera asset entry matching an enum identifier, None if not found'''
    if not identifier:
        return None
    return next((e for e in _ASSET_ENTRIES if e['id'] == identifier), None)

def camera_asset_enum_items(self, context):
    '''Items callback listing camera assets found by the last scan.
    Called on every redraw'''
    global _ENUM_ITEMS

    if not _ASSET_ENTRIES:
        _ENUM_ITEMS = [('NONE', 'No Camera Asset Found', 'No camera data marked as asset was found in your asset libraries')]
        return _ENUM_ITEMS

    ## Same camera name can exists in multiple blends, show the source file in this case
    names = [e['name'] for e in _ASSET_ENTRIES]
    _ENUM_ITEMS = []
    for i, entry in enumerate(_ASSET_ENTRIES):
        label = entry['name']
        if names.count(label) > 1:
            label = f'{label}  [{Path(entry["blend"]).stem}]'
        _ENUM_ITEMS.append((
            entry['id'], label,
            f'Camera asset "{entry["name"]}" from library "{entry["library"]}"\n{entry["relative"]}',
            'CAMERA_DATA', i))

    return _ENUM_ITEMS

def update_camera_source(self, context):
    '''Trigger asset libraries scan when switching to asset source'''
    if self.source == 'ASSET':
        get_camera_assets()

# endregion scan blend camera as asset

class STORYTOOLS_OT_create_camera(Operator):
    bl_idname = "storytools.create_camera"
    bl_label = "Create Camera"
    bl_description = "Create a camera with popup choices"
    bl_options = {"REGISTER", "UNDO"}

    name : bpy.props.StringProperty(
        name='Name',
        description="Name of Grease pencil object")

    source : bpy.props.EnumProperty(
        name='Source',
        description="Choose the camera data used by the new camera",
        items=(
            ('NEW', 'New', 'Create a new camera data using addon preferences defaults', 'CAMERA_DATA', 0),
            ('ASSET', 'Asset', 'Use a copy of a camera data marked as asset in your asset libraries', 'ASSET_MANAGER', 1),
            ),
        update=update_camera_source)

    asset : bpy.props.EnumProperty(
        name='Camera Asset',
        description="Camera data marked as asset, found in your asset libraries",
        items=camera_asset_enum_items)

    create_marker : bpy.props.BoolProperty(
        name='Create Marker',
        description="Create a camera timeline marker\
             \nActive camera will be changed at this marker",
        default=False, options={'SKIP_SAVE'})
    
    make_active : bpy.props.BoolProperty(
        name='Make Active',
        description="Make the new camera active",
        default=True)
    
    enter_camera : bpy.props.BoolProperty(
        name='Enter Camera',
        description="Enter in newly created camera view",
        default=True)

    ## Add local Dof toggle (reset by preferences on call)
    # use_dof : bpy.props.BoolProperty(
    #     name='Use Depth Of Field',
    #     description="Use Depth of field (default value can be changed in addon preferences > Settings > Camera)",
    #     default=False)

    def invoke(self, context, event):
        # self.use_dof = fn.get_addon_prefs().default_cam_use_dof
        # cam_ct = len(bpy.data.cameras)
        cam_ct = len([o for o in bpy.data.objects if o.type == 'CAMERA'])
        self.name = f'Camera_{cam_ct+1:03d}'
        
        if any(m.camera for m in context.scene.timeline_markers):
            self.create_marker = True

        if self.source == 'ASSET':
            ## Source is kept between calls, scan if it was not done yet in this session
            get_camera_assets()

        # return self.execute(context)
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, 'name')

        ## Camera data source: brand new or copy of an asset
        layout.row().prop(self, 'source', expand=True)
        if self.source == 'ASSET':
            ## Only use the last scan result here, scanning in draw code is not an option
            assets = _ASSET_ENTRIES
            row = layout.row(align=True)
            if assets:
                row.prop(self, 'asset', text='Camera')
            else:
                row.label(text='No camera asset found', icon='ERROR')
            if not assets:
                col = layout.column(align=True)
                col.label(text='Mark a camera data as asset in a blend', icon='INFO')
                col.label(text='saved inside one of your asset libraries', icon='BLANK1')

        layout.prop(self, 'make_active')
        if context.space_data.region_3d.view_perspective == 'CAMERA':
            col = layout.column(align=True)
            col.label(text='Already in camera view', icon='INFO')
            if self.source == 'ASSET':
                col.label(text='New camera will have same placement', icon='BLANK1')
                col.label(text='Settings come from the camera asset', icon='BLANK1')
            else:
                col.label(text='New camera will have same placement and settings', icon='BLANK1')
        else:
            row = layout.row()
            row.active = self.make_active
            row.prop(self, 'enter_camera')

        # layout.prop(self, 'use_dof')

        row =  layout.row()
        row.prop(self, 'create_marker')
        info = row.operator('storytools.info_note', text='', icon='QUESTION', emboss=False)
        info.title = 'Camera Marker Creation'
        info.text = "This will bind camera to a new marker at current frame\n"\
            "A camera-bound marker changes the active camera when playhead is at marker position\n"\
            "Markers behave like keys,they can be selected/renamed/moved/deleted in timeline editors"
        if any(m.camera for m in context.scene.timeline_markers):
            layout.label(text='There are camera markers in scene', icon='INFO')
            # layout.label(text='A camera marker', icon='BLANK1')
        else:
            if self.create_marker:
                col = layout.column(align=True)
                col.label(text='Add new marker and bind camera at current frame', icon='INFO')


    def execute(self, context):
        already_in_cam = context.space_data.region_3d.view_perspective == 'CAMERA'

        scn = context.scene
        cam_ref = None
        if already_in_cam:
            cam_ref = scn.camera
        
        prefs = fn.get_addon_prefs()

        from_asset = self.source == 'ASSET'
        if from_asset:
            entry = get_camera_asset_entry(self.asset)
            if not entry:
                self.report({'ERROR'}, 'No valid camera asset selected')
                return {"CANCELLED"}
            cam_data = load_camera_asset_data(entry['blend'], entry['name'])
            if not cam_data:
                self.report({'ERROR'}, f'Could not load camera asset "{entry["name"]}" from {entry["blend"]}')
                return {"CANCELLED"}
        else:
            cam_data = bpy.data.cameras.new(self.name)

        cam = bpy.data.objects.new(self.name, cam_data)

        ## When using an asset, all camera settings come from the asset data
        ## (in that case only placement is set, further down)
        if not from_asset:
            if already_in_cam:
                ## Copy settings from previous camera
                cam_data.lens = cam_ref.data.lens
                cam_data.clip_start = cam_ref.data.clip_start
                cam_data.clip_end = cam_ref.data.clip_end
                cam_data.dof.use_dof = cam_ref.data.dof.use_dof
                cam_data.dof.focus_distance = cam_ref.data.dof.focus_distance
                cam_data.dof.aperture_fstop = cam_ref.data.dof.aperture_fstop
            else:
                ## Apply addon preferences camera defaults
                cam_data.lens = prefs.default_cam_lens
                cam_data.clip_start = prefs.default_cam_clip_start
                cam_data.clip_end = prefs.default_cam_clip_end
                cam_data.dof.use_dof = prefs.default_cam_use_dof # self.use_dof

        if already_in_cam:
            cam.matrix_world = cam_ref.matrix_world
        else:
            rv3d = bpy.context.region_data or context.space_data.region_3d
            cam.matrix_world = rv3d.view_matrix.inverted()

        ## Link in active collection or create a dedicated collection for current scene
        ## using scene name in collection name might allow identification on multi_scene...

        camera_collection_name = f'cam_{context.scene.name}'
        cam_col = bpy.data.collections.get(camera_collection_name)
        if not cam_col:
            cam_col = bpy.data.collections.new(camera_collection_name)
            scn.collection.children.link(cam_col)
        cam_col.objects.link(cam)
        
        if self.make_active:
            scn.camera = cam
            if not already_in_cam and self.enter_camera:
                context.space_data.region_3d.view_perspective = 'CAMERA'

        
        if self.create_marker:
            m = scn.timeline_markers.new(name=f'F_{scn.frame_current}', frame=scn.frame_current)
            m.camera = cam
        
        ## update active index in UI (using ['index'] to avoid calling prop update)
        fn.update_ui_prop_index(context)
        # context.scene.st_camera_props['index'] = next((i for i, c in enumerate(scn.objects) if scn.camera == c), 0)

        # new_gp_index = next((i for i, o in enumerate(scn.objects) if o.type == 'GREASEPENCIL' and context.object == o), None)
        # if new_gp_index is not None:
        #     scn.gp_object_props['index'] = new_gp_index

        self.report({'INFO'}, f'{cam.name} Created')
        return {"FINISHED"}


class STORYTOOLS_OT_delete_camera(Operator):
    bl_idname = "storytools.delete_camera"
    bl_label = "Delete Camera"
    bl_description = "Delete active camera"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def execute(self, context):
        name = context.scene.camera.name
        bpy.data.objects.remove(context.scene.camera)
        next_cam = next((o for o in context.scene.objects if o.type == 'CAMERA'), None)
        if next_cam:
            context.scene.camera = next_cam
        
        fn.update_ui_prop_index(context)
        self.report({'INFO'}, f'Camera Removed: "{name}"')
        return {"FINISHED"}


classes = (
    STORYTOOLS_OT_create_camera,
    STORYTOOLS_OT_delete_camera)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)