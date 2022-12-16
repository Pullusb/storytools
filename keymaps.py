import bpy

addon_keymaps = []

def register():
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name = "Grease Pencil Stroke Paint Mode", space_type = "EMPTY")

    # TODO: Shortcut to change Mat / Brushes / Layer
    kmi = km.keymap_items.new('catname.opsname', type='ONE', value='PRESS')
    # kmi.properties.data_path=''
    addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    
    addon_keymaps.clear()