import bpy

from math import pi
from mathutils import Vector, Matrix

from bpy.types import Operator, PropertyGroup

from .. import fn

## Create object

def distance_selection_update(self, context):
    # print('self: ', dir(self))
    if self.place_from_cam and context.scene.camera:
        self.init_dist = fn.coord_distance_from_cam(context=context)
    else:
        self.init_dist = fn.coord_distance_from_view(context=context)


class STORYTOOLS_OT_create_object(Operator):
    bl_idname = "storytools.create_object"
    bl_label = "Create New Drawing"
    bl_description = "Create a new grease pencil object"
    bl_options = {"REGISTER", "UNDO"} # , "INTERNAL"

    name : bpy.props.StringProperty(
        name='Name',
        description="Name of Grease pencil object")
    
    parented : bpy.props.BoolProperty(
        name='Attached To Camera',
        description="When Creating the object, Attach it to the camera",
        default=False)
    
    init_dist : bpy.props.FloatProperty(
        name="Distance", description="Initial distance of new grease pencil object", 
        default=8.0, min=0.0, max=999, step=3, precision=3,
        subtype='DISTANCE')
    
    place_from_cam : bpy.props.BoolProperty(
        name='Use Active Camera',
        description="Create the object facing camera, else create from your current view",
        default=False, update=distance_selection_update)

    at_cursor : bpy.props.BoolProperty(
        name='At Cursor',
        description="Create object at cursor location, else centered position at cursor 'distance' facing view",
        default=False)
    
    track_to_cam : bpy.props.BoolProperty(
        name='Add Track To Camera',
        description="Add a track to constraint pointing at active camera\
            \nThis makes object's always face camera",
        default=False)

    def invoke(self, context, event):
        ## Suggest a numbered default name for quick use
        # gp_ct = len([o for o in context.scene.objects if o.type == 'GPENCIL'])
        gp_ct = len([o for o in bpy.data.objects if o.type == 'GPENCIL'])
        self.name = f'Drawing_{gp_ct+1:03d}'
        settings = context.scene.storytools_settings
        
        ## Calculate distance to 3D cursor
        # self.init_dist = settings.initial_distance # overwritten by dist from cusor
        # self.view_distance_from_cursor = fn.coord_distance_from_view(context=context)
        # self.cam_distance_from_cursor = None
        # if context.scene.camera:
        #     self.cam_distance_from_cursor = fn.coord_distance_from_cam(context=context)

        distance_selection_update(self, context)
        self.parented = settings.initial_parented
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, 'name')
        layout.prop(self, 'parented')
        layout.prop(self, 'at_cursor')
        row = layout.row()
        row.prop(self, 'init_dist')
        row.active = not self.at_cursor # enabled
        layout.prop(self, 'track_to_cam')

        if context.space_data.region_3d.view_perspective != 'CAMERA':
            col=layout.column()
            col.label(text='Not in camera', icon='ERROR')
            col.prop(self, 'place_from_cam', text='Face Active Camera')
        
        # if self.init_dist <= 0: (FIXME init_dist always positive, need futher check)
        #     viewpoint ='camera' if self.place_from_cam else 'view'
        #     col.label(text=f'Cursor is behind {viewpoint}', icon='ERROR') 
    
    def execute(self, context):
        prefs = fn.get_addon_prefs()
        scn = context.scene

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        
        
        r3d = context.space_data.region_3d
        
        if r3d.view_perspective != 'CAMERA' and self.place_from_cam:
            view_matrix = scn.camera.matrix_world
        else:    
            view_matrix = r3d.view_matrix.inverted()

        if self.at_cursor:
            loc = scn.cursor.location
        else:
            loc = view_matrix @ Vector((0.0, 0.0, -self.init_dist))
        
        ## Create GP object
        # TODO bonus : maybe check if want to use same data as another drawing ?

        ## Clean name
        self.name = self.name.strip()
        gp = bpy.data.grease_pencils.new(self.name)
        ob_name = self.name

        ob = bpy.data.objects.new(ob_name, gp)

        ## Set collection 
        ## Following is Only valid with a single scene !
        # draw_col = bpy.data.collections.get('Drawings')
        # if not draw_col:
        #     draw_col = bpy.data.collections.new('Drawings')
        #     bpy.scn.collection.children.link(draw_col)
        
        ## TODO : maybe better to always create a prefixed collection ?
        draw_col = next((c for c in scn.collection.children_recursive if c.name.startswith('Drawings')), None)
        if not draw_col:
            draw_col = next((c for c in scn.collection.children_recursive if c.name.startswith('GP')), None)
        if not draw_col:
            ## Create a drawing collection or direct link in root/active collection ?
            draw_col = context.collection # auto-fallback on scene collection

        draw_col.objects.link(ob)

        if self.parented:
            ob.parent = scn.camera

        ## Place
        _ref_loc, ref_rot, _ref_scale  = view_matrix.decompose()
        rot_mat = ref_rot.to_matrix().to_4x4() @ Matrix.Rotation(-pi/2, 4, 'X')
        loc_mat = Matrix.Translation(loc)
        new_mat = loc_mat @ rot_mat @ fn.get_scale_matrix((1,1,1))
        ob.matrix_world = new_mat

        ## Make active and selected
        context.view_layer.objects.active = ob
        ob.select_set(True)

        if self.track_to_cam:
            constraint = ob.constraints.new('TRACK_TO')
            constraint.target = scn.camera
            constraint.track_axis = 'TRACK_Y'
            constraint.up_axis = 'UP_Z'

        ## Configure
        # TODO: Set Active palette (Need a selectable loader)
        # fn.load_palette(path_to_palette)

        fn.load_default_palette(ob=ob)
        gp.edit_line_color[3] = prefs.default_edit_line_opacity # Bl default is 0.5
        gp.use_autolock_layers = True
        
        for l_name in reversed(['Sketch', 'Line', 'Color']):
            layer = gp.layers.new(l_name)
            layer.frames.new(scn.frame_current)
            layer.use_lights = False # Can be a project prefs
        
            ## Set default association
            ## TODO: Set default name as string in prefs ?
            if l_name in ['Line', 'Sketch']:
                fn.set_material_association(ob, layer, 'line')
            elif l_name == 'Color':
                fn.set_material_association(ob, layer, 'fill_white')

        ## update UI
        fn.update_ui_prop_index(context)

        # Enter Draw mode
        bpy.ops.object.mode_set(mode='PAINT_GPENCIL')
        fn.reset_draw_settings(context=context)

        return {"FINISHED"}

