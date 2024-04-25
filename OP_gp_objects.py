import bpy
import gpu

# from .fn import get_addon_prefs
from math import pi, radians, degrees
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.geometry import intersect_line_plane

from bpy.types import Context, Event, Operator, Panel, PropertyGroup
from bpy.props import CollectionProperty, PointerProperty
from gpu_extras.batch import batch_for_shader

from . import fn
from . import draw
from .fn import get_addon_prefs
from .constants import LAYERMAT_PREFIX

## Bonus
# - load guides if there are any

## possible modal cursor set
# ('DEFAULT', 'NONE', 'WAIT', 'CROSSHAIR', 'MOVE_X', 'MOVE_Y', 'KNIFE', 'TEXT', 
# 'PAINT_BRUSH', 'PAINT_CROSS', 'DOT', 'ERASER', 'HAND', 
# 'SCROLL_X', 'SCROLL_Y', 'SCROLL_XY', 'EYEDROPPER', 'PICK_AREA', 
# 'STOP', 'COPY', 'CROSS', 'MUTE', 'ZOOM_IN', 'ZOOM_OUT')

## Object transform

    # on_cam : bpy.props.BoolProperty(
    #     default=False, options={'SKIP_SAVE'})
        # if self.on_cam:
        #     self.ob = context.scene.camera
        #     if not self.ob:
        #         return {'CANCELLED'}

        #     ## Take view center when in viewcam
        #     if context.space_data.region_3d.view_perspective == 'CAMERA':
        #         self.init_world_loc = fn.get_cam_frame_world_center(self.ob)
        #     else:
        #         self.init_world_loc = self.ob.matrix_world.to_translation()

        # else:
        #     self.ob = context.object
        #     self.init_world_loc = self.ob.matrix_world.to_translation()

def draw_callback_wall(self, context):
    ## Restrict to current viewport
    if context.area != self.current_area:
        return

    prefs = get_addon_prefs()
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    shader.bind()

    previous_depth_test_value = gpu.state.depth_test_get()
    # gpu.state.depth_mask_set(True)
    gpu.state.blend_set('ALPHA')

    ## Draw behind zone
    gpu.state.depth_test_set('LESS')
    shader.uniform_float("color", prefs.visual_hint_end_color)
    batch = batch_for_shader(shader, 'TRIS', {"pos": self.coords})
    batch.draw(shader)

    if context.space_data.region_3d.view_perspective == 'CAMERA':
        ## Draw front zone (only in camera view to avoid flicking)
        gpu.state.depth_test_set('GREATER')
        shader.uniform_float("color", prefs.visual_hint_start_color)
        batch = batch_for_shader(shader, 'TRIS', {"pos": self.front_coords})
        batch.draw(shader)


    # Restore values
    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set(previous_depth_test_value)
    # gpu.state.depth_mask_set(False)

