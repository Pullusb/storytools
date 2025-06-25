## Render images and create a PDF

## bl_infos for potential standalone addon
# bl_info = {
#     "name": "Render Images to PDF",
#     "description": "Create PDF documents from rendered images using img2pdf",
#     "author": "Samuel Bernou",
#     "version": (1, 0, 0),
#     "blender": (4, 0, 0),
#     "location": "Render Properties > Render Images to PDF",
#     "warning": "",
#     "doc_url": "",
#     "category": "Render",
# }

import bpy
import os
import subprocess
import sys
from pathlib import Path
from bpy.props import StringProperty, CollectionProperty, BoolProperty
from bpy.types import Operator, Panel, PropertyGroup
from bpy_extras.io_utils import ImportHelper


def check_img2pdf_available():
    """Check if img2pdf module is available for import."""
    try:
        import img2pdf
        return True
    except ImportError:
        return False

def get_render_output_path():
    """Get the current render output directory using pathlib."""
    scene = bpy.context.scene
    render = scene.render
    filepath = render.filepath
    
    if not filepath:
        return None
    
    # Convert to Path object and get parent directory
    render_path = Path(os.path.abspath(bpy.path.abspath(filepath)))
    
    # If it's a file path, get the directory above)
    if render_path.suffix or render_path.name.endswith(('.', '#', '-', '_')):
        return render_path.parent
    else:
        return render_path

def get_export_pdf_name():
    if bpy.data.is_saved:
        # Use the current blend file name as base
        return Path(bpy.data.filepath).with_suffix('.pdf').name

    if (outpath := get_render_output_path()):
        stem = bpy.path.clean_name(outpath.stem.rstrip(('_#-./')))
        return outpath.with_stem(stem).with_suffix('.pdf').name
    
    else:
        return "Storyboard.pdf"

def get_image_files(directory):
    """Get all image files from a directory using pathlib."""
    if not directory or not directory.exists():
        return []
    
    # Common image extensions
    
    image_files = []
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in bpy.path.extensions_image:
            image_files.append(file_path)
    
    # Sort files naturally
    return sorted(image_files, key=lambda x: x.name.lower())


class RENDER_OT_install_img2pdf(Operator):
    """Install img2pdf module using pip"""
    bl_idname = "render.install_img2pdf"
    bl_label = "Install img2pdf"
    bl_description = "Install the img2pdf module required for PDF creation"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            # Get Python executable path
            python_exe = Path(sys.executable)
            
            # Install img2pdf using pip
            subprocess.check_call([
                str(python_exe), "-m", "pip", "install", "img2pdf"
            ])
            
            self.report({'INFO'}, "img2pdf module installed successfully!")
            return {'FINISHED'}
            
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f"Failed to install img2pdf: {e}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Unexpected error during installation: {e}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def draw(self, context):
        layout = self.layout
        layout.label(text="This will install the img2pdf module")
        layout.label(text="using pip. Continue?")


class RENDER_OT_images_to_pdf_all(Operator):
    """Create PDF from all images in render output folder"""
    bl_idname = "render.images_to_pdf_all"
    bl_label = "All Render Images to PDF"
    bl_description = "Create PDF from all images in the current render output folder"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Check if img2pdf is available
        if not check_img2pdf_available():
            bpy.ops.render.show_img2pdf_missing('INVOKE_DEFAULT')
            return {'CANCELLED'}

        # Get render output directory
        render_dir = get_render_output_path()
        if not render_dir:
            self.report({'ERROR'}, "No render output path set")
            return {'CANCELLED'}

        if not render_dir.exists():
            self.report({'ERROR'}, f"Render output directory does not exist: {render_dir}")
            return {'CANCELLED'}

        # Get all image files
        image_files = get_image_files(render_dir)
        if not image_files:
            self.report({'WARNING'}, f"No image files found in: {render_dir}")
            return {'CANCELLED'}

        # Create PDF
        try:
            import img2pdf
            
            # Create output PDF path
            pdf_path = render_dir / get_export_pdf_name()
            # pdf_path = render_dir.parent / get_export_pdf_name()
            
            # Convert images to PDF
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert([str(img) for img in image_files]))
            
            self.report({'INFO'}, f"PDF created: {pdf_path} ({len(image_files)} images)")
            ## Open created PDF
            if pdf_path.exists():
                bpy.ops.wm.path_open(filepath=str(pdf_path))
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create PDF: {e}")
            return {'CANCELLED'}


