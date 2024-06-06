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


        # Do not select if too distant
        closest_dist = (fn.location_to_region(objects[0].matrix_world.translation) - self.mouse).length
        print('closest_dist: ', closest_dist)
        if closest_dist > 10.0:
            return {'CANCELLED'}

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
    val = width if width > height else height
    
    # if (down_left.xy - top_right.xy).length < 1.0:
    val = max(val, 2.0) # Clamp to 2.0 as minimum value

    ## Set center and view distance 
    context.region_data.view_location.xy = global_bbox_center.xy
    context.region_data.view_distance = val

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
            ## ops has incorrect context
            # bpy.ops.view3d.view_axis(type='TOP', align_active=True, relative=True) 
            ## manual view set
            context.region_data.view_rotation = Quaternion()
            ## Also frame GP and cam
            frame_objects(context, target='ALL')

        ## Lock view
        context.region_data.lock_rotation = True # map_val

        space_data = bpy.context.space_data
        overlay = space_data.overlay

        ## Completely disable overlays ? 
        ## - Users may want to have some.
        ## - And some object selectability might be needed overlay for selection)
        ## For now let's do with overlays

        space_data.overlay.show_overlays = True

        ## If overlay are enabled:
        ## Viewport settings
        # Optional
        ## Might be disturbing not having the floor and axis...
        overlay.show_floor = True
        overlay.show_axis_y = True
        overlay.show_axis_x = True
        overlay.show_axis_z = False

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
        overlay.show_object_origins_all = True # Show all object origin
        overlay.show_extras = True # Needed to show camera (and lights)

        ## Gizmos
        space_data.show_gizmo = True
        space_data.show_gizmo_context = True
        space_data.show_gizmo_tool = True
        space_data.show_gizmo_object_translate = True # Hide translate ? 

        ## Remove top right corner navigation Gizmos
        space_data.show_gizmo_navigate = False

        ## Visibility filter special combination (serve to identify viewport as minimap)
        space_data.show_object_viewport_lattice = False # map_val
        space_data.show_object_viewport_light_probe = False # map_val


        ## Hide UI elements and stuffs
        space_data.show_region_ui = False
        space_data.show_region_tool_header = False
        space_data.show_region_toolbar = False

        ## - ! - hiding this one mean it cannot be used for customizing view (can be done with new gyzmo set)
        ## - BUT, also had user visual customization... kinda risky.
        space_data.show_region_header = False

        return {"FINISHED"}

class STORYTOOLS_OT_disable_minimap_viewport(Operator):
    bl_idname = "storytools.disable_minimap_viewport"
    bl_label = "Set Minimap Viewport"
    bl_description = "Disable current viewport as minimap"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        context.region_data.lock_rotation = False # map_val
        space_data = bpy.context.space_data
        space_data.show_object_viewport_lattice = True # map_val
        space_data.show_object_viewport_light_probe = True # map_val

        ## Ensure header gets back
        space_data.show_region_header = True
        # context.region_data.view_perspective = 'ORTHO'

        return {"FINISHED"}


### Keymap Click operator
## Override clicks with poll on whole minimap viewport (?)

class STORYTOOLS_OT_minimap_lc(Operator):
    bl_idname = "storytools.minimap_lc"
    bl_label = "Minimap Click"
    bl_description = "Minimap only click event"
    bl_options = {"REGISTER", "INTERNAL"}
    
    @classmethod
    def poll(cls, context):
        return fn.is_minimap_viewport(context)

    def execute(self, context):
        print('Left click !')
        return {"FINISHED"}


addon_keymaps = []

def register_keymap():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is None:
        return
    km = kc.keymaps.new(name = "3D View", space_type = "VIEW_3D")
    kmi = km.keymap_items.new('storytools.minimap_lc', type='LEFTMOUSE', value='CLICK')
    # kmi.properties.select_mode = 'Sketch Draw'
    addon_keymaps.append((km, kmi))

def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)    
    addon_keymaps.clear()

classes=(
STORYTOOLS_OT_select_map_object,
STORYTOOLS_OT_map_frame_objects,
STORYTOOLS_OT_setup_minimap_viewport,
STORYTOOLS_OT_disable_minimap_viewport,
STORYTOOLS_OT_minimap_lc,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # register_keymap()

def unregister():
    # unregister_keymap()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)