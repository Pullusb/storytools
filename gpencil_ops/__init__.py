from . import (
    frame_new,
    frame_jump,
    ui,
               )

modules = (
    frame_new,
    frame_jump,
    ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
