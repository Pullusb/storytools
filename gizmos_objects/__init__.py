from . import (
    obj_align_with_view,
    obj_move,
    )

modules = (
    obj_align_with_view,
    obj_move,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
