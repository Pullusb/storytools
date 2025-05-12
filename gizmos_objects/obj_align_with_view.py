import bpy
from mathutils.geometry import intersect_line_plane

from bpy.types import Operator
from mathutils import Vector, Matrix
from math import pi

from .. import fn

class STORYTOOLS_OT_align_with_view(Operator):
    bl_idname = "storytools.align_with_view"
    bl_label = "Align With View"
    bl_description = "Align object with view\
        \n+ Ctrl : Also set object Z axis pointing up\
        \n+ Shift : Bring in front of camera"
    bl_options = {"REGISTER", "UNDO"} # "INTERNAL"

    @classmethod
    def poll(cls, context):
        return context.object

    align : bpy.props.BoolProperty(name='Align with view', default=True, options={'SKIP_SAVE'})
    keep_z_up : bpy.props.BoolProperty(name='Keep Z Up', default=False, options={'SKIP_SAVE'})
    bring_in_view : bpy.props.BoolProperty(name='Bring In View', default=False, options={'SKIP_SAVE'})
    margin_ratio : bpy.props.FloatProperty(name='Margin', default=0.4, min=0.0, max=0.95, step=0.1, options={'SKIP_SAVE'})

    distance_to_view : bpy.props.FloatProperty(
        name='Distance', min=0.1, default=8.0)


    def invoke(self, context, event):
        self.keep_z_up = event.ctrl
        self.bring_in_view = event.shift
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'align')
        
        row = layout.row()
        row.prop(self, 'keep_z_up')
        row.enabled = self.align

        layout.prop(self, 'bring_in_view')

        row = layout.row()
        row.prop(self, 'distance_to_view')
        row.prop(self, 'margin_ratio')
        row.enabled = self.bring_in_view

    def execute(self, context):
        r3d = context.space_data.region_3d            
        
        pool = [o for o in context.selected_objects if o.type != 'CAMERA']
        if not pool:
            self.report({'WARNING'}, 'No compatible object for alignment in selection')
            return {'CANCELLED'}

        ## Sort by name ?
        pool_size = len(pool)

        if self.bring_in_view:
            z_vec = Vector((0.0, 0.0, -self.distance_to_view))
            aim = r3d.view_rotation @ z_vec
            view_origin = r3d.view_matrix.inverted().to_translation()
            new_loc = view_origin + aim

            ## when in view, use region to location
            if pool_size > 1:
                if context.space_data.region_3d.view_perspective == 'CAMERA':
                    scn = context.scene
                    cam = scn.camera
                    ## Find final camera frame vectors at given distance (local space)
                    if cam.data.type == 'ORTHO':
                        cam_frame = [Vector((c.x, c.y, -self.distance_to_view)) for c in cam.data.view_frame(scene=scn)]
                    else:
                        cam_frame = [intersect_line_plane(Vector(), c, z_vec, z_vec) for c in cam.data.view_frame(scene=scn)]

                    ## Find mid-height border
                    r = (cam_frame[0] + cam_frame[1]) / 2
                    l = (cam_frame[2] + cam_frame[3]) / 2
                    
                    w = r.x - l.x # same as (r - l).length
                    context.scene.cursor.location = r
                    margins = w * self.margin_ratio
                    chunk_width = (w - margins) / (pool_size - 1)

                    ## Calc poisition per object world space
                    # context.scene.cursor.location = Vector((l.x + chunk_width * pool_size - margins, l.y, l.z))# Dbg
                    locations = [cam.matrix_world @ Vector((l.x + (margins / 2) + i * chunk_width, l.y, l.z) )
                                 for i in range(pool_size)]

                else:
                    ## Free View
                    toolbar_width = next((r.width for r in context.area.regions if r.type == 'TOOLS'), 0)
                    sidebar_width = next((r.width for r in context.area.regions if r.type == 'UI'), 0)
                    locations = []
                    h = context.region.height / 2
                    # Remove some margin
                    w = context.region.width - toolbar_width - sidebar_width
                    margins = w * self.margin_ratio
                    chunk_width = (w - margins) / (pool_size - 1)
                    # context.scene.cursor.location = fn.region_to_location(Vector((context.region.width, h)), new_loc) # Dbg
                    for i in range(pool_size):
                        width_loc = toolbar_width + (margins / 2) + i * chunk_width
                        region_coord = Vector((width_loc, h))
                        locations.append(fn.region_to_location(region_coord, new_loc))

            else:
                locations = [new_loc]
                ## Compute origin position and offset
                # intersect_line_plane(view_origin, new_loc, new_loc, aim)
                # fn.get_cam_frame_world(scene)

        for i, ob in enumerate(pool):
            if self.bring_in_view:
                ob.matrix_world.translation = locations[i]

            if not self.align:
                continue

            if self.keep_z_up:
                ## Align to view but keep world Up
                z_vec = Vector((0.0, 0.0, 1.0))
                aim = r3d.view_rotation @ z_vec
                # Track Up
                ref_matrix = aim.to_track_quat('Z','Y').to_matrix().to_4x4()

            else:
                ## Aligned to view Matrix
                ref_matrix = r3d.view_matrix.inverted()

            ## Objects are rotated by 90° on X except for Text objects or empty image.
            rotate_90 = ob.type not in ('FONT', 'SPEAKER', 'LIGHT') and not (ob.type == 'EMPTY' and ob.empty_display_type == 'IMAGE')
            fn.assign_rotation_from_ref_matrix(ob, ref_matrix, rot_90=rotate_90)

        return {"FINISHED"}


