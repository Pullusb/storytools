import bpy
from pathlib import Path
from bpy.types import Operator
from mathutils import Vector
# import shutil

from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import CollectionProperty, PointerProperty
# from bl_operators.presets import AddPresetBase

from .. import fn


# class STORYTOOLS_OT_camera_change_focal(Operator):
#     bl_idname = "storytools.camera_change_focal"
#     bl_label = 'Camera Change Focal'
#     bl_description = ""
#     bl_options = {'REGISTER', 'INTERNAL'}

#     @classmethod
#     def poll(cls, context):
#         return context.scene.camera

#     def execute(self, context):
#         ret = fn.key_object(context.scene.camera, scale=False)
#         if ret:
#             self.report({'INFO'}, ret)
#         return {"FINISHED"}


def update_camera_change(self, context):
    ob = context.scene.objects[self.index]
    # print('Switch to object', ob.name)
    if ob.type != 'CAMERA':
        return

    cam = context.scene.camera
    if not cam:
        context.scene.camera = ob
        return

    ## Go in camera view
    context.space_data.region_3d.view_perspective = 'CAMERA'

    ## Sync passe partout
    show_pp, pp_alpha = cam.data.show_passepartout, cam.data.passepartout_alpha
    if cam.name != 'draw_cam':
        context.scene.camera = ob
        ob.data.show_passepartout, ob.data.passepartout_alpha = show_pp, pp_alpha
        return

    ## Here we are in draw camera
    if not cam.parent:
        ## set cam, if draw cam has no parent
        context.scene.camera = ob

    elif ob != cam.parent:
        ## Set cam and immediately enter draw mode
        context.scene.camera = ob
        if hasattr(bpy.types, 'GP_OT_draw_cam_switch'):

            # Get 'show_pp' from gp toolbox property
            ob.data.show_passepartout = context.scene.gptoolprops.drawcam_passepartout
            ob.data.passepartout_alpha = pp_alpha
            bpy.ops.gp.draw_cam_switch(cam_mode='draw')
            # cam.data.show_passepartout = show_pp

    return


class STORYTOOLS_camera_collection(PropertyGroup):
    index : bpy.props.IntProperty(default=-1, update=update_camera_change)

def show_lens(layout, object):
    if object.data.type == 'ORTHO':
        layout.prop(object.data, 'ortho_scale', text='', emboss=False)
    else:
        if object.data.lens_unit == 'FOV':
            layout.prop(object.data, 'angle', text='', emboss=False)
        else:
            layout.prop(object.data, 'lens', text='', emboss=False)

class STORYTOOLS_OT_camera_options(bpy.types.Operator):
    bl_idname = "storytools.camera_options"
    bl_label = 'Camera Options Menu'
    bl_description = "Show camera options"
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
        return context.window_manager.invoke_props_dialog(self, width=150)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        # if self.sidebar_width <= 290:
        show_lens(col, self.object)
        col.operator('storytools.make_active_and_select', text='Select Camera', icon='RESTRICT_SELECT_OFF').name = self.object_name


        ## TODO: Test to remove useless cancel button (and eventually OK button).
        ## /!\ "template_popup_confirm" exists, only compatible with 4.2+
        # layout.template_popup_confirm("", text="Ok", cancel_text="")

    def execute(self, context):
        return {"FINISHED"}

