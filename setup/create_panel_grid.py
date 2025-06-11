## Create a grid of panel suitable for static storyboard or quick thumbnails.
# 1.1

import bpy
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty
from bpy.types import Operator, Panel
from mathutils import Vector

# Ensure orthographic camera(s) fit the pages
# Add separate material for the lines
# Add option for radius

class STORYTOOLS_OT_create_frame_grid(Operator):
    """Create a grid of frames using grease pencil strokes"""
    bl_idname = "storytools.create_frame_grid"
    bl_label = "Create Frame Grid"
    bl_description = "Create storyboard grid with cutomizable features"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Canvas presets
    canvas_preset: EnumProperty(
        name="Canvas Preset",
        description="Predefined canvas sizes",
        items=[
            ('A4_PORTRAIT', "A4 Portrait", "A4 portrait format (10.5 x 14.85)"),
            ('A4_LANDSCAPE', "A4 Landscape", "A4 landscape format (14.85 x 10.5)"),
            ('16_9_LARGE', "16:9 Large", "Large 16:9 format (20 x 11.25)"),
            ('16_9_MEDIUM', "16:9 Medium", "Medium 16:9 format (16 x 9)"),
            ('SQUARE_LARGE', "Square Large", "Large square format (15 x 15)"),
            ('SQUARE_MEDIUM', "Square Medium", "Medium square format (12 x 12)"),
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
        default=0.5,
        min=0.0,
        max=10.0,
        step=0.1,
        precision=2
    )
    
    # Grid dimensions
    rows: IntProperty(
        name="Rows",
        description="Number of rows in the grid",
        default=5,
        min=1,
        max=20
    )
    
    columns: IntProperty(
        name="Columns",
        description="Number of columns in the grid", 
        default=2,
        min=1,
        max=20
    )
    
    # Panel margin
    panel_margin: FloatProperty(
        name="Panel Margin",
        description="Space between panels in the grid",
        default=0.2,
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
        default=30.0,
        min=10.0,
        max=50.0,
        step=1,
        precision=1
    )
    
    notes_header_height: FloatProperty(
        name="Notes Header Height",
        description="Height reserved for scene/panel number at top of notes area",
        default=0.3,
        min=0.0,
        max=1.0,
        step=0.1,
        precision=2
    )
    
    show_notes_frames: BoolProperty(
        name="Show Notes Frames",
        description="Show frame lines around the notes area (enclosing whole panel)",
        default=True
    )
    
    # Multiple pages
    num_pages: IntProperty(
        name="Number of Pages",
        description="Number of pages to create (stacked vertically)",
        default=1,
        min=1,
        max=10
    )
    
    page_spacing: FloatProperty(
        name="Page Spacing",
        description="Vertical spacing between pages",
        default=1.0,
        min=0.0,
        max=5.0,
        step=0.1,
        precision=2
    )
    
    # Canvas frame
    show_canvas_frame: BoolProperty(
        name="Show Canvas Frame",
        description="Add a border around the canvas to visualize its bounds",
        default=True
    )
    
    # Camera setup
    create_camera: BoolProperty(
        name="Create Camera",
        description="Create an orthographic camera to frame the storyboard",
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
        default=False
    )
    
    force_new_object: BoolProperty(
        name="Create New Object",
        description="Force creation of a new grease pencil object instead of using the active one",
        default=False
    )
    
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
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=450)
    
    def draw(self, context):
        layout = self.layout
        
        # Canvas settings
        box = layout.box()
        box.label(text="Canvas Settings", icon='MESH_PLANE')
        
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
        box.prop(self, "num_pages")
        if self.num_pages > 1:
            box.prop(self, "page_spacing")
        
        # Frame settings  
        box = layout.box()
        box.label(text="Panel Settings", icon='IMAGE_RGB')
        box.prop(self, "ratio_preset")
        if self.ratio_preset == 'CUSTOM':
            box.prop(self, "use_custom_xy")
            if self.use_custom_xy:
                col = box.column(align=True)
                col.prop(self, "custom_ratio_x")
                col.prop(self, "custom_ratio_y")
                if self.custom_ratio_y > 0:
                    calculated_ratio = self.custom_ratio_x / self.custom_ratio_y
                    box.label(text=f"Ratio: {calculated_ratio:.3f}")
            else:
                box.prop(self, "frame_ratio")
        box.prop(self, "coverage")
        
        # Grid settings
        box = layout.box()
        box.label(text="Grid Settings", icon='GRID')
        col = box.column(align=True)
        col.prop(self, "rows")
        col.prop(self, "columns")
        box.prop(self, "panel_margin")
        
        # Notes settings
        box = layout.box()
        box.label(text="Notes Settings", icon='TEXT')
        box.prop(self, "include_notes")
        if self.include_notes:
            box.prop(self, "notes_width_percent")
            box.prop(self, "notes_header_height")
            box.prop(self, "show_notes_frames")
        
        # Camera settings
        box = layout.box()
        box.label(text="Camera Settings", icon='CAMERA_DATA')
        box.prop(self, "create_camera")
        if self.create_camera:
            box.prop(self, "camera_margin")
            box.prop(self, "add_timeline_markers")
        
        # Object settings
        box = layout.box()
        box.label(text="Object Settings", icon='OUTLINER_OB_GREASEPENCIL')
        box.prop(self, "force_new_object")
        
        # Preview info
        layout.separator()
        total_frames = self.rows * self.columns * self.num_pages
        layout.label(text=f"Total Frames: {total_frames} ({self.rows}x{self.columns} x {self.num_pages} pages)", icon='INFO')
        
        # Calculate and show frame dimensions
        self._show_frame_dimensions(layout)
    
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

    def _show_frame_dimensions(self, layout):
        """Calculate and display frame dimensions in the UI"""
        effective_canvas_x = self.canvas_x - (2 * self.canvas_margin)
        effective_canvas_y = self.canvas_y - (2 * self.canvas_margin)
        
        if effective_canvas_x > 0 and effective_canvas_y > 0:
            # Account for panel margins
            grid_width = effective_canvas_x - (self.columns - 1) * self.panel_margin
            grid_height = effective_canvas_y - (self.rows - 1) * self.panel_margin
            
            if grid_width > 0 and grid_height > 0:
                space_x = grid_width / self.columns
                space_y = grid_height / self.rows
                
                # Calculate drawing area within each panel space
                if self.include_notes:
                    drawing_width = space_x * (100 - self.notes_width_percent) / 100
                    notes_width = space_x * self.notes_width_percent / 100
                else:
                    drawing_width = space_x
                    notes_width = 0
                
                # Apply coverage to get available drawing space
                available_x = drawing_width * self.coverage / 100
                available_y = space_y * self.coverage / 100
                
                # Get current ratio
                current_ratio = self._get_current_ratio()
                
                # Calculate final frame size
                if available_x / current_ratio <= available_y:
                    frame_width = available_x
                    frame_height = available_x / current_ratio
                else:
                    frame_height = available_y
                    frame_width = available_y * current_ratio
                    
                layout.label(text=f"Frame Size: {frame_width:.2f} x {frame_height:.2f}")
                layout.label(text=f"Drawing Area: {drawing_width:.2f} x {space_y:.2f}")
                if self.include_notes:
                    layout.label(text=f"Notes Area: {notes_width:.2f} x {space_y:.2f}")
                    
                # Show coverage effect
                if self.coverage < 100:
                    layout.label(text=f"Available Space: {available_x:.2f} x {available_y:.2f}")
            else:
                layout.label(text="Error: Panel margins too large!", icon='ERROR')
    
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
                bpy.ops.object.camera_add(location=(0, -10, 0))
                camera_obj = context.active_object
                camera_obj.name = camera_name
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
                
                # Set first camera as active scene camera
                scene.camera = camera_obj
            
            camera_objects.append(camera_obj)
        
        return camera_objects
    
    def _create_timeline_markers(self, context, camera_objects):
        """Create timeline markers for each camera"""
        scene = context.scene
        created_markers = 0
        updated_markers = 0
        
        for page, camera_obj in enumerate(camera_objects):
            marker_name = camera_obj.name  # Use same name as camera
            frame_number = page + 1  # Frame 1, 2, 3, etc.
            
            # Check if marker already exists
            existing_marker = None
            for marker in scene.timeline_markers:
                if marker.name == marker_name:
                    existing_marker = marker
                    break
            
            if existing_marker:
                # Update existing marker
                existing_marker.frame = frame_number
                if hasattr(existing_marker, 'camera'):
                    existing_marker.camera = camera_obj
                updated_markers += 1
            else:
                # Create new marker
                marker = scene.timeline_markers.new(marker_name, frame=frame_number)
                # Note: timeline markers don't have a direct camera property in most Blender versions
                # but we can still create them with the camera name for reference
                created_markers += 1
    
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
            pt.radius = 0.005 # Set a smaller radius
    
    def _create_panel_frame(self, drawing, panels_mat_index, center_x, center_y, width, height):
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
            pt.radius = 0.015
        
        # Add vertical separator line between drawing and notes area
        notes_width_ratio = self.notes_width_percent / 100
        separator_x = center_x - half_width + width * (1 - notes_width_ratio)
        
        drawing.add_strokes([2])
        stroke = drawing.strokes[-1]
        stroke.material_index = panels_mat_index
        
        stroke.points[0].position = Vector((separator_x, 0, center_y + half_height))
        stroke.points[1].position = Vector((separator_x, 0, center_y - half_height))
        stroke.points[0].radius = 0.015
        stroke.points[1].radius = 0.015
        
        # Add header separator line in notes area if header height > 0
        if self.notes_header_height > 0:
            header_y = center_y + half_height - self.notes_header_height
            
            drawing.add_strokes([2])
            stroke = drawing.strokes[-1]
            stroke.material_index = panels_mat_index
            
            stroke.points[0].position = Vector((separator_x, 0, header_y))
            stroke.points[1].position = Vector((center_x + half_width, 0, header_y))
            stroke.points[0].radius = 0.015
            stroke.points[1].radius = 0.015
    
    def execute(self, context):
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
        
        if need_new_object:
            gp_data = bpy.data.grease_pencils_v3.new("Storyboard Grid")
            obj = bpy.data.objects.new("Storyboard Grid", gp_data)
            context.collection.objects.link(obj)
            
            context.view_layer.objects.active = obj
            obj.select_set(True)
            
            for other_obj in context.selected_objects:
                if other_obj != obj:
                    other_obj.select_set(False)

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
            frame = layer.frames.new(context.scene.frame_start)
        
        drawing = frame.drawing
        
        # Setup Frames material (for drawing frames)
        frames_material = self._get_create_material(gp, 'Frames')
        
        frames_mat_index = next((i for i, mat in enumerate(gp.materials) if mat == frames_material), None)
        if frames_mat_index is None:
            self.report({'ERROR'}, 'No material index for Frames material')
            return {'CANCELLED'}
        
        # Setup Panels material (for notes/panel frames) - only if notes are enabled
        panels_mat_index = None
        if (self.include_notes and self.show_notes_frames) or self.show_canvas_frame:
            panels_material = self._get_create_material(gp, 'Panels', color=(0.01, 0.01, 0.01, 1.0))
            panels_mat_index = next((i for i, mat in enumerate(gp.materials) if mat == panels_material), None)
            if panels_mat_index is None:
                self.report({'ERROR'}, 'No material index for Panels material')
                return {'CANCELLED'}
        
        # Clear existing strokes
        drawing.remove_strokes()
        
        # Calculate dimensions
        effective_canvas_x = self.canvas_x - (2 * self.canvas_margin)
        effective_canvas_y = self.canvas_y - (2 * self.canvas_margin)
        
        if effective_canvas_x <= 0 or effective_canvas_y <= 0:
            self.report({'ERROR'}, 'Canvas margin too large for canvas size')
            return {'CANCELLED'}
        
        # Account for panel margins
        grid_width = effective_canvas_x - (self.columns - 1) * self.panel_margin
        grid_height = effective_canvas_y - (self.rows - 1) * self.panel_margin
        
        if grid_width <= 0 or grid_height <= 0:
            self.report({'ERROR'}, 'Panel margin too large for grid')
            return {'CANCELLED'}
        
        space_x = grid_width / self.columns
        space_y = grid_height / self.rows
        
        # Calculate drawing area (accounting for notes)
        drawing_width = space_x
        if self.include_notes:
            drawing_width = space_x * (100 - self.notes_width_percent) / 100
        
        available_x = drawing_width * self.coverage / 100
        available_y = space_y * self.coverage / 100
        
        # Calculate frame size
        if available_x / self.frame_ratio <= available_y:
            frame_width = available_x
            frame_height = available_x / self.frame_ratio
        else:
            frame_height = available_y
            frame_width = available_y * self.frame_ratio
        
        # Create frames for all pages        
        for page in range(self.num_pages):
            page_y_offset = -(page * (self.canvas_y + self.page_spacing))
            
            # Create canvas frame if requested
            if self.show_canvas_frame:
                self._create_canvas_frame(drawing, panels_mat_index, page_y_offset)
            
            # Calculate start position for this page (top-left of the drawing area)
            start_x = -(effective_canvas_x / 2)
            start_y = (effective_canvas_y / 2) + page_y_offset
            
            # Create panel frames
            panel_count = 0
            for r_idx in range(self.rows):
                for c_idx in range(self.columns):
                    panel_count += 1
                    
                    # Calculate panel boundaries (including margins)
                    panel_left = start_x + c_idx * (space_x + self.panel_margin)
                    panel_right = panel_left + space_x
                    panel_top = start_y - r_idx * (space_y + self.panel_margin)
                    panel_bottom = panel_top - space_y
                    
                    panel_center_y = (panel_top + panel_bottom) / 2
                    
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
                    
                    # Apply coverage to center the frame within the drawing area
                    available_drawing_x = drawing_width * self.coverage / 100
                    available_drawing_y = space_y * self.coverage / 100
                    
                    # Calculate final frame size (already calculated above, but recalculate for clarity)
                    if available_drawing_x / self.frame_ratio <= available_drawing_y:
                        final_frame_width = available_drawing_x
                        final_frame_height = available_drawing_x / self.frame_ratio
                    else:
                        final_frame_height = available_drawing_y
                        final_frame_width = available_drawing_y * self.frame_ratio
                    
                    # Create drawing frame (centered within the drawing area) - using Frames material
                    half_width = final_frame_width / 2
                    half_height = final_frame_height / 2
                    
                    corners = [
                        Vector((drawing_center_x - half_width, 0, panel_center_y + half_height)),  # top-left
                        Vector((drawing_center_x + half_width, 0, panel_center_y + half_height)),  # top-right
                        Vector((drawing_center_x + half_width, 0, panel_center_y - half_height)),  # bottom-right
                        Vector((drawing_center_x - half_width, 0, panel_center_y - half_height)),  # bottom-left
                    ]
                    
                    drawing.add_strokes([4])
                    stroke = drawing.strokes[-1]
                    stroke.cyclic = True
                    stroke.material_index = frames_mat_index  # Use Frames material for drawing frames
                    
                    for i, pt in enumerate(stroke.points):
                        pt.position = corners[i]
                        pt.radius = 0.02
                    
                    # Create notes frame if requested and if show_notes_frames is enabled - using Panels material
                    if self.include_notes and self.show_notes_frames and panels_mat_index is not None:
                        # Create frame around the entire panel area (not just notes portion)
                        panel_center_x = (panel_left + panel_right) / 2
                        self._create_panel_frame(drawing, panels_mat_index, panel_center_x, panel_center_y, space_x, space_y)
        
        # Create cameras if requested
        camera_objects = []
        if self.create_camera:
            camera_objects = self._create_cameras(context)
            
            # Create timeline markers if requested
            if self.add_timeline_markers:
                self._create_timeline_markers(context, camera_objects)
        
        ## Print infos
        # total_frames = self.rows * self.columns * self.num_pages
        # self.report({'INFO'}, f"Created {total_frames} frames on {self.num_pages} page(s)")
        
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
        layout.operator("storytools.create_frame_grid", icon='GRID')

classes = (
    STORYTOOLS_OT_create_frame_grid,
    # STORYTOOLS_PT_frame_grid_panel,  # Panel for use in standalone mode
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)