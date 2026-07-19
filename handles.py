import bpy
from bpy.app.handlers import persistent
from .constants import LAYERMAT_PREFIX, LAYERSTROKE_PREFIX, LAYERBRUSH_PREFIX
from .fn import (get_addon_prefs,
                 store_layer_brush,
                 restore_layer_brush,
                 store_layer_material,
                 restore_layer_material,
                 brush_sync_suppressed)

## Tracks the previously active layer as (object_name, layer_name) so a layer change can
## attribute the outgoing layer's brush before restoring the incoming one. Reset on file load.
_prev_layer = None

def get_object_and_scene():# -> tuple[None, None] | tuple[Any | None, Any]:
    """return scene and active object if object is a GP
    If there are mutliple main windows, return the scene and active GP object from first window with active GP
    Return: (scene, GP_object) or (None, None)
    """

    scn = None
    ob = None
    if len(bpy.context.window_manager.windows) == 1:
        scn = bpy.context.scene
        ob = bpy.context.object
        if not ob or ob.type != 'GREASEPENCIL':
            return None, None
        if not ob.data.layers.active:
            return None, None
    
    else:
        # Dirty fix for case of multi-main-window (for dual win hack, with storypencil or spark-sequencer
        ob = bpy.context.object
        if ob and ob.type == 'GREASEPENCIL':
            scn = bpy.context.scene
            ## Use current window direcly
            return scn, ob

        for win in bpy.context.window_manager.windows:
            if win.view_layer.objects.active and win.view_layer.objects.active.type == 'GREASEPENCIL':
                scn = win.scene
                ob = win.view_layer.objects.active
                return scn, ob

        return None, None
    
    return scn, ob

def layer_change_callback():
    # print('Layer has changed!')

    ## Disable Sync when sidebar is not visible ?
    ## TODO: Add the settings also in material settings panel to keep sync when panel is disabled
    if not get_addon_prefs().show_sidebar_ui:
        return

    scn, ob = get_object_and_scene()
    if scn is None or ob is None:
        return

    wm = bpy.context.window_manager

    global _prev_layer
    cur = ob.data.layers.active

    ## Brush + stroke type per layer: store the outgoing layer's brush, restore the incoming one.
    ## Brush activation via the asset system does not emit any msg_bus notification, so we cannot
    ## react to a brush change directly. Instead we piggyback the (working) layer-change event:
    ## the active brush is global and unchanged by the layer switch, so at this point it still
    ## reflects what was used on the previous (outgoing) layer.
    ## (independent from material sync, hence handled before the material skip flag)
    ## brush_sync_suppressed: muted by operators that resolve the brush outcome themselves
    ## (toolpresets merge preset + paired values synchronously in set_draw_tool)
    brush_mode = scn.storytools_settings.brush_layer_sync
    if cur and brush_mode != 'DISABLED' and not brush_sync_suppressed():
        ## Store outgoing: attribute the currently active brush to the previous layer
        if _prev_layer and _prev_layer[0] == ob.name and _prev_layer[1] != cur.name:
            prev = ob.data.layers.get(_prev_layer[1])
            if prev:
                store_layer_brush(scn, ob, prev, brush_mode)
        ## Restore incoming: set the brush + stroke type stored on the new active layer
        restore_layer_brush(scn, ob, cur, brush_mode)
        ## cleanup per-object keys of layers that no longer exists (renamed/deleted)
        if brush_mode == 'INDIVIDUAL':
            layer_names = [l.name for l in ob.data.layers]
            for prefix in (LAYERBRUSH_PREFIX, LAYERSTROKE_PREFIX):
                for k in [k for k in ob.keys() if k.startswith(prefix) and k[len(prefix):] not in layer_names]:
                    del ob[k]

    ## Keep the previous-layer tracker up to date whatever the sync/skip state
    if cur:
        _prev_layer = (ob.name, cur.name)

    if wm.get("skip_layer_sync_flag"):
        del wm["skip_layer_sync_flag"]
        return

    restore_layer_material(scn, ob, ob.data.layers.active, scn.storytools_settings.material_sync)