## ---
## Object Property groups and UIlist
## ---

class STORYTOOLS_OT_visibility_toggle(Operator):
    bl_idname = "storytools.visibility_toggle"
    bl_label = 'Toggle Visibility'
    bl_description = "Toggle and synchronize viewlayer visibility, viewport and render visibility"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True
    # def invoke(self, context, event):
    #     return self.execute(context)

    name : bpy.props.StringProperty()

    def execute(self, context):
        if not self.name:
            return {"CANCELLED"}
        ob = context.scene.objects.get(self.name)
        if not ob:
            return {"CANCELLED"}
        
        # hide = not ob.hide_viewport
        hide = ob.visible_get() # Already inversed
        
        ob.hide_viewport = hide
        ob.hide_render = hide
        # Set viewlayer visibility
        ob.hide_set(hide)
        return {"FINISHED"}

class STORYTOOLS_OT_object_draw(Operator):
    bl_idname = "storytools.object_draw"
    bl_label = 'Object Draw'
    bl_description = "Switch between drwa mode and object mode\
        \nEnter first GP object available\
        \nIf no GPencil object exists, pop-up creation menu"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    # name : bpy.props.StringProperty()
    def invoke(self, context, event):
        self.ctrl = event.ctrl
        return self.execute(context)

    def execute(self, context):
        ## Popup to select GP ? -> Pop panel with ctrl can miss-click, Need separate button
        # if self.ctrl:
        #     bpy.ops.wm.call_panel(name='STORYTOOLS_PT_drawings_ui', keep_open=True)
        #     return {"FINISHED"}

        ## If active object is a GP, go in draw mode or do nothing
        if context.object and context.object.type == 'GPENCIL':
            if context.mode != 'PAINT_GPENCIL':
                bpy.ops.object.mode_set(mode='PAINT_GPENCIL')
            else:
                bpy.ops.object.mode_set(mode='OBJECT')

            return {"FINISHED"}

        ## First GP object
        # gp = next((o for o in context.scene.objects if o.type == 'GPENCIL'), None)
        
        ## First (visible) GP objects
        gp = next((o for o in context.scene.objects if o.type == 'GPENCIL' if o.visible_get()), None)
        if gp:
            ## Set as active and select this gp object
            context.view_layer.objects.active = gp
            gp.select_set(True)
            bpy.ops.object.mode_set(mode='PAINT_GPENCIL')
            return {"FINISHED"}

        else:
            bpy.ops.storytools.create_object('INVOKE_DEFAULT')
            
        return {"FINISHED"}