class RENDER_OT_images_to_pdf_selected(Operator, ImportHelper):
    """Create PDF from selected images using file browser"""
    bl_idname = "render.images_to_pdf_selected"
    bl_label = "Selected Images to PDF"
    bl_description = "Create PDF from selected images using file browser"
    bl_options = {'REGISTER'}

    # File browser properties
    filter_image: BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    filter_folder: BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    
    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )
    
    directory: StringProperty(
        subtype='DIR_PATH',
    )

    pdf_name: StringProperty(
        name="PDF Name",
        description="Name for the output PDF file",
        default='Storyboard',
        # maxlen=255,
    )

    def invoke(self, context, event):
        # Set default directory to render output if available
        render_dir = get_render_output_path()
        if render_dir and render_dir.exists():
            self.directory = str(render_dir)
        
        if not str(self.pdf_name).strip() == '' or str(self.pdf_name) == 'Storyboard':
            ## if not already customized by user, defaut to automatic export name
            self.pdf_name = Path(get_export_pdf_name()).stem
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    # def draw(self, context):
    #     self.layout.prop(self, "pdf_name", text="PDF Name")

    def execute(self, context):
        # Check if img2pdf is available
        if not check_img2pdf_available():
            bpy.ops.render.show_img2pdf_missing('INVOKE_DEFAULT')
            return {'CANCELLED'}

        if not self.files:
            self.report({'WARNING'}, "No files selected")
            return {'CANCELLED'}

        # Build list of selected image files
        directory = Path(self.directory)
        selected_files = []
        
        for file_elem in self.files:
            file_path = directory / file_elem.name
            if file_path.exists() and file_path.is_file():
                selected_files.append(file_path)

        if not selected_files:
            self.report({'WARNING'}, "No valid image files selected")
            return {'CANCELLED'}

        # Sort files
        selected_files.sort(key=lambda x: x.name.lower())

        # Create PDF
        try:
            import img2pdf
            
            # Create output PDF path in same directory as selected images
            # pdf_path = directory / get_export_pdf_name() # Automatic naming

            if self.pdf_name.strip():
                final_name = self.pdf_name
                final_name = str(Path(final_name).with_suffix('.pdf'))
            else:
                final_name = get_export_pdf_name()

            pdf_path = directory / final_name
            
            # Convert images to PDF
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert([str(img) for img in selected_files]))

            self.report({'INFO'}, f"PDF created: {pdf_path} ({len(selected_files)} images)")
            if pdf_path.exists():
                bpy.ops.wm.path_open(filepath=str(pdf_path))
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create PDF:\n{e}")
            return {'CANCELLED'}


