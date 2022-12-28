import bpy
# from .preferences import get_addon_prefs
from math import pi
from mathutils import Vector, Matrix, Quaternion

from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import CollectionProperty, PointerProperty

from . import fn
from .preferences import get_addon_prefs
from .constants import LAYERMAT_PREFIX

# TODO: Build new object
# - facing camera
# - load "active" palette

## Pop up menu for config or keep it 

## Bonus
# - load guides if there are any

## possible modal cursor set
# ('DEFAULT', 'NONE', 'WAIT', 'CROSSHAIR', 'MOVE_X', 'MOVE_Y', 'KNIFE', 'TEXT', 
# 'PAINT_BRUSH', 'PAINT_CROSS', 'DOT', 'ERASER', 'HAND', 
# 'SCROLL_X', 'SCROLL_Y', 'SCROLL_XY', 'EYEDROPPER', 'PICK_AREA', 
# 'STOP', 'COPY', 'CROSS', 'MUTE', 'ZOOM_IN', 'ZOOM_OUT')

## Object transform

    # on_cam : bpy.props.BoolProperty(
    #     default=False, options={'SKIP_SAVE'})
        # if self.on_cam:
        #     self.ob = context.scene.camera
        #     if not self.ob:
        #         return {'CANCELLED'}

        #     ## Take view center when in viewcam
        #     if context.space_data.region_3d.view_perspective == 'CAMERA':
        #         self.init_world_loc = fn.get_cam_frame_world_center(self.ob)
        #     else:
        #         self.init_world_loc = self.ob.matrix_world.to_translation()

        # else:
        #     self.ob = context.object
        #     self.init_world_loc = self.ob.matrix_world.to_translation()

class STORYTOOLS_OT_object_depth_move(Operator):
    bl_idname = "storytools.object_depth_move"
    bl_label = "Object Depth Move"
    bl_description = "Move object Forward/backward (Slide left-right)\
                    \n+ Ctrl : Adjust Scale (Retain same size in camera framing)"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type != 'CAMERA'

    def invoke(self, context, event):
        self.init_mouse_x = event.mouse_x
        self.cam = bpy.context.scene.camera
        if not self.cam:
            self.report({'ERROR'}, 'No active camera')
            return {"CANCELLED"}

        self.cam_pos = self.cam.matrix_world.translation
        self.mode = 'distance'
        self.objects = [o for o in context.selected_objects if o.type != 'CAMERA']
        self.init_mats = [o.matrix_world.copy() for o in self.objects]
        
        if self.cam.data.type == 'ORTHO':
            context.area.header_text_set(f'Move factor: 0.00')
            # distance is view vector based
            self.view_vector = Vector((0,0,-1))
            self.view_vector.rotate(self.cam.matrix_world)
        else:
            self.init_vecs = [o.matrix_world.translation - self.cam_pos for o in self.objects]
            self.init_dists = [v.length for v in self.init_vecs]
            context.area.header_text_set(f'Move factor: 0.00 | Mode: {self.mode} (M to switch)')
        
        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def stop(self, context):
        context.area.header_text_set(None)
        context.window.cursor_set("DEFAULT")

    def modal(self, context, event):
        if self.mode == 'distance':
            factor = 0.1
            if event.shift:
                factor = 0.01
        else:
            # Smaller factor for proportional dist
            factor = 0.01
            if event.shift:
                factor = 0.001

        if event.type in {'MOUSEMOVE'}:
            diff = (event.mouse_x - self.init_mouse_x) * factor

            if self.cam.data.type == 'ORTHO':
                # just push in view vector direction
                context.area.header_text_set(f'Move factor: {diff:.2f}')
                for i, obj in enumerate(self.objects):
                    new_vec = self.init_mats[i].translation + (self.view_vector * diff)
                    obj.matrix_world.translation = new_vec
            else:
                # Push from camera point and scale accordingly
                context.area.header_text_set(f'Move factor: {diff:.2f} | Mode: {self.mode} (M to switch)')

                for i, obj in enumerate(self.objects):
                    if self.mode == 'distance':
                        ## move with the same length for everyone 
                        new_vec = self.init_vecs[i] + (self.init_vecs[i].normalized() * diff)
                    
                    else:
                        ## move with proportional factor from individual distance vector to camera
                        new_vec = self.init_vecs[i] + (self.init_vecs[i] * diff)

                    obj.matrix_world.translation = self.cam_pos + new_vec
                    
                    if event.ctrl: # Adjust scale only if Ctrl is pressed
                        dist_percentage = new_vec.length / self.init_dists[i]
                        obj.scale = self.init_mats[i].to_scale() * dist_percentage
                    else:
                        obj.scale = self.init_mats[i].to_scale() # reset to initial size


        if event.type in {'M'} and event.value == 'PRESS':
            # Switch mode
            self.mode = 'distance' if self.mode == 'proportional' else 'proportional'

        # cancel on release
        if event.type in {'LEFTMOUSE'}: # and event.value == 'PRESS'
            self.stop(context)
            ## Key objects
            for o in self.objects:
                fn.key_object(o, use_autokey=True)
            return {"FINISHED"}
        
        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            for i, obj in enumerate(self.objects):
                obj.matrix_world = self.init_mats[i]
            self.stop(context)
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}


