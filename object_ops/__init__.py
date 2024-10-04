from . import (
    obj_actions,
    autolock_switch,
)

modules = (
    obj_actions,
    autolock_switch,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