class RENDER_OT_show_img2pdf_missing(Operator):
    """Show dialog when img2pdf module is missing"""
    bl_idname = "render.show_img2pdf_missing"
    bl_label = "img2pdf Module Required"
    bl_description = "Show information about missing img2pdf module"
    bl_options = {'REGISTER', 'INTERNAL'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="The img2pdf module is required for PDF creation.", icon='ERROR')
        layout.separator()
        col = layout.column(align=True)
        col.label(text="This module is not currently installed in your")
        col.label(text="Blender Python environment.")
        layout.separator()
        layout.label(text="Click to install:")
        layout.separator()
        layout.operator("render.install_img2pdf", icon='IMPORT')

    def execute(self, context):
        return {'FINISHED'}

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

        ## Assign
        context.scene.world = world
        self.report({'INFO'}, "World background replace with a full white")
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
        # layout.label(text="These option might be of interest:")
        # layout.separator()

        ## Film transparent
        layout.label(text="Background transparency:", icon='IMAGE_ALPHA')
        layout.label(text="For pdf creation, transparency is not an issue (Appear on white)", icon='INFO')
        layout.prop(scn.render, 'film_transparent', text='Film Transparent')

        if not scn.render.film_transparent:
            layout.separator()
            layout.label(text="World:", icon='WORLD')
            if not scn.world:
                layout.label(text="No world set, background will appear black", icon='ERROR')
            layout.label(text="Without transparent, you may want to set a white world", icon='BLANK1')
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
That's best for photorealistic rendering,
but may not be suitable for storyboards.
If you want the "direct" colors, set it to 'Standard'"""

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

        ## We want to keep if 
        bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
        ## Launch PDF export right away ?
        return {'FINISHED'}


## Menu to use in storytools
class STORYTOOLS_MT_export_storyboard_to_pdf(bpy.types.Menu):
    """Storyboard export to pdf menu"""
    bl_label = "Create PDF From Images"
    bl_idname = "STORYTOOLS_MT_export_storyboard_to_pdf"

    def draw(self, context):
        layout = self.layout
        
        img2pdf_available = check_img2pdf_available()
        
        if not img2pdf_available:
            col = layout.column(align=True)
            col.label(text="img2pdf module not found", icon='ERROR')
            col.operator("render.install_img2pdf", icon='IMPORT')
            col.separator()

        col = layout.column(align=False)
        col.enabled = img2pdf_available

        col.operator("render.images_to_pdf_all", 
                    text="From Rendered Images", # Create PDF From Rendered Images
                    icon='FILE_IMAGE')
        
        col.operator("render.images_to_pdf_selected", 
                    text="From Files Selection", # Create PDF From Selected Files
                    icon='FILEBROWSER')

## Panel to use as standalone pdf creation tool.
# class RENDER_PT_images_to_pdf_panel(Panel):
#     """Panel in Render Properties for PDF creation tools"""
#     bl_label = "Render Images to PDF"
#     bl_idname = "RENDER_PT_images_to_pdf"
#     bl_space_type = 'PROPERTIES'
#     bl_region_type = 'WINDOW'
#     bl_context = "render"

#     def draw(self, context):
#         layout = self.layout
        
#         # Check if img2pdf is available
#         img2pdf_available = check_img2pdf_available()
        
#         if not img2pdf_available:
#             box = layout.box()
#             box.label(text="img2pdf module not found", icon='ERROR')
#             box.operator("render.install_img2pdf", icon='IMPORT')
#             layout.separator()

#         # Current render output info
#         render_dir = get_render_output_path()
#         if render_dir:
#             layout.label(text="Current Render Output:")
#             layout.label(text=str(render_dir), icon='FOLDER_REDIRECT')
            
#             if render_dir.exists():
#                 image_count = len(get_image_files(render_dir))
#                 layout.label(text=f"Images found: {image_count}")
#             else:
#                 layout.label(text="Directory does not exist", icon='ERROR')
#         else:
#             layout.label(text="No render output path set", icon='ERROR')

#         layout.separator()

#         # PDF creation operators
#         col = layout.column(align=True)
#         col.enabled = img2pdf_available
        
#         col.operator("render.images_to_pdf_all", 
#                     text="Create PDF from All Render Images", 
#                     icon='FILE_IMAGE')
        
#         col.operator("render.images_to_pdf_selected", 
#                     text="Create PDF from Selected Images", 
#                     icon='FILEBROWSER')


# Registration
classes = (
    WORLD_OT_create_white_world,
    STORYTOOLS_OT_render_storyboard_images,
    RENDER_OT_install_img2pdf,
    RENDER_OT_show_img2pdf_missing,
    RENDER_OT_images_to_pdf_all,
    RENDER_OT_images_to_pdf_selected,
    STORYTOOLS_MT_export_storyboard_to_pdf, # menu instanciated in setup/ui
    # RENDER_PT_images_to_pdf_panel, # standalone panel
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
