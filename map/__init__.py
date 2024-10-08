from . import (
    # gizmos_map,
    handler_draw_map,
    map_ops,
    # ui,
    )

modules = (
    # gizmos_map,
    handler_draw_map,
    map_ops,
    # ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
