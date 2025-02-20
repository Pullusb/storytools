from . import (
    draw_scale_figure,
    bake_figure,
    )

modules = (
    draw_scale_figure,
    bake_figure
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
