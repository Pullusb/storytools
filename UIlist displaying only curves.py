## AI generated, nimp but interesting

import bpy

def select_curve(self, context):
    # Obtain the selected curve object
    curve = context.scene.objects[self.curve_list_index]
    
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select the curve object
    curve.select_set(True)

class CurveList(bpy.types.UIList):
    
    @property
    def curve_list(self):
        # Get all objects in the scene
        objects = bpy.context.scene.objects
        
        # Return only the objects of type 'CURVE'
        return [obj for obj in objects if obj.type == 'CURVE']

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index, flt_flag):
        # Draw the name of the curve object in the list
        layout.label(text=item.name)

# class CurveList(bpy.types.UIList):
    # ...


class ObjectPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Storytools"
    
    def draw(self, context):
        layout = self.layout
        
        # Create a row containing the UI list
        row = layout.row()
        row.template_list("CURVE_UL_list", "", context.scene, "curve_objects", context.scene, "curve_objects_index")
        
        # Add a button to refresh the list
        row.operator("curve.refresh_list", text="Refresh")

classes = (
    # ...
    ObjectPanel,
    CurveList
)

def register():
    # ...
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add a shortcut to show the panel
    bpy.types.Scene.curve_objects = bpy.props.CollectionProperty(type=CurveObject)
    bpy.types.Scene.curve_objects_index = bpy.props.IntProperty()
    # bpy.types.VIEW3D_HT_header.append(menu_func)

def unregister():
    # ...
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.curve_objects
    del bpy.types.Scene.curve_objects_index
    # bpy.types.VIEW3D_HT_header.remove(menu_func)