def vector_to_matrix(vector, up=None) -> Matrix:
    '''Create a matrix from Vector
    ex: Can be used to apply rotation on 3d view'''
    
    # Normalize the input vector
    direction = vector.normalized()
    
    if up is None:
        # Define the up vector (typically the world's Z axis)
        up = Vector((0.0, 0.0, 1.0))

        # If the direction is close to the up vector, use a different up vector
        if abs(direction.dot(up)) > 0.999:
            up = Vector((0.0, 1.0, 0.0))
    
    # Compute the right vector
    right = direction.cross(up).normalized()
    
    # Recompute the up vector to ensure orthogonality
    up = right.cross(direction).normalized()
    
    # Create the matrix
    mat = Matrix((right, up, -direction)).transposed()

    return mat
    
def align_view_to_vector(vector, up=None, context=None) -> None:
    '''align current 3d view to vector'''

    context = context or bpy.context
    mat = vector_to_matrix(vector, up)

    r3d = context.space_data.region_3d
    if r3d.view_perspective == 'CAMERA':
        cam = context.space_data.camera
        ## Rotate camera from view pivot point
        ## Could be interesting to use view pivot point as well
        # pivot = context.space_data.region_3d.view_location
        # cam.matrix_world

        
        ## Camera rotate in place (pivot on itself)
        if cam.rotation_mode == 'QUATERNION':
            cam.rotation_quaternion = mat.to_quaternion()
        else:
            cam.rotation_euler = mat.to_euler(cam.rotation_mode)
    else:
        ## Rotate view (rotate on pivot point)
        context.space_data.region_3d.view_rotation = mat.to_quaternion()

