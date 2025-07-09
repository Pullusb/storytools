import bpy

import numpy as np

from bpy.types import Operator, PropertyGroup
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty, StringProperty

from .. import fn

def get_min_max_corner(positions, margin=0):
    ## Sort in place (modify list !!)
    positions.sort(key=lambda vec: (vec.x, vec.z))
    min_corner = positions[0]
    max_corner = positions[-1]
    
    if not margin:
        return min_corner, max_corner
    
    ## Add 20% margin to get strokes in frame
    diagonal = (min_corner - max_corner).length
    margin = diagonal * 0.2 / 2
    max_corner = max_corner + Vector((1, 0, 1)) * margin
    min_corner = min_corner + Vector((-1, 0, -1)) * margin
    return min_corner, max_corner

## unused - need to test performance
def any_point_in_rectangle_numpy(stroke, bottom_left, upper_right):
    """
    NumPy vectorized version - fastest for large point collections.
    """
    # Extract X and Z coordinates
    x_coords = np.array([p.position.x for p in stroke.points])
    z_coords = np.array([p.position.z for p in stroke.points])
    
    # Check bounds
    x_in_bounds = (x_coords >= bottom_left.x) & (x_coords <= upper_right.x)
    z_in_bounds = (z_coords >= bottom_left.z) & (z_coords <= upper_right.z)

    # Return True if any point satisfies both conditions
    return np.any(x_in_bounds & z_in_bounds)

def any_point_in_box(coords, min_corner, max_corner):
    ''' Check if any point in coords list is within the X-Z bounding box defined by min_corner and max_corner
    coords : list of Vector3 or tuple coordinates
    min_corner : Vector3, lower left corner of the bounding box
    max_corner : Vector3, upper right corner of the bounding box
    '''
    return any(min_corner.x <= co.x <= max_corner.x and min_corner.z <= co.z <= max_corner.z for co in coords)

## TODO: need a function to add pages (as a separate operator, but used in this case when need to offset last panel)

