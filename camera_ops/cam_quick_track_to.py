import bpy
from bpy.types import Operator
from mathutils import Vector, geometry
from .. import fn

class STORYTOOLS_OT_add_track_to_constraint(Operator):
    bl_idname = "storytools.add_track_to_constraint"
    bl_label = "Add TrackTo constraint"
    bl_description = "Create 'Track-to' constraint on camera, also known as 'Look at'\
        \nIf an empty is selected, used as target, else create a new empty"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    remove : bpy.props.BoolProperty(name='Remove', default=False, options={'SKIP_SAVE'},
                                    description='Remove all track to constraint on active camera')

    def remove_track_to_constraints(self, cam):
        rm_ct = 0
        existing_constraints = [c for c in cam.constraints if c.type in ('TRACK_TO', 'DAMPED_TRACK', 'LOCKED_TRACK')]
        for c in reversed(existing_constraints):
            cam.constraints.remove(c)
            rm_ct += 1
        return rm_ct

    def execute(self, context):
        scn = context.scene
        cam = scn.camera
        if self.remove:
            ct = self.remove_track_to_constraints(cam)
            if ct:
                self.report({'INFO'}, f'removed {ct} track constraints on camera')
            else:
                self.report({'WARNING'}, f'No track constraints to remove on camera')
            return {'FINISHED'}

        empty_objects_selection = [o for o in context.selected_objects if o.type == 'EMPTY']
        if empty_objects_selection:
            mire = empty_objects_selection[0]
        else:

            if context.object and context.object.type != 'CAMERA':
                ## Create on selected object distance (still centered)
                plane_no = Vector((0,0,-1))
                plane_no.rotate(cam.rotation_quaternion)
                pos = geometry.intersect_line_plane(cam.matrix_world.translation,
                                                   cam.matrix_world @ Vector((0,0,-10000)),
                                                   context.object.matrix_world.to_translation(),
                                                   plane_no,
                                                   False)
                if not pos:
                    # Create at object if intersect plane fail
                    pos = context.object.matrix_world.to_translation()
            else:
                # Create an empty in front of camera (at selected GP distance)
                pos = cam.matrix_world @ Vector((0,0,-5))

            mire = fn.empty_at(pos, name=f'{cam.name}_target', type='SPHERE', size=0.25, link=False) # PLAIN_AXES
            
            ## link in same collection as camera or create a dedicated look_at collection ?
            cam.users_collection[0].objects.link(mire)

        ###  Use the empty to create a track to constraint

        ## Remove existing track constraints
        ct = self.remove_track_to_constraints(cam)
        if ct:
            print(f'removed {ct} constaints before creating new')
        
        ## Add Damped track to (allow Roll)
        constraint = cam.constraints.new('DAMPED_TRACK')
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.target = mire
        return {"FINISHED"}


classes = (STORYTOOLS_OT_add_track_to_constraint,)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)