class STORYTOOLS_OT_object_depth_move(Operator):
    bl_idname = "storytools.object_depth_move"
    bl_label = "Object Depth Move"
    bl_description = "Move object Forward/backward (Slide left-right)\
                    \n+ Ctrl : Adjust Scale (Retain same size in camera framing)\
                    \n+ Shift : Precision mode"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not context.object:
            cls.poll_message_set("No active object")
            return False
        if context.object.type == 'CAMERA' and len(context.selected_objects) < 2:
            cls.poll_message_set("Cannot move camera object")
            return False
        return True
        # return context.object and context.object.type != 'CAMERA'

    def invoke(self, context, event):
        self.cam = bpy.context.scene.camera
        if not self.cam:
            self.report({'ERROR'}, 'No active camera')
            return {"CANCELLED"}
        if any(context.object.lock_location):
            self.report({'ERROR'}, "Active object's location is locked")
            return {'CANCELLED'}
        
        self.init_mouse_x = event.mouse_x
        self.shift_pressed = event.shift
        self.delta = 0
        self.cumulated_delta = 0

        self.cam_pos = self.cam.matrix_world.translation
        self.view_vector = Vector((0,0,-1))
        self.view_vector.rotate(self.cam.matrix_world)
        self.mode = 'distance'

        ## Consider all selected only in object mode
        if context.mode == 'OBJECT':
            self.objects = [o for o in context.selected_objects if o.type != 'CAMERA']
            if context.object.type != 'CAMERA' and context.object not in self.objects:
                self.objects.append(context.object)
        else:
            self.objects = [context.object]

        # Filter locked objects
        self.objects = [o for o in self.objects if not any(o.lock_location)] 
        if not self.objects:
            self.report({'ERROR'}, "Object is locked")
            return {'CANCELLED'}

        self.init_mats = [o.matrix_world.copy() for o in self.objects]
        
        if self.cam.data.type == 'ORTHO':
            context.area.header_text_set(f'Move factor: 0.00')
            # distance is view vector based
        else:
            self.init_vecs = [o.matrix_world.translation - self.cam_pos for o in self.objects]
            self.init_dists = [v.length for v in self.init_vecs]
            context.area.header_text_set(
                f'Move factor: 0.00 | Mode: {self.mode} (M to switch) | Ctrl: Adjust Scale | Shift: Precision')
        
        context.window.cursor_set("SCROLL_X")
        
        self.current_area = context.area # gpuDraw
        if get_addon_prefs().use_visual_hint:
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_wall, (self, context), 'WINDOW', 'POST_VIEW') # gpuDraw
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def stop(self, context):
        context.area.header_text_set(None)
        context.window.cursor_set("DEFAULT")
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW') # gpuDraw
        context.area.tag_redraw()
        ## refresh all view if in all viewport

    def modal(self, context, event):
        if self.mode == 'distance':
            factor = 0.1 if not event.shift else 0.01
        else:
            # Smaller factor for proportional dist
            factor = 0.01 if not event.shift else 0.001

        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.delta
            self.init_mouse_x = event.mouse_x

        if event.type in {'MOUSEMOVE'}:
            # diff = (event.mouse_x - self.init_mouse_x) * factor

            self.delta = (event.mouse_x - self.init_mouse_x) * factor
            diff = self.cumulated_delta + self.delta

            if self.cam.data.type == 'ORTHO':
                # just push in view vector direction
                context.area.header_text_set(f'Move factor: {diff:.2f}')
                for i, obj in enumerate(self.objects):
                    new_vec = self.init_mats[i].translation + (self.view_vector * diff)
                    obj.matrix_world.translation = new_vec
            else:
                # Push from camera point and scale accordingly
                context.area.header_text_set(
                    f'Move factor: {diff:.2f} | Mode: {self.mode} (M to switch) | Ctrl: Adjust scale | Shift: Slow')

                for i, obj in enumerate(self.objects):
                    if self.mode == 'distance':
                        ## move with the same length for everyone 
                        new_vec = self.init_vecs[i] + (self.init_vecs[i].normalized() * diff)
                    
                    else:
                        ## move with proportional factor from individual distance vector to camera
                        new_vec = self.init_vecs[i] + (self.init_vecs[i] * diff)

                    obj.matrix_world.translation = self.cam_pos + new_vec
                    
                    if event.ctrl: # Adjust scale only if Ctrl is pressed
                        dist_percentage = new_vec.length / self.init_dists[i]
                        obj.scale = self.init_mats[i].to_scale() * dist_percentage
                    else:
                        obj.scale = self.init_mats[i].to_scale() # reset to initial size

            ## Prepare coordinate for GPU draw
            d = 1000
            z_offset = 0.006
            self.coords = [
                Vector((-d,-d, -z_offset)),
                Vector((d,-d, -z_offset)),
                Vector((0, d, -z_offset)),
            ]
            for v in self.coords:
                v.rotate(self.cam.matrix_world)
                v += context.object.matrix_world.to_translation()
            
            self.front_coords = [
                Vector((-d,-d, z_offset)),
                Vector((d,-d, z_offset)),
                Vector((0, d, z_offset)),
            ]
            for v in self.front_coords:
                v.rotate(self.cam.matrix_world)
                v += context.object.matrix_world.to_translation()


        if event.type in {'M'} and event.value == 'PRESS':
            # Switch mode
            self.mode = 'distance' if self.mode == 'proportional' else 'proportional'

        # cancel on release
        if event.type in {'LEFTMOUSE'}: # and event.value == 'PRESS'
            draw.stop_callback(self, context)
            ## Key objects
            for o in self.objects:
                fn.key_object(o, use_autokey=True)
            return {"FINISHED"}
        
        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            for i, obj in enumerate(self.objects):
                obj.matrix_world = self.init_mats[i]
            draw.stop_callback(self, context)
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}