def subscribe_layer():
    subscribe_to = (bpy.types.GreasePencilv3Layers, "active") # Still named "v3", API may change later
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        # owner of msgbus subcribe (for clearing later)
        # owner=handle,
        owner=bpy.types.GreasePencil, # <-- can attach to an ID during all it's lifetime...
        # Args passed to callback function (tuple)
        args=(),
        # Callback function for property update
        notify=layer_change_callback,
        options={'PERSISTENT'},
    )

@persistent
def subscribe_layer_handler(dummy):
    ## reset the previous-layer tracker so a freshly opened file cannot mis-attribute a brush
    global _prev_layer
    _prev_layer = None
    subscribe_layer()

## material callback
def material_change_callback():
    # print(f'{bpy.context.object.name}: Material has changed!')

    ## Disable Sync when sidebar is not visible
    ## TODO: add the settings also in material settings panel to keep sync when panel is disabled
    if not get_addon_prefs().show_sidebar_ui:
        return

    scn, ob = get_object_and_scene()
    if scn is None or ob is None:
        return
    if not ob.active_material:
        return

    wm = bpy.context.window_manager
    if wm.get("skip_material_sync_flag"):
        del wm["skip_material_sync_flag"]
        return

    mode = scn.storytools_settings.material_sync
    if mode == 'DISABLED':
        return

    active_layer = ob.data.layers.active
    if not active_layer:
        return

    ## Store the material association for the active layer (INDIVIDUAL or GLOBAL)
    store_layer_material(scn, ob, active_layer, mode)

    ## cleanup per-object keys of layers that no longer exists (renamed/deleted)
    if mode == 'INDIVIDUAL':
        layer_names = [l.name for l in ob.data.layers]
        for k in [k for k in ob.keys() if k.startswith(LAYERMAT_PREFIX) and k[len(LAYERMAT_PREFIX):] not in layer_names]:
            del ob[k]

    ## Set selection to active object ot avoid un-sync selection on Layers stack
    ## (happen when an objet is selected but not active with 'lock object mode')
    # for l in ob.data.layers:
    #     l.select = l == ob.data.layers.active

    # bpy.context.scene.gptoolprops['layer_name'] = res.group('name')

def subscribe_material():
    # subscribe_to = (bpy.types.Material, "name") # When mat name is changed !
    subscribe_to = (bpy.types.Object, "active_material_index") # When mat name is changed !
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=bpy.types.GreasePencil,
        args=(),
        notify=material_change_callback,
        options={'PERSISTENT'},
    )

@persistent
def subscribe_material_handler(dummy):
    subscribe_material()

## Note: the brush per-layer association is handled entirely from layer_change_callback
## (store-on-layer-leave), because activating a brush through the asset system emits no
## msg_bus notification we could subscribe to. See layer_change_callback above.

def register():
    # bpy.types.GPencilLayer.use_material = '' # = bpy.props.StringProperty(name='Associated Material')

    # Subscribe for register (Avoid the to restart after first activation)
    bpy.app.timers.register(subscribe_layer, first_interval=1)
    bpy.app.timers.register(subscribe_material, first_interval=1)

    # Add a load handler when opening other blends (does not seeem to add msgbus twice)
    bpy.app.handlers.load_post.append(subscribe_layer_handler)
    bpy.app.handlers.load_post.append(subscribe_material_handler) # Need to restart after first activation


def unregister():
    bpy.app.handlers.load_post.remove(subscribe_material_handler)
    bpy.app.handlers.load_post.remove(subscribe_layer_handler)

    # delete layer index trigger
    bpy.msgbus.clear_by_owner(bpy.types.GreasePencil)
    # del bpy.types.GPencilLayer.use_material