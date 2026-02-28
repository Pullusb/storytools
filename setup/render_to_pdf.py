import bpy
from pathlib import Path
from bpy.props import StringProperty,BoolProperty
from bpy.types import Operator

class WORLD_OT_create_white_world(Operator):
    """Set World Background to White"""
    bl_idname = "world.create_white_world"
    bl_label = "Set White World"
    bl_description = "Set the world background color to white with nodes disabled"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get or create the world
        world_name = 'storyworld' # page_world
        world = bpy.data.worlds.get(world_name)
        if not world:
            world = next((w for w in bpy.data.worlds if w.name.startswith(world_name)), None)
        
        if not world:
            world = bpy.data.worlds.new(world_name)
            # Disable nodes
            world.use_nodes = False
            # Set background color to white
            world.color = (1.0, 1.0, 1.0)

        if world == context.scene.world:
            self.report({'INFO'}, 'World background already set')
            return {'CANCELLED'}
        ## Assign
        context.scene.world = world
        self.report({'INFO'}, 'World background replaced with "storyworld"')
        return {'FINISHED'}

class STORYTOOLS_OT_render_storyboard_images(Operator):
    bl_idname = "storytools.render_storyboard_images"
    bl_label = "Render Images"
    bl_description = "Set render filepath and render the storyboard images"
    bl_options = {'REGISTER', 'INTERNAL'}

    filepath: StringProperty(
        name="Filepath",
        description="Set the filepath for rendering images",
        default="",
        subtype='FILE_PATH',
    )

    set_range_to_marker: BoolProperty(
        name="Set Range To Marker",
        description="Set the render range to match the range of camera markers",
        default=False,
        options={'SKIP_SAVE'},
    )

    def invoke(self, context, event):
        ## prefill render output
        scn = context.scene
        if bpy.data.is_saved:
            blend_path = Path(bpy.data.filepath)
            folder_name = bpy.path.clean_name(blend_path.stem)
            self.filepath = f'//{folder_name}/{folder_name}_####'

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        scn = context.scene
        layout = self.layout

        ## Export path
        layout.label(text="Export Path:")
        layout.prop(self, "filepath", text="")
        
        # layout.label(text="Some options to consider")

        layout.separator()
        ## Film transparent
        layout.label(text="Background transparency:", icon='IMAGE_ALPHA')
        layout.label(text="For use in pdf, transparency is not an issue (Appear on white)", icon='INFO')
        layout.prop(scn.render, 'film_transparent', text='Film Transparent')

        if not scn.render.film_transparent:
            layout.separator()
            layout.label(text="World:", icon='WORLD')
            if not scn.world:
                layout.label(text="No world set, background will appear black", icon='ERROR')
            layout.label(text="With transparency off, you may want to set a white background", icon='BLANK1')
            layout.operator("world.create_white_world", text="Set White World", icon='WORLD')

        layout.separator()
        ## Color management
        layout.label(text="Color management View transform", icon='IMAGE_ALPHA')
        layout.prop(context.scene.view_settings, 'view_transform')
        
        if context.scene.view_settings.view_transform != 'Standard':
            row=layout.row()
            row.label(text='View transform is not "Standard"', icon='INFO')
            op = row.operator("storytools.info_note", text="", icon="QUESTION")
            op.title = "Color Management"
            op.text = """Most View transforms, like Agx or Filmic deliver more desaturated color.
Thoses are best for photorealistic rendering,
but may not be suitable for storyboards.
If you want "direct" colors, set it to 'Standard'"""

        layout.separator()
        ## Range check
        marker_frames = [m.frame for m in scn.timeline_markers if m.camera and m.name.startswith('stb')]
        if marker_frames:
            min_frame = min(marker_frames)
            max_frame = max(marker_frames)
            if min_frame != scn.frame_start or max_frame != scn.frame_end:
                layout.label(text="Render Range", icon='TIME')
                layout.label(text="Set timeline range to stb camera markers ?")
                layout.label(text=f"Marker range: {min_frame} - {max_frame}")
                layout.prop(self, "set_range_to_marker", text="Set Range to Marker")

        ## Format ?

    def execute(self, context):
        scn = context.scene
        if not self.filepath:
            self.report({'ERROR'}, "No filepath set for rendering")
            return {'CANCELLED'}

        scn.render.filepath = self.filepath

        if self.set_range_to_marker:
            marker_frames = [m.frame for m in scn.timeline_markers if m.camera and m.name.startswith('stb')]
            if marker_frames:
                min_frame = min(marker_frames)
                max_frame = max(marker_frames)
                scn.frame_start = min_frame
                scn.frame_end = max_frame

        bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
        return {'FINISHED'}


# Registration
classes = (
    WORLD_OT_create_white_world,
    STORYTOOLS_OT_render_storyboard_images,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
