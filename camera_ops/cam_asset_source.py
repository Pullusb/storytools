"""Camera data assets

UNUSED, replaced by the the Native asset browser with 'Browse Camera Assets' and button "Add To View' in its header.

Previous integration of the feature:
The scan is called in invoke() and the asset in draw() and execute()
  (get_camera_assets, get_all_asset_entries, get_camera_asset_entry, load_camera_asset_data)

In Properties:
    source : bpy.props.EnumProperty(
        name='Source',
        description="Choose the camera data used by the new camera",
        items=(
            ('NEW', 'New', 'Create a new camera data using addon preferences defaults', 'CAMERA_DATA', 0),
            ('ASSET', 'Asset', 'Use a copy of a camera data marked as asset in this file or in your asset libraries', 'ASSET_MANAGER', 1),
            ),
        update=update_camera_source)

    asset : bpy.props.EnumProperty(
        name='Camera Asset',
        description="Camera data marked as asset, found in your asset libraries or in current file",
        items=camera_asset_enum_items,
        update=update_camera_asset)

In invoke:
        
        if self.source == 'ASSET':
            ## Source is kept between calls, scan if it was not done yet in this session
            get_camera_assets()
            ## Name after the selected asset (fallback on default name if it disappeared)
            update_camera_asset(self, context)

In Draw:
        layout.row().prop(self, 'source', expand=True)
        if self.source == 'ASSET':
            ...

"""

import bpy
import os
from pathlib import Path

from .. import fn

## Default name of a new camera, kept in cam_create (used by update_camera_source below)
from .cam_create import get_default_camera_name


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
    """Return a list of (library_name, library_root, blend_path) for every blend of the enabled asset libraries"""
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
    """Return the names of the camera data marked as asset in blend, None if unreadable"""
    try:
        with bpy.data.libraries.load(str(blend), assets_only=True, link=False) as (data_from, _data_to):
            return sorted(data_from.cameras)
    except Exception as e:
        print(f'Storytools: Could not read camera assets in "{blend}": {e}')
        return None


## Result of the last library scan: list of entries as
## {'id': str, 'name': str, 'blend': str, 'library': str, 'relative': str, 'local': bool}
_ASSET_ENTRIES = []

## Items returned by the EnumProperty callback (must be kept alive on the python side)
_ENUM_ITEMS = []

## True once a scan ran in this session (avoid re-walking libraries on every dialog opening)
_IS_SCANNED = False

## Identifier prefix of the assets living in the current file
LOCAL_PREFIX = 'LOCAL::'

def get_camera_assets():
    """Fill _ASSET_ENTRIES global variable (once per session) to be read by enum update"""
    global _ASSET_ENTRIES, _IS_SCANNED
    if _IS_SCANNED:
        return

    _IS_SCANNED = True
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
                'local': False,
                })

    entries.sort(key=lambda e: (e['library'], e['relative'], e['name']))
    _ASSET_ENTRIES = entries

def get_local_camera_assets() -> list:
    """Return the entries for camera data marked as asset in the current file.
    Read live from bpy.data (cheap, always up to date), so this needs no scan or cache"""
    return [{
        'id': f'{LOCAL_PREFIX}{cam.name}',
        'name': cam.name,
        'blend': '',
        'library': 'Current File',
        'relative': '',
        'local': True,
        } for cam in sorted(bpy.data.cameras, key=lambda c: c.name) if cam.asset_data]

def get_all_asset_entries() -> list:
    """Return the library assets of the last scan, followed by the current file ones"""
    ## The current file may also be inside a library: skip its scanned (on disk, possibly
    ## outdated) version, local data is listed instead
    current = Path(bpy.path.abspath(bpy.data.filepath)) if bpy.data.filepath else None
    entries = [e for e in _ASSET_ENTRIES if not current or Path(e['blend']) != current]
    return entries + get_local_camera_assets()

def load_camera_asset_data(entry):
    """Return a local copy of the camera data described by entry, None if it could not be loaded.
    Local assets are directly duplicated, library ones are appended from their blend"""
    if entry['local']:
        source = bpy.data.cameras.get(entry['name'])
        if not source or not source.asset_data:
            return None
        cam_data = source.copy()
        fn.clear_asset_metadata(cam_data)
        return cam_data

    blend = Path(entry['blend'])
    data_name = entry['name']
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
    fn.clear_asset_metadata(cam_data)
    return cam_data

def get_camera_asset_entry(identifier) -> dict:
    """Return the camera asset entry matching an enum identifier, None if not found"""
    if not identifier:
        return None
    return next((e for e in get_all_asset_entries() if e['id'] == identifier), None)

def camera_asset_enum_items(self, context):
    """Items callback listing camera assets of last library scan and current file.
    Called on every redraw"""
    global _ENUM_ITEMS

    entries = get_all_asset_entries()
    if not entries:
        _ENUM_ITEMS = [('NONE', 'No Camera Asset Found', 'No camera data marked as asset was found in this file or in your asset libraries')]
        return _ENUM_ITEMS

    ## Same camera name can exists in multiple blends, show the source file in this case
    names = [e['name'] for e in entries]
    _ENUM_ITEMS = []
    for i, entry in enumerate(entries):
        label = entry['name']
        if entry['local']:
            ## Current file assets are listed last, always tag them (no scan or save needed)
            label = f'{label} [Current File]'
            description = f'Camera asset "{entry["name"]}" from the current file'
            icon = 'FILE_BLEND'
        else:
            if names.count(label) > 1:
                label = f'{label}  [{Path(entry["blend"]).stem}]'
            description = f'Camera asset "{entry["name"]}" from library "{entry["library"]}"\n{entry["relative"]}'
            icon = 'CAMERA_DATA'
        _ENUM_ITEMS.append((entry['id'], label, description, icon, i))

    return _ENUM_ITEMS

def update_camera_asset(self, context):
    """Name the new camera object after the selected asset"""
    entry = get_camera_asset_entry(self.asset)
    if entry:
        self.name = entry['name']

def update_camera_source(self, context):
    """Trigger asset libraries scan when switching to asset source
    and keep the camera name in sync with the source"""
    if self.source == 'ASSET':
        get_camera_assets()
        update_camera_asset(self, context)
    else:
        self.name = get_default_camera_name()
