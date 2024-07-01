import bpy
from bpy.types import Operator

from .. import fn

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
    
    ## TODO : with SPA sequencer, make it active for current shot
    make_active : bpy.props.BoolProperty(
        name='Make Active',
        description="Make the new camera active",
        default=True)
    
    enter_camera : bpy.props.BoolProperty(
        name='Enter Camera',
        description="Enter in newly created camera view",
        default=True)

    def invoke(self, context, event):
        # cam_ct = len(bpy.data.cameras)
        cam_ct = len([o for o in bpy.data.objects if o.type == 'CAMERA'])
        self.name = f'Camera_{cam_ct+1:03d}'
        
        if any(m.camera for m in context.scene.timeline_markers):
            self.create_marker = True

        # return self.execute(context)
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, 'name')

        layout.prop(self, 'make_active')
        if context.space_data.region_3d.view_perspective == 'CAMERA':
            col = layout.column(align=True)
            col.label(text='Already in camera view', icon='INFO')
            col.label(text='New camera will be at same place and same focal', icon='BLANK1')
        else:
            row = layout.row()
            row.active = self.make_active
            row.prop(self, 'enter_camera')

        row =  layout.row()

        row.prop(self, 'create_marker')
        info = row.operator('storytools.info_note', text='', icon='QUESTION', emboss=False)
        info.title = 'Camera Marker Creation'
        info.text = 'This will bind camera to a new marker at current frame\
            \nA camera-bound marker changes the active camera when playhead is at marker position\
            \nMarkers behave like keys,they can be selected/renamed/moved/deleted in timeline editors'
        if any(m.camera for m in context.scene.timeline_markers):
            layout.label(text='There are camera markers in scene', icon='INFO')
            # layout.label(text='A camera marker', icon='BLANK1')
        else:
            if self.create_marker:
                col = layout.column(align=True)
                col.label(text='Add new marker and bind camera at current frame', icon='INFO')


    def execute(self, context):
        already_in_cam = context.space_data.region_3d.view_perspective == 'CAMERA'

        scn = context.scene
        cam_ref = None
        if already_in_cam:
            cam_ref = scn.camera
        
        cam_data = bpy.data.cameras.new(self.name)
        cam = bpy.data.objects.new(self.name, cam_data)
        if already_in_cam:
            ## Copy settings from previous camera
            cam.matrix_world = cam_ref.matrix_world
            cam_data.lens = cam_ref.data.lens
            cam_data.clip_start = cam_ref.data.clip_start
            cam_data.clip_end = cam_ref.data.clip_end
        else:
            ## TODO place according to view
            area = bpy.context.area            
            rv3d = bpy.context.region_data
            cam.matrix_world = rv3d.view_matrix.inverted()
            # cam_data.lens = area.spaces.active.lens

        ## Link in active collection or create a dedicated collection for current scene
        ## using scene name in collection name might allow identification on multi_scene...

        camera_collection_name = f'cam_{context.scene.name}'
        cam_col = bpy.data.collections.get(camera_collection_name)
        if not cam_col:
            cam_col = bpy.data.collections.new(camera_collection_name)
            scn.collection.children.link(cam_col)
        cam_col.objects.link(cam)
        
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

        # new_gp_index = next((i for i, o in enumerate(scn.objects) if o.type == 'GPENCIL' and context.object == o), None)
        # if new_gp_index is not None:
        #     scn.gp_object_props['index'] = new_gp_index

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