import bpy
from bpy.props import IntProperty
from bpy.types import Operator
from mathutils import Vector

import numpy as np
import re

from .. import fn
from .create_static_storyboard import notes_default_bodys


class STORYTOOLS_OT_storyboard_add_pages(Operator):
    """Add new pages to an existing storyboard"""
    bl_idname = "storytools.storyboard_add_pages"
    bl_label = "Add Storyboard Pages"
    bl_description = "Add new pages to existing storyboard using an existing page as template"
    bl_options = {'REGISTER', 'UNDO'}
    
    num_pages: IntProperty(
        name="Number of Pages",
        description="Number of pages to add",
        default=1,
        min=1,
        soft_max=50,
        max=200
    )
    
    source_page: IntProperty(
        name="Source Page Number",
        description="Page number to use as template for new pages",
        default=1,
        min=1
    )

    def invoke(self, context, event):
        # Check if we have a storyboard grease pencil object
        if not context.object or context.object.type != 'GREASEPENCIL':
            self.report({'ERROR'}, "No Grease Pencil object selected")
            return {'CANCELLED'}
        
        # Check if we have timeline markers for pages
        scene = context.scene
        page_markers = [m for m in scene.timeline_markers if m.camera and m.name.startswith('stb_')]
        if not page_markers:
            self.report({'ERROR'}, "No storyboard page markers found")
            return {'CANCELLED'}
        
        # Set the maximum source page number
        self.source_page = min(self.source_page, len(page_markers))
        
        # Show dialog
        return context.window_manager.invoke_props_dialog(self, width=350)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        
        # Get number of existing pages
        scene = context.scene
        page_markers = [m for m in scene.timeline_markers if m.camera and m.name.startswith('stb_')]
        num_existing_pages = len(page_markers)
        
        layout.prop(self, "num_pages")
        layout.prop(self, "source_page")
        
        # Validation warnings
        if self.source_page > num_existing_pages:
            layout.label(text=f"Warning: Source page {self.source_page} doesn't exist", icon='ERROR')
            layout.label(text=f"Maximum page number is {num_existing_pages}")
        
        layout.separator()
        layout.label(text=f"Current pages: {num_existing_pages}")
        layout.label(text=f"Pages after adding: {num_existing_pages + self.num_pages}")
    
    def execute(self, context):
        scene = context.scene
        board_obj = context.object
        
        # Get existing page markers
        page_markers = [m for m in scene.timeline_markers if m.camera and m.name.startswith('stb_')]
        # page_markers.sort(key=lambda m: int(m.name.rsplit('_', 1)[1]))
        page_markers.sort(key=lambda m: m.frame)
        
        if self.source_page > len(page_markers):
            self.report({'ERROR'}, f"Source page {self.source_page} doesn't exist")
            return {'CANCELLED'}
        
        # Get source page marker and camera
        source_marker = page_markers[self.source_page - 1]
        source_camera = source_marker.camera
        print('source_camera: ', source_camera.name)
        
        # Get storyboard settings
        stb_settings = board_obj.get('stb_settings', {})
        if not stb_settings:
            self.report({'ERROR'}, "No storyboard settings found on object")
            return {'CANCELLED'}
        
        # Get storyboard collection
        stb_collection = scene.collection.children.get('Storyboard')
        if not stb_collection:
            self.report({'ERROR'}, "No 'Storyboard' collection found")
            return {'CANCELLED'}
        
        # Get source page bounds
        source_cam_frame = fn.get_cam_frame_world(source_camera, scene=scene)
        source_min = min(source_cam_frame, key=lambda v: (v.x, v.z))
        source_max = max(source_cam_frame, key=lambda v: (v.x, v.z))
        source_cam_frame_center = sum(source_cam_frame, Vector()) / len(source_cam_frame)

        # Calculate page spacing (distance between pages)
        page_height = source_max.z - source_min.z
        page_spacing = page_height + stb_settings.get('page_spacing', 0.2)
        
        # Find the last page position to place new pages after it
        last_marker = page_markers[-1]
        last_camera = last_marker.camera
        last_cam_frame = fn.get_cam_frame_world(last_camera, scene=scene)
        last_page_center = sum(last_cam_frame, Vector()) / len(last_cam_frame)
        
        offset_to_latest_page = last_page_center - source_cam_frame_center

        ## Get drawing to later reset some attributes
        drawing = None
        layer = next((layer for layer in board_obj.data.layers if layer.name == 'Frames'), None)
        if layer:
            frame = layer.current_frame()
            if frame:
                drawing = frame.drawing
                ## Seem like setting the attribute before adding stroke still works
                ## (otherwise opacity attr added and initialized at 0.0)
                point_count = drawing.attributes.domain_size('POINT')
                if not drawing.attributes.get('opacity'):
                    # print('Add missing opacity attribute')
                    opacity_attr = drawing.attributes.new(name='opacity', domain='POINT', type='FLOAT')
                    opacity_np_array = np.ones(point_count, dtype=np.float32) # np.full to specify values
                    opacity_attr.data.foreach_set('value', opacity_np_array)
                
                if not drawing.attributes.get('vertex_color'):
                    # print('Add missing vertex_color attribute')
                    vertex_color_attr = drawing.attributes.new(name='vertex_color', domain='POINT', type='FLOAT_COLOR')
                    vertex_color_np_array = np.zeros(point_count * 4, dtype=np.float32)
                    vertex_color_attr.data.foreach_set('color', vertex_color_np_array)

        # Create new pages
        for i in range(self.num_pages):
            new_page_num = len(page_markers) + i + 1
            
            # Calculate new page position
            new_page_offset = Vector((0, 0, -(page_spacing * (i + 1)))) + offset_to_latest_page
            
            # Create new camera
            new_camera = source_camera.copy()
            new_camera.data = source_camera.data.copy()
            new_camera.name = f"stb_cam_{new_page_num:02d}"
            new_camera.location = Vector((last_camera.location.x, last_camera.location.y, new_page_offset.z))
            ## link in same collection
            last_camera.users_collection[0].objects.link(new_camera)
            
            # Create new timeline marker
            new_marker = scene.timeline_markers.new(f"stb_cam_{new_page_num:02d}")
            new_marker.camera = new_camera
            new_marker.frame = last_marker.frame + (i + 1)
            
            # Duplicate strokes from source page
            self.duplicate_strokes_from_page(board_obj, source_min, source_max, new_page_offset)
            
            # Duplicate and update text objects
            self.duplicate_objects(stb_collection, source_min, source_max, new_page_offset, new_page_num, stb_settings)
                
        self.report({'INFO'}, f"Added {self.num_pages} new pages")
        return {'FINISHED'}
    
    def duplicate_strokes_from_page(self, board_obj, source_min, source_max, offset):
        """Duplicate grease pencil strokes from source page to new location"""
        for layer in board_obj.data.layers:
            if layer.name != 'Frames':  # Skip all layers except frame layer
                continue
            frame = layer.current_frame()
            if frame is None:
                continue
            
            drawing = frame.drawing
            strokes_to_duplicate = []
            
            # Find strokes within source page bounds
            for stroke in drawing.strokes:
                if any(source_min.x <= p.position.x <= source_max.x and 
                       source_min.z <= p.position.z <= source_max.z for p in stroke.points):
                    strokes_to_duplicate.append(stroke)
            

            drawing.add_strokes([len(s.points) for s in strokes_to_duplicate])

            new_strokes = drawing.strokes[-len(strokes_to_duplicate):]
            
            for stroke, new_stroke in zip(strokes_to_duplicate, new_strokes):
                new_stroke.material_index = stroke.material_index
                new_stroke.softness = stroke.softness
                new_stroke.fill_color = stroke.fill_color
                new_stroke.fill_opacity = stroke.fill_opacity
                new_stroke.start_cap = stroke.start_cap
                new_stroke.end_cap = stroke.end_cap

                new_stroke.cyclic = stroke.cyclic
                for i, point in enumerate(stroke.points):
                    new_stroke.points[i].position = point.position + Vector((0, 0, offset.z))
                    new_stroke.points[i].radius = point.radius
                    new_stroke.points[i].opacity = point.opacity
                    new_stroke.points[i].vertex_color = point.vertex_color
    
    def duplicate_objects(self, collection, source_min, source_max, offset, new_page_num, stb_settings):
        """Duplicate text objects from source page and update page numbers"""
        objects_to_duplicate = []
        
        # Find text objects within source page bounds
        for obj in collection.all_objects:
            if obj.type == 'GREASEPENCIL':
                continue
            world_pos = obj.matrix_world.translation
            if (source_min.x <= world_pos.x <= source_max.x and 
                source_min.z <= world_pos.z <= source_max.z):
                objects_to_duplicate.append(obj)

        # Duplicate text objects
        for obj in objects_to_duplicate:
            is_linked = obj.data.users > 2
            if obj.name.startswith("stb_logo"):
                is_linked = True  # Always link logo objects

            new_obj = obj.copy()
            if is_linked:
                new_obj.data = obj.data
            else:
                new_obj.data = obj.data.copy()
            new_obj.location = obj.location + offset
            
            ## link in same collection
            obj.users_collection[0].objects.link(new_obj)
            
            if is_linked:
                continue

            ## if not linked, update text content based on object type
            if new_obj.name.startswith("stb_shot_num"):
                # Update shot number if it contains page reference
                content = stb_settings.get("panel_header_left", "")
                if "{page}" in content:
                    new_obj.data.body = content.format(page=new_page_num)
                else:
                    new_obj.data.body = content
            
            elif new_obj.name.startswith("stb_panel_num"):
                # Update panel number
                content = stb_settings.get("panel_header_right", "")
                if "{page}" in content:
                    new_obj.data.body = content.format(page=new_page_num)
                else:
                    new_obj.data.body = content
            
            elif new_obj.name.startswith("panel_"):
                # Reset notes content
                content = notes_default_bodys.get(stb_settings.get("note_text_format", ""), "")
                new_obj.data.body = content
            
            elif new_obj.name.startswith("stb_page"):
                # Update page number in page headers/footers
                new_obj.data.body = re.sub(r'\d+', str(new_page_num).zfill(2), new_obj.data.body)
                ## For smart addition
                # if "{page}" in new_obj.data.body:
                #     new_obj.data.body = new_obj.data.body.replace("{page}", str(new_page_num))
                


def register():
    bpy.utils.register_class(STORYTOOLS_OT_storyboard_add_pages)


def unregister():
    bpy.utils.unregister_class(STORYTOOLS_OT_storyboard_add_pages)