class STORYTOOLS_OT_storyboard_offset_panel(Operator):
    bl_idname = "storytools.storyboard_offset_panel"
    bl_label = "Storyboard Offset Panels"
    bl_description = "Add a new panel, applying offset to all subsequent panels"
    bl_options = {'REGISTER', 'UNDO'}
    
    read_direction : EnumProperty(
        name="Read Direction",
        description="Reading Frame direction",
        items=(
            ('RIGHT', "Left To Right", "Read direction first left to right then top to bottom"),
            ('DOWN', "Top To Bottom", "Read direction first top to bottom then left to right"),
        ),
        default='RIGHT'
    )

    number_to_insert : IntProperty(
        name="Panel Number To Insert",
        description="Number of panel to insert a new one",
        default=1,
        min=1,
    )

    offset_amount : IntProperty(
        name="Number of empty panel to add",
        description="Default Frame offset between each shot",
        default=1,
        min=1,
    )

    stop_offset_number : IntProperty(
        name="Panel number to stop offset",
        description="Panel number to stop offset (cannot be greater than total panel number)",
        default=1,
        min=1,
    )

    stop_offset_on_empty_panels : BoolProperty(
        name="Stop Offset Empty Panels",
        description="Stop offsetting on next empty panel",
        default=False,
    )

    # ignore_empty_frames : BoolProperty(
    #     name="Ignore Empty Frames",
    #     description="Ignore empty frames when inserting panels",
    #     default=True,
    # )

    def invoke(self, context, event):
        ## check if a storyboard object is active
        if not context.object and context.object.type != 'GREASE_PENCIL':
            self.report({'ERROR'}, "No Storyboard Grease Pencil object selected")
            return {'CANCELLED'}
        
        board_obj = context.object
        ## Find panels
        self.material_index = next((i for i, ms in enumerate(board_obj.material_slots) if ms.material and ms.material.name == 'Panels'), None)
        if self.material_index is None:
            self.report({'ERROR'}, 'Abort: Could not find any "Frames" material in the storyboard object')
            return {'CANCELLED'}
        
        # handle case where layer was renamed ?
        grid = board_obj.data.layers.get('Frames')
        if not grid:
            self.report({'ERROR'}, 'Abort: There is no layer named "Frames" found')
            return {'CANCELLED'}

        dr = grid.current_frame().drawing
        ## TODO: create a more robust way to get panel framing
        panel_strokes = [s for s in dr.strokes if s.material_index == self.material_index and len(s.points) == 4]
        if not panel_strokes:
            self.report({'ERROR'}, 'Abort: No panel stroke found in the storyboard (stroke using "Frames" material in "Frames" Layer)')
            return {'CANCELLED'}
        
        self.number_of_panels = len(panel_strokes)
        self.stop_offset_number = self.number_of_panels -1 

        ## IDEA: On launch scan all to get every index containing empty panel (considering strokes)
        # corner_min, corner_max = get_min_max_corner([p.position for p in panel_strokes[0].points])
        # width = corner_max.x - corner_min.x
        # height = corner_max.z - corner_min.z

        # TODO: if row/column is 1x1, just hide read direction option
        if gen_settings := board_obj.get('stb_settings', None):
            column_num = gen_settings.get('columns', None)
            print('column_num: ', column_num)
            if column_num == 1:
                self.read_direction = 'DOWN'

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=420)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "read_direction")
        layout.prop(self, "number_to_insert")
        layout.label(text=f"Total Panels: {self.number_of_panels}")
        layout.separator()
        layout.prop(self, "stop_offset_number")
        # layout.prop(self, "stop_offset_on_empty_panels", text="Automatic stop on first empty panel")


        # if self.stop_offset_number > self.number_of_panels:
        #     self.stop_offset_number = self.number_of_panels - 1 

        if self.number_to_insert >= self.number_of_panels:
            layout.label(text="Warning: Inserting panel beyond current total panels is not possible")
        if self.stop_offset_number >= self.number_of_panels:
            layout.label(text="Warning: Stopping offset at or beyond current total panels is not possible")

    
    def execute(self, context):
        ## Create new scene and link the whole storyboard object and collection

        if self.number_to_insert >= self.number_of_panels or self.stop_offset_number >= self.number_of_panels:
            self.report({'ERROR'}, 'Cannot insert or stop offset at (or beyond current total panels')
            return {'CANCELLED'}

        ## detect all position, maybe it'
        scn = context.scene
        
        ## Keep default order or reorder based on name or frame number ??

        ## get all frames
        board_obj = context.object
        grid = board_obj.data.layers.get('Frames')
        dr = grid.current_frame().drawing
        panel_strokes = [s for s in dr.strokes if s.material_index == self.material_index and len(s.points) == 4]
        frame_corners = [get_min_max_corner([p.position for p in s.points]) for s in panel_strokes]
        
        ## Add center as a third element in list
        frames_coords = [(f[0], f[1], ((f[0] + f[1]) / 2)) for f in frame_corners]

        ## group by pages (camera boundaries)
        ## Create a list of lists pages = [[page1 frames...], [page2 frames...]]
        page_markers = [m for m in scn.timeline_markers if m.camera and m.name.startswith('stb_')]
        page_list = []
        for marker in page_markers:
            panel_framing = []
            camera = marker.camera
            cam_frame = fn.get_cam_frame_world(camera, scene=scn)
            cam_min, cam_max = get_min_max_corner(cam_frame)

            for i in range(len(frames_coords)-1,-1,-1):
                ## frame_coord -> tuple of vectors : (min_corner, max_corner, center)
                
                frame_coord = frames_coords[i]

                if any_point_in_box(frame_coord, cam_min, cam_max):
                    ## append in current page list and remove from source list
                    panel_framing.append(frames_coords.pop(i))

            ## Todo optional: if all strokes in pages are empty, ignore pages
            ## Easily doable, but heavy... better have a manual page range limit, start-end)
            page_list.append(panel_framing)

        ## sort by read direction in each groups
        for frames_list in page_list:
            ## sort frames by their center position
            if self.read_direction == 'RIGHT':
                # sort by Z then X
                frames_list.sort(key=lambda vecs: (-vecs[2].z, vecs[2].x))
            else:
                # sort by X then Z
                frames_list.sort(key=lambda vecs: (vecs[2].x, -vecs[2].z))
        
        ## create and setup new scene with content to create new camera and markers
        stb_collection = scn.collection.children.get('Storyboard')
        all_objects = []
        if stb_collection:
            all_objects = [o for o in stb_collection.all_objects if o.type != 'CAMERA' and o != board_obj]

        ## Concatenate all groups
        panels = [coords for pages in page_list for coords in pages]

        if not panels:
            self.report({'ERROR'}, 'No panels found to offset')
            return {'CANCELLED'}

        ## TODO: offset panel content and all objects in stb_collection that have origin point within panel coordinates
        
        ## Find insertion point (1-based index from user input)
        insert_index = min(self.number_to_insert - 1, len(panels))
        
        ## Process panels in reverse order from insertion point to avoid moving already moved content
        ## - 2 to avoid moving the last panel (which should be empty)
        # end_index = len(panels) - 2
        end_index = self.stop_offset_number - 1
        for i in range(end_index, insert_index - 1, -1):
            current_panel = panels[i]
            current_min, current_max, current_center = current_panel
            
            # Calculate target position for this panel (move to next panel position)
            target_panel_index = i + 1
            # if target_panel_index >= len(panels):
            #     # If target is beyond existing panels, extrapolate based on last panel spacing
            #     if len(panels) >= 2:
            #         last_spacing = panels[-1][2] - panels[-2][2]
            #         target_center = panels[-1][2] + last_spacing
            #     else:
            #         # Only one panel, use default spacing
            #         panel_width = current_max.x - current_min.x
            #         target_center = current_panel[2] + Vector((panel_width * 1.2, 0, 0))
            # else:
            #     ## Use existing panel position as target
            #     target_center = panels[target_panel_index][2]

            target_center = panels[target_panel_index][2]
            
            # Calculate offset vector for this specific panel
            offset_vector = target_center - current_center
            
            ## Check if we should stop on empty panels (going reverse...)
            # if self.stop_offset_on_empty_panels:
            #     panel_has_content = False
            #     for layer in board_obj.data.layers:
            #         if layer.name == 'Frames':
            #             # panel layout should not move (??)
            #             continue
            #         frame = layer.current_frame()
            #         if frame is None:
            #             continue
            #         drawing = frame.drawing
            #         for stroke in drawing.strokes:
            #             if any(current_min.x <= p.position.x <= current_max.x and 
            #                    current_min.z <= p.position.z <= current_max.z for p in stroke.points):
            #                 panel_has_content = True
            #                 break
            #         if panel_has_content:
            #             break
                
            #     if not panel_has_content:
            #         continue
            
            # Find grease pencil strokes to move within current panel
            strokes_to_move = []
            for layer in board_obj.data.layers:
                if layer.name == 'Frames':
                    continue
                frame = layer.current_frame()
                if frame is None:
                    continue
                drawing = frame.drawing
                for stroke in drawing.strokes:
                    if any(current_min.x <= p.position.x <= current_max.x and 
                           current_min.z <= p.position.z <= current_max.z for p in stroke.points):
                        strokes_to_move.append(stroke)
            
            if strokes_to_move:
                print(f'Panel {i + 1}: {len(strokes_to_move)} strokes to move')
            
            # Apply offset to grease pencil strokes
            for stroke in strokes_to_move:
                for point in stroke.points:
                    point.position += offset_vector
            
            # Move 3D objects in stb_collection that have origin within panel
            if all_objects:
                objects_to_move = []
                
                for ob_idx in range(len(all_objects)-1, -1, -1):
                    obj = all_objects[ob_idx]
                    
                    # Check if object origin is within current panel bounds
                    # world_pos = obj.matrix_world.translation
                    
                    world_pos = obj.location
                    # if any_point_in_box([world_pos], current_min, current_max):
                    if (current_min.x <= world_pos.x <= current_max.x and 
                        current_min.z <= world_pos.z <= current_max.z):
                        objects_to_move.append(all_objects.pop(ob_idx))
                
                if objects_to_move:
                    print(f'Panel {i + 1}: {len(objects_to_move)} objects to move')
                
                # Apply panel offset to 3D objects
                for obj in objects_to_move:
                    obj.location += offset_vector
        
        ## TODO reproduce initial texts in new panel

        return {'FINISHED'}


classes = (
    STORYTOOLS_OT_storyboard_offset_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    

def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