class STORYTOOLS_OT_object_pan(Operator):
    bl_idname = "storytools.object_pan"
    bl_label = 'Object Pan Translate'
    bl_description = "Translate active object, X/Y to lock on axis\
                    \n+ Ctrl : autolock on major axis\
                    \n+ Shift : Precision mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object

    def invoke(self, context, event):
        # TODO bonus : add multiselection support like depth move (only on object mode)
        self.ob = context.object
        if any(context.object.lock_location):
            self.report({'ERROR'}, "Active object's location is locked")
            return {'CANCELLED'}

        self.final_lock = self.lock = None
        self.shift_pressed = event.shift
        self.cumulated_translate = Vector((0, 0, 0))
        self.current_translate = Vector((0, 0, 0))
        self.init_world_loc = self.ob.matrix_world.to_translation()

        self.init_pos = self.ob.location.copy() # to restore if cancelled

        ## Axis Lock
        # view_matrix = context.space_data.region_3d.view_matrix
        # self.local_x = view_matrix.to_quaternion() @ Vector((1,0,0))
        # self.local_y = view_matrix.to_quaternion() @ Vector((0,1,0))
        view_rotation = context.space_data.region_3d.view_rotation
        self.local_x = view_rotation @ Vector((1,0,0))
        self.local_y = view_rotation @ Vector((0,1,0))
        self.lock_x_coords = [self.init_world_loc + self.local_x * 10000, 
                              self.init_world_loc + self.local_x * -10000]
        self.lock_y_coords = [self.init_world_loc + self.local_y * 10000, 
                              self.init_world_loc + self.local_y * -10000]

        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.init_vector = fn.region_to_location(self.init_mouse, self.init_world_loc)

        self.update_position(context, event)

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw.lock_axis_draw_callback, args, 'WINDOW', 'POST_VIEW')
        context.window.cursor_set("SCROLL_XY")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def update_position(self, context, event):
        mouse_co = Vector((event.mouse_x, event.mouse_y))

        ## Handle precision mode
        multiplier = 1 if not event.shift else 0.1
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_translate += self.current_translate
            self.init_vector = fn.region_to_location(mouse_co, self.init_world_loc)

        current_loc = fn.region_to_location(mouse_co, self.init_world_loc)
        self.current_translate = (current_loc - self.init_vector) * multiplier

        move_vec = self.current_translate + self.cumulated_translate

        lock = self.lock
        ## Override lock with ctrl auto-axis lock if pressed
        if event.ctrl:
            move_2d = mouse_co - self.init_mouse
            if abs(move_2d.x) >= abs(move_2d.y):
                lock = 'X'
            else:
                lock = 'Y'

        new_loc = self.init_world_loc + move_vec
        
        if lock:
            ## Use intersect line plane on object origin and cam X-Z plane
            if lock == 'X':
                plane_no = context.space_data.region_3d.view_rotation @ Vector((0,1,0))
            if lock == 'Y':
                plane_no = context.space_data.region_3d.view_rotation @ Vector((1,0,0))
            locked_pos = intersect_line_plane(new_loc, new_loc + plane_no, self.init_world_loc, plane_no)
            if locked_pos is not None:
                new_loc = locked_pos

        self.final_lock = lock

        ## Set new position
        self.ob.matrix_world.translation = new_loc

    def modal(self, context, event):    
        self.update_position(context, event)

        if event.type in ('X','Y') and event.value == 'PRESS':
            self.lock = event.type if self.lock != event.type else None

        if event.type == 'LEFTMOUSE': # and event.value == 'RELEASE'
            draw.stop_callback(self, context)
            fn.key_object(self.ob, use_autokey=True)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.ob.location = self.init_pos
            draw.stop_callback(self, context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        return {"FINISHED"}

class STORYTOOLS_OT_object_rotate(Operator):
    bl_idname = "storytools.object_rotate"
    bl_label = 'Object Rotate'
    bl_description = "Rotate active object on camera axis\
                    \n+ Ctrl : Snap on 15 degrees angles\
                    \n+ Shift : Precision mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object

    def invoke(self, context, event):
        self.ob = context.object
        if any(context.object.lock_rotation):
            self.report({'ERROR'}, "Active object's rotation is locked")
            return {'CANCELLED'}
    
        self.shift_pressed = event.shift
        self.cumulated_delta = 0
        self.current_delta = 0

        self.init_mat = self.ob.matrix_world.copy()

        self.view_vector = Vector((0,0,-1))
        r3d = context.space_data.region_3d
        self.view_vector.rotate(r3d.view_rotation) # r3d.view_matrix

        ## Snap on 15 degrees
        self.snap_step = radians(15)
        self.init_mouse_x = event.mouse_x

        context.window.cursor_set("SCROLL_XY")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def update_rotation(self, context, event):
        ## Adjust rotation speed according to precision mode
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse_x = event.mouse_x

        ## Calcualte rotation from last reference point
        multiplier = 0.01 if not event.shift else 0.001
        self.current_delta = (event.mouse_x - self.init_mouse_x) * multiplier

        ## Get final rotation
        final_rotation = self.cumulated_delta + self.current_delta
        
        ## Angle snap
        if event.ctrl:
            final_rotation = fn.snap_to_step(final_rotation, self.snap_step)

        context.area.header_text_set(f'Rotation: {degrees(final_rotation):.2f}')

        ## Rotate on view vector
        rot_matrix = Matrix.Rotation(final_rotation, 4, self.view_vector)

        mat = self.init_mat.copy()
        mat.translation = Vector((0,0,0))
        mat = rot_matrix @ mat
        mat.translation = self.init_mat.translation
        self.ob.matrix_world = mat

    def modal(self, context, event):        
        self.update_rotation(context, event)
        if event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")
            fn.key_object(self.ob, use_autokey=True)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.ob.matrix_world = self.init_mat
            context.area.header_text_set(None)
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        return {"FINISHED"}


class STORYTOOLS_OT_object_scale(Operator):
    bl_idname = "storytools.object_scale"
    bl_label = 'Object Scale'
    bl_description = "Scale object by going left-right\
                    \n+ Shift : Precision mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object

    def invoke(self, context, event):
        if any(context.object.lock_scale):
            self.report({'ERROR'}, "Active object's scale is locked")
            return {'CANCELLED'}
        self.init_scale = context.object.scale.copy()
        self.init_mouse_x = event.mouse_x

        self.shift_pressed = event.shift
        self.current_delta = 0
        self.cumulated_delta = 0

        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        multiplier = 0.01 if not event.shift else 0.001
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse_x = event.mouse_x

        self.current_delta = (event.mouse_x - self.init_mouse_x) * multiplier

        scale_offset = self.cumulated_delta + self.current_delta

        ## Mutliply by initial scale
        context.object.scale = self.init_scale * (1 + scale_offset)

        ## Add to initial scale (Less usable with bigger scales)
        # context.object.scale = self.init_scale + Vector([scale_offset]*3)

        if event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")

            ## Key all transforms
            fn.key_object(context.object, use_autokey=True)

            ## Key only scale
            # fn.key_object(context.object, loc=False, rot=False, use_autokey=True)

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.object.scale = self.init_scale
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

## Create object

def distance_selection_update(self, context):
    # print('self: ', dir(self))
    if self.place_from_cam and context.scene.camera:
        self.init_dist = fn.coord_distance_from_cam(context=context)
    else:
        self.init_dist = fn.coord_distance_from_view(context=context)


class STORYTOOLS_OT_create_object(Operator):
    bl_idname = "storytools.create_object"
    bl_label = "Create New Drawing"
    bl_description = "Create a new grease pencil object"
    bl_options = {"REGISTER", "UNDO"} # , "INTERNAL"

    name : bpy.props.StringProperty(
        name='Name',
        description="Name of Grease pencil object")
    
    parented : bpy.props.BoolProperty(
        name='Attached To Camera',
        description="When Creating the object, Attach it to the camera",
        default=False)
    
    init_dist : bpy.props.FloatProperty(
        name="Distance", description="Initial distance of new grease pencil object", 
        default=8.0, min=0.0, max=999, step=3, precision=3,
        subtype='DISTANCE')
    
    place_from_cam : bpy.props.BoolProperty(
        name='Use Active Camera',
        description="Create the object facing camera, else create from your current view",
        default=False, update=distance_selection_update)

    at_cursor : bpy.props.BoolProperty(
        name='At Cursor',
        description="Create object at cursor location, else centered position at cursor 'distance' facing view",
        default=False)
    
    track_to_cam : bpy.props.BoolProperty(
        name='Add Track To Camera',
        description="Add a track to constraint pointing at active camera\
            \nThis makes object's always face camera",
        default=False)

    def invoke(self, context, event):
        ## Suggest a numbered default name for quick use
        gp_ct = len([o for o in context.scene.objects if o.type == 'GPENCIL'])
        self.name = f'Drawing_{gp_ct+1:03d}'
        settings = context.scene.storytools_settings
        
        ## Calculate distance to 3D cursor
        # self.init_dist = settings.initial_distance # overwritten by dist from cusor
        # self.view_distance_from_cursor = fn.coord_distance_from_view(context=context)
        # self.cam_distance_from_cursor = None
        # if context.scene.camera:
        #     self.cam_distance_from_cursor = fn.coord_distance_from_cam(context=context)

        distance_selection_update(self, context)
        self.parented = settings.initial_parented
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, 'name')
        layout.prop(self, 'parented')
        layout.prop(self, 'at_cursor')
        row = layout.row()
        row.prop(self, 'init_dist')
        row.active = not self.at_cursor # enabled
        layout.prop(self, 'track_to_cam')

        if context.space_data.region_3d.view_perspective != 'CAMERA':
            col=layout.column()
            col.label(text='Not in camera', icon='ERROR')
            col.prop(self, 'place_from_cam', text='Face Active Camera')
        
        # if self.init_dist <= 0: (FIXME init_dist always positive, need futher check)
        #     viewpoint ='camera' if self.place_from_cam else 'view'
        #     col.label(text=f'Cursor is behind {viewpoint}', icon='ERROR') 
    
    def execute(self, context):
        prefs = get_addon_prefs()

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        # for o in context.scene.objects:o.select_set(False)
        
        r3d = context.space_data.region_3d
        
        if r3d.view_perspective != 'CAMERA' and self.place_from_cam:
            view_matrix = context.scene.camera.matrix_world
        else:    
            view_matrix = r3d.view_matrix.inverted()

        if self.at_cursor:
            loc = context.scene.cursor.location
        else:
            loc = view_matrix @ Vector((0.0, 0.0, -self.init_dist))
        
        ## Create GP object
        # TODO bonus : maybe check if want to use same data as another drawing

        ## Clean name
        self.name = self.name.strip()
        gp = bpy.data.grease_pencils.new(self.name)
        ob_name = self.name

        ob = bpy.data.objects.new(ob_name, gp)

        ## Set collection
        draw_col = bpy.data.collections.get('Drawings')
        if not draw_col:
            draw_col = bpy.data.collections.new('Drawings')
            bpy.context.scene.collection.children.link(draw_col)
        draw_col.objects.link(ob)

        if self.parented:
            ob.parent = context.scene.camera

        ## Place
        _ref_loc, ref_rot, _ref_scale  = view_matrix.decompose()
        rot_mat = ref_rot.to_matrix().to_4x4() @ Matrix.Rotation(-pi/2, 4, 'X')
        loc_mat = Matrix.Translation(loc)
        new_mat = loc_mat @ rot_mat @ fn.get_scale_matrix((1,1,1))
        ob.matrix_world = new_mat

        ## Make active and selected
        context.view_layer.objects.active = ob
        ob.select_set(True)

        if self.track_to_cam:
            constraint = ob.constraints.new('TRACK_TO')
            constraint.target = context.scene.camera
            constraint.track_axis = 'TRACK_Y'
            constraint.up_axis = 'UP_Z'

        ## Configure
        # TODO: Set Active palette (Need a selectable loader)
        # fn.load_palette(path_to_palette)

        fn.load_default_palette(ob=ob)
        gp.edit_line_color[3] = prefs.default_edit_line_opacity # Bl default is 0.5
        gp.use_autolock_layers = True
        
        for l_name in reversed(['Sketch', 'Line', 'Color']):
            layer = gp.layers.new(l_name)
            layer.frames.new(context.scene.frame_current)
            layer.use_lights = False # Can be a project prefs
        
            ## Set default association
            ## TODO: Set default name as string in prefs ?
            if l_name in ['Line', 'Sketch']:
                fn.set_material_association(ob, layer, 'line')
            elif l_name == 'Color':
                fn.set_material_association(ob, layer, 'fill_white')

        # Enter Draw mode
        bpy.ops.object.mode_set(mode='PAINT_GPENCIL')
        fn.reset_draw_settings(context=context)

        return {"FINISHED"}


