## Create a grid of panel suitable for static storyboard or quick thumbnails.
# 1.5

import bpy
import shutil

from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty, StringProperty
from bpy.types import Operator, Panel, Menu
# from bpy_extras.io_utils import ExportHelper, ImportHelper
from bl_operators.presets import AddPresetBase
from mathutils import Vector
from pathlib import Path

from ..constants import FONT_DIR, PRESETS_DIR, IMAGES_DIR
from .. import fn

# Preset system for storyboard settings
class STORYTOOLS_MT_storyboard_presets(Menu):
    """Storyboard presets menu"""
    bl_label = "Storyboard Presets"
    bl_idname = "STORYTOOLS_MT_storyboard_presets"
    preset_subdir = "storytools/storyboard"
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset

class STORYTOOLS_OT_add_storyboard_preset(AddPresetBase, Operator):
    """Add or remove a storyboard preset"""
    bl_idname = "storytools.add_storyboard_preset"
    bl_label = "Add Storyboard Preset"
    bl_description = "Add or remove a storyboard preset"
    preset_menu = "STORYTOOLS_MT_storyboard_presets"
    
    # Variable used for all preset values
    preset_defines = [
        "op = bpy.context.active_operator",
    ]
    
    # Properties to store in the preset (excluding operational properties)
    preset_values = [
        "op.canvas_x",
        "op.canvas_y", 
        "op.canvas_preset",
        "op.canvas_margin",
        "op.line_radius",
        "op.rows",
        "op.columns",
        "op.panel_margin_x",
        "op.panel_margin_y",
        "op.coverage",
        "op.frame_ratio",
        "op.custom_ratio_x",
        "op.custom_ratio_y", 
        "op.use_custom_xy",
        "op.ratio_preset",
        "op.include_notes",
        "op.notes_width_percent",
        "op.notes_header_height",
        "op.show_notes_frames",
        "op.create_text_objects",
        "op.use_custom_font",
        "op.note_text_format",
        "op.panel_header_left",
        "op.panel_header_right",
        "op.num_pages",
        "op.page_spacing",
        "op.include_page_header",
        "op.page_header_height",
        "op.enable_page_head_left",
        "op.page_head_left",
        "op.page_head_left_linked",
        "op.enable_page_head_center", 
        "op.page_head_center",
        "op.page_head_center_linked",
        "op.enable_page_head_right",
        "op.page_head_right",
        "op.page_head_right_linked",
        "op.include_page_footer",
        "op.page_footer_height",
        "op.enable_page_foot_left",
        "op.page_foot_left",
        "op.page_foot_left_linked",
        "op.enable_page_foot_center",
        "op.page_foot_center", 
        "op.page_foot_center_linked",
        "op.enable_page_foot_right",
        "op.enable_footer_logo",
        "op.footer_logo_path",
        "op.footer_logo_height",
        "op.show_canvas_frame",
        "op.create_camera",
        "op.camera_margin",
        "op.add_timeline_markers",
    ]
    
    preset_subdir = "storytools/storyboard"

'''
class STORYTOOLS_OT_export_storyboard_preset(Operator, ExportHelper):
    """Export current storyboard settings as a preset file"""
    bl_idname = "storytools.export_storyboard_preset"
    bl_label = "Export Storyboard Preset"
    bl_description = "Export current storyboard settings to a .py preset file"
    
    filename_ext = ".py"
    filter_glob: StringProperty(default="*.py", options={'HIDDEN'})
    
    def execute(self, context):
        # Get the active operator (should be the storyboard operator)
        if hasattr(context, 'active_operator') and hasattr(context.active_operator, 'canvas_x'):
            op = context.active_operator
        else:
            self.report({'ERROR'}, "No active storyboard operator found")
            return {'CANCELLED'}
        
        # Create preset content
        preset_content = [
            "import bpy",
            "op = bpy.context.active_operator",
            "",
        ]
        
        # Add all preset values
        preset_values = [
            "op.canvas_x",
            "op.canvas_y", 
            "op.canvas_margin",
            "op.line_radius",
            "op.rows",
            "op.columns",
            "op.panel_margin_x",
            "op.panel_margin_y",
            "op.coverage",
            "op.frame_ratio",
            "op.custom_ratio_x",
            "op.custom_ratio_y", 
            "op.use_custom_xy",
            "op.ratio_preset",
            "op.include_notes",
            "op.notes_width_percent",
            "op.notes_header_height",
            "op.show_notes_frames",
            "op.create_text_objects",
            "op.use_custom_font",
            "op.note_text_format",
            "op.panel_header_left",
            "op.panel_header_right",
            "op.num_pages",
            "op.page_spacing",
            "op.include_page_header",
            "op.page_header_height",
            "op.enable_page_head_left",
            "op.page_head_left",
            "op.page_head_left_linked",
            "op.enable_page_head_center", 
            "op.page_head_center",
            "op.page_head_center_linked",
            "op.enable_page_head_right",
            "op.page_head_right",
            "op.page_head_right_linked",
            "op.include_page_footer",
            "op.page_footer_height",
            "op.enable_page_foot_left",
            "op.page_foot_left",
            "op.page_foot_left_linked",
            "op.enable_page_foot_center",
            "op.page_foot_center", 
            "op.page_foot_center_linked",
            "op.enable_page_foot_right",
            "op.enable_footer_logo",
            "op.footer_logo_path",
            "op.footer_logo_height",
            "op.show_canvas_frame",
            "op.create_camera",
            "op.camera_margin",
            "op.add_timeline_markers",
        ]
        
        for prop_path in preset_values:
            prop_name = prop_path.split('.')[-1]
            try:
                value = getattr(op, prop_name)
                if isinstance(value, str):
                    preset_content.append(f'{prop_path} = "{value}"')
                else:
                    preset_content.append(f'{prop_path} = {repr(value)}')
            except AttributeError:
                continue
        
        # Write to file
        try:
            with open(self.filepath, 'w') as f:
                f.write('\n'.join(preset_content))
            self.report({'INFO'}, f"Preset exported to {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export preset: {str(e)}")
            return {'CANCELLED'}

class STORYTOOLS_OT_import_storyboard_preset(Operator, ImportHelper):
    """Import storyboard settings from a preset file"""
    bl_idname = "storytools.import_storyboard_preset"
    bl_label = "Import Storyboard Preset"
    bl_description = "Import storyboard settings from a .py preset file"
    
    filename_ext = ".py"
    filter_glob: StringProperty(default="*.py", options={'HIDDEN'})
    
    def execute(self, context):
        # Check if we have an active storyboard operator
        if not (hasattr(context, 'active_operator') and hasattr(context.active_operator, 'canvas_x')):
            self.report({'ERROR'}, "No active storyboard operator found")
            return {'CANCELLED'}
        
        try:
            # Read and execute the preset file
            with open(self.filepath, 'r') as f:
                preset_code = f.read()
            
            # Create a safe execution environment
            exec_globals = {
                'bpy': bpy,
                '__builtins__': {'True': True, 'False': False}
            }
            exec_locals = {}
            
            exec(preset_code, exec_globals, exec_locals)
            
            self.report({'INFO'}, f"Preset imported from {self.filepath}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import preset: {str(e)}")
            return {'CANCELLED'}
'''