class STORYTOOLS_OT_object_pan(Operator):
    bl_idname = "storytools.object_pan"
    bl_label = 'Object Pan Translate'
    bl_description = "Translate active object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object

    def invoke(self, context, event):
        
        self.ob = context.object
        self.init_world_loc = self.ob.matrix_world.to_translation()

        self.init_pos = self.ob.location.copy() # to restore if cancelled
        self.init_mouse_x = event.mouse_x
        self.init_mouse_y = event.mouse_y
        self.init_mouse = Vector((event.mouse_x, event.mouse_y))

        self.init_vector = fn.region_to_location(self.init_mouse, self.init_world_loc)

        context.window.cursor_set("SCROLL_XY")
        context.window_manager.modal_handler_add(self)
        self.update_position(context, event)
        return {'RUNNING_MODAL'}

    def update_position(self, context, event):
        mouse_co = Vector((event.mouse_x, event.mouse_y))
        # delta_x = event.mouse_x - self.init_mouse_x
        # context.object.location = self.init_pos * (1 + delta_x * 0.01)
        vec = fn.region_to_location(mouse_co, self.init_world_loc)
        move_vec = vec - self.init_vector
        
        ## move by vector (recompose matrix)
        self.ob.matrix_world.translation = self.init_world_loc + move_vec

    def modal(self, context, event):
        
        self.update_position(context, event)
        
        if event.type == 'LEFTMOUSE': # and event.value == 'RELEASE'
            context.window.cursor_set("DEFAULT")
            
            fn.key_object(self.ob)

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.ob.location = self.init_pos
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        return {"FINISHED"}

