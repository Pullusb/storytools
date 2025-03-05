import bpy

from math import pi
from mathutils import Vector, Matrix

from bpy.types import Operator, PropertyGroup

from .. import fn

## Create object

def distance_selection_update(self, context):
    # print('self: ', dir(self))
    if self.face_camera and context.scene.camera:
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
    
    face_camera : bpy.props.BoolProperty(
        name='Use Active Camera',
        description="Create the object facing camera, else create from your current view",
        default=False, update=distance_selection_update)

    at_cursor : bpy.props.BoolProperty(
        name='At Cursor',
        description="Create object at cursor location, else centered position at cursor 'distance' facing view",
        default=False)

    use_location : bpy.props.BoolProperty(
        name='Use Location',
        description="Use the location of the new grease pencil object",
        default=False,
        options={'SKIP_SAVE'})

    location : bpy.props.FloatVectorProperty(
        name='Location',
        description="Location of the new grease pencil object",
        default=(0.0, 0.0, 0.0),
        size=3,
        options={'SKIP_SAVE'})
    
    track_to_cam : bpy.props.BoolProperty(
        name='Add Track To Camera',
        description="Add a track to constraint pointing at active camera\
            \nThis makes object's always face camera",
        default=False)
    
    # add option to enter draw mode (always On currently)

    def invoke(self, context, event):
        ## Suggest a numbered default name for quick use
        # gp_ct = len([o for o in context.scene.objects if o.type == 'GREASEPENCIL'])
        gp_ct = len([o for o in bpy.data.objects if o.type == 'GREASEPENCIL'])
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
        return context.window_manager.invoke_props_dialog(self, width=280)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, 'name')
        layout.prop(self, 'parented')
        layout.prop(self, 'track_to_cam')

        ## When location is passed, hide other options
        if not self.use_location:
            layout.label(text='Position:')
            layout.prop(self, 'at_cursor')
            row = layout.row()
            row.prop(self, 'init_dist')
            row.active = not self.at_cursor # enabled

            if context.space_data.region_3d.view_perspective != 'CAMERA':
                box = layout.box()
                col = box.column()
                col.label(text='Not in camera', icon='ERROR')
                col.prop(self, 'face_camera', text='Face Active Camera')
        
        # if self.init_dist <= 0: (FIXME init_dist always positive, need futher check)
        #     viewpoint ='camera' if self.face_camera else 'view'
        #     col.label(text=f'Cursor is behind {viewpoint}', icon='ERROR') 
    
    def execute(self, context):
        loc = self.location if self.use_location else None
        fn.create_gp_object(
            name=self.name,
            parented=self.parented,
            at_cursor=self.at_cursor,
            init_dist=self.init_dist,
            face_camera=self.face_camera,
            track_to_cam=self.track_to_cam,
            enter_draw_mode=True,
            location=loc,
            context=context
        )
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
    bl_description = "Switch between draw mode and object mode\
        \nEnter first GP object available\
        \nIf no GPencil object exists, pop-up creation menu\
        \n+ Shift : pop-up creation menu"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    # name : bpy.props.StringProperty()
    def invoke(self, context, event):
        self.ctrl = event.ctrl
        self.shift = event.shift
        
        return self.execute(context)

    def execute(self, context):
        ## Popup to select GP ? -> Pop panel with ctrl can miss-click, Need separate button
        # if self.ctrl:
        #     bpy.ops.wm.call_panel(name='STORYTOOLS_PT_drawings_ui', keep_open=True)
        #     return {"FINISHED"}

        if self.shift:
            bpy.ops.storytools.create_object('INVOKE_DEFAULT')
            return {"FINISHED"}

        ## If active object is a GP, go in draw mode or do nothing
        if context.object and context.object.type == 'GREASEPENCIL':
            if not context.object.visible_get():
                ## Show error if object is invisible
                mess = [f'Active object "{context.object.name}" is not visible',
                        ]
                ## /!\ Adding property in popup message close popup when released !
                # [context.object, 'hide_viewport', 'Visibility', 'BLANK1'],

                fn.show_message_box(_message=mess, _icon='ERROR')
                return {"CANCELLED"}

            if context.mode != 'PAINT_GREASE_PENCIL':
                # bpy.ops.storytools.make_active_and_select(name = context.object.name, mode='PAINT_GREASE_PENCIL')
                bpy.ops.object.mode_set(mode='PAINT_GREASE_PENCIL')
            else:
                # bpy.ops.storytools.make_active_and_select(name = context.object.name)
                bpy.ops.object.mode_set(mode='OBJECT')

            context.object.select_set(True)

            return {"FINISHED"}

        ## First GP object
        # gp = next((o for o in context.scene.objects if o.type == 'GREASEPENCIL'), None)
        
        ## First (visible) GP objects
        gp = next((o for o in context.scene.objects if o.type == 'GREASEPENCIL' if o.visible_get()), None)
        if gp:
            ## Set as active and select this gp object
            context.view_layer.objects.active = gp
            gp.select_set(True)
            bpy.ops.object.mode_set(mode='PAINT_GREASE_PENCIL')
            return {"FINISHED"}

        else:
            bpy.ops.storytools.create_object('INVOKE_DEFAULT')
            
        return {"FINISHED"}


