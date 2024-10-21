from . import (
    # gizmos_map,
    handler_draw_map,
    map_ops,
    gizmo_map_toolbar,
    # ui,
    )

modules = (
    # gizmos_map,
    handler_draw_map,
    map_ops,
    gizmo_map_toolbar,
    # ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