## Property groups

def update_object_change(self, context):
    ob = context.scene.objects[self.index]
    # print('Switch to object', ob.name)
    if ob.type != 'GPENCIL' or context.object is ob:
        return

    prev_mode = context.mode
    possible_gp_mods = ('OBJECT', 
                        'EDIT_GPENCIL', 'SCULPT_GPENCIL', 'PAINT_GPENCIL',
                        'WEIGHT_GPENCIL', 'VERTEX_GPENCIL')

    if prev_mode not in possible_gp_mods:
        prev_mode = None

    mode_swap = False
    
    ## TODO optional: Option to stop mode sync ?
    ## Set in same mode as previous object
    if context.scene.tool_settings.lock_object_mode:
        context.scene.tool_settings.lock_object_mode = False
        ## Error changing mode if in draw mode then hidden
        if context.mode != 'OBJECT':
            mode_swap = True
            
            bpy.ops.object.mode_set(mode='OBJECT')

        ## Set active
        context.view_layer.objects.active = ob

        ## Keep same mode accross objects
        if not ob.hide_viewport and mode_swap and prev_mode is not None:
            bpy.ops.object.mode_set(mode=prev_mode)

        context.scene.tool_settings.lock_object_mode = True
            
    else:
        ## Keep same mode accross objects
        context.view_layer.objects.active = ob
        if not ob.hide_viewport and prev_mode is not None and context.mode != prev_mode:
            bpy.ops.object.mode_set(mode=prev_mode)

    for o in [o for o in context.scene.objects if o.type == 'GPENCIL']:
        o.select_set(o == ob) # select only active (when not in object mode)
    
    # if not ob.visible_get():
    #     print('Object is hidden!')


class CUSTOM_object_collection(PropertyGroup):

    # need an index for the native object list
    index : bpy.props.IntProperty(default=-1, update=update_object_change)
    
    # point_prop : PointerProperty(
    #     name="Object",
    #     type=bpy.types.Object)

