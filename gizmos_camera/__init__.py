from . import (
    cam_move,
    view_locked_pan,
    # cam_shift,
    )

modules = (
    cam_move,
    view_locked_pan,
    # cam_shift,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
