from . import (workspace_setup,
               reset_draw_settings,
               viewport_options,
               story_palettes,
               create_material,
               git_update,
               ui,
               )

modules = (
    workspace_setup,
    reset_draw_settings,
    viewport_options,
    story_palettes,
    create_material,
    git_update,
    ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
