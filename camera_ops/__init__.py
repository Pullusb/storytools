from . import (cam_data,
               cam_toggle_parent,
               cam_quick_track_to,
               )

modules = (
    cam_data,
    cam_toggle_parent,
    cam_quick_track_to,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
