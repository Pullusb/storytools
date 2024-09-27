import bpy

from mathutils import Vector, Matrix

from bpy.types import Operator
from bpy.props import BoolProperty

from .. import fn

def add_frame(available_layers, frame_number, reference_num=None, duplicate=False):
    """On available layers list, add frame at frame_number
    if reference frame number is passed, look for 
    """
    if reference_num is None:
        reference_num = frame_number
    
    for l in available_layers:
        if not duplicate:
            ## Simple add
            l.frames.new(frame_number=frame_number)
            l.frames.update()
            continue

        ## Case of duplication
        prev_frame = next((f for f in reversed(l.frames) if f.frame_number <= reference_num), None)
        
        if prev_frame is None:
            # New plain key
            l.frames.new(frame_number=frame_number)

        else:
            # Copy from previous key
            new_frame = l.frames.copy(prev_frame)
            new_frame.frame_number = frame_number
        
        l.frames.update()

def apply_offset_at_frame(available_layers, frame_number, offset):
    '''Apply offset value on frames in layer list where frames >= frame_number'''
    for layer in available_layers:
        for frame in reversed(layer.frames):
            if frame.frame_number >= frame_number:
                frame.frame_number = frame.frame_number + offset

class STORYTOOLS_OT_new_frame(Operator):
    bl_idname = "storytools.new_frame"
    bl_label = 'New frame'
    bl_description = "Add or duplicate previous frame" # TODO update description for Ctrl Behavior
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    duplicate : BoolProperty(name='Duplicate', default=False,
                             description='Create new keys with content of the previous one',
                             options={'SKIP_SAVE'})

    offset_next_frames : BoolProperty(name='Offset Next Frames', default=False,
                             description='Offset subsequent frames instead of squeezing new keys before next',
                             options={'SKIP_SAVE'})

    ## Add option to use on active layer only ?
    # active_only : BoolProperty(name='Active Only', default=False,
    #                          description='Use active greae pencil layer only',
    #                          options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties) -> str:
        if properties.duplicate:
            desc = 'Create new Grease pencil frames with content of previous frame (on unlocked and visible layers)'
        else:
            desc = 'Create new Grease pencil empty frames (on unlocked and visible layers)'
        
        ## Precisions
        desc += '\nJump forward if frame(s) already exists at current cursor\
                 \nCtrl + Click : Offset subsequent frames'
        return desc

    def invoke(self, context, event):
        self.offset_next_frames = event.ctrl
        return self.execute(context)

    def execute(self, context):
        ## List existing frame

        gap = fn.get_addon_prefs().gp_frame_offset

        # layer = context.object.data.layers.active
        
        ## Consider all unlocked layers
        available_layers = [l for l in context.object.data.layers if not l.hide and not l.lock]

        ## All frames (on all unlocked layers)
        frames_nums = sorted(set([f.frame_number for l in available_layers for f in l.frames]))

        current = context.scene.frame_current

        if current not in frames_nums:
            ## Easy case: Create in place (add an offset relative to previous frames ? optionally offset next ?)

            ## Apply gap offset from previous frame ?

            add_frame(available_layers, current, duplicate=self.duplicate)

            if self.offset_next_frames:
                ## Offset next frame to respect gap (if needed)
                next_frame_num = next((i for i in frames_nums if i > current), None)
                if next_frame_num is not None and (current_gap := next_frame_num - current) < gap:
                    ## Offset just the missing amount
                    missing_offset = gap - current_gap
                    
                    ## Keep current inbetween gap size (if there is frame before) else force fixed gap
                    prev_frame_num = next((i for i in reversed(frames_nums) if i < current), None)
                    if prev_frame_num is not None:
                        missing_offset = min((next_frame_num - prev_frame_num) - (next_frame_num - current), missing_offset)

                    apply_offset_at_frame(available_layers, next_frame_num, missing_offset)
                    
                    ## IDEA ? Should offset affect spa-sequencer subsequents in-out values in scene ?...
                    ## Not for now... user may not be aware + codependent with a specific addon. Prefs options ?

            return {'FINISHED'}

        ## -- Here cursor is over a frame

        ## Get number of next frame
        next_frame_num = next((i for i in frames_nums if i > current), None)

        if self.offset_next_frames:
            if next_frame_num is not None:
                current_gap = next_frame_num - current
                print('current_gap: ', current_gap)
                ## Always apply same offset
                # apply_offset_at_frame(available_layers, current + 1, gap)

                ## OR: Offset only if next frame is less than twice the gap
                if current_gap <= gap * 2:
                    offset = gap
                    
                    ## Optionnaly force exact gap between new and next
                    # offset = gap + max(current_gap, gap) 

                    apply_offset_at_frame(available_layers, current + 1, offset)

            new_num = current + gap
            add_frame(available_layers, new_num, reference_num=current, duplicate=self.duplicate)
            bpy.context.scene.frame_set(new_num)
            self.report({'INFO'}, f'Create frame(s), jumping {new_num - current} forward')
            return {'FINISHED'}


        if next_frame_num is None or next_frame_num - current > gap * 2:
            new_num = current + gap

        elif next_frame_num == current + 1:
            ## Stop and raise error ? (Not user friendly, better to create frame after anyway)
            # self.report({'ERROR'}, f'There are already frames at {current + 1}, offset the frame first')
            # return {'CANCELLED'}

            ## Create after boundary block of frame
            boundary_frame_num = next((n for n in range(current, frames_nums[-1]) if n + 1 not in frames_nums), None)

            if boundary_frame_num is None:
                new_num = frames_nums[-1] + gap
            else:
                ## Calculate best place after boundary frame
                next_frame_after_boundary = next((num for num in frames_nums if num > boundary_frame_num), None)
                if next_frame_after_boundary - boundary_frame_num > gap * 2:
                    new_num = boundary_frame_num + gap
                else:
                    new_num = boundary_frame_num + round((next_frame_after_boundary - boundary_frame_num) / 2)
                
            ## Jump after next key and create whenever possible
        else:        
            new_num = current + round((next_frame_num - current) / 2)


        if new_num in frames_nums:
            ## Should never happen if above is correct
            self.report({'ERROR'}, f'Error, a frame is already at {new_num}')
            return {'CANCELLED'}

        add_frame(available_layers, new_num, reference_num=current, duplicate=self.duplicate)

        ## Jump at frame
        
        ## ? add frame creation hint ? (not consistent with Blender UI... and too gamified)
        bpy.context.scene.frame_set(new_num)
        # bpy.context.scene.frame_current = new_num
        self.report({'INFO'}, f'Create frame(s), jumping {new_num - current} forward')

        return {'FINISHED'}


classes = (
    STORYTOOLS_OT_new_frame,
    )

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