class STORYTOOLS_OT_align_with_view(Operator):
    bl_idname = "storytools.align_with_view"
    bl_label = "Align With View"
    bl_description = "Align object with view\
        \nCtrl + Click align but keep object Z axis pointing up"
    bl_options = {"REGISTER", "UNDO"} # "INTERNAL"

    @classmethod
    def poll(cls, context):
        return context.object

    keep_z_up : bpy.props.BoolProperty(name='Keep Z Up', default=False)

    def invoke(self, context, event):
        self.keep_z_up = event.ctrl
        return self.execute(context)

    def execute(self, context):
        r3d = context.space_data.region_3d            
        
        for ob in context.selected_objects:
            
            ## Handle  camera object
            if ob.type == 'CAMERA':
                continue
            ## skip active camera if selected and IN cam view
            # if context.scene.camera \
            #     and ob == context.scene.camera \
            #     and context.space_data.region_3d.view_perspective == 'CAMERA':
            #     continue

            if self.keep_z_up:
                ## Align to view but keep world Up
                Z_up_vec = Vector((0.0, 0.0, 1.0))
                aim = r3d.view_rotation @ Z_up_vec
                # Track Up
                ref_matrix = aim.to_track_quat('Z','Y').to_matrix().to_4x4()
            
            else:
                ## Aligned to view Matrix
                ref_matrix = r3d.view_matrix.inverted()

            ## Objects are rotated by 90° on X except for Text objects.
            fn.assign_rotation_from_ref_matrix(ob, ref_matrix, rot_90=ob.type != 'FONT')

        return {"FINISHED"}


