import bpy

from bpy.types import Operator
from bpy.app.handlers import persistent

class STORYTOOLS_OT_lock_view(Operator):
    bl_idname = "storytools.lock_view"
    bl_label = 'Lock Current View'
    bl_description = "Lock current viewport orbit navigation"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        r3d = context.space_data.region_3d
        r3d.lock_rotation = not r3d.lock_rotation
        return {"FINISHED"}

class VIEW3D_OT_locked_pan(bpy.types.Operator):
    bl_idname = "view3d.locked_pan"
    bl_label = "Locked Pan"
    bl_description = "Locked Pan, a wrapper for pan operation\
                    \nOnly valid when viewport has locked rotation (region_3d.lock_rotation)"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        # context.area.type == 'VIEW_3D'
        return context.space_data.region_3d.lock_rotation

    def execute(self, context):
        # print("Locked rotation - Pan wrapper") # Dbg
        bpy.ops.view3d.move("INVOKE_DEFAULT")
        return {'FINISHED'}

## --- KEYMAPS

addon_keymaps = []
def register_keymaps():
    print("Register locked pan keymaps") #Dbg
    addon = bpy.context.window_manager.keyconfigs.addon

    ## Key properteis to compare
    ## Other: active, compare, idname, name, repeat, map_type
    # key_props = [
    # 'type',
    # 'value',
    # 'ctrl',
    # 'alt',
    # 'shift',
    # 'oskey',
    # 'any',
    # 'key_modifier',
    # ]

    ## Scan current keymaps to replicate
    user_km = bpy.context.window_manager.keyconfigs.user.keymaps.get('3D View')
    if not user_km:
        print('-- Storytools could not reach user keymap')
        return

    if len(addon_keymaps):
        ## Skip if keymaps are already registered, avoid duplicates
        return

    for skmi in user_km.keymap_items:
        # Only replicate view3d.rotate (orbit) shortcut
        if skmi.idname != 'view3d.rotate':
            continue

        # skmi.show_expanded = True #Dbg

        ## By default 3 shortcut exists : MOUSEROTATE, MIDDLEMOUSE, TRACKPADPAN
        ## Trackball shortcut skip (?)
        if skmi.type == 'MOUSEROTATE':
            continue

        ## Check if duplicates exists (/!\ seems duplicate can be found, but actually removed right away on loading)
        # km_dup = next((k for k in user_km.keymap_items 
        #                 if k.idname == "view3d.locked_pan"
        #                 and all(getattr(skmi, x) == getattr(k, x) for x in key_props)), None)
        # if km_dup:
        #     print(f'--> "{skmi.name} > {skmi.type} > {skmi.value}" shortcut already have a lock pan equivalent') # Dbg
        #     continue
        
        # print(f'>-> Create {skmi.name} > {skmi.type} > {skmi.value}" shortcut to lock pan') # Dbg
        ## Create duplicate
        km = addon.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new(
            idname="view3d.locked_pan",
            type=skmi.type,
            value=skmi.value,
            ctrl=skmi.ctrl,
            alt=skmi.alt,
            shift=skmi.shift,
            oskey=skmi.oskey,
            any=skmi.any,
            key_modifier=skmi.key_modifier,
            )

        addon_keymaps.append((km, kmi))
    
    # print("keymap register - OK\n") #dbg

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

@persistent
def set_lockpan_km(dummy):
    register_keymaps()

classes=(
    STORYTOOLS_OT_lock_view,
    VIEW3D_OT_locked_pan,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymaps()
    bpy.app.handlers.load_post.append(set_lockpan_km)

def unregister():
    unregister_keymaps()
    bpy.app.handlers.load_post.remove(set_lockpan_km)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    