class STORYTOOLS_UL_gp_objects_list(bpy.types.UIList):
    # Constants (flags)
    # Be careful not to shadow FILTER_ITEM (i.e. UIList().bitflag_filter_item)!
    # E.g. VGROUP_EMPTY = 1 << 0

    # Custom properties, saved with .blend file. E.g.
    # use_filter_empty: bpy.props.BoolProperty(
    #     name="Filter Empty", default=False, options=set(),
    #     description="Whether to filter empty vertex groups",
    # )

    # The draw_item function is called for each item of the collection that is visible in the list.
    #   data is the RNA object containing the collection,
    #   item is the current drawn item of the collection,
    #   icon is the "computed" icon for the item (as an integer, because some objects like materials or textures
    #   have custom icons ID, which are not available as enum items).
    #   active_data is the RNA object containing the active property for the collection (i.e. integer pointing to the
    #   active item of the collection).
    #   active_propname is the name of the active property (use 'getattr(active_data, active_propname)').
    #   index is index of the current item in the collection.
    #   flt_flag is the result of the filtering process for this item.
    #   Note: as index and flt_flag are optional arguments, you do not have to use/declare them here if you don't
    #         need them.

    # Called for each drawn item.
        ## active (draw) : GREASEPENCIL
        ## sculpt : SCULPTMODE_HLT
        ## active edit : EDITMODE_HLT
        ## others : OUTLINER_DATA_GREASEPENCIL

        # hide_ico = 'OUTLINER_OB_GREASEPENCIL' if item.active else 'HIDE_OFF'
        # source_ico = 'NETWORK_DRIVE' if item.is_project else 'USER' # BLANK1
        # row.label(text='', icon=source_ico)
        # row.prop(item, 'hide', text='', icon=hide_ico, invert_checkbox=True)

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index): # , flt_flag
        settings = context.scene.storytools_settings
        row = layout.row()
        if item == context.view_layer.objects.active:
            # EDIT_GPENCIL, SCULPT_GPENCIL, WEIGHT_GPENCIL, VERTEX_GPENCIL

            if context.mode == 'OBJECT':
                icon = 'OBJECT_DATA'
            elif context.mode == 'WEIGHT_GPENCIL':
                icon = 'MOD_VERTEX_WEIGHT'
            elif context.mode == 'SCULPT_GPENCIL':
                icon = 'SCULPTMODE_HLT'
            elif context.mode == 'EDIT_GPENCIL':
                icon = 'EDITMODE_HLT'
            else:
                icon = 'GREASEPENCIL'
        else:
            icon = 'OUTLINER_OB_GREASEPENCIL'
        name_row = row.row()
        name_row.prop(item, 'name', icon=icon, text='',emboss=False)
        name_row.active = item.visible_get()

        if settings.show_gp_users:
            if item.data.users > 1:
                row.template_ID(item, "data")
            else:
                row.label(text='', icon='BLANK1')
        
        if settings.show_gp_parent:
            if item.parent:
                row.label(text='', icon='DECORATE_LINKED')
            else:
                row.label(text='', icon='BLANK1')
        
        # subrow.alignment = 'RIGHT'
        if settings.show_gp_in_front:
            subrow = row.row()
            subrow.prop(item, 'show_in_front', text='', icon='MOD_OPACITY', emboss=False)
            subrow.active = item.show_in_front

        ## Clickable toggle, set and sync hide from viewlayer, viewport and render 
        ## (Can lead to confusion with blender model... but heh !)
        if item.visible_get():
            row.operator('storytools.visibility_toggle', text='', icon='HIDE_OFF', emboss=False).name = item.name
        else:
            row.operator('storytools.visibility_toggle', text='', icon='HIDE_ON', emboss=False).name = item.name
    
    # Called once to draw filtering/reordering options.
    # def draw_filter(self, context, layout):
    #     pass

    # Called once to filter/reorder items.
    def filter_items(self, context, data, propname):
        # This function gets the collection property (as the usual tuple (data, propname)), and must return two lists:
        # * The first one is for filtering, it must contain 32bit integers were self.bitflag_filter_item marks the
        #   matching item as filtered (i.e. to be shown), and 31 other bits are free for custom needs. Here we use the
        #   first one to mark VGROUP_EMPTY.
        # * The second one is for reordering, it must return a list containing the new indices of the items (which
        #   gives us a mapping org_idx -> new_idx).
        # Please note that the default UI_UL_list defines helper functions for common tasks (see its doc for more info).
        # If you do not make filtering and/or ordering, return empty list(s) (this will be more efficient than
        # returning full lists doing nothing!).

        # Default return values.
        flt_flags = []
        flt_neworder = []

        #### Do filtering/reordering here...
        ## data : scene struct -> propname: 'objects' string 
        objs = getattr(data, propname)
        # objs: scene objects collection
    
        helper_funcs = bpy.types.UI_UL_list

        flt_flags = [self.bitflag_filter_item if o.type == 'GPENCIL'
                     and not o.name.startswith('.') else 0 for o in objs]

        ## By name
        # flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, objs, "name", reverse=False)

        ## BONUS option: By distance to camera ? (need to be computed OTF... possible ?)

        return flt_flags, flt_neworder


## Cannot append to GPencil 'Add' menu, being an operator_menu_enum "object.gpencil_add"
# def menu_add_storytools_gp(self, context):
#     """Storyboard GP object entries in the Add Object > Gpencil Menu"""
#     if context.mode == 'OBJECT':
#         self.layout.operator('storytools.create_object', text="Storyboard Drawing")

## to test -> bl_options = {'HIDE_HEADER'}

classes=(
STORYTOOLS_OT_create_object,
STORYTOOLS_OT_object_draw,
STORYTOOLS_OT_visibility_toggle,
CUSTOM_object_collection, ## Test all bugged
STORYTOOLS_UL_gp_objects_list,
)

def register(): 
    # bpy.types.Scene.index_constant = -1
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.gp_object_props = bpy.props.PointerProperty(type=CUSTOM_object_collection)
    
    # bpy.types.GPENCIL_MT_....append(menu_add_storytools_gp)

def unregister():
    # bpy.types.GPENCIL_MT_....remove(menu_add_storytools_gp)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # del bpy.types.Scene.index_constant
    del bpy.types.Scene.gp_object_props