## ---
## Object Property groups and UIlist
## ---

class STORYTOOLS_OT_visibility_toggle(Operator):
    bl_idname = "storytools.visibility_toggle"
    bl_label = 'Toggle Visibility'
    bl_description = "Toggle and synchronize viewlayer visibility, viewport and render visibility"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True
    # def invoke(self, context, event):
    #     return self.execute(context)

    name : bpy.props.StringProperty()

    def execute(self, context):
        if not self.name:
            return {"CANCELLED"}
        ob = context.scene.objects.get(self.name)
        if not ob:
            return {"CANCELLED"}
        
        # hide = not ob.hide_viewport
        hide = ob.visible_get() # Already inversed
        
        ob.hide_viewport = hide
        ob.hide_render = hide
        # Set viewlayer visibility
        ob.hide_set(hide)
        return {"FINISHED"}

class STORYTOOLS_OT_object_draw(Operator):
    bl_idname = "storytools.object_draw"
    bl_label = 'Object Draw'
    bl_description = "Set draw mode\
        \nEnter first GP object available\
        \nIf no GPencil object exists, pop-up creation menu"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    # name : bpy.props.StringProperty()
    def invoke(self, context, event):
        self.ctrl = event.ctrl
        return self.execute(context)

    def execute(self, context):
        ## Popup to select GP ? -> Pop panel with ctrl can miss-click, Need separate button
        # if self.ctrl:
        #     bpy.ops.wm.call_panel(name='STORYTOOLS_PT_drawings_ui', keep_open=True)
        #     return {"FINISHED"}

        ## If active object is a GP, go in draw mode or do nothing
        if context.object and context.object.type == 'GPENCIL':
            if context.mode != 'PAINT_GPENCIL':
                bpy.ops.object.mode_set(mode='PAINT_GPENCIL')

            return {"FINISHED"}

        ## First GP object
        # gp = next((o for o in context.scene.objects if o.type == 'GPENCIL'), None)
        
        ## First (visible) GP objects
        gp = next((o for o in context.scene.objects if o.type == 'GPENCIL' if o.visible_get()), None)
        if gp:
            ## Set as active and select this gp object
            context.view_layer.objects.active = gp
            gp.select_set(True)
            bpy.ops.object.mode_set(mode='PAINT_GPENCIL')
            return {"FINISHED"}

        else:
            bpy.ops.storytools.create_object('INVOKE_DEFAULT')
            
        return {"FINISHED"}


