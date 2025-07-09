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

class STORYTOOLS_OT_create_animatic_from_board(Operator):
    bl_idname = "storytools.create_animatic_from_board"
    bl_label = "Create Animatic From Storyboard"
    bl_description = "Create animatic scene from the current marker pages and storyboard frames\
        \nEverything is linked into an 'Animatic' scene to setup different camera markers"
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

    resolution_x : IntProperty(
        name="Animatic Resolution X",
        description="Width resolution of for the animatic scene. height is calculated based on the aspect ratio",
        default=1920,
        min=100,
    )

    frame_offset : IntProperty(
        name="Frame Offset",
        description="Default Frame offset between each shot",
        default=72,
        min=1,
    )

    fps : IntProperty(
        name="Frame Rate",
        description="Frames per second for the animatic scene",
        default=24,
        min=1,
        max=120
    )

    ## TODO: Add poll

    ## need a target scene name ?

    def invoke(self, context, event):
        ## check if a storyboard object is active
        if not context.object:
            self.report({'ERROR'}, "No Storyboard Grease Pencil object selected")
            return {'CANCELLED'}
        
        board_obj = context.object
        self.material_index = next((i for i, ms in enumerate(board_obj.material_slots) if ms.material and ms.material.name == 'Frames'), None)
        if self.material_index is None:
            self.report({'ERROR'}, 'Abort: Could not find any "Frames" material in the storyboard object')
            return {'CANCELLED'}
        
        # handle case where layer was renamed ?
        grid = board_obj.data.layers.get('Frames')
        if not grid:
            self.report({'ERROR'}, 'Abort: There is no layer named "Frames" found')
            return {'CANCELLED'}

        dr = grid.current_frame().drawing
        st_frames = [s for s in dr.strokes if s.material_index == self.material_index]
        if not st_frames:
            self.report({'ERROR'}, 'Abort: No frames stroke found in the storyboard (stroke using "Frames" material in "Frames" Layer)')
            return {'CANCELLED'}
        
        self.number_of_frames = len(st_frames)

        corner_min, corner_max = get_min_max_corner([p.position for p in st_frames[0].points])
        width = corner_max.x - corner_min.x
        height = corner_max.z - corner_min.z
        self.aspect_ratio = height / width if width != 0 else 1.0

        ## Change direction if there is only one columns

        # TODO: if row/column is 1x1, just hide read direction option
        if gen_settings := board_obj.get('stb_settings', None):
            column_num = gen_settings.get('columns', None)
            print('column_num: ', column_num)
            if column_num == 1:
                self.read_direction = 'DOWN'

        ## create list of positions

        # if context.object.mode != 'OBJECT':
        #     self.report({'ERROR'}, "Please switch to Object mode")
        #     return {'CANCELLED'}
        ## Scan current storyboard to show number of frame detected and aspect ratio

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=380)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "read_direction")
        layout.prop(self, "fps", text="Frame Rate")

        layout.separator()
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "frame_offset", text="Shot Duration")
        row.label(text=" Frames")
        col.label(text=f"Time Per Panel: {self.frame_offset * (1 / self.fps):.2f} seconds")

        layout.separator()
        row = layout.row(align=True)
        row.prop(self, "resolution_x", text="Resolution")
        row.label(text=f" x {round(self.resolution_x * self.aspect_ratio)}")

        layout.separator()
        layout.label(text=f"Number of panel frames: {self.number_of_frames}")
        # layout.label(text=f"Detected Aspect Ratio: {self.aspect_ratio:.2f}")
    
    def execute(self, context):
        ## Create new scene and link the whole storyboard object and collection

        ## detect all position, maybe it'
        source_scene = context.scene
        page_markers = [m for m in source_scene.timeline_markers if m.camera and m.name.startswith('stb_')]
        
        ## Keep default order or reorder based on name or frame number ??

        ## get all frames
        board_obj = context.object
        grid = board_obj.data.layers.get('Frames')
        dr = grid.current_frame().drawing
        stroke_frames = [s for s in dr.strokes if s.material_index == self.material_index]
        frame_corners = [get_min_max_corner([p.position for p in s.points]) for s in stroke_frames]
        
        ## Add center as a third element in list
        frames_coords = [(f[0], f[1], ((f[0] + f[1]) / 2)) for f in frame_corners]

        ## group by pages (camera boundaries)
        ## Create a list of lists pages = [[page1 frames...], [page2 frames...]]
        page_list = []
        for marker in page_markers:
            draw_frames = []
            camera = marker.camera
            cam_frame = fn.get_cam_frame_world(camera, scene=source_scene)
            cam_min, cam_max = get_min_max_corner(cam_frame)

            for i in range(len(frames_coords)-1,-1,-1):
                ## frame_coord -> tuple of vectors : (min_corner, max_corner, center)
                
                frame_coord = frames_coords[i]

                if any_point_in_box(frame_coord, cam_min, cam_max):
                    ## append in current page list and remove from source list
                    draw_frames.append(frames_coords.pop(i))

            ## Todo optional: if all strokes in pages are empty, ignore pages
            ## Easily doable, but heavy... better have a manual page range limit, start-end)
            page_list.append(draw_frames)

        ## sort by read direction in each groups
        for frames_list in page_list:
            ## sort frames by their center position
            if self.read_direction == 'RIGHT':
                # sort by Z then X
                frames_list.sort(key=lambda vecs: (-vecs[2].z, vecs[2].x))
            else:
                # sort by X then Z
                frames_list.sort(key=lambda vecs: (vecs[2].x, -vecs[2].z))

        ## Concatenate all groups ? (not needed for now)

        ## create and setup new scene with content to create new camera and markers
        scn = bpy.data.scenes.get('Animatic')
        if scn is None:
            scn = bpy.data.scenes.new('Animatic')
        
        scn.render.fps = self.fps
        scn.render.resolution_x = self.resolution_x
        scn.render.resolution_y = round(self.resolution_x * self.aspect_ratio)


        stb_collection = source_scene.collection.children.get('Storyboard')
        if not board_obj.name in stb_collection.all_objects:
            # Link the storyboard object to the new scene only if not already in Storyboard collection
            scn.collection.objects.link(board_obj)

        ## Link Storyboard collection and Hide initial camera collection
        scn.collection.children.link(stb_collection)
        ## Hide the initial camera collection in animatic scene

        # stb_vlcol = scn.view_layer[0].layer_collection.children.get('Storyboard')
        # if stb_vlcol:
        #     camera_vlcol = stb_vlcol.children.get('Storyboard Cameras')
        #     if camera_vlcol:
        #         camera_vlcol.exclude = True

        ## More robust : get the "Storyboard Cameras" collection by name
        page_cam_col = next((col for col in scn.collection.children_recursive if col.name == 'Storyboard Cameras'), None)
        if page_cam_col:
            if vl_page_cam := fn.get_view_layer_collection(page_cam_col, view_layer=scn.view_layers[0]):
                vl_page_cam.exclude = True


        ## Create collection for cameras
        animatic_collection = bpy.data.collections.get('Animatic') # Later
        if not animatic_collection:
            animatic_collection = bpy.data.collections.new('Animatic')
        ## Link if not there
        if animatic_collection not in scn.collection.children_recursive:
            scn.collection.children.link(animatic_collection)

        y_loc = -5
        frame_count = 1
        scn.frame_start = 1
        for page_count, page in enumerate(page_list):
            for frame_coords in page:
                ## frame_coords is a tuple of vectors (min_corner, max_corner, center)
                min_corner, max_corner, center = frame_coords
                
                ## Create a new camera for each frame
                cam_name = f"anim_{frame_count:04d}"
                ## get if already exists ?
                cam_data = bpy.data.cameras.new(name=cam_name)
                cam_obj = bpy.data.objects.new(cam_name, cam_data)
                animatic_collection.objects.link(cam_obj)

                ## Set camera location and rotation
                cam_obj.location = Vector((center.x, y_loc, center.z))
                cam_obj.rotation_euler = (1.5708, 0, 0)
                cam_data.type = 'ORTHO'

                width = max_corner.x - min_corner.x
                height = max_corner.z - min_corner.z

                ref_size = height if height > width else width
                
                ## TODO: add margin multiplier on ortho scale
                cam_data.ortho_scale = ref_size


                ## Create a marker for the camera
                panel_name = f"panel_{frame_count}" #:03d
                marker = scn.timeline_markers.new(name=panel_name, frame=(frame_count * self.frame_offset) - self.frame_offset)
                marker.camera = cam_obj

                frame_count += 1
                ## Bonus (long): find a good method to get related text and use it as pseudo-subtitles text (fitted into drawing)

            ## continuously push ending frame            
            scn.frame_end = (frame_count * self.frame_offset) - self.frame_offset

        ## make animatic scene active
        bpy.context.window.scene = scn        
        return {'FINISHED'}
        

