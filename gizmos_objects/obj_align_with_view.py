import bpy
from mathutils.geometry import intersect_line_plane

from bpy.types import Operator

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

            ## Objects are rotated by 90° on X except for Text objects.
            fn.assign_rotation_from_ref_matrix(ob, ref_matrix, rot_90=ob.type != 'FONT')

        return {"FINISHED"}

classes=(
STORYTOOLS_OT_align_with_view,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)