import bpy
# from .preferences import get_addon_prefs
from math import pi
from mathutils import Vector, Matrix, Quaternion
from . import fn
from .preferences import get_addon_prefs

# TODO: Build new object
# - facing camera
# - load "active" palette

## Pop up menu for config or keep it 

## Bonus
# - load guides if there are any

## UI
# - Add '+' button in a GP UI-list


# def create_new_gp_object():
#     pass


class STORYTOOLS_OT_create_object(bpy.types.Operator):
    bl_idname = "storytools.create_object"
    bl_label = "Create New Drawing"
    bl_description = "Create a new grease pencil object"
    bl_options = {"REGISTER"} # , "INTERNAL"

    name : bpy.props.StringProperty(name='Name')
    
    parented : bpy.props.BoolProperty(name='Attached To Camera',
        description="When Creating the object, Attach it to the camera",
        default=False)
    
    init_dist : bpy.props.FloatProperty(
        name="Distance", description="Initial distance of new grease pencil object", 
        default=8.0, min=0.0, max=600, step=3, precision=1)
    
    place_from_cam : bpy.props.BoolProperty(name='Use Active Camera',
        description="Create the object facing camera, else create from your current view",
        default=False)

    def invoke(self, context, event):
        # Suggest a numbered default name for quick use
        gp_ct = len([o for o in context.scene.objects if o.type == 'GPENCIL'])
        self.name = f'Drawing_{gp_ct+1:03d}'
        settings = context.scene.storytools_settings
        self.init_dist = settings.initial_distance
        self.parented = settings.initial_parented
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, 'name')
        layout.prop(self, 'init_dist')
        layout.prop(self, 'parented')
        if context.space_data.region_3d.view_perspective != 'CAMERA':
            col=layout.column()
            col.label(text='Not in camera', icon='ERROR')
            col.prop(self, 'place_from_cam', text='Face Active Camera')
            
    
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

        loc = view_matrix @ Vector((0.0, 0.0, -self.init_dist))
        
        ## Create GP object
        #TODO: maybe check if want to use same data as another drawing
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
        
        # Enter Draw mode
        bpy.ops.object.mode_set(mode='PAINT_GPENCIL')

        return {"FINISHED"}

class STORYTOOLS_OT_align_with_view(bpy.types.Operator):
    bl_idname = "storytools.align_with_view"
    bl_label = "Align With View"
    bl_description = "Align object with view"
    bl_options = {"REGISTER"} # "INTERNAL"

    @classmethod
    def poll(cls, context):
        return context.object # and context.object.type == 'GPENCIL'

    keep_z_up : bpy.props.BoolProperty(name='Keep Z Up', default=False)

    def execute(self, context):
        r3d = context.space_data.region_3d            
        
        for ob in context.selected_objects:
    
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

""" 
class STORYTOOLS_UL_gp_objects_list(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # self.use_filter_show = True # force open/close the search feature
        # prefs = get_addon_prefs()
        # split = layout.split(align=False, factor=0.3)
        row = layout.row()

        ## active (draw) : GREASEPENCIL
        ## sculpt : SCULPTMODE_HLT
        ## active edit : EDITMODE_HLT
        ## others : OUTLINER_DATA_GREASEPENCIL

        hide_ico = 'OUTLINER_OB_GREASEPENCIL' if item.active else 'HIDE_OFF'
        source_ico = 'NETWORK_DRIVE' if item.is_project else 'USER' # BLANK1
        
        row.label(text='', icon=source_ico)
        row.prop(item, 'hide', text='', icon=hide_ico, invert_checkbox=True) 
        subrow = row.row(align=True)
        subrow.prop(item, 'tag', text='')
        subrow.prop(item, 'name', text='')
        subrow.enabled = not item.is_project
"""
class STORYTOOLS_UL_gp_objects_list(bpy.types.UIList):
    # Constants (flags)
    # Be careful not to shadow FILTER_ITEM (i.e. UIList().bitflag_filter_item)!
    # E.g. VGROUP_EMPTY = 1 << 0

    # Custom properties, saved with .blend file. E.g.
    # use_filter_empty: bpy.props.BoolProperty(
    #     name="Filter Empty", default=False, options=set(),
    #     description="Whether to filter empty vertex groups",
    # )

    # Called for each drawn item.
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        # # 'DEFAULT' and 'COMPACT' layout types should usually use the same draw code.
        # if self.layout_type in {'DEFAULT', 'COMPACT'}:
        #     pass
        # # 'GRID' layout type should be as compact as possible (typically a single icon!).
        # elif self.layout_type == 'GRID':
        #     pass

        for o in context.scene.objects:
            if o.type != 'GPENCIL':
                continue
            row = layout.row()
            if o == context.view_layer.objects.active:
                # if context.mode == 'PAINT'
                icon = 'GREASEPENCIL'
                # row.label(text='', icon='GREASEPENCIL')
            else:
                icon = 'OUTLINER_DATA_GREASEPENCIL'
                # row.label(text='', icon='OUTLINER_DATA_GREASEPENCIL')
            
            row.label(text=o.name, icon=icon)
            if o.data.users > 1:
                row.template_ID(o, "data")
            else:
                row.label(text='',icon='BLANK1')


    # Called once to draw filtering/reordering options.
    def draw_filter(self, context, layout):
        # Nothing much to say here, it's usual UI code...
        pass

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

        # Do filtering/reordering here...

        return flt_flags, flt_neworder


## to test -> bl_options = {'HIDE_HEADER'}

classes=(
STORYTOOLS_OT_create_object,
STORYTOOLS_OT_align_with_view,
STORYTOOLS_UL_gp_objects_list,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)