class STORYTOOLS_UL_camera_list(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index): # , flt_flag
        # layout.label(text=item.name)
        # row = layout.row()
        row = layout.row(align=True)

        ## Check sidebar width for responsive UI
        sidebar_width = next((r.width for r in context.area.regions if r.type == 'UI'), 0) / context.preferences.system.ui_scale

        in_draw = False
        icon = 'CAMERA_DATA'
        cam = context.scene.camera
        if cam is not None:
            if item == cam:
                icon = 'OUTLINER_OB_CAMERA'
            elif cam.name == 'draw_cam' and cam in item.children:
                in_draw = True
                icon = 'CON_CAMERASOLVER'
        
        row.prop(item, 'name', icon=icon, text='', emboss=False)

        settings = context.scene.storytools_settings

        ## Show data when no single user (whill showup with Draw Cam)
        # if item.data.users > 1:
        #     row.template_ID(item, "data")
        # else:
        #     row.label(text='', icon='BLANK1')
        
        ## Show if had parent (not that interesting with cameras)
        # if item.parent:
        #     row.label(text='', icon='DECORATE_LINKED')
        # else:
        #     row.label(text='', icon='BLANK1')
        
        ## If draw_cam ops is available (>> Moved to side icons)
        # if hasattr(bpy.types, 'GP_OT_draw_cam_switch'):
        #     if in_draw:
        #         row.operator('gp.draw_cam_switch', text='', icon='LOOP_BACK', emboss=True)
        #     elif item == cam:
        #         row.operator('gp.draw_cam_switch', text='', icon='CON_CAMERASOLVER', emboss=True).cam_mode = 'draw'
        #         # row.label(text='', icon='DOT')
        #     else:
        #         row.label(text='', icon='BLANK1')

        # if item.visible_get():
        #     # row.label(text='', icon='HIDE_OFF')
        #     row.operator('storytools.visibility_toggle', text='', icon='HIDE_OFF', emboss=False).name = item.name
        # else:
        #     # row.label(text='', icon='HIDE_ON')
        #     row.operator('storytools.visibility_toggle', text='', icon='HIDE_ON', emboss=False).name = item.name

        if settings.show_cam_settings and sidebar_width > 310:
            show_lens(row, item)

            # Select camera # show only with big lateral bar
            row.operator('storytools.make_active_and_select', text='', icon='RESTRICT_SELECT_OFF').name = item.name
        else:
            ## Collapsed panel with infos
            op = row.operator('storytools.camera_options', text='', icon='THREE_DOTS', emboss=False)
            op.object_name = item.name
        # if sidebar_width <= 290:

    # Called once to draw filtering/reordering options.
    # def draw_filter(self, context, layout):
    #     pass

    # Called once to filter/reorder items.
    def filter_items(self, context, data, propname):

        flt_flags = []
        flt_neworder = []

        #### Do filtering/reordering here...
        ## data : scene struct -> propname: 'objects' string 
        objs = getattr(data, propname)
        # flt_flags = [self.bitflag_filter_item if o.type == 'CAMERA' else 0 for o in objs]
        
        ## Without manipulation camera
        flt_flags = [self.bitflag_filter_item if o.type == 'CAMERA' and o.name not in ('draw_cam', 'object_cam') else 0 for o in objs]
        
        ## By name
        # helper_funcs = bpy.types.UI_UL_list
        # flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, objs, "name", reverse=False)

        return flt_flags, flt_neworder

class STORYTOOLS_OT_set_focal(Operator):
    bl_idname = "storytools.set_focal"
    bl_label = 'Set Focal'
    bl_description = "Set focal on active camera"
    bl_options = {'REGISTER', 'INTERNAL'}

    lens : bpy.props.IntProperty(name='Focal')

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def execute(self, context):
        context.scene.camera.data.lens = self.lens
        return {"FINISHED"}

""" # Custom Presets
class STORYTOOLS_OT_add_focal_preset(AddPresetBase, Operator):
    '''Add a Camera Focal Preset'''
    bl_idname = "camera.focal_preset_add"
    bl_label = "Add Camera Focal Preset"
    preset_menu = "STORYTOOLS_MT_focal_presets"

    # variable used for all preset values
    preset_defines = [
        "cam = bpy.context.scene.camera"
    ]

    # properties to store in the preset
    preset_values = [
        "cam.data.lens",
    ]

    # where to store the preset
    preset_subdir = "camera/focal"
 """

classes=(
    # STORYTOOLS_OT_camera_change_focal,
    STORYTOOLS_OT_camera_options,
    STORYTOOLS_camera_collection,
    STORYTOOLS_UL_camera_list,
    STORYTOOLS_OT_set_focal,
    # STORYTOOLS_OT_add_focal_preset,
)

def register(): 
    ## For custom presets
    # preset_path = Path(bpy.utils.preset_paths('')[0])
    # focal_presets = preset_path / 'camera' / 'focal'
    # bundled_presets = Path(__package__, 'presets', 'camera', 'focal')
    # if not focal_presets.exists():
    #     focal_presets.mkdir(parents=True, exist_ok=True)
    #     for src_file in bundled_presets.iterdir():
    #         shutil.copy2(src_file, focal_presets / src_file.name)

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.st_camera_props = bpy.props.PointerProperty(type=STORYTOOLS_camera_collection)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.st_camera_props