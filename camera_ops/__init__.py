from . import (cam_data,
               cam_toggle_parent,
               cam_quick_track_to,
               cam_create,
               cam_exclude_filter,
               )

modules = (
    cam_data,
    cam_toggle_parent,
    cam_quick_track_to,
    cam_create,
    cam_exclude_filter,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
