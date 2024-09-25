import bpy

from mathutils import Vector, Matrix

from bpy.types import Operator
from bpy.props import BoolProperty

# from .. import fn

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
            continue

        ## Case of duplication
        prev_frame = next((f for f in reversed(l.frames) if f.frame_number < reference_num), None)
        
        if prev_frame is None:
            # New plain key
            l.frames.new(frame_number=frame_number)

        else:
            # Copy from previous key
            new_frame = l.frames.copy(prev_frame)
            new_frame.frame_number = frame_number


class STORYTOOLS_OT_new_frame(Operator):
    bl_idname = "storytools.new_frame"
    bl_label = 'New frame'
    bl_description = "Add or duplicate previous frame"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    duplicate : BoolProperty(name='Duplicate', default=False,
                             description='Create new keys with content of the previous one',
                             options={'SKIP_SAVE'})

    def execute(self, context):
        ## List existing frame

        gap = 12
        # layer = context.object.data.layers.active
        
        ## Consider all unlocked layers
        available_layers = [l for l in context.object.data.layers if not l.hide and not l.lock]

        ## All frames (on all unlocked layers)
        frames_nums = sorted(set([f.frame_number for l in available_layers for f in l.frames]))

        current = context.scene.frame_current

        if current not in frames_nums:
            ## Easy case: Create in place (add an offset relative to previous frames ? optionally offset next ?)
            add_frame(available_layers, current, duplicate=self.duplicate)

        else:
            ## We're on a frame
            ## Check where to create a new one

            ## get number of next frame
            next_frame_num = next((num for num in frames_nums if num > current), None)

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
                self.report({'ERROR'}, f'Error, a frame is already at {new_num}')
                return {'CANCELLED'}

            add_frame(available_layers, new_num, reference_num=current, duplicate=self.duplicate)
            
            ## Jump at frame

            ## ? add frame creation hint ? (not consistent with Blender UI... and too gamified)
            bpy.context.scene.frame_set(new_num)
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
