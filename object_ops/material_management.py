import bpy
import re

from bpy.types import Operator, PropertyGroup
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
    FloatVectorProperty,
    PointerProperty,
    EnumProperty,
)


# class STORYTOOLS_OT_load_materials_from_object(Operator):
#     bl_idname = "storytools.load_materials_from_object"
#     bl_label = 'Load Materials From Object'
#     bl_description = "Load materials from pointed object to active object's materials stack"
#     bl_options = {'REGISTER', 'UNDO'}

#     @classmethod
#     def poll(cls, context):
#         return True
#     # def invoke(self, context, event):
#     #     return self.execute(context)

#     name : StringProperty()

#     def execute(self, context):
#         if not self.name:
#             return {"CANCELLED"}

#         ob = context.scene.objects.get(self.name)
#         if not ob:
#             return {"CANCELLED"}
        
#         # hide = not ob.hide_viewport
#         hide = ob.visible_get() # Already inversed
        
#         ob.hide_viewport = hide
#         ob.hide_render = hide
#         # Set viewlayer visibility
#         ob.hide_set(hide)
#         return {"FINISHED"}

class STORYTOOLS_OT_load_material(Operator):
    bl_idname = "storytools.load_material"
    bl_label = 'Load Material'
    bl_description = "Load material by name"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'
    
    name : StringProperty()

    def execute(self, context):
        if not self.name:
            return {"CANCELLED"}

        obj = context.object
        mat = bpy.data.materials.get(self.name)
        if not mat:
            self.report({'WARNING'}, f'"{mat.name}" not found')
            return {"CANCELLED"}
        
        if mat in obj.data.materials[:]:
            self.report({'WARNING'}, f'"{mat.name}" is already in stack')
            return {"CANCELLED"}
        
        ## Append material to object
        obj.data.materials.append(mat)
        self.report({'INFO'}, f'Added material "{mat.name}"')
        return {"FINISHED"}

class STORYTOOLS_OT_add_existing_materials(Operator):
    bl_idname = "storytools.add_existing_materials"
    bl_label = 'Add Existing Material'
    bl_description = "Add an existing material to active object stack"
    bl_options = {'REGISTER', 'UNDO'}

    all_materials : BoolProperty(
        name='Show All Materials', default=True,
        description='Show all materials in blend')

    hide_duplicates : BoolProperty(
        name='Hide Duplicates (.001. ...)', default=False,
        description='Hide material duplication\
            \nMaterials using names like "Material.001"')
    
    hide_already_loaded : BoolProperty(
        name='Hide Loaded Material', default=False,
        description='Hide materials already present in stack')

    # @classmethod
    # def poll(cls, context):
    #     return True

    def invoke(self, context, event):
        self.data_materials = [mat for mat in bpy.data.materials if mat.is_grease_pencil]

        self.scene_materials = [mat for obj in context.scene.objects if obj.type == 'GREASEPENCIL' for mat in obj.data.materials if mat.is_grease_pencil]
        self.scene_materials = list(set(self.scene_materials))

        self.re_dup = re.compile(r'\.\d{3}$')

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text='Filters')
        col = box.column()
        col.prop(self, "all_materials")
        col.prop(self, "hide_duplicates")
        col.prop(self, "hide_already_loaded")
        
        ## TODO: Split list between - Scene and Data
        

        ## Material
        col = layout.column()
        col.label(text=f'{len(context.object.data.materials)} materials on object')
        materials = self.data_materials if self.all_materials else self.scene_materials
        for mat in materials:
            if self.hide_already_loaded and mat in context.object.data.materials[:]:
                continue

            if self.hide_duplicates and self.re_dup.search(mat.name):
                continue

            row = col.row(align=True)
            row.operator("storytools.load_material", text=mat.name, icon_value=mat.preview_ensure().icon_id, emboss=False).name = mat.name

            in_stack_icon = 'CHECKMARK' if mat in context.object.data.materials[:] else 'BLANK1'
            row.label(text='', icon=in_stack_icon)


    def execute(self, context):
        return {"FINISHED"}


classes=(
    STORYTOOLS_OT_load_material,
    # STORYTOOLS_OT_load_materials_from_object,
    STORYTOOLS_OT_add_existing_materials,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