class STORYTOOLS_OT_align_view_to_object(Operator):
    bl_idname = "storytools.align_view_to_object"
    bl_label = "Align view to object"
    bl_description = "Align 3d view to active objects orientation"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object

    opposite : bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self.opposite = event.ctrl
        return self.execute(context)

    def execute(self, context):
        r3d = context.space_data.region_3d
        init_persp = r3d.view_perspective
        if context.object.type != 'GREASEPENCIL':
            bpy.ops.view3d.view_axis(align_active=True, type='FRONT', relative=False)

        else:
            mat = context.object.matrix_world
            settings = context.scene.tool_settings
            orient = settings.gpencil_sculpt.lock_axis # 'VIEW', 'AXIS_Y', 'AXIS_X', 'AXIS_Z', 'CURSOR'
            ## if alignement is front / side / top, use native operators

            if orient == 'VIEW':
                ## A. Just Align with object front ?
                # bpy.ops.view3d.view_axis(align_active=True, type='FRONT', relative=False)
                
                ## B. Guess plane from active
                # (if plane normal is aligned with one of the main axis)
                ob = context.object
                if not ob.data.layers.active:
                    bpy.ops.view3d.view_axis(align_active=True, type='FRONT', relative=False)
                else:
                    _co, no = fn.get_frame_coord_and_normal(ob, ob.data.layers.active.current_frame())
                    
                    ## Align with 
                    align_view_to_vector(-no) # inverted ? (probably not always right)

                ## Compare with view vector to align with closest side ?
                # view_vec = context.space_data.region_3d.view_rotation @ Vector((0,0,1))

            elif orient == 'CURSOR':
                ## temp solution

                ## orient view with plane
                plane_no = Vector((0,0,-1))
                plane_no.rotate(context.scene.cursor.matrix)

                up = None
                ## Pass up vec if we want to orient with cursor as well (often not needed)
                ## note: in this case we could directly use cursor matrix

                # up = Vector((0,1,0))
                # up.rotate(context.scene.cursor.matrix)
                align_view_to_vector(plane_no, up)

            elif orient == 'AXIS_Y': # front (X-Z)
                bpy.ops.view3d.view_axis(align_active=True, type='FRONT', relative=False)
                # plane_no = Vector((0,1,0))
                # plane_no.rotate(mat)

            elif orient == 'AXIS_X': # side (Y-Z)
                bpy.ops.view3d.view_axis(align_active=True, type='RIGHT', relative=False)
                # plane_no = Vector((1,0,0))
                # plane_no.rotate(mat)

            elif orient == 'AXIS_Z': # top (X-Y)
                bpy.ops.view3d.view_axis(align_active=True, type='TOP', relative=False)
                # plane_no = Vector((0,0,1))
                # plane_no.rotate(mat)

            # co, no = fn.get_gp_draw_plane(context)
            ## else determine the plane and move view matrix


        if self.opposite:
            ## Equivalent of numpad 9 ? (but not really opposing to view)
            # bpy.ops.view3d.view_orbit(angle=3.14159, type='ORBITRIGHT')

            r3d.update() # need to update, else previous changes are skipped
            
            view_up_axis = r3d.view_rotation @ Vector((0,1,0))
                        
            ## Create rotation matrix
            loc = r3d.view_location.copy()
            r3d.view_location = (0,0,0) # Even without, seem to be reseted when applying matrix
            
            ## Create rotation matrix
            rot_matrix = Matrix.Rotation(pi, 3, view_up_axis)
            ## Convert to 4x4
            rot_matrix = rot_matrix.to_4x4()
            ## Or integrate the matrix in a 4x4
            # rot_matrix = Matrix.LocRotScale(
            #     None, # context.space_data.region_3d.view_location, # loc
            #     rot_matrix, # rot # Matrix.Rotation(pi, 4, view_up_axis).to_quaternion()
            #     None, # default scale
            #     )

            ## Apply the rotation
            r3d.view_matrix = r3d.view_matrix @ rot_matrix
            
            ## Restore location
            r3d.view_location = loc

        ## Restore initial perspective mode
        if init_persp != 'CAMERA' and init_persp != r3d.view_perspective:
            r3d.view_perspective = init_persp

        return {"FINISHED"}

class STORYTOOLS_OT_opposite_view(Operator):
    bl_idname = "storytools.opposite_view"
    bl_label = "Opposite View"
    bl_description = "Turn to opposite view, Rotate by 180 degrees around orbit focal point"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        r3d = context.space_data.region_3d
        view_up_axis = r3d.view_rotation @ Vector((0,1,0))
        rot_mat = Matrix.Rotation(pi, 3, view_up_axis)
        loc = r3d.view_location.copy()
        r3d.view_location = (0,0,0) # not needed ?
        r3d.view_matrix = r3d.view_matrix @ rot_mat.to_4x4()
        r3d.view_location = loc
        return {'FINISHED'}

classes=(
STORYTOOLS_OT_align_with_view,
STORYTOOLS_OT_align_view_to_object,
STORYTOOLS_OT_opposite_view,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)