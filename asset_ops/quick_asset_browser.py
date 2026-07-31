"""Toggle blender asset browser from an operator.
Slpit-open on bottom half of current area.
Specify a kind of asset, cycle its sources (catalog of the user library, whole library, current file).
Specify a search term for Alt + Click
"""

import bpy

from pathlib import Path
from bpy.types import Operator


# region area handling

def area_center(area) -> tuple:
    """Return the window space coordinates of an area center"""
    return (area.x + area.width // 2, area.y + area.height // 2)

def get_asset_browser_below(screen, area, tolerance=10):
    """Return the asset browser directly below given area or None
    Only if area touches bottom edge and cover most of its width"""
    if not area:
        return None

    for other in screen.areas:
        if other == area or other.type != 'FILE_BROWSER':
            continue
        if other.spaces.active.browse_mode != 'ASSETS':
            continue
        ## Areas bounds do not match exactly because of separator
        if abs((other.y + other.height) - area.y) > tolerance:
            continue
        overlap = min(other.x + other.width, area.x + area.width) - max(other.x, area.x)
        if overlap < area.width / 2:
            continue
        return other

    return None

def split_area_as_asset_browser(context, factor=0.3):
    """Split current area horizontally and turn the lower part into an asset browser.
    Return the new asset browser area, None if split failed"""
    src = context.area
    if not src:
        return None

    ## Areas geometry is only recomputed on the next screen refresh, so the new area cannot be
    ## identified by its position right away: compare the area list instead
    known = set(context.screen.areas)
    region = next((r for r in src.regions if r.type == 'WINDOW'), None)

    with context.temp_override(area=src, region=region):
        ## Factor is the position of the horizontal split line. Below 0.5, blender gives the
        ## new area to the lower part, current area keeping the upper one (see 'factor' prop)
        res = bpy.ops.screen.area_split(direction='HORIZONTAL', factor=factor)

    if 'FINISHED' not in res:
        return None

    area = next((a for a in context.screen.areas if a not in known), None)
    if not area:
        return None

    area.ui_type = 'ASSETS'
    return area

def collapse_asset_browser(context, area, browser) -> bool:
    """Collapse the asset browser back into area using ops. Return False on failure"""
    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
    with context.temp_override(area=area, region=region):
        ## Source area expands over the target one, which is the one removed
        res = bpy.ops.screen.area_join(source_xy=area_center(area), target_xy=area_center(browser))
    return 'FINISHED' in res

# endregion area handling


# region libraries and catalogs

def get_user_library():
    """Return the first enabled user asset library, None if nothing in the preferences"""
    return next((lib for lib in bpy.context.preferences.filepaths.asset_libraries
                 if lib.enabled and lib.path), None)

def get_user_library_reference() -> str:
    """Return the asset library reference of the first enabled user library
    Fallback on 'ALL' when no asset library is set in the preferences"""
    library = get_user_library()
    return library.name if library else 'ALL'

def set_asset_library(params, library) -> str:
    """Set the library source of an asset browser, return the reference actually in use"""
    try:
        params.asset_library_reference = library
    except TypeError:
        ## Library name is not a valid enum identifier (should not happen, do not break the setup)
        print(f'Storytools: Could not set asset library to "{library}"')
    return params.asset_library_reference

## Asset catalogs are not exposed to python: read from definition file
## blender's asset system writes at the root of every library (AssetCatalogService)
CATALOG_FILENAME = 'blender_assets.cats.txt'

## Nil uuid: catalog_id when browser shows all catalogs
NIL_CATALOG_ID = '00000000-0000-0000-0000-000000000000'

def read_library_catalogs(library_path) -> list:
    """Parse the catalog definition file of an asset library.
    Return a list of (uuid, catalog path, simple name), empty when there is no catalog file
    Note: catalogs created in the UI are only written on save (Catalog > Save Catalogs)"""
    catalog_file = Path(bpy.path.abspath(library_path)) / CATALOG_FILENAME
    if not catalog_file.is_file():
        return []

    catalogs = []
    try:
        lines = catalog_file.read_text(encoding='utf-8').splitlines()
    except OSError as e:
        print(f'Storytools: Could not read asset catalogs in "{catalog_file}": {e}')
        return []

    for line in lines:
        line = line.strip()
        ## Comments, empty lines and the version marker are not catalog definitions
        if not line or line.startswith(('#', 'VERSION')):
            continue
        ## "UUID:catalog/path/for/assets:simple catalog name"
        parts = line.split(':')
        if len(parts) < 2:
            continue
        catalogs.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ''))

    return catalogs

