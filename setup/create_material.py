import bpy

class STORYTOOLS_OT_create_material_from_color(bpy.types.Operator):
    bl_idname = "storytools.create_material_from_color"
    bl_label = "Load basic palette"
    bl_description = "Use current greae pencil vertex color"
    bl_options = {"REGISTER", "INTERNAL"}

    mode : bpy.props.EnumProperty(
        items=(
            ('STROKE', "Stroke", "Create a new material from color, with Stroke enabled"),
            ('FILL', "Fill", "Create a new material from color, with Fill enabled"),
            ('BOTH', "Both", "Create a new material from color, with Stroke and Fill enabled"),
        ),
        default='STROKE',
        name="Mode",
        description="Material settings",
    )
    
    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    def execute(self, context):
        settings = context.tool_settings.gpencil_paint
        ## Get current color and use it to crewate material
        color = settings.brush.color
        # print('color: ', color)
        
        ## Get the non-gamma corrected color
        color = color.from_srgb_to_scene_linear()

        ## WIP : If not printed in console, get black color sometimes
        ## need a custom property to store an individual color
        # print('color: ', color)

        ## Add alpha 1.0 (need 4 components)
        color = (color[0], color[1], color[2], 1.0)

        ## Find the name or use default
        mat = bpy.data.materials.new(name="Color")
        bpy.data.materials.create_gpencil_data(mat)
        context.object.data.materials.append(mat)

        mat.grease_pencil.show_stroke = self.mode in ('STROKE', 'BOTH')
        mat.grease_pencil.show_fill = self.mode in ('FILL', 'BOTH')
        mat.grease_pencil.color = color
        mat.grease_pencil.fill_color = color

        self.report({'INFO'}, f'Created material {mat.name}')
        return {"FINISHED"}
    

classes=(
STORYTOOLS_OT_create_material_from_color,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)