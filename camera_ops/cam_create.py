import bpy
from bpy.types import Operator

from .. import fn

def get_default_camera_name() -> str:
    """Return the incremental name used for a brand new camera"""
    cam_ct = len([o for o in bpy.data.objects if o.type == 'CAMERA'])
    return f'Camera_{cam_ct+1:03d}'


class STORYTOOLS_OT_create_camera(Operator):
    bl_idname = "storytools.create_camera"
    bl_label = "Create Camera"
    bl_description = "Create a camera with popup choices"
    bl_options = {"REGISTER", "UNDO"}

    name : bpy.props.StringProperty(
        name='Name',
        description="Name of Grease pencil object")

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

    copy_settings : bpy.props.BoolProperty(
        name='Copy Settings',
        description="Copy lens, clips and depth of field from the camera currently in view\
            \nOtherwise use the defaults of the addon preferences",
        default=True)

    ## Internal prop, set by invoke: the dialog only offers to copy settings when user is already looking through a camera view
    in_camera : bpy.props.BoolProperty(
        name='In Camera View',
        description="Viewport was looking through a camera when the operator was called",
        default=False, options={'SKIP_SAVE', 'HIDDEN'})

    ## Add local Dof toggle (reset by preferences on call)
    # use_dof : bpy.props.BoolProperty(
    #     name='Use Depth Of Field',
    #     description="Use Depth of field (default value can be changed in addon preferences > Settings > Camera)",
    #     default=False)

    def invoke(self, context, event):
        # self.use_dof = fn.get_addon_prefs().default_cam_use_dof
        self.name = get_default_camera_name()
        self.in_camera = context.space_data.region_3d.view_perspective == 'CAMERA' and context.scene.camera is not None

        if any(m.camera for m in context.scene.timeline_markers):
            self.create_marker = True

        # return self.execute(context)
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, 'name')

        layout.prop(self, 'make_active')
        if self.in_camera:
            col = layout.column(align=True)
            col.label(text='Already in camera view', icon='INFO')
            col.label(text='New camera will have same placement', icon='BLANK1')
            layout.prop(self, 'copy_settings', text='Copy Current Settings')
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

        ## Use or pop asset browser with cam search to use with 'Add To View' button.
        ## In the end directly show in camera sidebar
        # layout.separator()
        # col = layout.column(align=True)
        # col.use_property_split = False
        # col.label(text='Alternatively, you can use camera assets from browser')
        # col.operator('storytools.browse_assets', icon='ASSET_MANAGER').kind = 'CAMERA'
        # col.label(text="Then use browser's 'Add To View'", icon='INFO')


    def execute(self, context):
        already_in_cam = context.space_data.region_3d.view_perspective == 'CAMERA'

        scn = context.scene
        cam_ref = None
        is_cam_ref_active = is_cam_ref_selected = None
        if already_in_cam:
            cam_ref = scn.camera
            is_cam_ref_active = cam_ref == context.object
            is_cam_ref_selected = cam_ref.select_get()

        prefs = fn.get_addon_prefs()

        ## Name is set by invoke, fallback for a direct call (from a script or a keymap)
        name = self.name.strip() or get_default_camera_name()

        cam_data = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cam_data)

        if cam_ref and self.copy_settings:
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

        ## Placement always follows the viewed camera, whatever the settings choice
        if cam_ref:
            cam.matrix_world = cam_ref.matrix_world
        else:
            rv3d = bpy.context.region_data or context.space_data.region_3d
            cam.matrix_world = rv3d.view_matrix.inverted()

        ## Link in the collection dedicated to the cameras of current scene
        fn.get_camera_collection(scn).objects.link(cam)
        
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

        ## Transfer active and selection from cam ref (if any)
        if is_cam_ref_active:
            context.view_layer.objects.active = cam
        if is_cam_ref_selected:
            cam_ref.select_set(False)
            ## Should it deselect the previous cam ?
            cam.select_set(True)

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