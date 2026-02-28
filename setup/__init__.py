from . import (
    render_static_storyboard,
    workspace_setup,
    reset_draw_settings,
    viewport_options,
    story_palettes,
    create_static_storyboard,
    storyboard_add_pages,
    storyboard_panel_management,
    generate_marker_animatic,
    ui,
)

modules = (
    workspace_setup,
    reset_draw_settings,
    viewport_options,
    story_palettes,
    create_static_storyboard,
    storyboard_add_pages,
    storyboard_panel_management,
    generate_marker_animatic,
    render_static_storyboard,
    ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
