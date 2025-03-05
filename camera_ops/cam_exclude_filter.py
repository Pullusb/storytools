# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import (
    PropertyGroup,
    UIList,
    Operator,
    Panel
)
from bpy.props import (
    StringProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
    IntProperty
)
from bpy.app.handlers import persistent

# Property Groups for storing exclusion lists
class STORYTOOLS_PG_excluded_object(PropertyGroup):
    """Object exclusion entry for camera"""
    object: PointerProperty(type=bpy.types.Object)
    
class STORYTOOLS_PG_excluded_collection(PropertyGroup):
    """Collection exclusion entry for camera"""
    collection: PointerProperty(type=bpy.types.Collection)

class STORYTOOLS_PG_collection_reference(PropertyGroup):
    ## This collection property is only used to store current scene collections for prop_search
    name: StringProperty()
    collection: PointerProperty(type=bpy.types.Collection)

class STORYTOOLS_PG_camera_exclude_props(PropertyGroup):
    """Camera exclusion properties"""
    enabled: BoolProperty(
        name="Enable Exclusions",
        description="Enable object and collection exclusions for this camera",
        default=True,
        update=lambda self, context: update_exclusion_visibility(context)
    )
    excluded_objects: CollectionProperty(type=STORYTOOLS_PG_excluded_object)
    excluded_collections: CollectionProperty(type=STORYTOOLS_PG_excluded_collection)
    active_object_index: IntProperty(default=0)
    active_collection_index: IntProperty(default=0)

# Operators
class STORYTOOLS_OT_add_excluded_object_from_selection(Operator):
    bl_idname = "storytools.add_excluded_object_from_selection"
    bl_label = "Add Selected Object to Exclusion List"
    bl_description = "Add selected object to the camera exclusion list"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera and context.selected_objects
    
    def execute(self, context):
        cam = context.scene.camera
        if not hasattr(cam, 'exclude_props') or not cam.exclude_props:
            return {'CANCELLED'}
        
        for obj in context.selected_objects:
            # Skip if object is a camera
            if obj.type == 'CAMERA':
                continue
                
            # Check if object is already in list
            if not any(item.object == obj for item in cam.exclude_props.excluded_objects):
                item = cam.exclude_props.excluded_objects.add()
                item.object = obj
                
        update_exclusion_visibility(context)
        return {'FINISHED'}

class STORYTOOLS_OT_search_add_excluded_object(Operator):
    bl_idname = "storytools.search_add_excluded_object"
    bl_label = "Search Object to Add In Exclusion List"
    bl_description = "Search Object by name to add in camera exclusion list"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    object_name: StringProperty(name="Object Name")
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera and hasattr(context.scene.camera, 'exclude_props')
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, "object_name", bpy.context.scene, "objects")
    
    def execute(self, context):
        cam = context.scene.camera
        obj = bpy.data.objects.get(self.object_name)
        
        if not obj or not hasattr(cam, 'exclude_props') or not cam.exclude_props:
            return {'CANCELLED'}
        
        # Check if object is already in list
        if not any(item.object == obj for item in cam.exclude_props.excluded_objects):
            item = cam.exclude_props.excluded_objects.add()
            item.object = obj
            
        update_exclusion_visibility(context)
        return {'FINISHED'}

class STORYTOOLS_OT_remove_excluded_object(Operator):
    bl_idname = "storytools.remove_excluded_object"
    bl_label = "Remove Object from Exclusion List"
    bl_description = "Remove selected object from camera exclusion list"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    index: IntProperty()
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera and hasattr(context.scene.camera, 'exclude_props') and len(context.scene.camera.exclude_props.excluded_objects)
    
    def execute(self, context):
        cam = context.scene.camera
        if self.index >= 0 and self.index < len(cam.exclude_props.excluded_objects):
            obj = cam.exclude_props.excluded_objects[self.index].object
            if obj:
                obj.hide_viewport = obj.hide_render = False
            cam.exclude_props.excluded_objects.remove(self.index)
            cam.exclude_props.active_object_index = self.index - 1
        else:
            cam.exclude_props.active_object_index = len(cam.exclude_props.excluded_objects) - 1
        update_exclusion_visibility(context)
        return {'FINISHED'}