## Property groups

def update_object_change(self, context):
    ob = context.scene.objects[self.index]
    # print('Switch to object', ob.name)
    if ob.type != 'GPENCIL' or context.object is ob:
        return

    prev_mode = context.mode
    possible_gp_mods = ('OBJECT', 
                        'EDIT_GPENCIL', 'SCULPT_GPENCIL', 'PAINT_GPENCIL',
                        'WEIGHT_GPENCIL', 'VERTEX_GPENCIL')

    if prev_mode not in possible_gp_mods:
        prev_mode = None

    mode_swap = False
    
    ## TODO optional: Option to stop mode sync ?
    ## Set in same mode as previous object
    if context.scene.tool_settings.lock_object_mode:
        if context.mode != 'OBJECT':
            mode_swap = True
            bpy.ops.object.mode_set(mode='OBJECT')

        # set active
        context.view_layer.objects.active = ob

        ## keep same mode accross objects
        if mode_swap and prev_mode is not None:
            bpy.ops.object.mode_set(mode=prev_mode)
            
    else:
        ## keep same mode accross objects
        context.view_layer.objects.active = ob
        if context.mode != prev_mode is not None:
            bpy.ops.object.mode_set(mode=prev_mode)

    for o in [o for o in context.scene.objects if o.type == 'GPENCIL']:
        o.select_set(o == ob) # select only active (when not in object mode)