class STORYTOOLS_OT_push_markers(Operator):
    bl_idname = "storytools.push_markers"
    bl_label = "Push Markers"
    bl_description = "Push all markers to the right of the current frame by 1 (10 with Shift pressed)"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        name="Direction",
        description="Direction to push the markers",
        items=(
            ('LEFT', "Left", "Push markers to the left"),
            ('RIGHT', "Right", "Push markers to the right"),
        ),
        default='RIGHT'
    )

    def invoke(self, context, event):
        self.step = 10 if event.shift else 1
        return self.execute(context)

    def execute(self, context):
        current_frame = context.scene.frame_current
        step = self.step if self.direction == 'RIGHT' else -self.step

        moved = False
        for marker in context.scene.timeline_markers:
            marker.select = marker.frame > current_frame
            if marker.frame > current_frame:
                marker.frame += step
                moved = True
        
        if not moved:
            self.report({'WARNING'}, "No markers subsequent markers to move")
            return {'FINISHED'}

        ## Show 
        fps = context.scene.render.fps

        ordered_markers = sorted([m for m in context.scene.timeline_markers], key=lambda m: m.frame)

        current_marker = max((m for m in ordered_markers if m.frame <= current_frame), key=lambda m: m.frame, default=None)
        next_marker = min((m for m in ordered_markers if m.frame > current_frame), key=lambda m: m.frame, default=None)
        if not current_marker or not next_marker:
            return {'FINISHED'}

        ## Use last marker as reference for frame padding
        padding = len(str(next_marker.frame)) # could be ordered_markers[-1] frame ? more logic ?
        frame_count = next_marker.frame - current_marker.frame
        marker_time = frame_count / fps
        self.report({'INFO'}, f"Current shot: {frame_count:0{padding}d} frames. Time: {marker_time:.2f}s")
        return {'FINISHED'}