class STORYTOOLS_OT_object_scale(Operator):
    bl_idname = "storytools.object_scale"
    bl_label = 'Object Scale'
    bl_description = "Scale object by going left-right"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object

    def invoke(self, context, event):
        self.init_scale = context.object.scale.copy()
        self.init_mouse_x = event.mouse_x
        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        delta = event.mouse_x - self.init_mouse_x
        context.object.scale = self.init_scale * (1 + delta * 0.01)
        
        if event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")

            ## Key all transforms
            fn.key_object(context.object, use_autokey=True)

            ## Key only scale
            # fn.key_object(context.object, loc=False, rot=False, use_autokey=True)

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.object.scale = self.init_scale
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}
    
    # def execute(self, context):
    #     with context.temp_override(selected_objects=[context.object]):
    #         bpy.ops.transform.resize('INVOKE_DEFAULT')
    #     bpy.ops.transform.resize('INVOKE_DEFAULT')
    #     return {"FINISHED"}

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
    bl_options = {"REGISTER"} # , "INTERNAL"

    name : bpy.props.StringProperty(name='Name',
        description="Name of Grease pencil object")
    
    parented : bpy.props.BoolProperty(name='Attached To Camera',
        description="When Creating the object, Attach it to the camera",
        default=False)
    
    init_dist : bpy.props.FloatProperty(
        name="Distance", description="Initial distance of new grease pencil object", 
        default=8.0, min=0.0, max=600, step=3, precision=1)
    
    place_from_cam : bpy.props.BoolProperty(name='Use Active Camera',
        description="Create the object facing camera, else create from your current view",
        default=False, update=distance_selection_update)

    at_cursor : bpy.props.BoolProperty(name='At Cursor',
        description="Create object at cursor location, else centered position at cursor 'distance' facing view",
        default=False)

    def invoke(self, context, event):
        ## Suggest a numbered default name for quick use
        gp_ct = len([o for o in context.scene.objects if o.type == 'GPENCIL'])
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

        if context.space_data.region_3d.view_perspective != 'CAMERA':
            col=layout.column()
            col.label(text='Not in camera', icon='ERROR')
            col.prop(self, 'place_from_cam', text='Face Active Camera')
        
        # if self.init_dist <= 0: (FIXME init_dist always positive, need futher check)
        #     viewpoint ='camera' if self.place_from_cam else 'view'
        #     col.label(text=f'Cursor is behind {viewpoint}', icon='ERROR') 
    
    def execute(self, context):
        prefs = get_addon_prefs()

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        # for o in context.scene.objects:o.select_set(False)
        
        r3d = context.space_data.region_3d
        
        if r3d.view_perspective != 'CAMERA' and self.place_from_cam:
            view_matrix = context.scene.camera.matrix_world
        else:    
            view_matrix = r3d.view_matrix.inverted()

        if self.at_cursor:
            loc = context.scene.cursor.location
        else:
            loc = view_matrix @ Vector((0.0, 0.0, -self.init_dist))
        
        ## Create GP object
        # TODO: maybe check if want to use same data as another drawing
        # (need to show number of user)
        gp = bpy.data.grease_pencils.new(self.name)
        ob_name = self.name

        ob = bpy.data.objects.new(ob_name, gp)

        ## Set collection
        draw_col = bpy.data.collections.get('Drawings')
        if not draw_col:
            draw_col = bpy.data.collections.new('Drawings')
            bpy.context.scene.collection.children.link(draw_col)
        draw_col.objects.link(ob)

        if self.parented:
            ob.parent = context.scene.camera

        ## Place
        _ref_loc, ref_rot, _ref_scale  = view_matrix.decompose()
        rot_mat = ref_rot.to_matrix().to_4x4() @ Matrix.Rotation(-pi/2, 4, 'X')
        loc_mat = Matrix.Translation(loc)
        new_mat = loc_mat @ rot_mat @ fn.get_scale_matrix((1,1,1))
        ob.matrix_world = new_mat

        ## Make active and selected
        context.view_layer.objects.active = ob
        ob.select_set(True)

        ## Configure
        # TODO: Set Active palette (Need a selectable loader)
        # fn.load_palette(path_to_palette)
        fn.load_default_palette(ob=ob)
        gp.edit_line_color[3] = prefs.default_edit_line_opacity # 0.2 # Bl default is 0.5
        
        for l_name in reversed(['Sketch', 'Line', 'Color']):
            layer = gp.layers.new(l_name)
            # CHOICE: new frame creation -> Usual default is frame_current
            layer.frames.new(context.scene.frame_start)
            layer.use_lights = False # Can be a project prefs
        
            ## Set default association
            ## TODO: set default name as string in prefs ?
            if l_name in ['Line', 'Sketch']:
                fn.set_material_association(ob, layer, 'line')
            elif l_name == 'Color':
                fn.set_material_association(ob, layer, 'fill_white')

        # Enter Draw mode
        bpy.ops.object.mode_set(mode='PAINT_GPENCIL')
        fn.reset_draw_settings(context=context)

        return {"FINISHED"}