def find_catalog(names=(), prefix='', library=None) -> tuple:
    """Return the (uuid, path) of the first catalog of a library named after one of names,
    else of the first one starting with prefix. ('', '') when nothing matches.
    Comparison is case insensitive, on the last component of the catalog path (its name)"""
    library = library or get_user_library()
    if not library:
        return ('', '')

    names = tuple(name.lower() for name in names)
    prefix = prefix.lower()

    fallback = ('', '')
    for uuid, path, _simple_name in read_library_catalogs(library.path):
        name = path.rsplit('/', 1)[-1].strip().lower()
        if name in names:
            return (uuid, path)
        if prefix and not fallback[0] and name.startswith(prefix):
            fallback = (uuid, path)

    return fallback

def has_local_object_assets(name_prefixes=(), object_types=()) -> bool:
    """True when the current file holds an object marked as asset of one of object_types,
    or whose name starts with one of name_prefixes (browser is filtered on objects,
    assets of other data types are not listed)"""
    name_prefixes = tuple(prefix.lower() for prefix in name_prefixes)
    object_types = tuple(object_types)

    return any(ob.asset_data
               and (ob.type in object_types or ob.name.lower().startswith(name_prefixes))
               for ob in bpy.data.objects)

def get_asset_sources(kind) -> list:
    """Return the sources the browser cycles through for a kind of asset, in order,
    as a list of (library reference, catalog uuid, label).
    The catalog and the current file steps are only listed when they have something to show,
    so the cycle shrinks down to a single source when there is nothing else"""
    user_library = get_user_library_reference()
    sources = []

    catalog, catalog_path = find_catalog(kind['catalog_names'], kind['catalog_prefix'])
    if catalog:
        sources.append((user_library, catalog, f'{user_library} > {catalog_path}'))

    sources.append((user_library, '', f'{user_library} (all catalogs)'))

    ## Assets of the current file belong to no library, they get their own step
    if has_local_object_assets(kind['name_prefixes'], kind['object_types']):
        sources.append(('LOCAL', '', 'Current File'))

    return sources

# endregion libraries and catalogs

# region browser setup

def setup_asset_browser(area, source, search='', filter_id='filter_object') -> bool:
    """Set an asset browser area to list the assets of a source (see get_asset_sources),
    showing only the data type of filter_id ('filter_object', 'filter_material'...).
    The search field is only used when the source has no catalog to filter the assets out.
    Return False if the space is not initialised yet (params exist after the first draw)"""
    params = area.spaces.active.params
    if params is None:
        return False

    library, catalog, _label = source
    set_asset_library(params, library)
    params.catalog_id = catalog
    if not catalog:
        params.filter_search = search

    ## Single data type: an asset to place in the scene is an object asset
    params.use_filter_blendid = True
    filters = params.filter_asset_id
    for identifier in dir(filters):
        if identifier.startswith(('filter_', 'experimental_filter_')):
            setattr(filters, identifier, identifier == filter_id)

    area.tag_redraw()
    return True

def setup_asset_browser_deferred(area, source, search='', filter_id='filter_object', attempts=5):
    """Apply the asset browser setup on a timer, waiting for the space to be initialised"""
    remaining = [attempts]

    def apply_setup():
        try:
            if setup_asset_browser(area, source, search, filter_id):
                return None
        except ReferenceError:
            ## Area was closed in the meantime
            return None
        remaining[0] -= 1
        return 0.1 if remaining[0] > 0 else None

    bpy.app.timers.register(apply_setup, first_interval=0.1)

def cycle_asset_source(params, sources) -> str:
    """Set the asset browser to the source following the one it currently shows.
    Return a label of the source now in use"""
    ## Where we are in the cycle (a source set by hand in the browser restarts it)
    catalog_id = '' if params.catalog_id == NIL_CATALOG_ID else params.catalog_id
    current = next((i for i, (library, catalog, _label) in enumerate(sources)
                    if library == params.asset_library_reference and catalog == catalog_id), -1)

    library, catalog, label = sources[(current + 1) % len(sources)]
    set_asset_library(params, library)
    params.catalog_id = catalog
    return label

def toggle_search_field(params, search) -> str:
    """Swap the search field of an asset browser between the searched text and nothing.
    Return the text in use"""
    params.filter_search = '' if params.filter_search == search else search
    return params.filter_search

# endregion browser setup


# region browse operator

## Customization for browse button, per kind of asset:
##   label: name of the assets, used in the button tooltip
##   search: text set in the search field when there is no catalog to filter on
##   catalog_names / catalog_prefix: catalog of the user library to select, by exact name first
##   name_prefixes / object_types: what identifies those assets in the current file
##   filter_id: data type listed by the browser, as named in FileAssetSelectParams.filter_asset_id
ASSET_KINDS = {
    'CAMERA': {
        'label': 'Camera',
        'search': 'cam',
        'catalog_names': ('cameras', 'camera'),
        'catalog_prefix': 'cam',
        'name_prefixes': ('cam',),
        'object_types': ('CAMERA',),
        'filter_id': 'filter_object',
        },

    'GREASEPENCIL': {
        'label': 'Grease Pencil',
        'search': 'gp',
        'catalog_names': ('grease pencils', 'grease pencil', 'gpencils', 'gpencil', 'gps', 'gp', 'Drawings'),
        'catalog_prefix': 'gp',
        'name_prefixes': ('gp', 'grease'),
        'object_types': ('GREASEPENCIL',),
        'filter_id': 'filter_object',
        },
    }