class STORYTOOLS_OT_time_compression(Operator):
    bl_idname = "storytools.time_compression"
    bl_label = "Time Compression"
    bl_description = "Compress or dilate the timeline by adding or removing one frame between all existing markers"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        name="Operation",
        description="Choose whether to compress or dilate the timeline",
        items=(
            ('COMPRESS', "Compress", "Remove one frame between all markers"),
            ('DILATE', "Dilate", "Add one frame between all markers"),
        ),
        default='COMPRESS'
    )

    def invoke(self, context, event):
        self.force_compress = event.ctrl
        return self.execute(context)

    def report_average_time(self, context, markers):
        # Calculate average time between frames
        total_time = 0
        frame_differences = []

        for i in range(1, len(markers)):
            frame_diff = markers[i].frame - markers[i - 1].frame
            frame_differences.append(frame_diff)
            total_time += frame_diff

        if frame_differences:
            avg_time = total_time / len(frame_differences)
            avg_time_seconds = avg_time / context.scene.render.fps
            self.report({'INFO'}, f"Average time between frames: {avg_time:.2f} frames ({avg_time_seconds:.2f} seconds)")

    def execute(self, context):
        ## Sort markers by frame number
        markers = sorted(context.scene.timeline_markers, key=lambda m: m.frame)
        if len(markers) < 2:
            self.report({'WARNING'}, "Not enough markers to perform time compression or dilation")
            return {'CANCELLED'}

        step = -1 if self.direction == 'COMPRESS' else 1

        if self.direction == 'DILATE':
            for i in range(1, len(markers)):
                markers[i].frame += i * step
            
            self.report_average_time(context, markers)
            return {'FINISHED'}

        if not self.force_compress:
            ## Avoid first using 0
            for i in range(len(markers) - 1, 0, -1):
                if markers[i].frame - markers[i - 1].frame <= 1:
                    print('Marker too close:', markers[i].name, markers[i].frame)
                    self.report({'WARNING'}, "Some markers are too close to compress (Ctrl + Click to bypass and still compress other)")
                    return {'CANCELLED'}
        
        # Avoid first using 1
        for i in range(1, len(markers)):
            frame_numbers = [m.frame for m in markers]
            for j in range(1, len(markers)):
                if j < i:
                    ## Don't touch already compressed markers
                    continue

                if frame_numbers[j - 1] >= frame_numbers[j] - 1:
                    break

                markers[j].frame -= 1
        
        self.report_average_time(context, markers)

        # self.report({'INFO'}, f"Timeline {'compressed' if step == -1 else 'dilated'} successfully")
        return {'FINISHED'}

## --- Marker management in Timeline

class STORYTOOLS_PG_board_animatic(PropertyGroup):
    show_marker_management: BoolProperty(
        name="Show Marker Management",
        description="Show the marker management UI in timeline headers",
        default=False,
    )

def marker_management_ui(self, context):
    """Add a panel to the marker management UI"""
    layout = self.layout
    layout.label(text="Markers:")
    row = layout.row(align=True)
    row.operator("storytools.push_markers", text="", icon="TRIA_LEFT").direction = 'LEFT'
    row.operator("storytools.push_markers", text="", icon="TRIA_RIGHT").direction = 'RIGHT'

    row = layout.row(align=True)
    row.operator("storytools.time_compression", text="", icon="TRIA_LEFT").direction = 'COMPRESS'
    row.operator("storytools.time_compression", text="", icon="TRIA_RIGHT").direction = 'DILATE'

classes = (
    STORYTOOLS_OT_create_animatic_from_board,
    STORYTOOLS_OT_push_markers,
    STORYTOOLS_OT_time_compression,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # bpy.types.DOPESHEET_HT_header.append(marker_management_ui)

def unregister():
    # bpy.types.DOPESHEET_HT_header.remove(marker_management_ui)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
