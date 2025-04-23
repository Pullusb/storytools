from .. import (
            properties,
            # tool_list,
               )

modules = (
    properties,
    # tool_list,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