## Static items (not a callback): python must keep the strings of an enum alive
ASSET_KIND_ITEMS = tuple(
    (identifier, kind['label'], f"Browse the {kind['label'].lower()} object assets")
    for identifier, kind in ASSET_KINDS.items())


class STORYTOOLS_OT_browse_assets(Operator):
    bl_idname = "storytools.browse_assets"
    bl_label = "Browse Assets"
    bl_options = {"REGISTER", "INTERNAL"}

    ## Blender's area split gives the new area to the lower part only when factor is below 0.5
    ## (above, current area becomes the lower one and would be turned into the asset browser)
    factor : bpy.props.FloatProperty(
        name='Height Factor',
        description="Height of the new asset browser area, as a ratio of current area height",
        default=0.3, min=0.1, max=0.49, options={'SKIP_SAVE'})

    kind : bpy.props.EnumProperty(
        name='Asset Kind',
        description="Kind of asset the browser is set up for",
        items=ASSET_KIND_ITEMS, options={'SKIP_SAVE'})

    search : bpy.props.StringProperty(
        name='Search',
        description="Text set in the search field of the asset browser\
            \nUse the default search of the asset kind when left empty",
        default='', options={'SKIP_SAVE'})

    toggle_search : bpy.props.BoolProperty(
        name='Toggle Search',
        description="Swap the search field between the searched text and nothing (Alt)",
        default=False, options={'SKIP_SAVE'})

    cycle_library : bpy.props.BoolProperty(
        name='Cycle Library',
        description="Cycle the source between the asset catalog, your whole user library\
            \nand the current file when it holds such assets (Ctrl)",
        default=False, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return context.screen and context.area

    @classmethod
    def description(cls, context, properties):
        kind = ASSET_KINDS.get(properties.kind, ASSET_KINDS['CAMERA'])
        label = kind['label']
        return f"Show the {label.lower()} objects of your asset library.\
            \nActivate '{label}' catalog or add '{kind['search']}' in search field.\
            \nClick: Split area to an asset browser or collapse it.\
            \nCtrl + Click: cycle sources: {label} catalog > User Library > Current File(if any {label} assets).\
            \nAlt + Click: Swap the search field between '{kind['search']}' and nothing."

    def invoke(self, context, event):
        self.cycle_library = event.ctrl
        self.toggle_search = event.alt
        return self.execute(context)

    def execute(self, context):
        kind = ASSET_KINDS[self.kind]
        search = self.search or kind['search']

        area = context.area
        ## Only the asset browser opened right below is ours to swap settings on or collapse
        browser = get_asset_browser_below(context.screen, area)

        if browser:
            ## Modifiers swap one setting at a time, leaving the other one as the user set it
            if self.toggle_search or self.cycle_library:
                params = browser.spaces.active.params
                if params is None:
                    ## Area was just created and not drawn yet: apply the whole setup instead
                    sources = get_asset_sources(kind)
                    setup_asset_browser_deferred(browser, sources[0], search, kind['filter_id'])
                    return {"FINISHED"}

                if self.toggle_search:
                    search = toggle_search_field(params, search)
                    self.report({'INFO'}, f'Asset search: "{search}"' if search else 'Asset search cleared')
                else:
                    label = cycle_asset_source(params, get_asset_sources(kind))
                    self.report({'INFO'}, f'Asset source: {label}')

                browser.tag_redraw()
                return {"FINISHED"}

            ## Without modifier the button toggles the browser: collapse the one it opened
            if not collapse_asset_browser(context, area, browser):
                self.report({'ERROR'}, 'Could not collapse the asset browser')
                return {"CANCELLED"}
            return {"FINISHED"}

        browser = split_area_as_asset_browser(context, factor=self.factor)
        if not browser:
            self.report({'ERROR'}, 'Could not split current area to open an asset browser')
            return {"CANCELLED"}

        ## On a fresh browser, modifiers open it one step further in what they cycle or swap
        search = '' if self.toggle_search else search
        sources = get_asset_sources(kind)
        source = sources[1 % len(sources)] if self.cycle_library else sources[0]
        ## Space params of a fresh area are created when it is first drawn
        if not setup_asset_browser(browser, source, search, kind['filter_id']):
            setup_asset_browser_deferred(browser, source, search, kind['filter_id'])
        return {"FINISHED"}

# endregion browse operator


classes=(
STORYTOOLS_OT_browse_assets,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
