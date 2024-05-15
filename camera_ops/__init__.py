from . import (cam_data, cam_toggle_parent)

modules = (
    cam_data,
    cam_toggle_parent,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
