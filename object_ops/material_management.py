import bpy
import re

from mathutils import Color
from math import isclose
from bpy.types import Operator, PropertyGroup
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
)

from .. import fn

def get_other_gp_objects(self, context):
    """Return a list of Grease Pencil object, without the active
    as tuple to use as reference object (for dynamic enum prop update)"""
    gp_in_scene = [o for o in context.scene.objects if o.type == 'GREASEPENCIL']

    ## Add all GP objects from data
    gp_in_other_scenes = [o for o in bpy.data.objects if o.type == 'GREASEPENCIL' and o not in gp_in_scene]
    all_gps = gp_in_scene + gp_in_other_scenes

    ## Remove active object from list
    all_gps = [o for o in all_gps if o != context.object]

    objects = [(obj.name, obj.name, f"Use {obj.name} as template") 
               for obj in all_gps]

    return objects

class STORYTOOLS_OT_load_materials_from_object(Operator):
    bl_idname = "storytools.load_materials_from_object"
    bl_label = 'Load Materials From Object'
    bl_description = "Load materials from pointed object to active object's materials stack"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    reference_object : EnumProperty(
        name="Reference Object",
        description="Reference object to get materials from",
        items=get_other_gp_objects,
        options={'SKIP_SAVE'}
    )

    def invoke(self, context, event):
        if len([o for o in bpy.data.objects if o.type == 'GREASEPENCIL']) < 2:
            self.report({'WARNING'}, 'No other Grease Pencil object found')
            return {"CANCELLED"}
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "reference_object", text='Source')

    def execute(self, context):
        if not self.reference_object:
            self.report({'WARNING'}, 'No object selected')
            return {"CANCELLED"}
        source_obj = bpy.data.objects.get(self.reference_object)
        if not source_obj:
            self.report({'ERROR'}, 'Object not found')
            return {"CANCELLED"}
        
        ct = 0
        for mat in source_obj.data.materials:
            if mat not in context.object.data.materials[:]:
                print("Adding", mat.name)
                context.object.data.materials.append(mat)
                ct += 1
        self.report({'INFO'}, f'{ct} materials added')
        return {"FINISHED"}

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

class STORYTOOLS_OT_create_material_from_color(bpy.types.Operator):
    bl_idname = "storytools.create_material_from_color"
    bl_label = "Create Material From Color"
    bl_description = "Add new material from current greaese pencil vertex color"
    bl_options = {"REGISTER", "INTERNAL"}

    mode : bpy.props.EnumProperty(
        items=(
            ('STROKE', "Stroke", "Create a new material from color, with Stroke enabled"),
            ('FILL', "Fill", "Create a new material from color, with Fill enabled"),
            ('BOTH', "Both", "Create a new material from color, with Stroke and Fill enabled"),
        ),
        default='STROKE',
        name="Mode",
        description="New material stroke and fill settings",
    )

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'


    def invoke(self, context, event):
        self.obj = context.object
        settings = context.tool_settings.gpencil_paint
        ## Get current color and use it to crewate material
        color = Color(settings.brush.color)
        
        ## Get the non-gamma corrected color
        color = color.from_srgb_to_scene_linear()

        ## Custom property to store an individual color
        # print('color: ', color)

        ## Add alpha 1.0 (need 4 components)
        self.color = (color[0], color[1], color[2], 1.0)

        ## TODO: check color against existing materials
        ## if exists propose to use it (would happen for absolute color, of if comming from a palette)
        ## list all materials with same value

        self.similar_materials = []
        for material in bpy.data.materials:
            if not material.is_grease_pencil:
                continue
            if self.mode == 'STROKE' and (not material.grease_pencil.show_stroke or material.grease_pencil.show_fill):
                continue
            if self.mode == 'FILL' and (material.grease_pencil.show_stroke or not material.grease_pencil.show_fill):
                continue
            if self.mode == 'BOTH' and (not material.grease_pencil.show_stroke or not material.grease_pencil.show_fill):
                continue

            if self.mode in ('STROKE', 'BOTH'):
                ref = material.grease_pencil.color
            else:
                ref = material.grease_pencil.fill_color

            if material.grease_pencil.color:
                # if not all(abs(ref[i] - self.color[i]) > 0.00000001 for i in range(3)):
                if all(isclose(ref[i], self.color[i], abs_tol=0.0001) for i in range(3)):
                    self.similar_materials.append(material)

        if not self.similar_materials:
            return self.execute(context)

        return context.window_manager.invoke_props_dialog(
            self,
            width=360, 
            title='Similar Materials Detected', 
            confirm_text='Create New Material',
            cancel_default=False)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text='Materials exists with same color:', icon='INFO')
        for material in self.similar_materials:
            row = col.row(align=True)
            row.label(text=material.name) # , icon_value=material.preview_ensure().icon_id
            text = 'Add To Stack'
            icon = 'ADD'
            if material in self.obj.data.materials[:]:
                text = 'Already In Stack'
                icon = 'CHECKMARK'
                row.enabled = False
            row.operator("storytools.load_material", text=text, icon=icon).name = material.name

    def execute(self, context):
        ## Find the name or use default
        mat_name = "Color_fill" if self.mode == 'FILL' else "Color"
        mat = bpy.data.materials.new(name=mat_name)
        bpy.data.materials.create_gpencil_data(mat)
        self.obj.data.materials.append(mat)

        mat.grease_pencil.show_stroke = self.mode in ('STROKE', 'BOTH')
        mat.grease_pencil.show_fill = self.mode in ('FILL', 'BOTH')
        mat.grease_pencil.color = self.color
        mat.grease_pencil.fill_color = self.color

        ## Make new slot active
        self.obj.active_material_index = len(self.obj.material_slots)

        self.report({'INFO'}, f'Created material {mat.name}')
        return {"FINISHED"}


classes=(
    STORYTOOLS_OT_load_material,
    STORYTOOLS_OT_add_existing_materials,
    STORYTOOLS_OT_load_materials_from_object,
    STORYTOOLS_OT_create_material_from_color,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
