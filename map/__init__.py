from . import (
    # gizmos_map,
    handler_draw_map,
    map_ops,
    map_roll,
    map_place_gp,
    gizmo_map_toolbar,
    )

modules = (
    # gizmos_map,
    handler_draw_map,
    map_ops,
    map_roll,
    map_place_gp,
    gizmo_map_toolbar,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
