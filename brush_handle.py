import bpy
from bpy.app.handlers import persistent

def set_material_by_name(ob, mat_name):
    if mat_name is None or mat_name == '':
        return
    for i, ms in enumerate(ob.material_slots):
        if not ms.material:
            continue
        m = ms.material
        if m.name == mat_name:
            print(f':{i}:', m.name, ob.active_material_index)
            ob.active_material_index = i
            return

def layer_change_callback():
    print('Layer has changed!')

    ob = bpy.context.object
    if not ob or ob.type != 'GPENCIL':
        return
    if not ob.data.layers.active:
        return
    
    mode = 'INDIVIDUAL'
    
    if mode == 'INDIVIDUAL':
        ## using custom prop
        # if not hasattr(ob.data.layers.active, 'material'):
        #     return
        ## set_material_by_name(ob, ob.data.layers.active['material'])

        if ob.data.layers.active.info in ob.keys():
            set_material_by_name(ob, ob[ob.data.layers.active.info])
    else:
        scn = bpy.context.scene
        if not hasattr(scn, 'gp_mat_by_layer'):
            return
        set_material_by_name(ob, scn.gp_mat_by_layer.get(ob.data.layers.active.info))

@persistent
def subscribe_layer_handler(dummy):
    subscribe_to = (bpy.types.GreasePencilLayers, "active_index")
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

## material callback
def material_change_callback():
    print(f'{bpy.context.object.name}: Material has changed!')
    ob = bpy.context.object
    if not ob or ob.type != 'GPENCIL':
        return
    if not ob.data.layers.active:
        return
    if not ob.active_material:
        return
    
    mode = 'INDIVIDUAL'
    
    if mode == 'INDIVIDUAL':
        ## use active_material_index
        # ob.data.layers.active['material'] = ob.active_material.name

        ## custom prop method
        # if ob.data.layers.active.info not in ob.data.keys():

        ob[ob.data.layers.active.info] = ob.active_material.name
        
        ## cleanup ?
        all_keys = [k for k in ob.keys()] # if in loop, error IDpropgroup size has changed
        for k in all_keys:
            if k not in [l.info for l in ob.data.layers]:
                del ob[k]
        
        ## using LayerType prop
        # ob.data.layers.active.use_material = ob.active_material.name ## not working 

    else: # GLOBAL
        scn=bpy.context.scene
        # Attach material.name to layer info on a scene prop
        # spread accross other layer
        if not hasattr(scn, 'gp_mat_by_layer'):
            # scn['gp_mat_by_layer'] = {}
            bpy.types.Scene.gp_mat_by_layer = {}

        layer_dict = scn.gp_mat_by_layer
        layer_dict[ob.data.layers.active.info] = ob.active_material.name


    ## Set selection to active object ot avoid un-sync selection on Layers stack
    ## (happen when an objet is selected but not active with 'lock object mode')
    # for l in ob.data.layers:
    #     l.select = l == ob.data.layers.active

    # bpy.context.scene.gptoolprops['layer_name'] = res.group('name')

@persistent
def subscribe_material_handler(dummy):
    # subscribe_to = (bpy.types.Material, "name") # When mat name is changed !
    subscribe_to = (bpy.types.Object, "active_material_index") # When mat name is changed !
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=bpy.types.GreasePencil,
        args=(),
        notify=material_change_callback,
        options={'PERSISTENT'},
    )

## brush callback ?
'''
def brush_change_callback():
    print('Brush has changed!')
    ob = bpy.context.object
    if not ob or ob.type != 'GPENCIL':
        return
    if not ob.data.layers.active:
        return
    ## Associate brush with current [object] layer

@persistent
def subscribe_brush_handler(dummy):
    subscribe_to = (bpy.types.Brush, "name")
    # subscribe_to = (bpy.context.scene.tool_settings.gpencil_paint, "brush")
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        # owner of msgbus subcribe (for clearing later)
        # owner=handle,
        owner=bpy.types.GreasePencil, # <-- can attach to an ID during all it's lifetime...

        # Args passed to callback function (tuple)
        args=(),
        # Callback function for property update
        
        notify=brush_change_callback,
        options={'PERSISTENT'},
    )
'''

def register():
    # subscribe_layer_handler(0)
    # subscribe_brush_handler(0)
    # bpy.types.GPencilLayer.use_material = '' # = bpy.props.StringProperty(name='Associated Material')
    bpy.app.handlers.load_post.append(subscribe_layer_handler) # need to restart after first activation
    bpy.app.handlers.load_post.append(subscribe_material_handler) # need to restart after first activation
    
    # bpy.app.handlers.load_post.append(subscribe_brush_handler) # need to restart after first activation
    
    # register_keymaps()

def unregister():
    # unregister_keymaps()
    
    # bpy.app.handlers.load_post.remove(subscribe_brush_handler)
    bpy.app.handlers.load_post.remove(subscribe_material_handler)
    bpy.app.handlers.load_post.remove(subscribe_layer_handler)

    # delete layer index trigger
    bpy.msgbus.clear_by_owner(bpy.types.GreasePencil)
    # del bpy.types.GPencilLayer.use_material