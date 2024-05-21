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
    
    make_active : bpy.props.BoolProperty(
        name='Make Active',
        description="Make the new camera active",
        default=True)

    def invoke(self, context, event):
        cam_ct = len(bpy.data.cameras)
        self.name = f'Camera_{cam_ct+1:03d}'
        
        if any(m.camera for m in context.scene.timeline_markers):
            self.create_marker = True

        # return self.execute(context)
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, 'name')

        layout.prop(self, 'create_marker')
        if len(bpy.data.cameras):
            layout.label(text='There are camera markers in scene', icon='INFO')

        layout.prop(self, 'make_active')

        if context.space_data.region_3d.view_perspective == 'CAMERA':
            layout.label(text='Already in camera view', icon='INFO')
            layout.label(text='New camera will be at same place and same focal', icon='BLANK1')

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
        
        self.report({'INFO'}, f'{cam.name} Created')
        return {"FINISHED"}


classes = (STORYTOOLS_OT_create_camera,)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)