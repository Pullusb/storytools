from . import (workspace_setup,
               story_palettes,
               git_update,
               )

modules = (
    git_update,
    story_palettes,
    workspace_setup,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