## Property groups

def update_object_change(self, context):
    ob = context.scene.objects[self.index]
    # print('Switch to object', ob.name)
    if ob.type != 'GREASEPENCIL' or context.object is ob:
        return

    prev_mode = context.mode
    possible_gp_mods = ('OBJECT', 
                        'EDIT_GREASE_PENCIL', 'SCULPT_GREASE_PENCIL', 'PAINT_GREASE_PENCIL',
                        'WEIGHT_GREASE_PENCIL', 'VERTEX_GPENCIL')

    if prev_mode not in possible_gp_mods:
        prev_mode = None

    mode_swap = False

    ## Full skip if object is not visible
    if not ob.visible_get(view_layer=context.view_layer):
        return

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
            prev_mode = 'EDIT' if prev_mode == 'EDIT_GREASE_PENCIL' else prev_mode
            bpy.ops.object.mode_set(mode=prev_mode)

        context.scene.tool_settings.lock_object_mode = True
            
    else:
        ## Keep same mode accross objects
        context.view_layer.objects.active = ob
        if ob.visible_get(view_layer=context.view_layer) and prev_mode is not None and context.mode != prev_mode:
            prev_mode = 'EDIT' if prev_mode == 'EDIT_GREASE_PENCIL' else prev_mode
            bpy.ops.object.mode_set(mode=prev_mode)

    for o in [o for o in context.scene.objects if o.type == 'GREASEPENCIL']:
        o.select_set(o == ob) # select only active (when not in object mode)
    
    # if not ob.visible_get():
    #     print('Object is hidden!')


class STORYTOOLS_object_collection(PropertyGroup):
    ## need an index for the native object list
    index : bpy.props.IntProperty(default=-1, update=update_object_change)
    
    # point_prop : PointerProperty(
    #     name="Object",
    #     type=bpy.types.Object)

