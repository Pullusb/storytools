from . import obj_actions

modules = (
    obj_actions,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
