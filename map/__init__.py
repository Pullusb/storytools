from . import (
    # gizmos_map,
    handler_draw_map,
    map_ops,
    panels,
    )

modules = (
    # gizmos_map,
    handler_draw_map,
    map_ops,
    panels,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
