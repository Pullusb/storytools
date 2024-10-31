import bpy

from mathutils import Vector, Matrix
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty,
                        CollectionProperty)
from bpy.types import Operator

from .. import fn

def check_for_frames(ob, active_only=True):
    if ob.type != 'GPENCIL':
        return 'Not a Grease Pencil object'

    if not (layer := ob.data.layers.active):
        return "No active layer on grease pencil object"

    if not len(layer.frames):
        return f'No frames on active layer {layer.info}'

    return False


## Ops partially copied from GP Toolbox (Public, GPL, same author ^^)
class STORYTOOLS_OT_greasepencil_frame_jump(Operator):
    bl_idname = "storytools.greasepencil_frame_jump"
    bl_label = 'Jump to GPencil Keyframe'
    bl_description = "Jump to prev/next keyframe on active and selected layers of active grease pencil object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    # next : BoolProperty(
    #     name="Next GP frame", description="Go to next or previous grease pencil frame", 
    #     default=True, options={'HIDDEN', 'SKIP_SAVE'})
    direction : EnumProperty(
        name="Jump to GP frame", description="Go to next or previous grease pencil frame", 
        items=(
            ('NEXT', 'Next', 'Jump to next keyframe', 0),
            ('PREV', 'Previous', 'Jump to previous keyframe', 1),   
            ),
        default='NEXT', options={'HIDDEN', 'SKIP_SAVE'})

    target : EnumProperty(
        name="Target layer", description="Choose wich layer to consider for keyframe change", 
        default='FILTERED', options={'HIDDEN', 'SKIP_SAVE'}, # default should be ACTIVE if not in filtered mode
        items=(
            ('ACTIVE', 'Active and selected', 'Jump in keyframes of active and other selected layers ', 0),
            ('VISIBLE', 'Visibles layers', 'Jump in keyframes of visibles layers', 1),   
            ('ACCESSIBLE', 'Visible and unlocked layers', 'Jump in keyframe of all layers', 2),   
            ('ALL', 'All', 'All layer, even locked and hidden', 3),   
            ('FILTERED', 'Filtered', 'Use layer filter from storytools GP settings', 4),
            ))

    keyframe_type : EnumProperty(
        name="Keyframe Filter", description="Filter jump to specific keyframe type",
        default='FILTERED', options={'HIDDEN', 'SKIP_SAVE'},
        items=(
            ('ALL', 'All', 'All keyframe types', 'KEYFRAME', 0),
            ('CURRENT', 'Use Current Type', 'Use currently hovered type', 'ACTION_TWEAK', 1),
            ('FILTERED', 'Use UI Filter', 'Use storytools gp settings choice', 'FILTER', 2),
            ('KEYFRAME', 'Keyframe', '', 'KEYTYPE_KEYFRAME_VEC', 3),
            ('BREAKDOWN', 'Breakdown', '', 'KEYTYPE_BREAKDOWN_VEC', 4),
            ('MOVING_HOLD', 'Moving Hold', '', 'KEYTYPE_MOVING_HOLD_VEC', 5),
            ('EXTREME', 'Extreme', '', 'KEYTYPE_EXTREME_VEC', 6),
            ('JITTER', 'Jitter', '', 'KEYTYPE_JITTER_VEC', 7),
            ('GENERATED', 'Generated', '', 'KEYTYPE_GENERATED_VEC', 8),
            ))

    # sent_by_gizmo : BoolProperty(
    #     name="Sent ", description="Internal properties to check if sent using gizmo", 
    #     default=False, options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties) -> str:
        ## User mande description is passed
        if properties.direction == 'NEXT':
            desc = 'Jump to next grease pencil frame'
        else:
            desc = 'Jump to previous grease pencil frame'
        # desc += '\nCtrl + Click: Include object animation keys'
        desc += '\n+ Ctrl : Consider visible layers keys (instead of active only)'
        desc += '\n+ Shift : Consider unlocked and visible layers'
        desc += '\n+ Ctrl + Shift : all (even locked and hidden)'

        return desc

    def invoke(self, context, event):
        # self.prefs = fn.get_addon_prefs()
        ## If there is a clic event, consider that it was launched using gizmo button
        if self.target == 'FILTERED':
            self.target = context.scene.storytools_gp_settings.frame_target_layers
            
        if event.type == 'LEFTMOUSE':
            if event.shift:
                self.target = 'ACCESSIBLE'
            if event.ctrl:
                self.target = 'VISIBLE'
            if event.ctrl and event.shift:
                self.target = 'ALL'

            ## Consider object keys ? 
            # if event.ctrl:
            #     # Need to add object_keys bool prop
            #     self.object_keys = True

        return self.execute(context)

    def execute(self, context):
        if error_message := check_for_frames(context.object):
            self.report({'ERROR'}, error_message)
            return {'CANCELLED'}

        if self.target == 'ACTIVE':
            gpl = [l for l in context.object.data.layers if l.select and not l.hide]
            if not context.object.data.layers.active in gpl:
                gpl.append(context.object.data.layers.active)
        
        elif self.target == 'VISIBLE':
            gpl = [l for l in context.object.data.layers if not l.hide]
        
        elif self.target == 'ACCESSIBLE':
            gpl = [l for l in context.object.data.layers if not l.hide and not l.lock]

        elif self.target == 'ALL':
            gpl = [l for l in context.object.data.layers]

        ## Always put active layer first in list (if in list) for keyframe_type checking
        active_layer = context.object.data.layers.active
        if active_layer and active_layer in gpl:
            gpl.insert(0, gpl.pop(gpl.index(active_layer)))

        current = context.scene.frame_current
        p = n = None

        mins = []
        maxs = []

        ## Filter key_type according to preferences
        key_type = self.keyframe_type
        if key_type == 'FILTERED':
            key_type = context.scene.storytools_gp_settings.keyframe_type
        
        ## Filter key_type by hovered one
        if key_type == 'CURRENT':
            ## Find current hover type (fallback to all)
            key_type = next((f.keyframe_type for l in gpl for f in l.frames if f.frame_number == current), 'ALL')

        for l in gpl:
            for f in l.frames:
                # keyframe type filter
                if key_type != 'ALL' and key_type != f.keyframe_type:
                    continue

                if f.frame_number < current:
                    p = f.frame_number
                if f.frame_number > current:
                    n = f.frame_number
                    break

            mins.append(p)
            maxs.append(n)
            p = n = None

        mins = [i for i in mins if i is not None]
        maxs = [i for i in maxs if i is not None]

        if mins:
            p = max(mins)
        if maxs:
            n = min(maxs)

        ## Double the frame set to avoid refresh problem (had one in 2.91.2) ?
        if self.direction == 'NEXT' and n is not None:
            context.scene.frame_set(n)
            # context.scene.frame_current = n
        elif self.direction == 'PREV' and p is not None:
            context.scene.frame_set(p)
            # context.scene.frame_current = p
        else:
            direction = 'next' if self.direction == 'NEXT' else 'previous'
            plural = '' if self.target == 'ACTIVE' else 's'
            kt_hint = f' ({key_type.title()} type)' if key_type not in ('ALL',) else ''
                
            self.report({'INFO'}, f'No {direction} keyframe on {self.target.lower()} layer{plural}{kt_hint}')
            return {"CANCELLED"}

        return {"FINISHED"}


