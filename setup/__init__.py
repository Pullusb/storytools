from . import (workspace_setup,
               viewport_options,
               story_palettes,
               git_update,
               )

modules = (
    workspace_setup,
    # viewport_options,
    story_palettes,
    git_update,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
