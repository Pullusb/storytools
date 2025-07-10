import bpy

import numpy as np

from bpy.types import Operator, PropertyGroup
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty, StringProperty

from .. import fn
from . create_static_storyboard import notes_default_bodys

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

## TODO: need a function to add/remove pages (as a separate operator, but used in this case when need to offset last panel or remove pages)

class STORYTOOLS_OT_storyboard_offset_panel(Operator):
    bl_idname = "storytools.storyboard_offset_panel"
    bl_label = "Storyboard Offset Panels"
    bl_description = "Add or remove a panel, applying offset to all subsequent panels"
    bl_options = {'REGISTER', 'UNDO'}
    
    offset_direction : EnumProperty(
        name="Offset Direction",
        description="Direction to offset panels",
        items=(
            ('FORWARD', "Forward (Add Panel)", "Offset panels forward to make room for a new panel"),
            ('BACKWARD', "Backward (Remove Panel)", "Offset panels backward to fill the gap of a removed panel"),
        ),
        default='FORWARD'
    )
    
    read_direction : EnumProperty(
        name="Read Direction",
        description="Reading Frame direction",
        items=(
            ('RIGHT', "Left To Right", "Read direction first left to right then top to bottom"),
            ('DOWN', "Top To Bottom", "Read direction first top to bottom then left to right"),
        ),
        default='RIGHT'
    )

    insert_index : IntProperty(
        name="Panel Number",
        description="Panel number to insert (forward) or remove (backward)",
        default=1,
        min=1,
    )

    offset_amount : IntProperty(
        name="Number of empty panel to add",
        description="Default Frame offset between each shot",
        default=1,
        min=1,
    )

    stop_index : IntProperty(
        name="Panel number to stop offset",
        description="Panel number to stop offset (cannot be greater than total panel number)",
        default=1,
        min=1,
    )

    # stop_offset_on_empty_panels : BoolProperty(
    #     name="Stop Offset Empty Panels",
    #     description="Stop offsetting on next empty panel",
    #     default=False,
    # )

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
        self.stop_index = self.number_of_panels -1 

        ## IDEA: On launch scan all to get every index containing empty panel (considering strokes)
        # corner_min, corner_max = get_min_max_corner([p.position for p in panel_strokes[0].points])
        # width = corner_max.x - corner_min.x
        # height = corner_max.z - corner_min.z

        # TODO: If row/column is 1x1, just hide read direction option entirely ?
        if gen_settings := board_obj.get('stb_settings', None):
            column_num = gen_settings.get('columns', None)
            if column_num == 1:
                self.read_direction = 'DOWN'

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=420)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "offset_direction")
        layout.prop(self, "read_direction")
        
        # Update label based on direction
        if self.offset_direction == 'FORWARD':
            layout.prop(self, "insert_index", text="Panel Number To Insert")
        else:
            layout.prop(self, "insert_index", text="Panel Number To Remove")
            
        layout.label(text=f"Total Panels: {self.number_of_panels}")
        layout.separator()
        layout.prop(self, "stop_index")
        layout.label(text="(Stop panel is included)")
        # layout.prop(self, "stop_offset_on_empty_panels", text="Automatic stop on first empty panel")

        # if self.stop_index > self.number_of_panels:
        #     self.stop_index = self.number_of_panels - 1 

        if self.offset_direction == 'FORWARD':
            if self.insert_index >= self.number_of_panels:
                layout.label(text="Warning: Inserting panel beyond current total panels is not possible")
        else:
            if self.insert_index > self.number_of_panels:
                layout.label(text="Warning: Cannot remove a panel that doesn't exist")
                
        if self.stop_index >= self.number_of_panels:
            layout.label(text="Warning: Stopping offset at or beyond current total panels is not possible")

    def get_page_and_index(self, index, page_list):
        """From global index, return index of page and index of panel in that page"""
        ct = 0
        for page_index, panels in enumerate(page_list):
            for i in range(len(panels)):
                if ct + i == index:
                    return page_index, i
            ct += len(panels)
        return None, None

    def execute(self, context):
        ## Create new scene and link the whole storyboard object and collection

        if self.offset_direction == 'FORWARD' and self.insert_index >= self.number_of_panels:
            self.report({'ERROR'}, 'Cannot insert panel at or beyond current total panels')
            return {'CANCELLED'}
        
        if self.offset_direction == 'BACKWARD' and self.insert_index > self.number_of_panels:
            self.report({'ERROR'}, 'Cannot remove a panel that doesn\'t exist')
            return {'CANCELLED'}
            
        if self.stop_index >= self.number_of_panels:
            self.report({'ERROR'}, 'Cannot stop offset at or beyond current total panels')
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
        
        ## Find insertion point (1-based index from user input)
        insert_index = min(self.insert_index - 1, len(panels) - 1)
        end_index = min(self.stop_index - 1, len(panels) - 1)
        

        moved_text_objects = {}
        to_remove_text_objects = []
        ## Precalculate iteration parameters based on direction
        if self.offset_direction == 'FORWARD':
            # Forward: iterate backward from end to start
            start_idx = end_index
            stop_idx = insert_index - 1
            step = -1
            # For forward offset: source is current panel (i), target is next panel (i+1)
            get_source_idx = lambda i: i
            get_target_idx = lambda i: i + 1
            direction_text = "forward"
            panel_duplication_index = insert_index
            panel_to_remove_index = self.stop_index
        else:  # BACKWARD
            # Backward: iterate forward from start to end
            start_idx = insert_index
            stop_idx = end_index + 1
            # if start_idx == stop_idx:
            #     stop_idx = end_index + 1 

            step = 1
            # For backward offset: source is next panel (i+1), target is current panel (i)
            get_source_idx = lambda i: i + 1
            get_target_idx = lambda i: i
            direction_text = "backward"
            panel_duplication_index = self.stop_index
            panel_to_remove_index = insert_index

        ## Store text in panel that will be stripped
        print('panel_duplication_index: ', panel_duplication_index)
        print('panel_to_remove_index: ', panel_to_remove_index)
        if panel_duplication_index == panel_to_remove_index:
            self.report({'ERROR'}, 'Cannot duplicate and remove the same panel at the same time')
            return {'CANCELLED'}

        for ob in all_objects:
            if ob.type == 'FONT':
                loc = ob.matrix_world.translation
                if any_point_in_box([loc], 
                        panels[panel_duplication_index][0], panels[panel_duplication_index][1]):
                    # Store text objects to move later
                    moved_text_objects[ob] = ob.location.copy()
    
                if any_point_in_box([loc], 
                        panels[panel_to_remove_index][0], panels[panel_to_remove_index][1]):
                    # Store text objects to move later
                    to_remove_text_objects.append(ob)
    
        ## Single loop for both directions
        for i in range(start_idx, stop_idx, step):
            source_idx = get_source_idx(i)
            target_idx = get_target_idx(i)
            
            # Skip if source panel doesn't exist
            if source_idx >= len(panels):
                continue
                
            source_panel = panels[source_idx]
            target_panel = panels[target_idx]
            
            source_min, source_max, source_center = source_panel
            target_min, target_max, target_center = target_panel
            
            # Calculate offset vector (from source to target)
            offset_vector = target_center - source_center
            
            # Find grease pencil strokes to move from source panel
            strokes_to_move = []
            for layer in board_obj.data.layers:
                if layer.name == 'Frames':
                    continue
                frame = layer.current_frame()
                if frame is None:
                    continue
                drawing = frame.drawing
                for stroke in drawing.strokes:
                    if any(source_min.x <= p.position.x <= source_max.x and 
                           source_min.z <= p.position.z <= source_max.z for p in stroke.points):
                        strokes_to_move.append(stroke)
            
            # if strokes_to_move:
            #     print(f'Panel {i + 1}: {len(strokes_to_move)} strokes to move {direction_text}')
            
            # Apply offset to grease pencil strokes
            for stroke in strokes_to_move:
                for point in stroke.points:
                    point.position += offset_vector
            
            # Move 3D objects from source panel
            if all_objects:
                objects_to_move = []
                
                # Iterate backward through objects to safely remove during iteration
                for ob_idx in range(len(all_objects)-1, -1, -1):
                    obj = all_objects[ob_idx]
                    
                    # Check if object origin is within source panel bounds
                    world_pos = obj.location
                    if (source_min.x <= world_pos.x <= source_max.x and 
                        source_min.z <= world_pos.z <= source_max.z):
                        objects_to_move.append(all_objects.pop(ob_idx))
                
                # if objects_to_move:
                #     print(f'Panel {i + 1}: {len(objects_to_move)} objects to move {direction_text}')
                
                # Apply panel offset to 3D objects
                for obj in objects_to_move:
                    obj.location += offset_vector

        ## Add / remove text where needed
        ## swap instead of delete when moving backward ?
        
        stb_settings = board_obj.get('stb_settings')
        for obj, loc in moved_text_objects.items():
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            ## Link in same collection
            obj.users_collection[0].objects.link(new_obj)
            ## Adjust object name to a more coherent thing
            # new_obj.name 

            ## replace (currently have the location of copy-source)
            new_obj.location = loc # replace at original location

            # Reset to initial text
            if stb_settings:
                content = None
                if new_obj.name.startswith("stb_shot_num"):
                    content = stb_settings.get("panel_header_left")
                
                elif new_obj.name.startswith("stb_panel_num"):
                    content = stb_settings.get("panel_header_right")
                
                elif new_obj.name.startswith("panel_"):
                    content = notes_default_bodys.get(stb_settings.get("note_text_format",''))
                
                if content is not None:
                    new_obj.data.body = content

        ## remove text in destination panel after offset to avoid duplication
        for obj in reversed(to_remove_text_objects):
            page_id, page_panel_id = self.get_page_and_index(panel_to_remove_index, page_list)
            if page_id and page_panel_id:
                ## For the sake of user, start count at 1 (not page 0 or panel 0)
                # print(f'Remove text {obj.name} at page {page_id + 1}, panel {page_panel_id + 1}. (global index: {panel_to_remove_index + 1})')
            bpy.data.objects.remove(obj, do_unlink=True)
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