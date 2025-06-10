## Create a grid of panel suitable for quick storyboard thumbnails.

import bpy
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty
from bpy.types import Operator, Panel
from mathutils import Vector

# TODO:
# - Add option to add a frame for the canvas itself
# - Add option to create an orthographic camera facing the canvas
# - Optionally : Add place for action notes, dialog notes, scene, panel numbers
# - Out of this operator scope, but find a way to somehow detect the frames for easy rearange, duplicate, add, remove, etc

class STORYTOOLS_OT_create_frame_grid(Operator):
    """Create a grid of frames using grease pencil strokes"""
    bl_idname = "storytools.create_frame_grid"
    bl_label = "Create Frame Grid"
    bl_description = "Create a grid of rectangular frames"
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
    
    # Frame settings
    coverage: FloatProperty(
        name="Coverage (%)",
        description="Percentage of space each frame occupies",
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
        # CUSTOM doesn't change values
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        
        # Canvas settings
        box = layout.box()
        box.label(text="Canvas Settings", icon='MESH_PLANE')
        
        # Canvas preset with update callback
        row = box.row()
        row.prop(self, "canvas_preset")
        # if self.canvas_preset != 'CUSTOM':
        #     row.operator("storytools.update_canvas_preset", text="", icon='FILE_REFRESH')
        
        col = box.column(align=True)
        # TODO: add value to choose overall canvas size when not in custom to affect the end real world size.
        col.enabled = self.canvas_preset == 'CUSTOM'
        col.prop(self, "canvas_x")
        col.prop(self, "canvas_y")
            
        box.prop(self, "canvas_margin")
        
        # Frame settings  
        box = layout.box()
        box.label(text="Panel Settings", icon='IMAGE_RGB') # Frame Settings
        box.prop(self, "ratio_preset")
        if self.ratio_preset == 'CUSTOM':
            box.prop(self, "use_custom_xy")
            if self.use_custom_xy:
                col = box.column(align=True)
                col.prop(self, "custom_ratio_x")
                col.prop(self, "custom_ratio_y")
                # Show calculated ratio
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
        
        # Object settings
        box = layout.box()
        box.label(text="Object Settings", icon='OUTLINER_OB_GREASEPENCIL')
        box.prop(self, "force_new_object")
        # TODO: Add option to create separate material or use line (if exists)
        
        # Preview info
        layout.separator()
        total_frames = self.rows * self.columns
        layout.label(text=f"Total Frames: {total_frames}", icon='INFO')
        
        # Calculate and show frame dimensions
        effective_canvas_x = self.canvas_x - (2 * self.canvas_margin)
        effective_canvas_y = self.canvas_y - (2 * self.canvas_margin)
        
        if effective_canvas_x > 0 and effective_canvas_y > 0:
            space_x = effective_canvas_x / self.columns
            space_y = effective_canvas_y / self.rows
            
            available_x = space_x * self.coverage / 100
            available_y = space_y * self.coverage / 100
            
            # Get current ratio
            current_ratio = self.frame_ratio
            if self.ratio_preset != 'CUSTOM':
                ratio_values = {
                    '16_9': 1.778, '16_10': 1.600, '4_3': 1.333, '3_2': 1.500,
                    '185_1': 1.850, '235_1': 2.350, '1_1': 1.000, '9_16': 0.563
                }
                current_ratio = ratio_values[self.ratio_preset]
            elif self.use_custom_xy and self.custom_ratio_y > 0:
                current_ratio = self.custom_ratio_x / self.custom_ratio_y
            
            # Calculate frame size
            if available_x / current_ratio <= available_y:
                frame_width = available_x
                frame_height = available_x / current_ratio
            else:
                frame_height = available_y
                frame_width = available_y * current_ratio
                
            layout.label(text=f"Frame Size: {frame_width:.2f} x {frame_height:.2f}")
    
    def execute(self, context):
        # Update canvas dimensions from preset
        self.update_canvas_preset(context)
        
        # Update ratio from preset if not custom
        if self.ratio_preset != 'CUSTOM':
            ratio_values = {
                '16_9': 1.778, '16_10': 1.600, '4_3': 1.333, '3_2': 1.500,
                '185_1': 1.850, '235_1': 2.350, '1_1': 1.000, '9_16': 0.563
            }
            self.frame_ratio = ratio_values[self.ratio_preset]
        elif self.use_custom_xy:
            # Calculate ratio from x:y values
            if self.custom_ratio_y > 0:
                self.frame_ratio = self.custom_ratio_x / self.custom_ratio_y
        
        # Determine if we need to create a new grease pencil object
        need_new_object = (self.force_new_object or 
                          not context.object or 
                          context.object.type != 'GREASEPENCIL')
        
        if need_new_object:
            # Create a new grease pencil object
            STORYTOOLS_data = bpy.data.grease_pencils_v3.new("Frame Grid")
            obj = bpy.data.objects.new("Frame Grid", STORYTOOLS_data)
            context.collection.objects.link(obj)
            
            # Make it the active object
            context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # Deselect other objects
            for other_obj in context.selected_objects:
                if other_obj != obj:
                    other_obj.select_set(False)
                    
            self.report({'INFO'}, "Created new Grease Pencil object")
        else:
            obj = context.object
        
        gp = obj.data
        
        # Setup layer, frame, material
        if not (layer := gp.layers.get('Frames')):
            layer = gp.layers.new('Frames', set_active=False)
            layer.lock = True
            ## Sent to bottom -> Should probably stay at the top of the stack to see even with overlapping drawings.
            gp.layers.move_bottom(layer)

        
        frame = next((f for f in layer.frames), None)
        if frame is None:
            frame = layer.frames.new(context.scene.frame_start)
        
        drawing = frame.drawing
        
        # Setup material
        if not (material := gp.materials.get('Frames')):
            material = bpy.data.materials.get('Frames')
            if material and material.is_grease_pencil:
                gp.materials.append(material)
            else:
                material = bpy.data.materials.new('Frames')
                bpy.data.materials.create_gpencil_data(material)
                gp.materials.append(material)
        
        mat_index = next((i for i, mat in enumerate(gp.materials) if mat == material), None)
        if mat_index is None:
            self.report({'ERROR'}, 'No material index for Frames material')
            return {'CANCELLED'}
        
        # Clear existing strokes
        drawing.remove_strokes()
        
        # Apply margin to canvas
        effective_canvas_x = self.canvas_x - (2 * self.canvas_margin)
        effective_canvas_y = self.canvas_y - (2 * self.canvas_margin)
        
        if effective_canvas_x <= 0 or effective_canvas_y <= 0:
            self.report({'ERROR'}, 'Canvas margin too large for canvas size')
            return {'CANCELLED'}
        
        # Calculate frame dimensions
        space_x = effective_canvas_x / self.columns
        space_y = effective_canvas_y / self.rows
        
        available_x = space_x * self.coverage / 100
        available_y = space_y * self.coverage / 100
        
        if available_x / self.frame_ratio <= available_y:
            frame_width = available_x
            frame_height = available_x / self.frame_ratio
        else:
            frame_height = available_y
            frame_width = available_y * self.frame_ratio
        
        # Calculate start position (accounting for margin)
        start_corner = Vector((
            -(effective_canvas_x / 2), 
            0, 
            (effective_canvas_y / 2)
        ))
        
        # Create frames
        for r_idx in range(self.rows):
            for c_idx in range(self.columns):
                # Calculate frame center position
                center_x = start_corner.x + (c_idx + 0.5) * space_x
                center_y = start_corner.z - (r_idx + 0.5) * space_y
                
                # Calculate corners
                half_width = frame_width / 2
                half_height = frame_height / 2
                
                corners = [
                    Vector((center_x - half_width, 0, center_y + half_height)),  # top-left
                    Vector((center_x + half_width, 0, center_y + half_height)),  # top-right
                    Vector((center_x + half_width, 0, center_y - half_height)),  # bottom-right
                    Vector((center_x - half_width, 0, center_y - half_height)),  # bottom-left
                ]
                
                # Create stroke
                drawing.add_strokes([4])
                stroke = drawing.strokes[-1]
                stroke.cyclic = True
                stroke.material_index = mat_index
                
                for i, pt in enumerate(stroke.points):
                    pt.position = corners[i]
                    pt.radius = 0.02
        
        ## Loop when using redo panel
        # self.report({'INFO'}, 
        #     f"Created {self.rows * self.columns} frames ({self.rows}x{self.columns} grid)")
        
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
    # STORYTOOLS_PT_frame_grid_panel,  # Panel for use in standalone mode, should fo into storuytools.ui
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
