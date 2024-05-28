import bpy
from math import pi
from mathutils import Vector, Matrix, Quaternion
from bpy.types import Operator, PropertyGroup
import numpy as np
from .. import fn

## Operator to set object selection from multi-gizmos or minimapview (using keymap poll)

class STORYTOOLS_OT_select_map_object(Operator):
    bl_idname = "storytools.select_object"
    bl_label = "Select Map Object "
    bl_description = "Select a map object"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}
    
    def invoke(self, context, event):
        self.mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        return self.execute(context)

    def set_object_active(self, context, ob):
        if context.object == ob:
            return
        if context.object:
            # prev = context.object
            context.object.select_set(False)            
            ## Maybe need to force change mode ? 
            # ## Ensure mode is object
            # if context.mode != 'OBJECT':
            #     lock_obj_mode_flag = False
            #     if context.scene.tool_settings.lock_object_mode:
            #         ## Temporarily remove object mode lock
            #         lock_obj_mode_flag = True
            #         context.scene.tool_settings.lock_object_mode = False
                
            #     bpy.ops.object.mode_set(mode='OBJECT')
            #     # context.view_layer.objects.active = ob
                
            #     if lock_obj_mode_flag:
            #         context.scene.tool_settings.lock_object_mode = True

        context.view_layer.objects.active = ob
        ob.select_set(True)

    def execute(self, context):
        objects = [o for o in context.scene.objects if o.type in ('GPENCIL',) and o.visible_get()]
        if not objects:
            return {'CANCELLED'}
        
        if len(objects) == 1:
            ## selection is already first object in list (objects[0])
            pass
        else:
            objects.sort(lambda x: (fn.location_to_region(x.matrix_world.translation) - self.mouse).length)

        self.set_object_active(context, objects[0])
        return {'FINISHED'}
            
        # prefs = fn.get_addon_prefs()
        # if context.mode != 'OBJECT':
        #     bpy.ops.object.mode_set(mode='OBJECT')
        # bpy.ops.object.select_all(action='DESELECT')
        # # for o in context.scene.objects:o.select_set(False)
        
        # r3d = context.space_data.region_3d
        
        # if r3d.view_perspective != 'CAMERA' and self.place_from_cam:
        #     view_matrix = context.scene.camera.matrix_world
        # else:    
        #     view_matrix = r3d.view_matrix.inverted()

        return {"FINISHED"}

def frame_objects(context, target):
    objects = [o for o in context.scene.objects if o.type in ('GPENCIL',) and o.visible_get()]

    if target == 'ALL' and context.scene.camera:
        objects.append(context.scene.camera)
    # objects = [o for o in context.view_layer.objects if o.type in ('GPENCIL',) and o.visible_get()]
    if not objects:
        return {'CANCELLED'}

    # with context.temp_override(active=objects[0], selected_objects=objects, selected_editable_objects=objects, selected_ids=objects):
    #     # bpy.ops.view3d.view_selected('INVOKE_DEFAULT', use_all_regions=False)
    #     bpy.ops.view3d.view_selected()

    ## as of 4.1.1 override do not works with view3d.view_selected : https://projects.blender.org/blender/blender/issues/112141
    ## Trying a full homemade method

    # calculate x/y Bbox
    global_bbox = [ob.matrix_world @ Vector(v) for ob in objects for v in ob.bound_box]
    # global_bbox_center = Vector(np.mean(global_bbox, axis=0))
    sorted_x = sorted(global_bbox,key = lambda x : x.x)
    sorted_y = sorted(global_bbox,key = lambda x : x.y)
    sorted_z = sorted(global_bbox,key = lambda x : x.z)

    down_left = Vector((sorted_x[0].x, sorted_y[0].y, sorted_z[0].z))
    top_right = Vector((sorted_x[-1].x, sorted_y[-1].y, sorted_z[-1].z))
    
    global_bbox_center = (down_left + top_right) / 2
    # bbox_2d = [sorted_x[0].x, sorted_x[-1].x, sorted_y[0].y, sorted_y[-1].y]

    ## Debug
    # context.scene.cursor.location = down_left
    # fn.empty_at(down_left, name='DL', size=0.2)
    # fn.empty_at(top_right, name='TR', size=0.2)


    width = sorted_x[-1].x - sorted_x[0].x
    height = sorted_y[-1].y - sorted_y[0].y
    # print('width: ', width)
    # print('height: ', height)
    
    ## Set center and view distance 
    context.region_data.view_location.xy = global_bbox_center.xy        
    context.region_data.view_distance = width if width > height else height

    if context.region_data.view_location.z < top_right.z:
        context.region_data.view_location.z = top_right.z + 0.2

