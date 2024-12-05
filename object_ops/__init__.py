from . import (
    obj_actions,
    autolock_switch,
    snap_cursor,
)

modules = (
    obj_actions,
    autolock_switch,
    snap_cursor,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