class STORYTOOLS_OT_create_static_storyboard_pages(Operator):
    bl_idname = "storytools.create_static_storyboard_pages"
    bl_label = "Create Static Storyboard Pages"
    bl_description = "Generate a modulable storyboard grid\
        \nAdjust settings in redo panel\
        \nFor performance, set the number of pages after everything else (leave at 1 during setup)"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Canvas presets
    canvas_preset: EnumProperty(
        name="Canvas",
        description="Predefined canvas sizes",
        items=[
            ('A4_PORTRAIT', "A4 Portrait", "A4 portrait format (10.5 x 14.85)"),
            ('A4_LANDSCAPE', "A4 Landscape", "A4 landscape format (14.85 x 10.5)"),
            ('16_9_LARGE', "16:9", "16:9 format (20 x 11.25)"),
            # ('16_9_MEDIUM', "16:9 Medium", "Medium 16:9 format (16 x 9)"),
            ('SQUARE_LARGE', "Square", "square format (15 x 15)"),
            # ('SQUARE_MEDIUM', "Square Medium", "Medium square format (12 x 12)"),
            ('CUSTOM', "Custom", "Custom canvas dimensions"),
        ],
        default='A4_PORTRAIT'
    )
    
    # Canvas dimensions
    canvas_x: FloatProperty(
        name="Canvas Width",
        description="Width of the canvas",
        default=10.5,
        min=0.1,
        max=100.0,
        step=1,
        precision=2
    )
    
    canvas_y: FloatProperty(
        name="Canvas Height", 
        description="Height of the canvas",
        default=14.85,
        min=0.1,
        max=100.0,
        step=1,
        precision=2
    )
    
    canvas_margin: FloatProperty(
        name="Canvas Margin",
        description="Margin from canvas edges",
        default=0.4,
        min=0.0,
        max=10.0,
        step=0.1,
        precision=2
    )

    line_radius: FloatProperty(
        name="Line Thickness",
        description="Thickness of the lines",
        default=0.01,
        min=0.0001,
        max=0.5,
        step=0.001,
        precision=2
    )
    
    # Grid dimensions
    rows: IntProperty(
        name="Rows",
        description="Number of rows in the grid",
        default=3,
        min=1,
        max=20
    )
    
    columns: IntProperty(
        name="Columns",
        description="Number of columns in the grid", 
        default=1,
        min=1,
        max=20
    )
    
    # Panel margins (separate X and Y)
    panel_margin_x: FloatProperty(
        name="Panel Margin X",
        description="Horizontal space between panels in the grid",
        default=0.3,
        min=0.0,
        max=2.0,
        step=0.1,
        precision=2
    )
    
    panel_margin_y: FloatProperty(
        name="Panel Margin Y",
        description="Vertical space between panels in the grid",
        default=0.3,
        min=0.0,
        max=2.0,
        step=0.1,
        precision=2
    )
    
    # Frame settings
    coverage: FloatProperty(
        name="Coverage (%)",
        description="Percentage of space each frame occupies within its allocated area",
        default=90.0,
        min=10.0,
        max=100.0,
        step=1,
        precision=1
    )
    
    frame_ratio: FloatProperty(
        name="Frame Ratio",
        description="Width/Height ratio of frames",
        default=1.778,
        min=0.1,
        max=10.0,
        step=0.01,
        precision=3
    )
    
    custom_ratio_x: FloatProperty(
        name="X",
        description="Custom ratio width value",
        default=16.0,
        min=0.1,
        max=100.0,
        step=1,
        precision=1
    )
    
    custom_ratio_y: FloatProperty(
        name="Y", 
        description="Custom ratio height value",
        default=9.0,
        min=0.1,
        max=100.0,
        step=1,
        precision=1
    )
    
    use_custom_xy: BoolProperty(
        name="Use X:Y Values",
        description="Use X:Y values instead of direct ratio",
        default=False
    )
    
    ratio_preset: EnumProperty(
        name="Ratio Preset",
        description="Common aspect ratio presets",
        items=[
            ('CUSTOM', "Custom", "Use custom ratio"),
            ('16_9', "16:9 - Widescreen", "16:9 aspect ratio (1.778)"),
            ('16_10', "16:10 - Computer Monitor", "16:10 aspect ratio (1.600)"),
            ('4_3', "4:3 - Standard TV", "4:3 aspect ratio (1.333)"),
            ('3_2', "3:2 - 35mm Film", "3:2 aspect ratio (1.500)"),
            ('185_1', "1.85:1 - Academy Flat", "1.85:1 aspect ratio (1.850)"),
            ('235_1', "2.35:1 - CinemaScope", "2.35:1 aspect ratio (2.350)"),
            ('1_1', "1:1 - Square", "Square aspect ratio (1.000)"),
            ('9_16', "9:16 - Portrait", "Portrait 9:16 (0.563)"),
        ],
        default='16_9'
    )
    
    # Notes space
    include_notes: BoolProperty(
        name="Include Notes Space",
        description="Reserve space on the right for action and dialog notes",
        default=True
    )
    
    notes_width_percent: FloatProperty(
        name="Notes Width (%)",
        description="Percentage of panel width to reserve for notes",
        default=45.0,
        min=10.0,
        max=80.0,
        soft_max=50.0,
        step=1,
        precision=1
    )
    
    notes_header_height: FloatProperty(
        name="Notes Header Height",
        description="Height reserved for scene/panel number at top of notes area",
        default=0.46,
        min=0.0,
        soft_max=1.0,
        max=4.0,
        step=0.1,
        precision=2
    )
    
    show_notes_frames: BoolProperty(
        name="Show Notes Frames",
        description="Show frame lines around the notes area (enclosing whole panel)",
        default=True
    )
    
    # Text objects
    create_text_objects: BoolProperty(
        name="Create Text Objects",
        description="Create text objects in the notes area for each panel",
        default=True
    )

    use_custom_font: BoolProperty(
        name="Custom Font",
        description="Load a custom font for text objects\
            \nAllow use of Bold, Italic and Bold-Italic styles in notes\
            \nFont is packed into blend file to avoid linking issues",
        default=True
    )

    note_text_format: EnumProperty(
        name="Text",
        description="Initial text to add in each panel notes area",
        items=[
            ('None', "Nothing", "No title in text area"),
            ('Notes', "Notes", "Add Note title text in text area"),
            ('ActionDialog', "Action/Dialog", "Add Action and Dialog titles in text area"),
            ('ActionDialogLighting', "Action/Dialog/Lighting", "Add Action, Dialog and Lighting titles in text area"),
        ],
        default='Notes'
    )
    
    # Panel header text fields
    panel_header_left: StringProperty(
        name="Left Header",
        description="Text for left side of panel header",
        default="SC: ", # Or "S "
        maxlen=64
    )
    
    panel_header_right: StringProperty(
        name="Right Header",
        description="Text for right side of panel header",
        default="/", # Or "Panel: "
        maxlen=64
    )
    
    # Multiple pages
    num_pages: IntProperty(
        name="Number of Pages",
        description="Number of pages to create (stacked vertically)",
        default=1,
        min=1,
        soft_max=100,
        max=1000
    )
    
    page_spacing: FloatProperty(
        name="Page Spacing",
        description="Vertical spacing between pages",
        default=0.0,
        min=0.0,
        max=5.0,
        step=0.1,
        precision=2
    )
    
    # Page Header Properties
    include_page_header: BoolProperty(
        name="Include Page Header",
        description="Add header text at the top of each page",
        default=True
    )
    
    page_header_height: FloatProperty(
        name="Header Height",
        description="Height reserved for page header",
        default=0.2,
        min=0.1,
        max=2.0,
        step=0.1,
        precision=2
    )
    
    # Header text locations
    enable_page_head_left: BoolProperty(
        name="Enable Left",
        description="Enable left header text",
        default=True
    )
    
    page_head_left: StringProperty(
        name="Left Text",
        description="Left header text",
        default="Project: ",
        maxlen=256
    )
    
    page_head_left_linked: BoolProperty(
        name="Linked",
        description="Share text data across all pages",
        default=True
    )
    
    enable_page_head_center: BoolProperty(
        name="Enable Center",
        description="Enable center header text",
        default=False
    )
    
    page_head_center: StringProperty(
        name="Center Text",
        description="Center header text",
        default="Sequence: ",
        maxlen=256
    )
    
    page_head_center_linked: BoolProperty(
        name="Linked",
        description="Share text data across all pages",
        default=True
    )
    
    enable_page_head_right: BoolProperty(
        name="Enable Right",
        description="Enable right header text",
        default=True
    )
    
    page_head_right: StringProperty(
        name="Right Text",
        description="Right header text",
        default="Company: ",
        maxlen=256
    )
    
    page_head_right_linked: BoolProperty(
        name="Linked",
        description="Share text data across all pages",
        default=True
    )
    
    # Page Footer Properties
    include_page_footer: BoolProperty(
        name="Include Page Footer",
        description="Add footer text at the bottom of each page",
        default=True
    )
    
    page_footer_height: FloatProperty(
        name="Footer Height",
        description="Height reserved for page footer",
        default=0.2,
        min=0.1,
        max=2.0,
        step=0.1,
        precision=2
    )
    
    # Footer text locations
    enable_page_foot_left: BoolProperty(
        name="Enable Left",
        description="Enable left footer text",
        default=True
    )
    
    page_foot_left: StringProperty(
        name="Left Text",
        description="Left footer text",
        default="Artist: ",
        maxlen=256
    )
    
    page_foot_left_linked: BoolProperty(
        name="Linked",
        description="Share text data across all pages",
        default=True
    )
    
    enable_page_foot_center: BoolProperty(
        name="Enable Center",
        description="Enable center footer text",
        default=False
    )
    
    page_foot_center: StringProperty(
        name="Center Text",
        description="Center footer text",
        default="Date: ",
        maxlen=256
    )
    
    page_foot_center_linked: BoolProperty(
        name="Linked",
        description="Share text data across all pages",
        default=True
    )
    
    enable_page_foot_right: BoolProperty(
        name="Enable Right",
        description="Enable right footer text (pagination is always enabled)",
        default=True
    )
    
    # Footer Logo Properties
    enable_footer_logo: BoolProperty(
        name="Enable Footer Logo",
        description="Add a logo image to the bottom left of the footer",
        default=False
    )
    
    footer_logo_path: StringProperty(
        name="Logo Path",
        description="Path to the logo image file",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
    )
    
    footer_logo_height: FloatProperty(
        name="Logo Height (%)",
        description="Height of the logo as percentage of available footer space",
        default=65.0,
        min=1,
        soft_min=10.0,
        max=200,
        soft_max=95.0,
        step=5.0,
        precision=1
    )
    
    # Canvas frame
    show_canvas_frame: BoolProperty(
        name="Show Canvas Frame",
        description="Add a border around the canvas to visualize its bounds",
        default=False
    )
    
    # Camera setup
    create_camera: BoolProperty(
        name="Create Cameras",
        description="Create orthographic camera(s) to frame the storyboard pages",
        default=True
    )
    
    camera_margin: FloatProperty(
        name="Camera Margin",
        description="Extra space around the canvas for the camera view",
        default=0.0,
        min=0.0,
        max=5.0,
        step=0.1,
        precision=2
    )
    
    # Timeline markers
    add_timeline_markers: BoolProperty(
        name="Add Timeline Markers",
        description="Add timeline markers bound to camera frame numbers",
        default=True
    )
    
    force_new_object: BoolProperty(
        name="Create New Object",
        description="Force creation of a new grease pencil object instead of using the active one",
        default=False
    )

    remove_pre_generated: BoolProperty(
        name="Remove Pre-generated Elements",
        description="Remove all previously generated text objects, cameras, and timeline markers before creating new ones",
        default=True
    )
    
    def _validate_image_path(self, filepath):
        """Validate if the path points to a valid image file"""
        if not filepath:
            return False
        
        path = Path(filepath)
        if not path.exists():
            return False
        
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tga', '.tiff', '.tif', '.exr', '.hdr'}
        return path.suffix.lower() in valid_extensions
    
    def update_canvas_preset(self, context):
        """Update canvas dimensions based on preset"""
        if self.canvas_preset == 'A4_PORTRAIT':
            self.canvas_x = 10.5
            self.canvas_y = 14.85
        elif self.canvas_preset == 'A4_LANDSCAPE':
            self.canvas_x = 14.85
            self.canvas_y = 10.5
        elif self.canvas_preset == '16_9_LARGE':
            self.canvas_x = 20.0
            self.canvas_y = 11.25
        elif self.canvas_preset == '16_9_MEDIUM':
            self.canvas_x = 16.0
            self.canvas_y = 9.0
        elif self.canvas_preset == 'SQUARE_LARGE':
            self.canvas_x = 15.0
            self.canvas_y = 15.0
        elif self.canvas_preset == 'SQUARE_MEDIUM':
            self.canvas_x = 12.0
            self.canvas_y = 12.0
    
    def _load_settings_from_object(self, obj):
        """Load settings from object's custom properties"""
        if not obj or 'stb_settings' not in obj:
            return
        
        settings = obj['stb_settings']
        # Apply all pre-existing settings
        for prop_name, value in settings.items():
            if hasattr(self, prop_name):
                try:
                    setattr(self, prop_name, value)
                except (TypeError, ValueError):
                    # Skip properties that can't be set (e.g., different types)
                    pass
    
    def _save_settings_to_object(self, obj):
        """Save current settings to object's custom properties"""
        if not obj:
            return

        ## All prop except Preset
        saved_prop = [
        'canvas_x', 'canvas_y',
        'canvas_margin',
        'line_radius',
        'rows', 'columns',
        'panel_margin_x', 'panel_margin_y',
        'coverage',
        'frame_ratio',
        'custom_ratio_x', 'custom_ratio_y', 'use_custom_xy', 'ratio_preset',
        'include_notes', 'notes_width_percent', 'notes_header_height', 'show_notes_frames',
        'create_text_objects','use_custom_font','note_text_format', 'panel_header_left', 'panel_header_right',
        'num_pages', 'page_spacing',
        'include_page_header', 'page_header_height',
        'enable_page_head_left', 'page_head_left', 'page_head_left_linked',
        'enable_page_head_center', 'page_head_center', 'page_head_center_linked', 'enable_page_head_right',
        'page_head_right', 'page_head_right_linked',
        'include_page_footer', 'page_footer_height',
        'enable_page_foot_left', 'page_foot_left', 'page_foot_left_linked',
        'enable_page_foot_center', 'page_foot_center', 'page_foot_center_linked',
        'enable_page_foot_right',
        'enable_footer_logo', 'footer_logo_path', 'footer_logo_height',
        'show_canvas_frame',
        'create_camera', 'camera_margin', 'add_timeline_markers',
        'force_new_object', 'remove_pre_generated',
        ]
        # Get all property names from the operator
        settings = {}
        for prop_name in saved_prop:
            settings[prop_name] = getattr(self, prop_name)

        obj['stb_settings'] = settings
    
    def _remove_pre_generated_elements(self, context):
        """Remove all pre-generated storyboard elements"""
        removed_count = {'objects': 0, 'markers': 0}
        
        # Collections to check for objects
        collection_prefixes = [
            "Storyboard Text",
            "Storyboard panel header", 
            "Storyboard Page Headers",
            "Storyboard Page Footers",
            "Storyboard Cameras",
            "Storyboard Logos"
        ]
        
        # Object name prefixes to remove
        object_prefixes = [
            "panel_",
            "stb_shot_num_",
            "stb_panel_num_",
            "stb_page_header_",
            "stb_page_footer_",
            "stb_cam_",
            "stb_logo_"
        ]
        
        # Remove objects
        for collection_name in collection_prefixes:
            collection = bpy.data.collections.get(collection_name)
            if collection:
                # Remove all objects in the collection
                for obj in list(collection.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed_count['objects'] += 1
                
                # Remove the collection itself
                bpy.data.collections.remove(collection)
        
        # Remove objects by name prefix (in case they're not in collections)
        for obj in list(bpy.data.objects):
            if any(obj.name.startswith(prefix) for prefix in object_prefixes):
                bpy.data.objects.remove(obj, do_unlink=True)
                removed_count['objects'] += 1
        
        # Remove timeline markers
        scene = context.scene
        markers_to_remove = []
        for marker in scene.timeline_markers:
            if marker.name.startswith("stb_cam_"):
                markers_to_remove.append(marker)
        
        for marker in markers_to_remove:
            scene.timeline_markers.remove(marker)
            removed_count['markers'] += 1
        
        # Remove unused text datablocks
        text_prefixes = [
            "panel_",
            "stb_shot_num_",
            "stb_panel_num_",
            "stb_page_header_",
            "stb_page_footer_"
        ]
        
        for text_data in list(bpy.data.curves):
            if text_data.users == 0 and any(text_data.name.startswith(prefix) for prefix in text_prefixes):
                bpy.data.curves.remove(text_data)
        
        return removed_count
    
    def invoke(self, context, event):
        # Load settings from active object if it has stb_settings
        if context.object and context.object.type == 'GREASEPENCIL':
            self._load_settings_from_object(context.object)
        
        if not self.footer_logo_path:
            # Set default logo path to Blender Logo or StoryTools logo
            self.footer_logo_path = str(Path(IMAGES_DIR) / "blender_logo_no_socket_black.png")

        ## Force customization in redo to avoid confusion
        return self.execute(context)
    
    def draw(self, context):
        layout = self.layout

        # Preset system
        row = layout.row(align=True)
        row.menu("STORYTOOLS_MT_storyboard_presets", text=STORYTOOLS_MT_storyboard_presets.bl_label)
        row.operator("storytools.add_storyboard_preset", text="", icon='ADD')
        row.operator("storytools.add_storyboard_preset", text="", icon='REMOVE').remove_active = True
        
        # Import/Export presets
        # row = layout.row(align=True)
        # row.operator("storytools.export_storyboard_preset", text="Export Preset", icon='EXPORT')
        # row.operator("storytools.import_storyboard_preset", text="Import Preset", icon='IMPORT')

        # layout.separator()

        # Canvas settings
        box = layout.box()
        box.label(text="Canvas Settings", icon='FILE')
        
        row = box.row()
        row.prop(self, "canvas_preset")
        
        col = box.column(align=True)
        col.enabled = self.canvas_preset == 'CUSTOM'
        col.prop(self, "canvas_x")
        col.prop(self, "canvas_y")
            
        box.prop(self, "canvas_margin")
        box.prop(self, "show_canvas_frame")
        
        # Multiple pages
        box = layout.box()
        box.label(text="Pages", icon='DOCUMENTS')

        row = box.row()
        row.prop(self, "num_pages")
        subrow = row.row()
        subrow.enabled = self.num_pages > 1
        subrow.prop(self, "page_spacing")
        
        # Page Header
        col = box.column()
        col.prop(self, "include_page_header")
        if self.include_page_header:
            subcol = col.column(align=True)
            subcol.prop(self, "page_header_height")
            
            # Header locations
            header_box = subcol.box()
            header_col = header_box.column(align=True)
            header_col.label(text="Header Locations:")
            
            # Left header
            row = header_col.row()
            row.prop(self, "enable_page_head_left", text='Left')
            subrow = row.row()
            subrow.enabled = self.enable_page_head_left
            subrow.prop(self, "page_head_left", text="")
            subrow.prop(self, "page_head_left_linked", text="", icon='LINKED' if self.page_head_left_linked else 'UNLINKED')
            
            # Center header
            row = header_col.row()
            row.prop(self, "enable_page_head_center", text='Center')
            subrow = row.row()
            subrow.enabled = self.enable_page_head_center
            subrow.prop(self, "page_head_center", text="")
            subrow.prop(self, "page_head_center_linked", text="", icon='LINKED' if self.page_head_center_linked else 'UNLINKED')
            
            # Right header
            row = header_col.row()
            row.prop(self, "enable_page_head_right", text='Right')
            subrow = row.row()
            subrow.enabled = self.enable_page_head_right
            subrow.prop(self, "page_head_right", text="")
            subrow.prop(self, "page_head_right_linked", text="", icon='LINKED' if self.page_head_right_linked else 'UNLINKED')
        
        # Page Footer
        col = box.column()
        col.prop(self, "include_page_footer")
        if self.include_page_footer:
            subcol = col.column(align=True)
            subcol.prop(self, "page_footer_height")
            
            # Footer locations
            footer_box = subcol.box()
            footer_col = footer_box.column(align=True)
            footer_col.label(text="Footer Locations:")
            
            # Left footer
            row = footer_col.row()
            row.prop(self, "enable_page_foot_left", text='Left')
            subrow = row.row()
            subrow.enabled = self.enable_page_foot_left
            subrow.prop(self, "page_foot_left", text="")
            subrow.prop(self, "page_foot_left_linked", text="", icon='LINKED' if self.page_foot_left_linked else 'UNLINKED')
            
            # Center footer
            row = footer_col.row()
            row.prop(self, "enable_page_foot_center", text='Center')
            subrow = row.row()
            subrow.enabled = self.enable_page_foot_center
            subrow.prop(self, "page_foot_center", text="")
            subrow.prop(self, "page_foot_center_linked", text="", icon='LINKED' if self.page_foot_center_linked else 'UNLINKED')
            
            # Right footer (pagination - always enabled)
            row = footer_col.row()
            row.prop(self, "enable_page_foot_right", text='Right')
            subrow = row.row()
            subrow.enabled = self.enable_page_foot_right
            subrow.label(text="Page: XX (Pagination)")
            
            # Footer Logo
            logo_box = footer_col.box()
            logo_col = logo_box.column()
            logo_col.prop(self, "enable_footer_logo")
            if self.enable_footer_logo:
                logo_col.prop(self, "footer_logo_path")
                logo_col.prop(self, "footer_logo_height")
                
                # Show validation status
                if self.footer_logo_path:
                    if self._validate_image_path(self.footer_logo_path):
                        logo_col.label(text="✓ Valid image path", icon='FILE_TICK')
                    else:
                        logo_col.label(text="✗ Invalid image path", icon='ERROR')


        # Grid settings
        box = layout.box()
        box.label(text="Grid Settings", icon='GRID')
        col = box.column(align=True)
        col.prop(self, "rows")
        col.prop(self, "columns")
        
        # Separate X and Y panel margins
        margin_col = box.column(align=True)
        margin_col.prop(self, "panel_margin_x")
        margin_col.prop(self, "panel_margin_y")

        # Frame settings  
        box = layout.box()
        col = box.column()
        col.label(text="Panel Settings", icon='OUTLINER_DATA_GP_LAYER')
        col.prop(self, "ratio_preset")
        if self.ratio_preset == 'CUSTOM':
            col.prop(self, "use_custom_xy")
            if self.use_custom_xy:
                ratio_col = col.column(align=True)
                ratio_col.prop(self, "custom_ratio_x")
                ratio_col.prop(self, "custom_ratio_y")
                if self.custom_ratio_y > 0:
                    calculated_ratio = self.custom_ratio_x / self.custom_ratio_y
                    col.label(text=f"Ratio: {calculated_ratio:.3f}")
            else:
                col.prop(self, "frame_ratio")
        
        row = col.row()
        row.prop(self, "coverage")
        row.prop(self, "line_radius")
        
        # Notes settings
        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "include_notes", text="")
        row.label(text="Notes Settings", icon='TEXT')
        col = box.column()
        if self.include_notes:
            col.prop(self, "notes_width_percent")
            col.prop(self, "notes_header_height")
            col.prop(self, "show_notes_frames")
            col.prop(self, "create_text_objects")
            row = col.row()
            row.enabled = self.create_text_objects
            row.prop(self, "note_text_format")
            row.prop(self, "use_custom_font")
            
            # Panel header text fields
            if self.notes_header_height > 0:
                header_text_box = col.box()
                header_text_col = header_text_box.column(align=True)
                header_text_col.label(text="Panel Header Text:")
                header_text_col.prop(self, "panel_header_left")
                header_text_col.prop(self, "panel_header_right")
        
        # Camera settings
        box = layout.box()
        col = box.column()
        row = col.row(align=True)
        row.prop(self, "create_camera", text="")
        row.label(text="Add Cameras", icon='CAMERA_DATA')
        row = col.row()
        if self.create_camera:
            row.prop(self, "camera_margin", text="Margin")
            row.prop(self, "add_timeline_markers", text='Bound Markers')
        
        # Object settings
        box = layout.box()
        col = box.column()
        col.label(text="Object Settings", icon='OUTLINER_OB_GREASEPENCIL')
        col.prop(self, "force_new_object")
        col.prop(self, "remove_pre_generated")
        
        # Preview info
        layout.separator()
        total_frames = self.rows * self.columns * self.num_pages
        layout.label(text=f"Total Frames: {total_frames} ({self.rows}x{self.columns} x {self.num_pages} pages)", icon='INFO')

    def _setup_text(self, obj):
        ## Add black material for text
        if not (text_mat := bpy.data.materials.get('stb_text_color')):
            text_mat = bpy.data.materials.new('stb_text_color')
            text_mat.use_nodes = False
            text_mat.diffuse_color = (0,0,0,1)
            text_mat.specular_intensity = 0
            text_mat.roughness = 0
        if not text_mat in obj.data.materials[:]:
            obj.data.materials.append(text_mat)
        
        ## Apply custom Typography
        if self.use_custom_font:
            regular = bpy.data.fonts.load(str(FONT_DIR / 'Lato' / "Lato-Regular.ttf"), check_existing=True)
            bold = bpy.data.fonts.load(str(FONT_DIR / 'Lato' / "Lato-Bold.ttf"), check_existing=True)
            italic = bpy.data.fonts.load(str(FONT_DIR / 'Lato' / "Lato-Italic.ttf"), check_existing=True)
            bold_italic = bpy.data.fonts.load(str(FONT_DIR / 'Lato' / "Lato-BoldItalic.ttf"), check_existing=True)

            obj.data.font = regular
            obj.data.font_bold = bold
            obj.data.font_italic = italic
            obj.data.font_bold_italic = bold_italic

            ## Pack the font to avoid link issues
            regular.pack()
            bold.pack()
            italic.pack()
            bold_italic.pack()

    def _get_create_material(self, gp, name, color=(0.0, 0.0, 0.0, 1.0), fill_color=(1.0, 1.0, 1.0, 1.0)):
        if not (mat := gp.materials.get(name)):
            mat = bpy.data.materials.get(name)
            if mat and mat.is_grease_pencil:
                gp.materials.append(mat)
            else:
                mat = bpy.data.materials.new(name)
                bpy.data.materials.create_gpencil_data(mat)
                mat.grease_pencil.color = color  # Set stroke color
                mat.grease_pencil.fill_color = fill_color  # Set fill color
                gp.materials.append(mat)
        return mat

    def _get_current_ratio(self):
        """Get the current aspect ratio based on settings"""
        if self.ratio_preset != 'CUSTOM':
            ratio_values = {
                '16_9': 1.778, '16_10': 1.600, '4_3': 1.333, '3_2': 1.500,
                '185_1': 1.850, '235_1': 2.350, '1_1': 1.000, '9_16': 0.563
            }
            return ratio_values[self.ratio_preset]
        elif self.use_custom_xy and self.custom_ratio_y > 0:
            return self.custom_ratio_x / self.custom_ratio_y
        else:
            return self.frame_ratio
    
    def _create_footer_logo(self, context):
        """Create footer logo objects for each page"""
        if not self.enable_footer_logo or not self._validate_image_path(self.footer_logo_path):
            return [], 0, 0
            
        logo_objects = []
        created_count = 0
        reused_count = 0
        
        # Calculate actual logo height as percentage of full footer space
        actual_logo_height = (self.page_footer_height + self.canvas_margin) * (self.footer_logo_height / 100.0)
        
        # Position logo so its LEFT EDGE respects the canvas margin
        logo_x_start = -(self.canvas_x / 2) + self.canvas_margin
        
        master_logo = None
        actual_logo_width = 0
        
        for page in range(self.num_pages):
            page_y_offset = -(page * (self.canvas_y + self.page_spacing))
            footer_y = -(self.canvas_y / 2) + (self.canvas_margin + self.page_footer_height) / 2 + page_y_offset
            
            # Create or get logo collection
            if not (logo_collection := bpy.data.collections.get("Storyboard Logos")):
                logo_collection = bpy.data.collections.new("Storyboard Logos")
            if not logo_collection in context.scene.collection.children_recursive:
                self.parent_collection.children.link(logo_collection)
            
            # Create logo object
            logo_name = f"stb_logo_{page + 1:02d}"
            
            # Check if logo already exists
            logo_obj = bpy.data.objects.get(logo_name)
            
            if logo_obj and logo_obj.type == 'MESH':
                reused_count += 1
                logo_objects.append(logo_obj)
                # Get actual dimensions after scaling
                if logo_obj.data.vertices:
                    bounds = [v.co for v in logo_obj.data.vertices]
                    min_x = min(bound.x for bound in bounds)
                    max_x = max(bound.x for bound in bounds)
                    # Calculate width including current scale
                    actual_logo_width = (max_x - min_x) * logo_obj.scale.x
                
                # Position logo with its left edge at the margin
                logo_center_x = logo_x_start + (actual_logo_width / 2)
                logo_obj.location = (logo_center_x, 0, footer_y)
                
                # Set master logo for subsequent pages
                if page == 0:
                    master_logo = logo_obj
            else:
                # Import new logo as mesh plane (only for first page, then duplicate)
                if page == 0:
                    try:
                        # Store current selection
                        selected_objects = context.selected_objects[:]
                        active_object = context.active_object
                        
                        # Clear selection
                        bpy.ops.object.select_all(action='DESELECT')
                        
                        # Use pathlib for file operations
                        logo_path = Path(self.footer_logo_path)
                        
                        # Import image as mesh plane
                        bpy.ops.image.import_as_mesh_planes(
                            use_auto_refresh=False,
                            relative=False,
                            shader='SHADELESS',
                            render_method='BLENDED',
                            filepath=str(logo_path),
                            files=[{"name": logo_path.name}],
                            directory=str(logo_path.parent),
                            force_reload=True,
                            offset=True,
                            align_axis='-Y',
                            size_mode='ABSOLUTE',
                            height=actual_logo_height
                        )
                        
                        # Get the imported object
                        logo_obj = context.active_object
                        if logo_obj:
                            # Rename the object
                            logo_obj.name = logo_name
                            
                            # Move to logo collection
                            if logo_obj.name in context.collection.objects:
                                context.collection.objects.unlink(logo_obj)
                            logo_collection.objects.link(logo_obj)
                            
                            # Get actual dimensions of the imported logo
                            if logo_obj.data.vertices:
                                bounds = [v.co for v in logo_obj.data.vertices]
                                min_x = min(bound.x for bound in bounds)
                                max_x = max(bound.x for bound in bounds)
                                actual_logo_width = max_x - min_x
                            
                            # Position logo with its left edge at the margin
                            logo_center_x = logo_x_start + (actual_logo_width / 2)
                            logo_obj.location = (logo_center_x, 0, footer_y)
                            
                            logo_objects.append(logo_obj)
                            created_count += 1
                            master_logo = logo_obj
                        
                        # Restore selection
                        bpy.ops.object.select_all(action='DESELECT')
                        for obj in selected_objects:
                            obj.select_set(True)
                        if active_object:
                            context.view_layer.objects.active = active_object
                            
                    except Exception as e:
                        print(f"Failed to import logo: {e}")
                        self.report({'WARNING'}, f"Failed to import logo: {e}")
                else:
                    # Create linked duplicate for subsequent pages
                    if master_logo and actual_logo_width > 0:
                        logo_copy = master_logo.copy()
                        logo_copy.name = logo_name
                        logo_center_x = logo_x_start + (actual_logo_width / 2)
                        logo_copy.location = (logo_center_x, 0, footer_y)
                        logo_collection.objects.link(logo_copy)
                        logo_objects.append(logo_copy)
                        created_count += 1
        
        # Store the actual logo width for text offset calculation
        self._logo_width = actual_logo_width
        
        return logo_objects, created_count, reused_count
    
    def _create_page_header_text_objects(self, context):
        """Create header text objects for each page"""
        if not self.include_page_header:
            return [], 0, 0
            
        header_objects = []
        created_count = 0
        reused_count = 0
        
        # Calculate dimensions
        effective_canvas_x = self.canvas_x - (2 * self.canvas_margin)
        header_text_size = 0.2
        
        # Get or create shared text datablocks for linked text
        shared_text_data = {}
        
        if self.enable_page_head_left and self.page_head_left_linked:
            textdata_name = "stb_page_header_left"
            if not (textdata := bpy.data.curves.get(textdata_name)):
                textdata = bpy.data.curves.new(textdata_name, 'FONT')
                textdata.body = self.page_head_left
            shared_text_data['left'] = textdata
        
        if self.enable_page_head_center and self.page_head_center_linked:
            textdata_name = "stb_page_header_center"
            if not (textdata := bpy.data.curves.get(textdata_name)):
                textdata = bpy.data.curves.new(textdata_name, 'FONT')
                textdata.body = self.page_head_center
            shared_text_data['center'] = textdata
        
        if self.enable_page_head_right and self.page_head_right_linked:
            textdata_name = "stb_page_header_right"
            if not (textdata := bpy.data.curves.get(textdata_name)):
                textdata = bpy.data.curves.new(textdata_name, 'FONT')
                textdata.body = self.page_head_right
            shared_text_data['right'] = textdata
            
        for page in range(self.num_pages):
            page_y_offset = -(page * (self.canvas_y + self.page_spacing))
            header_y = (self.canvas_y / 2) - (self.canvas_margin + self.page_header_height) / 2 + page_y_offset
            
            # Create or get header collection
            if not (header_collection := bpy.data.collections.get("Storyboard Page Headers")):
                header_collection = bpy.data.collections.new("Storyboard Page Headers")
            if not header_collection in context.scene.collection.children_recursive:
                self.parent_collection.children.link(header_collection)
            
            # Left header text
            if self.enable_page_head_left:
                obj_name = f"stb_page_header_left_{page + 1:02d}"
                obj = bpy.data.objects.get(obj_name)
                
                if obj and obj.type == 'FONT':
                    reused_count += 1
                else:
                    if self.page_head_left_linked and 'left' in shared_text_data:
                        text_data = shared_text_data['left']
                    else:
                        text_data = bpy.data.curves.new(obj_name, 'FONT')
                        text_data.body = self.page_head_left
                    
                    obj = bpy.data.objects.new(obj_name, text_data)
                    self._setup_text(obj)
                    header_collection.objects.link(obj)
                    created_count += 1
                
                obj.data.size = header_text_size
                obj.data.align_x = 'LEFT'
                obj.data.align_y = 'CENTER'
                obj.location = (-(effective_canvas_x / 2), 0, header_y)
                obj.rotation_euler = (1.5708, 0, 0)
                header_objects.append(obj)
            
            # Center header text
            if self.enable_page_head_center:
                obj_name = f"stb_page_header_center_{page + 1:02d}"
                obj = bpy.data.objects.get(obj_name)
                
                if obj and obj.type == 'FONT':
                    reused_count += 1
                else:
                    if self.page_head_center_linked and 'center' in shared_text_data:
                        text_data = shared_text_data['center']
                    else:
                        text_data = bpy.data.curves.new(obj_name, 'FONT')
                        text_data.body = self.page_head_center
                    
                    obj = bpy.data.objects.new(obj_name, text_data)
                    self._setup_text(obj)
                    header_collection.objects.link(obj)
                    created_count += 1
                
                obj.data.size = header_text_size
                obj.data.align_x = 'CENTER'
                obj.data.align_y = 'CENTER'
                obj.location = (0, 0, header_y)
                obj.rotation_euler = (1.5708, 0, 0)
                header_objects.append(obj)
            
            # Right header text
            if self.enable_page_head_right:
                obj_name = f"stb_page_header_right_{page + 1:02d}"
                obj = bpy.data.objects.get(obj_name)
                
                if obj and obj.type == 'FONT':
                    reused_count += 1
                else:
                    if self.page_head_right_linked and 'right' in shared_text_data:
                        text_data = shared_text_data['right']
                    else:
                        text_data = bpy.data.curves.new(obj_name, 'FONT')
                        text_data.body = self.page_head_right
                    
                    obj = bpy.data.objects.new(obj_name, text_data)
                    self._setup_text(obj)
                    header_collection.objects.link(obj)
                    created_count += 1
                
                obj.data.size = header_text_size
                obj.data.align_x = 'RIGHT'
                obj.data.align_y = 'CENTER'
                obj.location = ((effective_canvas_x / 2), 0, header_y)
                obj.rotation_euler = (1.5708, 0, 0)
                header_objects.append(obj)
        
        return header_objects, created_count, reused_count
    
    def _create_page_footer_text_objects(self, context):
        """Create footer text objects for each page"""
        if not self.include_page_footer:
            return [], 0, 0
            
        footer_objects = []
        created_count = 0
        reused_count = 0
        
        # Calculate dimensions
        effective_canvas_x = self.canvas_x - (2 * self.canvas_margin)
        footer_text_size = 0.15
        
        # Calculate logo offset for left text positioning
        logo_offset = 0
        if self.enable_footer_logo and self._validate_image_path(self.footer_logo_path):
            # Use actual logo width if available, otherwise estimate
            if hasattr(self, '_logo_width'):
                logo_offset = self._logo_width + 0.05  # Add some spacing
            else:
                # Fallback: estimate based on height (for first run before logo is created)
                actual_logo_height = self.page_footer_height * (self.footer_logo_height / 100.0)
                logo_offset = actual_logo_height + 0.05
        
        # Get or create shared text datablocks for linked text
        shared_text_data = {}
        
        if self.enable_page_foot_left and self.page_foot_left_linked:
            textdata_name = "stb_page_footer_left"
            if not (textdata := bpy.data.curves.get(textdata_name)):
                textdata = bpy.data.curves.new(textdata_name, 'FONT')
                textdata.body = self.page_foot_left
            shared_text_data['left'] = textdata
        
        if self.enable_page_foot_center and self.page_foot_center_linked:
            textdata_name = "stb_page_footer_center"
            if not (textdata := bpy.data.curves.get(textdata_name)):
                textdata = bpy.data.curves.new(textdata_name, 'FONT')
                textdata.body = self.page_foot_center
            shared_text_data['center'] = textdata
            
        for page in range(self.num_pages):
            page_y_offset = -(page * (self.canvas_y + self.page_spacing))
            footer_y = -(self.canvas_y / 2) + (self.canvas_margin + self.page_footer_height) / 2 + page_y_offset
            
            # Create or get footer collection
            if not (footer_collection := bpy.data.collections.get("Storyboard Page Footers")):
                footer_collection = bpy.data.collections.new("Storyboard Page Footers")
            if not footer_collection in context.scene.collection.children_recursive:
                self.parent_collection.children.link(footer_collection)
            
            # Left footer text (adjusted for logo if present)
            if self.enable_page_foot_left:
                obj_name = f"stb_page_footer_left_{page + 1:02d}"
                obj = bpy.data.objects.get(obj_name)
                
                if obj and obj.type == 'FONT':
                    reused_count += 1
                else:
                    if self.page_foot_left_linked and 'left' in shared_text_data:
                        text_data = shared_text_data['left']
                    else:
                        text_data = bpy.data.curves.new(obj_name, 'FONT')
                        text_data.body = self.page_foot_left
                    
                    obj = bpy.data.objects.new(obj_name, text_data)
                    self._setup_text(obj)
                    footer_collection.objects.link(obj)
                    created_count += 1
                
                obj.data.size = footer_text_size
                obj.data.align_x = 'LEFT'
                obj.data.align_y = 'CENTER'
                # Position text accounting for logo space
                left_x_position = -(self.canvas_x / 2) + self.canvas_margin + logo_offset
                obj.location = (left_x_position, 0, footer_y)
                obj.rotation_euler = (1.5708, 0, 0)
                footer_objects.append(obj)
            
            # Center footer text
            if self.enable_page_foot_center:
                obj_name = f"stb_page_footer_center_{page + 1:02d}"
                obj = bpy.data.objects.get(obj_name)
                
                if obj and obj.type == 'FONT':
                    reused_count += 1
                else:
                    if self.page_foot_center_linked and 'center' in shared_text_data:
                        text_data = shared_text_data['center']
                    else:
                        text_data = bpy.data.curves.new(obj_name, 'FONT')
                        text_data.body = self.page_foot_center
                    
                    obj = bpy.data.objects.new(obj_name, text_data)
                    self._setup_text(obj)
                    footer_collection.objects.link(obj)
                    created_count += 1
                
                obj.data.size = footer_text_size
                obj.data.align_x = 'CENTER'
                obj.data.align_y = 'CENTER'
                obj.location = (0, 0, footer_y)
                obj.rotation_euler = (1.5708, 0, 0)
                footer_objects.append(obj)
            
            # Right footer text (pagination - always enabled if footer is enabled)
            if self.enable_page_foot_right:
                obj_name = f"stb_page_footer_pagination_{page + 1:02d}"
                obj = bpy.data.objects.get(obj_name)
                
                is_new_page = False
                if obj and obj.type == 'FONT':
                    reused_count += 1
                else:
                    text_data = bpy.data.curves.new(obj_name, 'FONT')
                    obj = bpy.data.objects.new(obj_name, text_data)
                    self._setup_text(obj)
                    footer_collection.objects.link(obj)
                    created_count += 1
                    is_new_page = True
                
                # Always update pagination text as it's page-specific
                if is_new_page:
                    obj.data.body = f"Page: {page + 1:02d}"
                
                obj.data.size = footer_text_size
                obj.data.align_x = 'RIGHT'
                obj.data.align_y = 'CENTER'
                obj.location = ((effective_canvas_x / 2), 0, footer_y)
                obj.rotation_euler = (1.5708, 0, 0)
                footer_objects.append(obj)
        
        return footer_objects, created_count, reused_count
    
    def _create_text_objects(self, context, panels_start_y, effective_canvas_y):
        """Create or reuse text objects for each panel notes area"""
        text_objects = []
        created_count = 0
        reused_count = 0
        
        # Calculate dimensions first
        effective_canvas_x = self.canvas_x - (2 * self.canvas_margin)
        
        grid_width = effective_canvas_x - (self.columns - 1) * self.panel_margin_x
        grid_height = effective_canvas_y - (self.rows - 1) * self.panel_margin_y
        
        space_x = grid_width / self.columns
        space_y = grid_height / self.rows
        
        notes_width = space_x * self.notes_width_percent / 100
        text_width = notes_width * 0.9  # 90% of notes area width

        default_bodys = {
            'None' : '',
            'Notes' : 'Notes:\n',
            'ActionDialog' : 'Action:\n\n\n\nDialog:\n',
            'ActionDialogLighting' : 'Action:\n\n\n\nDialog:\n\n\n\nLighting:\n',
            }

        panel_count = 0
        for page in range(self.num_pages):
            page_y_offset = -(page * (self.canvas_y + self.page_spacing))
            start_x = -(effective_canvas_x / 2)
            start_y = panels_start_y + page_y_offset
            
            for r_idx in range(self.rows):
                for c_idx in range(self.columns):
                    panel_count += 1
                    
                    # Calculate panel boundaries using separate X and Y margins
                    panel_left = start_x + c_idx * (space_x + self.panel_margin_x)
                    panel_top = start_y - r_idx * (space_y + self.panel_margin_y)
                    panel_bottom = panel_top - space_y
                    panel_center_y = (panel_top + panel_bottom) / 2
                    
                    # Calculate notes area position
                    drawing_width = space_x * (100 - self.notes_width_percent) / 100
                    notes_left = panel_left + drawing_width
                    notes_center_x = notes_left + notes_width / 2
                    
                    # Check if text object already exists
                    text_name = f"panel_{panel_count:04d}"
                    text_obj = bpy.data.objects.get(text_name)

                    is_new_text = False
                    if text_obj and text_obj.type == 'FONT': # and text_obj.data.body not in default_bodys.values()
                        # Reuse existing text object
                        reused_count += 1
                    else:
                        # Create new text object
                        text_data = bpy.data.curves.new(text_name, 'FONT')
                        text_obj = bpy.data.objects.new(text_name, text_data)
                        self._setup_text(text_obj)
                        
                        # Create or get text collection
                        if not (text_collection := bpy.data.collections.get("Storyboard Text")):
                            text_collection = bpy.data.collections.new("Storyboard Text")
                        if not text_collection in context.scene.collection.children_recursive:
                            self.parent_collection.children.link(text_collection)
                        
                        text_collection.objects.link(text_obj)
                        created_count += 1
                        is_new_text = True
                    
                    # Configure text object
                    text_data = text_obj.data
                    
                    # Set text content only for new objects
                    if is_new_text:
                        text_data.body = default_bodys.get(self.note_text_format, '')

                    # Set overflow to NONE (default)
                    text_data.overflow = 'NONE'
                    text_data.size = 0.15
                    
                    # Set text box width to 90% of notes area width
                    if not text_data.text_boxes:
                        text_data.text_boxes.new()
                    text_data.text_boxes[0].width = text_width
                    text_data.text_boxes[0].height = 0  # Auto height
                    
                    # Position text object in notes area
                    text_obj.location = (notes_center_x - text_width/2, 0, panel_center_y + space_y/2 - 0.1)
                    text_obj.rotation_euler = (1.5708, 0, 0)  # 90 degrees to face camera
                    
                    # Set alignment
                    text_data.align_x = 'LEFT'
                    text_data.align_y = 'TOP'
                    
                    text_objects.append(text_obj)
        
        return text_objects, created_count, reused_count
    
    def _create_header_text_objects(self, context, panels_start_y, effective_canvas_y):
        """Create header text objects for shot and panel numbers"""
        # Return early if notes are disabled or header height is 0
        if not self.include_notes or self.notes_header_height <= 0:
            return [], 0, 0
            
        header_text_objects = []
        created_count = 0
        reused_count = 0
        
        # Calculate dimensions first
        effective_canvas_x = self.canvas_x - (2 * self.canvas_margin)
        
        grid_width = effective_canvas_x - (self.columns - 1) * self.panel_margin_x
        grid_height = effective_canvas_y - (self.rows - 1) * self.panel_margin_y
        
        space_x = grid_width / self.columns
        space_y = grid_height / self.rows
        
        drawing_width = space_x * (100 - self.notes_width_percent) / 100
        
        # Calculate text size based on header height
        base_text_size = 0.15
        header_text_size = max(0.1, min(base_text_size, self.notes_header_height * 0.6))
        
        panel_count = 0
        for page in range(self.num_pages):
            page_y_offset = -(page * (self.canvas_y + self.page_spacing))
            start_x = -(effective_canvas_x / 2)
            start_y = panels_start_y + page_y_offset
            
            for r_idx in range(self.rows):
                for c_idx in range(self.columns):
                    panel_count += 1
                    
                    # Calculate panel boundaries using separate X and Y margins
                    panel_left = start_x + c_idx * (space_x + self.panel_margin_x)
                    panel_top = start_y - r_idx * (space_y + self.panel_margin_y)
                    panel_bottom = panel_top - space_y
                    panel_center_y = (panel_top + panel_bottom) / 2
                    
                    # Calculate header area position (above drawing area)
                    header_y = panel_center_y + (space_y - self.notes_header_height) / 2
                    header_margin = 0.1  # Small margin from edges
                    
                    # Create or get header text collection
                    if not (header_collection := bpy.data.collections.get("Storyboard panel header")):
                        header_collection = bpy.data.collections.new("Storyboard panel header")
                    if not header_collection in context.scene.collection.children_recursive:
                        self.parent_collection.children.link(header_collection)
                    
                    # Create shot number text (left side) - using custom text
                    shot_text_name = f"stb_shot_num_{panel_count:04d}"
                    shot_text_obj = bpy.data.objects.get(shot_text_name)
                    
                    is_new_shot = False
                    if shot_text_obj and shot_text_obj.type == 'FONT':
                        reused_count += 1
                    else:
                        shot_text_data = bpy.data.curves.new(shot_text_name, 'FONT')
                        shot_text_obj = bpy.data.objects.new(shot_text_name, shot_text_data)
                        self._setup_text(shot_text_obj)
                        header_collection.objects.link(shot_text_obj)
                        created_count += 1
                        is_new_shot = True
                    
                    # Configure shot text object
                    shot_text_data = shot_text_obj.data
                    
                    if is_new_shot:
                        shot_text_data.body = self.panel_header_left
                    
                    shot_text_data.overflow = 'NONE'
                    shot_text_data.size = header_text_size
                    shot_text_data.align_x = 'LEFT'
                    shot_text_data.align_y = 'CENTER'
                    
                    # Position shot text at left side of header area
                    shot_text_obj.location = (panel_left + header_margin, 0, header_y)
                    shot_text_obj.rotation_euler = (1.5708, 0, 0)
                    
                    header_text_objects.append(shot_text_obj)
                    
                    # Create panel number text (right side) - using custom text
                    panel_text_name = f"stb_panel_num_{panel_count:04d}"
                    panel_text_obj = bpy.data.objects.get(panel_text_name)
                    
                    is_new_panel = False
                    if panel_text_obj and panel_text_obj.type == 'FONT':
                        reused_count += 1
                    else:
                        panel_text_data = bpy.data.curves.new(panel_text_name, 'FONT')
                        panel_text_obj = bpy.data.objects.new(panel_text_name, panel_text_data)
                        self._setup_text(panel_text_obj)
                        header_collection.objects.link(panel_text_obj)
                        created_count += 1
                        is_new_panel = True
                    
                    # Configure panel text object
                    panel_text_data = panel_text_obj.data
                    
                    if is_new_panel:
                        panel_text_data.body = self.panel_header_right
                    
                    panel_text_data.overflow = 'NONE'
                    panel_text_data.size = header_text_size
                    panel_text_data.align_x = 'RIGHT'
                    panel_text_data.align_y = 'CENTER'
                    
                    # Position panel text at right side of header area (with margin)
                    header_right = panel_left + drawing_width
                    panel_text_obj.location = (header_right - header_margin*5, 0, header_y)
                    panel_text_obj.rotation_euler = (1.5708, 0, 0)

                    header_text_objects.append(panel_text_obj)
        
        return header_text_objects, created_count, reused_count
    
    def _create_cameras(self, context):
        """Create or reuse orthographic cameras for each page"""
        camera_objects = []
        created_count = 0
        reused_count = 0
        
        for page in range(self.num_pages):
            # Calculate camera bounds for this page
            cam_width = self.canvas_x + 2 * self.camera_margin
            cam_height = self.canvas_y + 2 * self.camera_margin
            
            # Calculate Y offset for this page
            page_y_offset = -(page * (self.canvas_y + self.page_spacing))
            
            # Check if camera already exists
            camera_name = f"stb_cam_{page + 1:02d}"
            camera_obj = bpy.data.objects.get(camera_name)
            
            if camera_obj and camera_obj.type == 'CAMERA':
                # Reuse existing camera
                reused_count += 1
            else:
                # Create new camera
                cam_data = bpy.data.cameras.new(camera_name)
                camera_obj = bpy.data.objects.new(camera_name, cam_data)
                
                if not (cam_collection := bpy.data.collections.get("Storyboard Cameras")):
                    cam_collection = bpy.data.collections.new("Storyboard Cameras")
                if not cam_collection in context.scene.collection.children_recursive:
                    self.parent_collection.children.link(cam_collection)


                cam_collection.objects.link(camera_obj)
                created_count += 1
            
            camera = camera_obj.data
            
            # Set to orthographic
            camera.type = 'ORTHO'
            camera.ortho_scale = max(cam_width, cam_height)
            
            # Position camera to look at the center of this specific page
            camera_obj.location = (0, -10, page_y_offset)
            camera_obj.rotation_euler = (1.5708, 0, 0)  # 90 degrees in radians
            
            # Set scene resolution to match canvas ratio (only for the first camera)
            if page == 0:
                scene = context.scene
                if cam_width > cam_height:
                    scene.render.resolution_x = 1920
                    scene.render.resolution_y = int(1920 * cam_height / cam_width)
                else:
                    scene.render.resolution_y = 1920
                    scene.render.resolution_x = int(1920 * cam_width / cam_height)
                
                ## Set first camera as active scene camera
                scene.camera = camera_obj
            
            camera_objects.append(camera_obj)

        return camera_objects
    
    def _create_timeline_markers(self, context, camera_objects):
        """Create timeline markers for each camera"""
        scene = context.scene
        
        for page, camera_obj in enumerate(camera_objects):
            marker_name = camera_obj.name # Use same name as camera
            frame_number = page + 1  # Frame 1, 2, 3, etc.

            ## Check if marker already exists
            if marker := scene.timeline_markers.get(marker_name):
                # Update existing marker
                marker.frame = frame_number
            else:
                # Create new marker
                marker = scene.timeline_markers.new(marker_name, frame=frame_number)
            ## Assign camera
            marker.camera = camera_obj
    
    def _create_canvas_frame(self, drawing, mat_index, page_y_offset=0):
        """Create a border frame around the canvas"""
        half_width = self.canvas_x / 2
        half_height = self.canvas_y / 2
        
        corners = [
            Vector((-half_width, 0, half_height + page_y_offset)),    # top-left
            Vector((half_width, 0, half_height + page_y_offset)),     # top-right
            Vector((half_width, 0, -half_height + page_y_offset)),    # bottom-right
            Vector((-half_width, 0, -half_height + page_y_offset)),   # bottom-left
        ]
        
        drawing.add_strokes([4])
        stroke = drawing.strokes[-1]
        stroke.cyclic = True
        stroke.material_index = mat_index
        
        for i, pt in enumerate(stroke.points):
            pt.position = corners[i]
            pt.radius = 0.0007
    
    def _create_panel_frame(self, drawing, panels_mat_index, center_x, center_y, width, height, drawing_area_height=None):
        """Create a frame around the entire panel area with notes separator lines"""
        half_width = width / 2
        half_height = height / 2

        # Create outer frame around entire panel
        corners = [
            Vector((center_x - half_width, 0, center_y + half_height)),  # top-left
            Vector((center_x + half_width, 0, center_y + half_height)),  # top-right
            Vector((center_x + half_width, 0, center_y - half_height)),  # bottom-right
            Vector((center_x - half_width, 0, center_y - half_height)),  # bottom-left
        ]
        
        drawing.add_strokes([4])
        stroke = drawing.strokes[-1]
        stroke.cyclic = True
        stroke.material_index = panels_mat_index
        
        for i, pt in enumerate(stroke.points):
            pt.position = corners[i]
            pt.radius = self.line_radius
        
        # Add vertical separator line between drawing and notes area
        notes_width_ratio = self.notes_width_percent / 100
        separator_x = center_x - half_width + width * (1 - notes_width_ratio)
        
        drawing.add_strokes([2])
        stroke = drawing.strokes[-1]
        stroke.material_index = panels_mat_index
        
        stroke.points[0].position = Vector((separator_x, 0, center_y + half_height))
        stroke.points[1].position = Vector((separator_x, 0, center_y - half_height))
        stroke.points[0].radius = self.line_radius
        stroke.points[1].radius = self.line_radius

        # Add header separator line above the drawing frame area if header height > 0
        if self.include_notes and self.notes_header_height > 0:
            # Calculate the drawing area bounds
            notes_width_ratio = self.notes_width_percent / 100
            drawing_area_width = width * (1 - notes_width_ratio)
            drawing_left = center_x - half_width
            
            # Position header separator above the drawing area
            if drawing_area_height is not None:
                header_y = center_y + (drawing_area_height/2 - self.notes_header_height/2)
            else:
                header_y = center_y + half_height - self.notes_header_height
            
            drawing.add_strokes([2])
            stroke = drawing.strokes[-1]
            stroke.material_index = panels_mat_index
            
            # Header separator spans the width of the drawing area only
            stroke.points[0].position = Vector((drawing_left, 0, header_y))
            stroke.points[1].position = Vector((drawing_left + drawing_area_width, 0, header_y))
            stroke.points[0].radius = self.line_radius
            stroke.points[1].radius = self.line_radius
    
    def execute(self, context):
        # Initialize logo width tracking
        self._logo_width = 0
        
        # Remove pre-generated elements if requested
        if self.remove_pre_generated:
            removed_count = self._remove_pre_generated_elements(context)
            # self.report({'INFO'}, f"Removed {removed_count['objects']} objects and {removed_count['markers']} timeline markers")

        # Update canvas dimensions and ratio from presets
        self.update_canvas_preset(context)
        
        if self.ratio_preset != 'CUSTOM':
            ratio_values = {
                '16_9': 1.778, '16_10': 1.600, '4_3': 1.333, '3_2': 1.500,
                '185_1': 1.850, '235_1': 2.350, '1_1': 1.000, '9_16': 0.563
            }
            self.frame_ratio = ratio_values[self.ratio_preset]
        elif self.use_custom_xy:
            if self.custom_ratio_y > 0:
                self.frame_ratio = self.custom_ratio_x / self.custom_ratio_y
        
        # Create or get grease pencil object
        need_new_object = (self.force_new_object or 
                          not context.object or 
                          context.object.type != 'GREASEPENCIL')

        ## Get Create a main collection
        self.parent_collection = bpy.data.collections.get("Storyboard")
        if not self.parent_collection:
            self.parent_collection = bpy.data.collections.new("Storyboard")
        if not self.parent_collection in context.scene.collection.children_recursive:
            context.scene.collection.children.link(self.parent_collection)

        frame_number = context.scene.frame_start

        if need_new_object:
            gp_data = bpy.data.grease_pencils_v3.new("Storyboard")
            obj = bpy.data.objects.new("Storyboard", gp_data)
            context.collection.objects.link(obj)
            context.view_layer.objects.active = obj
            ## Create default layers and palette
            fn.load_default_palette(obj)
            fn.create_default_layers(obj, frame=frame_number)
            target_active = gp_data.layers.get('Sketch')
            if not target_active and len(gp_data.layers):
                target_active = gp_data.layers[-1]
            gp_data.layers.active = target_active

            ## Change selection
            # obj.select_set(True)
            # for other_obj in context.selected_objects:
            #     if other_obj != obj:
            #         other_obj.select_set(False)

        else:
            obj = context.object
        
        gp = obj.data
        
        # Setup layers and materials
        if not (layer := gp.layers.get('Frames')):
            layer = gp.layers.new('Frames', set_active=False)
            layer.lock = True
            gp.layers.move_bottom(layer)
        
        frame = next((f for f in layer.frames), None)
        if frame is None:
            frame = layer.frames.new(frame_number)
        
        drawing = frame.drawing

        # Setup Frames material (for drawing frames)
        frames_material = self._get_create_material(gp, 'Frames', color=(0.015, 0.015, 0.015, 1.0))
        
        frames_mat_index = next((i for i, mat in enumerate(gp.materials) if mat == frames_material), None)
        if frames_mat_index is None:
            self.report({'ERROR'}, 'No material index for Frames material')
            return {'CANCELLED'}
        
        # Setup Panels material (for notes/panel frames) - only if notes are enabled
        panels_mat_index = None
        if (self.include_notes and self.show_notes_frames) or self.show_canvas_frame:
            panels_material = self._get_create_material(gp, 'Panels')
            panels_mat_index = next((i for i, mat in enumerate(gp.materials) if mat == panels_material), None)
            if panels_mat_index is None:
                self.report({'ERROR'}, 'No material index for Panels material')
                return {'CANCELLED'}
        
        # Clear existing strokes
        drawing.remove_strokes()
        
        # Calculate dimensions accounting for headers and footers
        effective_canvas_x = self.canvas_x - (2 * self.canvas_margin)
        effective_canvas_y = self.canvas_y - (2 * self.canvas_margin)
        
        # Account for page header and footer
        if self.include_page_header:
            effective_canvas_y -= self.page_header_height
        if self.include_page_footer:
            effective_canvas_y -= self.page_footer_height
        
        if effective_canvas_x <= 0 or effective_canvas_y <= 0:
            self.report({'ERROR'}, 'Canvas margin and header/footer too large for canvas size')
            return {'CANCELLED'}
        
        # Account for panel margins (using separate X and Y margins)
        grid_width = effective_canvas_x - (self.columns - 1) * self.panel_margin_x
        grid_height = effective_canvas_y - (self.rows - 1) * self.panel_margin_y
        
        if grid_width <= 0 or grid_height <= 0:
            self.report({'ERROR'}, 'Panel margin too large for grid')
            return {'CANCELLED'}
        
        space_x = grid_width / self.columns
        space_y = grid_height / self.rows
        
        # Calculate drawing area (accounting for notes)
        drawing_width = space_x
        if self.include_notes:
            drawing_width = space_x * (100 - self.notes_width_percent) / 100
        
        # Calculate available space for drawing frames
        available_x = drawing_width * self.coverage / 100
        available_y = space_y * self.coverage / 100
        
        # Account for header height when show_notes_frames is enabled
        drawing_area_height = space_y
        if self.include_notes and self.show_notes_frames and self.notes_header_height > 0:
            drawing_area_height = space_y - self.notes_header_height
            available_y = drawing_area_height * self.coverage / 100
        
        # Calculate frame size
        if available_x / self.frame_ratio <= available_y:
            frame_width = available_x
            frame_height = available_x / self.frame_ratio
        else:
            frame_height = available_y
            frame_width = available_y * self.frame_ratio
        
        # Calculate panels start position (accounting for header)
        canvas_top = self.canvas_y / 2 - self.canvas_margin
        if self.include_page_header:
            canvas_top -= self.page_header_height
        panels_start_y = canvas_top - (effective_canvas_y / 2) + (effective_canvas_y / 2)
        
        # Create frames for all pages        
        for page in range(self.num_pages):
            page_y_offset = -(page * (self.canvas_y + self.page_spacing))
            
            # Create canvas frame if requested
            if self.show_canvas_frame:
                self._create_canvas_frame(drawing, panels_mat_index, page_y_offset)
            
            # Calculate start position for this page (top-left of the drawing area)
            start_x = -(effective_canvas_x / 2)
            start_y = panels_start_y + page_y_offset
            
            # Create panel frames
            panel_count = 0
            for r_idx in range(self.rows):
                for c_idx in range(self.columns):
                    panel_count += 1
                    
                    # Calculate panel boundaries (using separate X and Y margins)
                    panel_left = start_x + c_idx * (space_x + self.panel_margin_x)
                    panel_right = panel_left + space_x
                    panel_top = start_y - r_idx * (space_y + self.panel_margin_y)
                    panel_bottom = panel_top - space_y
                    
                    panel_center_y = (panel_top + panel_bottom) / 2
                    
                    # Adjust panel center if header is above drawing area
                    drawing_center_y = panel_center_y
                    if self.include_notes and self.show_notes_frames and self.notes_header_height > 0:
                        # Shift drawing area down by half the header height
                        drawing_center_y = panel_center_y - self.notes_header_height / 2
                    
                    # Calculate drawing area within the panel
                    if self.include_notes:
                        # Drawing area is on the left side of the panel
                        drawing_left = panel_left
                        drawing_right = panel_left + drawing_width
                    else:
                        # Drawing area is centered in the panel
                        drawing_left = panel_left + (space_x - drawing_width) / 2
                        drawing_right = drawing_left + drawing_width
                    
                    drawing_center_x = (drawing_left + drawing_right) / 2
                    
                    # Create drawing frame (centered within the drawing area) - using Frames material
                    half_width = frame_width / 2
                    half_height = frame_height / 2
                    
                    corners = [
                        Vector((drawing_center_x - half_width, 0, drawing_center_y + half_height)),  # top-left
                        Vector((drawing_center_x + half_width, 0, drawing_center_y + half_height)),  # top-right
                        Vector((drawing_center_x + half_width, 0, drawing_center_y - half_height)),  # bottom-right
                        Vector((drawing_center_x - half_width, 0, drawing_center_y - half_height)),  # bottom-left
                    ]
                    
                    drawing.add_strokes([4])
                    stroke = drawing.strokes[-1]
                    stroke.cyclic = True
                    stroke.material_index = frames_mat_index  # Use Frames material for drawing frames
                    
                    for i, pt in enumerate(stroke.points):
                        pt.position = corners[i]
                        pt.radius = self.line_radius
                    
                    # Create notes frame if requested and if show_notes_frames is enabled - using Panels material
                    if self.include_notes and self.show_notes_frames and panels_mat_index is not None:
                        # Create frame around the entire panel area (not just notes portion)
                        panel_center_x = (panel_left + panel_right) / 2
                        self._create_panel_frame(drawing, panels_mat_index, panel_center_x, panel_center_y, space_x, space_y, drawing_area_height)
        
        # Create page header and footer text objects
        if self.include_page_header:
            header_objects, created_header, reused_header = self._create_page_header_text_objects(context)
        
        # Create footer logo first (so we know its width for text positioning)
        if self.enable_footer_logo and self._validate_image_path(self.footer_logo_path):
            logo_objects, created_logo, reused_logo = self._create_footer_logo(context)
        
        if self.include_page_footer:
            footer_objects, created_footer, reused_footer = self._create_page_footer_text_objects(context)
        
        # Create text objects if requested
        if self.include_notes and self.create_text_objects:
            text_objects, created_text, reused_text = self._create_text_objects(context, panels_start_y, effective_canvas_y)

            # Create header text objects if header height > 0
            header_text_objects, created_panel_header, reused_panel_header = self._create_header_text_objects(context, panels_start_y, effective_canvas_y)
        
        # Create cameras if requested
        camera_objects = []
        if self.create_camera:
            camera_objects = self._create_cameras(context)
            
            # Create timeline markers if requested
            if self.add_timeline_markers:
                self._create_timeline_markers(context, camera_objects)

            ## Set first cam active in view
            context.region_data.view_perspective = 'CAMERA'

        # Save current settings to the object
        self._save_settings_to_object(obj)

        return {'FINISHED'}