""" # WIP flip frame ops, modal copied from object pan
class STORYTOOLS_OT_flip_frames(Operator):
    bl_idname = "storytools.flip_frames"
    bl_label = 'Flip Frames'
    bl_description = "Flip in frames by dragging left-right"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    def invoke(self, context, event):
        self.ob = context.object
        self.layer = context.object.data.layers.active
        if not self.layer:
            self.report({'ERROR'}, "No active layer on Grease pencil object")
            return {'CANCELLED'}

        if not len(self.layer.frames):
            self.report({'ERROR'}, f'No frames on active layer {self.layer.info}')
            return {'CANCELLED'}

        self.shift_pressed = event.shift
        self.cumulated_translate = Vector((0, 0, 0))
        self.current_translate = Vector((0, 0, 0))

        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.init_vector = fn.region_to_location(self.init_mouse, self.init_world_loc)

        self.update_position(context, event)

        ## Placement helpers
        # self._guide_handle = bpy.types.SpaceView3D.draw_handler_add(draw.guide_callback, args, 'WINDOW', 'POST_VIEW')
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

        # new_loc = self.init_world_loc + move_vec


    def modal(self, context, event):    
        self.update_position(context, event)

        if event.type == 'LEFTMOUSE': # and event.value == 'RELEASE'
            # draw.stop_callback(self, context)
            ## just quit
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.ob.matrix_world = self.init_mat
            # draw.stop_callback(self, context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        return {"FINISHED"}
"""

classes = (STORYTOOLS_OT_greasepencil_frame_jump,)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)