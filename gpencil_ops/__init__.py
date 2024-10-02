from . import (
    frame_new,
    frame_jump,
               )

modules = (
    frame_new,
    frame_jump,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
