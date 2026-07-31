from . import (quick_asset_browser,
               asset_add_to_view,
               )

modules = (
    quick_asset_browser,
    asset_add_to_view,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