class STORYTOOLS_OT_align_with_view(Operator):
    bl_idname = "storytools.align_with_view"
    bl_label = "Align With View"
    bl_description = "Align object with view\
        \nCtrl + Click align but keep object Z axis pointing up"
    bl_options = {"REGISTER", "UNDO"} # "INTERNAL"

    @classmethod
    def poll(cls, context):
        return context.object # and context.object.type == 'GPENCIL'

    keep_z_up : bpy.props.BoolProperty(name='Keep Z Up', default=False)

    def invoke(self, context, event):
        self.keep_z_up = event.ctrl
        return self.execute(context)

    def execute(self, context):
        r3d = context.space_data.region_3d            
        
        for ob in context.selected_objects:
            ## skip camera object
            if ob.type == 'CAMERA':
                continue

            ## skip active camera if selected and IN cam view
            # if context.scene.camera \
            #     and ob == context.scene.camera \
            #     and context.space_data.region_3d.view_perspective == 'CAMERA':
            #     continue
    
            if self.keep_z_up:
                ## Align to view but keep world Up
                Z_up_vec = Vector((0.0, 0.0, 1.0))
                aim = r3d.view_rotation @ Z_up_vec
                world_aligned_mat = aim.to_track_quat('Z','Y').to_matrix().to_4x4() # Track Up
                fn.assign_rotation_from_ref_matrix(ob, world_aligned_mat)
            
            else:
                ## Align to view
                view_matrix = r3d.view_matrix.inverted()
                fn.assign_rotation_from_ref_matrix(ob, view_matrix)

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
    
    ## TODO: add pref to choose if mode should be transfered ?
    ## Set in same mode as previous object
    if context.scene.tool_settings.lock_object_mode:
        if context.mode != 'OBJECT':
            mode_swap = True
            bpy.ops.object.mode_set(mode='OBJECT')

        # set active
        context.view_layer.objects.active = ob

        ## keep same mode accross objects
        if mode_swap and prev_mode is not None:
            bpy.ops.object.mode_set(mode=prev_mode)
            
    else:
        ## keep same mode accross objects
        context.view_layer.objects.active = ob
        if context.mode != prev_mode is not None:
            bpy.ops.object.mode_set(mode=prev_mode)

    ob.select_set(True)


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
        # layout.label(text=item.name)
        row = layout.row()
        if item == context.view_layer.objects.active:
            # if context.mode == 'PAINT'
            icon = 'GREASEPENCIL'
            # row.label(text='', icon='GREASEPENCIL')
        else:
            icon = 'OUTLINER_OB_GREASEPENCIL'
            # row.label(text='', icon='OUTLINER_DATA_GREASEPENCIL')
        
        # row.label(text=item.name, icon=icon)
        row.prop(item, 'name', icon=icon, text='',emboss=False)
        if item.data.users > 1:
            row.template_ID(item, "data")
        else:
            row.label(text='', icon='BLANK1')
        
        if item.parent:
            row.label(text='', icon='DECORATE_LINKED')
        else:
            row.label(text='', icon='BLANK1')
        
        ## Clickable toggle, set and sync hide from viewlayer, viewport and render 
        ## (Can lead to confusion with blender model... but heh !)
        # if item.hide_viewport:
        if item.visible_get():
            # row.label(text='', icon='HIDE_OFF')
            row.operator('storytools.visibility_toggle', text='', icon='HIDE_OFF', emboss=False).name = item.name
        else:
            # row.label(text='', icon='HIDE_ON')
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

        flt_flags = [self.bitflag_filter_item if o.type == 'GPENCIL' else 0 for o in objs]
        ## By name
        # flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, objs, "name", reverse=False)

        ## BONUS option: By distance to camera ? (need to be computed OTF... possible ?)

        return flt_flags, flt_neworder


## to test -> bl_options = {'HIDE_HEADER'}

classes=(
STORYTOOLS_OT_create_object,
STORYTOOLS_OT_align_with_view,
STORYTOOLS_OT_object_pan,
STORYTOOLS_OT_object_scale,
STORYTOOLS_OT_object_depth_move,
STORYTOOLS_OT_visibility_toggle,
CUSTOM_object_collection, ## Test all bugged
STORYTOOLS_UL_gp_objects_list,
)

def register(): 
    # bpy.types.Scene.index_constant = -1
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gp_object_props = bpy.props.PointerProperty(type=CUSTOM_object_collection)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # del bpy.types.Scene.index_constant
    del bpy.types.Scene.gp_object_props