class STORYTOOLS_OT_map_frame_objects(Operator):
    bl_idname = "storytools.map_frame_objects"
    bl_label = "Frame Object"
    bl_description = "Move and zoom Map to frame objects"
    bl_options = {"REGISTER", "INTERNAL"} # "UNDO", 
    
    target : bpy.props.StringProperty(name='Framing Target', default='ALL', options={'SKIP_SAVE'})

    def execute(self, context):
        frame_objects(context, target=self.target)
        return {"FINISHED"}


class STORYTOOLS_OT_setup_minimap_viewport(Operator):
    bl_idname = "storytools.setup_minimap_viewport"
    bl_label = "Set Minimap Viewport"
    bl_description = "Setup current viewport as minimap\
        \nAdjust viewport settings so viewport is considered as minimap\
        \n(determined by viewport orientation and combination of tool-settings"
    bl_options = {"REGISTER", "INTERNAL"} # "UNDO", 

    def execute(self, context):

        ## Set TOP ortho view (if needed)
        if context.region_data.view_perspective != 'ORTHO':
            context.region_data.view_perspective = 'ORTHO'

        euler_view = context.region_data.view_matrix.to_euler()
        if euler_view[1] != 0.0 or euler_view[1] != 0.0:
            # bpy.ops.view3d.view_axis(type='TOP', align_active=True, relative=True)
            context.region_data.view_rotation = Quaternion()
        
            frame_objects(context, target='ALL')

        ## Lock view
        context.region_data.lock_rotation = True

        overlay = context.space_data.overlay

        ## Completely disable overlays ? 
        ## Users may want to have some. + some object selectable might need overlay for selection through)
        bpy.context.space_data.overlay.show_overlays = True

        ## If overlay are enabled:
        ## Viewport settings
        # Optional
        overlay.show_floor = False
        overlay.show_axis_z = False
        overlay.show_axis_y = False
        overlay.show_axis_x = False

        # Mandatory
        overlay.show_annotation = False
        overlay.show_cursor = False
        overlay.show_text = False
        overlay.show_stats = False
        overlay.show_look_dev = False
        overlay.show_bones = False
        overlay.show_outline_selected = False
        overlay.show_viewer_attribute = False
        overlay.show_relationship_lines = False
        overlay.show_outline_selected = True # Keep selection overlay

        overlay.show_extras = True # Needed to show camera (and lights)

        ## Gizmos
        bpy.context.space_data.show_gizmo_navigate = False
        ## Do not show navigate
        # bpy.context.space_data.show_gizmo_object_translate = True # ?
        return {"FINISHED"}

class STORYTOOLS_OT_disable_minimap_viewport(Operator):
    bl_idname = "storytools.disable_minimap_viewport"
    bl_label = "Set Minimap Viewport"
    bl_description = "Disable current viewport as minimap"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        context.region_data.lock_rotation = False
        

        # context.region_data.view_perspective = 'ORTHO'
        return {"FINISHED"}

classes=(
STORYTOOLS_OT_select_map_object,
STORYTOOLS_OT_map_frame_objects,
STORYTOOLS_OT_setup_minimap_viewport,
STORYTOOLS_OT_disable_minimap_viewport,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)