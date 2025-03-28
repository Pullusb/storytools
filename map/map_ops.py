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
        objects = [o for o in context.scene.objects if o.type in ('GREASEPENCIL',) and o.visible_get()]
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
        
        # if r3d.view_perspective != 'CAMERA' and self.face_camera:
        #     view_matrix = context.scene.camera.matrix_world
        # else:    
        #     view_matrix = r3d.view_matrix.inverted()

        return {"FINISHED"}

class STORYTOOLS_OT_map_frame_objects(Operator):
    bl_idname = "storytools.map_frame_objects"
    bl_label = "Frame Object"
    bl_description = "Move and zoom Map to frame objects"
    bl_options = {"REGISTER", "INTERNAL"} # "UNDO", 
    
    target : bpy.props.StringProperty(name='Framing Target', 
                default='ALL',
                description='Frame target (in ALL, GP, ACTIVE)', 
                options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        if properties.target == 'GP':
            return 'Frame all Grease pencil objects'
        elif properties.target == 'ALL':
            return 'Frame camera and all Grease pencil objects'
        elif properties.target == 'ACTIVE':
            return 'Frame active object'
        else:
            return 'Frame objects'

    def execute(self, context):
        # TODO: make it a modal function to make the reframe movement smooth

        ## On certain condition, use View All when there are no GP objects
        if self.target in ('GP', 'ALL') and not len([o for o in context.scene.objects if o.type in ('GREASEPENCIL',)]):
            bpy.ops.view3d.view_all('INVOKE_DEFAULT')
            return {"CANCELLED"}
        fn.frame_objects(context, target=self.target)
        return {"FINISHED"}


def set_minimap_viewport_settings(context) -> None:
    ## Set TOP ortho view (if needed)
    if context.region_data.view_perspective != 'ORTHO':
        context.region_data.view_perspective = 'ORTHO'

    # euler_view = context.region_data.view_matrix.to_euler()
    # if euler_view[1] != 0.0 or euler_view[1] != 0.0:
    #     ## ops has incorrect context
    #     # bpy.ops.view3d.view_axis(type='TOP', align_active=True, relative=True) 
    ## manual view set
    context.region_data.view_rotation = Quaternion()
    ## Also frame GP and cam
    fn.frame_objects(context, target='ALL')

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
    # overlay.show_outline_selected = False
    overlay.show_viewer_attribute = False
    overlay.show_relationship_lines = False
    
    overlay.use_gpencil_grid = False
    overlay.use_gpencil_fade_objects = False
    
    overlay.show_outline_selected = True # Keep selection overlay
    overlay.show_object_origins_all = False # Show all object origin ?
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

class STORYTOOLS_OT_setup_minimap_viewport(Operator):
    bl_idname = "storytools.setup_minimap_viewport"
    bl_label = "Set Minimap Viewport"
    bl_description = "Setup current viewport as minimap\
        \nAdjust viewport settings so viewport is considered as minimap\
        \n(determined by viewport orientation and combination of tool-settings"
    bl_options = {"REGISTER", "INTERNAL"}

    split_viewport : bpy.props.BoolProperty(name='Split Viewport', default=False, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties) -> str:
        if properties.split_viewport:
            desc = 'Split current area to create a minimap viewport'
        else:
            desc = 'Setup current viewport as minimap'
        
        ## Precisions
        desc += '\nAdjust viewport settings so viewport is considered as minimap\
                 \n(determined by viewport orientation and combination of tool-settings'
        return desc

    def invoke(self, context, event):
        if not self.split_viewport:
            ## if there is no other viewport in screens
            viewport_count = 0
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        viewport_count += 1

            if viewport_count == 1:
                wm = bpy.context.window_manager
                return wm.invoke_props_dialog(self)
        
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        col=layout.column(align=True)
        col.label(text='This is the only viewport!', icon='ERROR')
        col.label(text='Are you sure you want to use it as minimap ?')
        col.label(text='(Viewport view settings are lost)')
        col.separator()
        col.label(text='Alternatively you can split current viewport:')
        col.operator('storytools.setup_minimap_viewport', text='Split With Minimap', icon='SPLIT_HORIZONTAL').split_viewport = True        

    def execute(self, context):
        if self.split_viewport:
            bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.49)
        set_minimap_viewport_settings(context)
        return {"FINISHED"}
    
class STORYTOOLS_OT_setup_minimap_on_pointed_editor(Operator):
    bl_idname = "storytools.setup_minimap_on_pointed_editor"
    bl_label = "Set Minimap Viewport On Editor"
    bl_description = "Setup minimap in pointer editor (split)"
    bl_options = {"REGISTER", "INTERNAL"}

    split_editor : bpy.props.BoolProperty(name='Split Editor', default=False, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties) -> str:
        if properties.split_editor:
            desc = 'Split pointed editor to create a minimap editor'
        else:
            desc = 'Replace pointed editor to minimap'
        
        ## Precisions
        desc += '\nAdjust editor settings so editor is considered as minimap\
                 \n(determined by editor orientation and combination of tool-settings'
        return desc

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        context.window.cursor_set("PICK_AREA")
        return {'RUNNING_MODAL'}

    def build_override_area_from_mouse(self, context, event):
        override = None
        screen = context.window.screen
        for i, area in enumerate(screen.areas):
            if (area.x < event.mouse_x < area.x + area.width
            and area.y < event.mouse_y < area.y + area.height):
                print(f"Set Minimap in area of {area.type}")
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {'window': context.window, 'screen': screen, 'area': area, 'region': region}
                # self.report({'INFO'}, f'Screen {screen.name} area of {area.type} index {i}')
                break
        return override

    def modal(self, context, event):
        if event.type == 'LEFTMOUSE':        
            # init_areas = [(a, a.type) for a in context.screen.areas]
            override = self.build_override_area_from_mouse(context, event)
            if not override:
                context.window.cursor_set("DEFAULT")
                self.report({'ERROR'}, 'No area found')
                return {'CANCELLED'}
            
            # splitted = False
            with context.temp_override(**override):
                # if self.split_editor:
                #     bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.49)
                #     splitted = True
    
                ## Change type to viewport
                if context.area.type != 'VIEW_3D':
                    context.area.type = 'VIEW_3D'
            
            ## re-use mouse location ?
            override = self.build_override_area_from_mouse(context, event)
            with context.temp_override(**override):
                set_minimap_viewport_settings(context)
            
            context.window.cursor_set("DEFAULT")
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
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
## No keymap registered for now, could be used to create a custom minimap context menu

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
STORYTOOLS_OT_setup_minimap_on_pointed_editor,
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