class STORYTOOLS_OT_search_add_excluded_collection(Operator):
    bl_idname = "storytools.search_add_excluded_collection"
    bl_label = "Search Collection To Add To Exclusion List"
    bl_description = "Search collection by name and add it to camera exclusion list"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    collection_name: StringProperty(name="Collection Name")
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera and hasattr(context.scene.camera, 'exclude_props')
    
    def invoke(self, context, event):
        wm = context.window_manager
        ## Fill a temporary collection list to search in
        # scene_collections = getattr(wm, "scene_collections", None)
        # if scene_collections is None:
        #     bpy.types.WindowManager.scene_collections = CollectionProperty(type=STORYTOOLS_PG_collection_reference)
        #     scene_collections = getattr(wm, "scene_collections", None)

        # # Fill with all current scene collections
        # wm.scene_collections.clear()
        # for col in context.scene.collection.children_recursive:
        #     item = wm.scene_collections.add()
        #     item.name = col.name
        #     item.collection = col
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        ## Try to fetch in current scene only (with temporary collection to search in...)
        # layout.prop_search(self, "collection_name", context.window_manager, "scene_collections") # temp collection
        ## In all data
        layout.prop_search(self, "collection_name", bpy.data, "collections") # all data
        
        # layout.prop_search(self, "collection_name", context.scene.collection, "children_recursive") # <- rna_uiItemPointerR: property not found: Collection.children_recursive
    
    def execute(self, context):
        cam = context.scene.camera
        # print(self.collection_name)
        col = bpy.data.collections.get(self.collection_name)

        if not col or not hasattr(cam, 'exclude_props') or not cam.exclude_props:
            return {'CANCELLED'}
        
        # Check if collection is already in list
        if not any(item.collection == col for item in cam.exclude_props.excluded_collections):
            item = cam.exclude_props.excluded_collections.add()
            item.collection = col
            
        update_exclusion_visibility(context)
        return {'FINISHED'}

class STORYTOOLS_OT_remove_excluded_collection(Operator):
    bl_idname = "storytools.remove_excluded_collection"
    bl_label = "Remove Collection from Exclusion List"
    bl_description = "Remove collection from camera exclusion list"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: IntProperty()
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera and hasattr(context.scene.camera, 'exclude_props') and len(context.scene.camera.exclude_props.excluded_collections)
    
    def execute(self, context):
        cam = context.scene.camera
        if self.index >= 0 and self.index < len(cam.exclude_props.excluded_collections):
            col = cam.exclude_props.excluded_collections[self.index].collection
            if col:
                col.hide_viewport = col.hide_render = False
            cam.exclude_props.excluded_collections.remove(self.index)
            cam.exclude_props.active_collection_index = self.index - 1
        else:
            cam.exclude_props.active_collection_index = len(cam.exclude_props.excluded_collections) - 1

        update_exclusion_visibility(context)
        return {'FINISHED'}