class CUSTOM_object_collection(PropertyGroup):

    # need an index for the native object list
    index : bpy.props.IntProperty(default=-1, update=update_object_change)
    
    # point_prop : PointerProperty(
    #     name="Object",
    #     type=bpy.types.Object)

class STORYTOOLS_UL_gp_objects_list(bpy.types.UIList):
    # Constants (flags)
    # Be careful not to shadow FILTER_ITEM (i.e. UIList().bitflag_filter_item)!
    # E.g. VGROUP_EMPTY = 1 << 0

    # Custom properties, saved with .blend file. E.g.
    # use_filter_empty: bpy.props.BoolProperty(
    #     name="Filter Empty", default=False, options=set(),
    #     description="Whether to filter empty vertex groups",
    # )

    # The draw_item function is called for each item of the collection that is visible in the list.
    #   data is the RNA object containing the collection,
    #   item is the current drawn item of the collection,
    #   icon is the "computed" icon for the item (as an integer, because some objects like materials or textures
    #   have custom icons ID, which are not available as enum items).
    #   active_data is the RNA object containing the active property for the collection (i.e. integer pointing to the
    #   active item of the collection).
    #   active_propname is the name of the active property (use 'getattr(active_data, active_propname)').
    #   index is index of the current item in the collection.
    #   flt_flag is the result of the filtering process for this item.
    #   Note: as index and flt_flag are optional arguments, you do not have to use/declare them here if you don't
    #         need them.

    # Called for each drawn item.
        ## active (draw) : GREASEPENCIL
        ## sculpt : SCULPTMODE_HLT
        ## active edit : EDITMODE_HLT
        ## others : OUTLINER_DATA_GREASEPENCIL

        # hide_ico = 'OUTLINER_OB_GREASEPENCIL' if item.active else 'HIDE_OFF'
        # source_ico = 'NETWORK_DRIVE' if item.is_project else 'USER' # BLANK1
        # row.label(text='', icon=source_ico)
        # row.prop(item, 'hide', text='', icon=hide_ico, invert_checkbox=True)

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index): # , flt_flag
        settings = context.scene.storytools_settings
        row = layout.row()
        if item == context.view_layer.objects.active:
            icon = 'GREASEPENCIL'
        else:
            icon = 'OUTLINER_OB_GREASEPENCIL'
        row.prop(item, 'name', icon=icon, text='',emboss=False)
        # row.prop(item, 'name', text='',emboss=False)

        if settings.show_gp_users:
            if item.data.users > 1:
                row.template_ID(item, "data")
            else:
                row.label(text='', icon='BLANK1')
        
        if settings.show_gp_parent:
            if item.parent:
                row.label(text='', icon='DECORATE_LINKED')
            else:
                row.label(text='', icon='BLANK1')
        
        # subrow.alignment = 'RIGHT'
        if settings.show_gp_in_front:
            subrow = row.row()
            subrow.prop(item, 'show_in_front', text='', icon='MOD_OPACITY', emboss=False)
            subrow.active = item.show_in_front

        ## Clickable toggle, set and sync hide from viewlayer, viewport and render 
        ## (Can lead to confusion with blender model... but heh !)
        if item.visible_get():
            row.operator('storytools.visibility_toggle', text='', icon='HIDE_OFF', emboss=False).name = item.name
        else:
            row.operator('storytools.visibility_toggle', text='', icon='HIDE_ON', emboss=False).name = item.name
    
    # Called once to draw filtering/reordering options.
    # def draw_filter(self, context, layout):
    #     pass

    # Called once to filter/reorder items.
    def filter_items(self, context, data, propname):
        # This function gets the collection property (as the usual tuple (data, propname)), and must return two lists:
        # * The first one is for filtering, it must contain 32bit integers were self.bitflag_filter_item marks the
        #   matching item as filtered (i.e. to be shown), and 31 other bits are free for custom needs. Here we use the
        #   first one to mark VGROUP_EMPTY.
        # * The second one is for reordering, it must return a list containing the new indices of the items (which
        #   gives us a mapping org_idx -> new_idx).
        # Please note that the default UI_UL_list defines helper functions for common tasks (see its doc for more info).
        # If you do not make filtering and/or ordering, return empty list(s) (this will be more efficient than
        # returning full lists doing nothing!).

        # Default return values.
        flt_flags = []
        flt_neworder = []

        #### Do filtering/reordering here...
        ## data : scene struct -> propname: 'objects' string 
        objs = getattr(data, propname)
        # objs: scene objects collection
    
        helper_funcs = bpy.types.UI_UL_list

        flt_flags = [self.bitflag_filter_item if o.type == 'GPENCIL' else 0 for o in objs]
        ## By name
        # flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, objs, "name", reverse=False)

        ## BONUS option: By distance to camera ? (need to be computed OTF... possible ?)

        return flt_flags, flt_neworder