class STORYTOOLS_PT_frame_grid_panel(Panel):
    """Panel for frame grid tools"""
    bl_label = "Frame Grid"
    bl_idname = "STORYTOOLS_PT_frame_grid"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Grease Pencil"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("storytools.create_static_storyboard_pages", icon='GRID')

def create_default_presets():
    source_presets = Path(PRESETS_DIR) / 'storyboard'
    
    if not source_presets.exists():
        return
    
    user_stb_presets = Path(bpy.utils.preset_paths("storytools/storyboard")[0])
    if not user_stb_presets.exists():
        user_stb_presets.mkdir(parents=True, exist_ok=True)

    for preset_src in source_presets.iterdir():
        if preset_src.suffix != '.py':
            continue
        preset_dest = user_stb_presets / preset_src.name
        
        if preset_dest.exists():
            continue

        shutil.copy(preset_src, preset_dest)

classes = (
    STORYTOOLS_MT_storyboard_presets,
    STORYTOOLS_OT_add_storyboard_preset,
    # STORYTOOLS_OT_export_storyboard_preset, Additional exporter 
    # STORYTOOLS_OT_import_storyboard_preset, Additional exporter
    STORYTOOLS_OT_create_static_storyboard_pages,
    # STORYTOOLS_PT_frame_grid_panel,  # Panel for use in standalone mode
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    ## Copy default presets to users presets directory if they don't exist
    ## TODO: Maybe add it as a separate operator...
    create_default_presets()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)