class STORYTOOLS_OT_grease_pencil_options(bpy.types.Operator):
    bl_idname = "storytools.grease_pencil_options"
    bl_label = 'Grease Pencil Options Menu'
    bl_description = "Show grease pencil options"
    bl_options = {'REGISTER', 'INTERNAL'}

    object_name : bpy.props.StringProperty(name='')

    def invoke(self, context, event):
        if not self.object_name:
            return {"CANCELLED"}
        self.object = bpy.data.objects.get(self.object_name)
        if not self.object:
            self.report({"ERROR"}, f'Could not found object named "{self.object_name}"')
            return {"CANCELLED"}

        # self.sidebar_width = next((r.width for r in context.area.regions if r.type == 'UI'), 0) / context.preferences.system.ui_scale
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        item = self.object

        ## ! Always show users infos even when elements are not collapsed !
        # if self.sidebar_width <= 380:
        if item.data.users > 1:
            col.label(text='Multiple Data Users:', icon='USER')
            col.template_ID(item, "data")
        else:
            col.label(text='Unique Data User', icon='USER')

        # if self.sidebar_width <= 270:
        ## parent infos
        if item.parent:
            col.label(text=f'Object Parented to "{item.parent.name}"', icon='DECORATE_LINKED')
        else:
            col.label(text='Object Is Not Parented', icon='BLANK1') # DECORATE_LINKED

        ## In front infos
        col.prop(item, 'show_in_front', text='In Front', icon='MOD_OPACITY')
        
        # if self.sidebar_width <= 240:
        if item.visible_get():
            col.operator('storytools.visibility_toggle', text='Toggle Visibility', icon='HIDE_OFF').name = item.name
        else:
            col.operator('storytools.visibility_toggle', text='Toggle Visibility', icon='HIDE_ON').name = item.name

        ## TODO: Test to remove useless cancel button (and eventually OK button).
        ## /!\ "template_popup_confirm" exists, only compatible with 4.2+
        # layout.template_popup_confirm("", text="Ok", cancel_text="")

    def execute(self, context):
        return {"FINISHED"}

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
        sidebar_width = next((r.width for r in context.area.regions if r.type == 'UI'), 0) / context.preferences.system.ui_scale
        settings = context.scene.storytools_settings
        row = layout.row(align=True)
        if item == context.view_layer.objects.active:
            # EDIT_GPENCIL, SCULPT_GPENCIL, WEIGHT_GPENCIL, VERTEX_GPENCIL

            if context.mode == 'OBJECT':
                icon = 'OBJECT_DATA'
            elif context.mode == 'WEIGHT_GREASE_PENCIL':
                icon = 'MOD_VERTEX_WEIGHT'
            elif context.mode == 'SCULPT_GREASE_PENCIL':
                icon = 'SCULPTMODE_HLT'
            elif context.mode == 'EDIT_GREASE_PENCIL':
                icon = 'EDITMODE_HLT'
            else:
                icon = 'GREASEPENCIL'
        else:
            icon = 'OUTLINER_OB_GREASEPENCIL'
        name_row = row.row()
        name_row.prop(item, 'name', icon=icon, text='', emboss=False)
        name_row.active = item.visible_get()

        ## Prepare visibility according to toggles
        limits = [380, 340, 300, 260]
        for i, prop_name in enumerate(('show_gp_users', 'show_gp_parent', 'show_gp_in_front', 'show_gp_visibility')):
            if getattr(settings, prop_name) == 'HIDE':
                for j, num in enumerate(limits[:i + 1]):
                    # Adjust limits to show left items if right ones are disabled
                    limits[j] = num - 40

        if settings.show_gp_users != 'HIDE':
            if settings.show_gp_users == 'SHOW' or sidebar_width > limits[0]: # 380:
                if item.data.users > 1:
                    if sidebar_width > 700:
                        row.template_ID(item, "data")
                    else:
                        # row.label(text=f'{item.data.users}') # text align left and cut object name
                        row.label(text='', icon='USER')
                else:
                    row.label(text='', icon='BLANK1')

        if settings.show_gp_parent != 'HIDE':
            if settings.show_gp_parent == 'SHOW' or sidebar_width > limits[1]: # 330:
                if item.parent:
                    row.label(text='', icon='DECORATE_LINKED')
                else:
                    row.label(text='', icon='BLANK1')
        
        if settings.show_gp_in_front != 'HIDE':
            if settings.show_gp_in_front == 'SHOW' or sidebar_width > limits[2]: # 300:
                subrow = row.row()
                subrow.prop(item, 'show_in_front', text='', icon='MOD_OPACITY', emboss=False)
                subrow.active = item.show_in_front

        if settings.show_gp_visibility != 'HIDE':
            if settings.show_gp_visibility == 'SHOW' or sidebar_width > limits[3]:
                ## Viz Clickable toggle, set and sync hide from all 3 view state [viewlayer, viewport and render]
                ## (Can lead to confusion with blender default... but heh!)

                if item.visible_get():
                    icon = 'HIDE_OFF' if not item.hide_render else 'RESTRICT_RENDER_ON' # VIS_SEL_10
                    row.operator('storytools.visibility_toggle', text='', icon=icon, emboss=False).name = item.name
                else:
                    icon = 'HIDE_ON' if item.hide_render else 'RESTRICT_RENDER_OFF' # VIS_SEL_01
                    row.operator('storytools.visibility_toggle', text='', icon=icon, emboss=False).name = item.name
    
        ## Infos pop-up for collapse items
        # if sidebar_width <= 550:
        row.operator('storytools.grease_pencil_options', text='', icon='THREE_DOTS', emboss=False).object_name = item.name

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

        flt_flags = [self.bitflag_filter_item if o.type == 'GREASEPENCIL'
                     and not o.name.startswith('.') else 0 for o in objs]

        ## By name
        # helper_funcs = bpy.types.UI_UL_list
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
STORYTOOLS_object_collection, ## Test all bugged
STORYTOOLS_OT_grease_pencil_options,
STORYTOOLS_UL_gp_objects_list,
)

def register(): 
    # bpy.types.Scene.index_constant = -1
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.gp_object_props = bpy.props.PointerProperty(type=STORYTOOLS_object_collection)
    
    # bpy.types.GPENCIL_MT_....append(menu_add_storytools_gp)

def unregister():
    # bpy.types.GPENCIL_MT_....remove(menu_add_storytools_gp)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # del bpy.types.Scene.index_constant
    del bpy.types.Scene.gp_object_props