# UI Lists
class STORYTOOLS_UL_excluded_objects(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item.object:
            layout.prop(item.object, "name", text="", emboss=False, icon_value=icon)
        else:
            layout.label(text="Invalid Object")

class STORYTOOLS_UL_excluded_collections(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item.collection:
            layout.prop(item.collection, "name", text="", emboss=False, icon='COLLECTION_NEW')
        else:
            layout.label(text="Invalid Collection")

def is_valid(obj):
    """Check if a Blender object reference is valid."""
    try:
        # Attempting to access any attribute of an invalid object will raise an ReferenceError
        obj.name
        return True
    except ReferenceError:
        return False    

# Function to update object visibility based on active camera's exclusion list
def update_exclusion_visibility(context):
    """Update visibility of objects based on active camera's exclusion list"""
    # print('--> in update_exclusion_visibility')
    
    # First show all objects from all cameras
    # show_all_excluded_objects(context)

    ## Maybe less dangerous to use names instead of objects...
    scn = context.scene
    current_cam = scn.camera

    if not current_cam or not hasattr(current_cam, 'exclude_props') or not current_cam.exclude_props:
        return

    ## return if disabled. Doing prevent restoring visibility of object in other cameras, but maybe it's preferable...
    # if not current_cam.exclude_props.enabled:
    #     return

    ## list all objects targeted by exclusion in current scene
    scene_cameras = [o for o in scn.objects if o.type == 'CAMERA' and o.exclude_props.enabled]

    ## Cleanup invalid objects in excluded_objects and excluded_collections
    for cam in scene_cameras:
        ## Cleanup objects
        for i in range(len(cam.exclude_props.excluded_objects) -1, -1, -1):
            item = cam.exclude_props.excluded_objects[i]
            if not is_valid(item.object) or item.object.name not in scn.objects: # not item.object.users
                print(f'Camera "{cam.name}" visibility exclusion cleanup: remove item "{item}"')
                cam.exclude_props.excluded_objects.remove(i)
                cam.exclude_props.active_object_index = min(cam.exclude_props.active_object_index, len(cam.exclude_props.excluded_objects) - 1)
        
        ## Cleanup collections
        for i in range(len(cam.exclude_props.excluded_collections) -1, -1, -1):
            item = cam.exclude_props.excluded_collections[i]
            if not is_valid(item.collection) or not item.collection.users:
                print(f'Camera "{cam.name}" visibility exclusion cleanup: remove item "{item}"')
                cam.exclude_props.excluded_collections.remove(i)
                cam.exclude_props.active_collection_index = min(cam.exclude_props.active_collection_index, len(cam.exclude_props.excluded_collections) - 1)

    all_excluded_objects = [i.object for cam in scene_cameras for i in cam.exclude_props.excluded_objects]
    all_excluded_collections = [i.collection for cam in scene_cameras for i in cam.exclude_props.excluded_collections]

    ## early return : doing that will prevent to restore visibility from object in other cameras !
    # if not all_excluded_objects and not all_excluded_collections:
    #     return

    ## Then hide objects for current camera if enabled
    ## ? do not affect render state ?

    current_obj_exclude = [i.object for i in current_cam.exclude_props.excluded_objects]
    for obj in all_excluded_objects:
        obj.hide_viewport = obj.hide_render = obj in current_obj_exclude
    
    current_col_exclude = [i.collection for i in current_cam.exclude_props.excluded_collections]
    for col in all_excluded_collections: 
        col.hide_viewport = col.hide_render = col in current_col_exclude


# def show_all_excluded_objects(context):
#     """Show all objects that might be in any camera's exclusion list"""
#     # Show objects from all cameras' exclusion lists
#     for cam in [obj for obj in bpy.data.objects if obj.type == 'CAMERA']:
#         if not hasattr(cam, 'exclude_props') or not cam.exclude_props:
#             continue
            
#         for item in cam.exclude_props.excluded_objects:
#             if item.object and item.object.name in bpy.data.objects:  # Check if object still exists
#                 item.object.hide_viewport = False
                
#         for item in cam.exclude_props.excluded_collections:
#             if item.collection and item.collection.name in bpy.data:  # Check if collection still exists
#                 item.collection.hide_viewport = False

# Create a unique identifier for msgbus subscription
msgbus_owner = object()

# Message bus callback
def camera_change_callback():
    """Callback when active camera changes"""
    update_exclusion_visibility(bpy.context)

# Subscribe to active camera changes
def subscribe_to_camera_changes():
    """Subscribe to camera changes via msgbus"""
    subscribe_to = (bpy.types.Scene, "camera")
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=msgbus_owner,
        args=(),
        notify=camera_change_callback,
        options={'PERSISTENT'},
    )

@persistent
def load_handler(dummy):
    """Handler called when a new blend file is loaded"""
    subscribe_to_camera_changes()
    # Update visibility based on active camera
    update_exclusion_visibility(bpy.context)

# Classes to register
classes = (
    STORYTOOLS_PG_collection_reference,
    STORYTOOLS_PG_excluded_object,
    STORYTOOLS_PG_excluded_collection,
    STORYTOOLS_PG_camera_exclude_props,
    STORYTOOLS_OT_add_excluded_object_from_selection,
    STORYTOOLS_OT_search_add_excluded_object,
    STORYTOOLS_OT_remove_excluded_object,
    STORYTOOLS_OT_search_add_excluded_collection,
    STORYTOOLS_OT_remove_excluded_collection,
    STORYTOOLS_UL_excluded_objects,
    STORYTOOLS_UL_excluded_collections,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register property group on Camera objects
    bpy.types.Object.exclude_props = PointerProperty(type=STORYTOOLS_PG_camera_exclude_props)
    
    # Setup msgbus subscription
    subscribe_to_camera_changes()
    
    # Register load handler
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    # Remove load handler
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    
    # Clear msgbus subscription
    bpy.msgbus.clear_by_owner(msgbus_owner)
    
    # Remove property group
    del bpy.types.Object.exclude_props
    
    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()