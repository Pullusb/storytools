from . import (cam_move)

modules = (
    cam_move,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
