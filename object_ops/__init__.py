from . import (
    obj_actions,
    autolock_switch,
    snap_cursor,
    set_origin,
    material_management,
)

modules = (
    obj_actions,
    autolock_switch,
    snap_cursor,
    set_origin,
    material_management,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