class STORYTOOLS_OT_object_key_transform(Operator):
    bl_idname = "storytools.object_key_transform"
    bl_label = 'Key Object Transforms'
    bl_description = "Key active object Loc / Rot / Scale"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object

    def execute(self, context):
        ret = fn.key_object(context.object)
        if ret:
            self.report({'INFO'}, ret)
        return {"FINISHED"}

## Cannot append to GPencil 'Add' menu, being an operator_menu_enum "object.gpencil_add"
# def menu_add_storytools_gp(self, context):
#     """Storyboard GP object entries in the Add Object > Gpencil Menu"""
#     if context.mode == 'OBJECT':
#         self.layout.operator('storytools.create_object', text="Storyboard Drawing")

## to test -> bl_options = {'HIDE_HEADER'}

classes=(
STORYTOOLS_OT_create_object,
STORYTOOLS_OT_align_with_view,
STORYTOOLS_OT_object_pan,
STORYTOOLS_OT_object_rotate,
STORYTOOLS_OT_object_scale,
STORYTOOLS_OT_object_depth_move,
STORYTOOLS_OT_object_draw,
STORYTOOLS_OT_visibility_toggle,
STORYTOOLS_OT_object_key_transform,
CUSTOM_object_collection, ## Test all bugged
STORYTOOLS_UL_gp_objects_list,
)

def register(): 
    # bpy.types.Scene.index_constant = -1
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.gp_object_props = bpy.props.PointerProperty(type=CUSTOM_object_collection)
    
    # bpy.types.GPENCIL_MT_....append(menu_add_storytools_gp)

def unregister():
    # bpy.types.GPENCIL_MT_....remove(menu_add_storytools_gp)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # del bpy.types.Scene.index_constant
    del bpy.types.Scene.gp_object_props