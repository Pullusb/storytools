from . import (
    workspace_setup,
    reset_draw_settings,
    viewport_options,
    story_palettes,
    create_static_storyboard,
    storyboard_add_pages,
    storyboard_panel_management,
    generate_marker_animatic,
    render_to_pdf,
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
    render_to_pdf,
    ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
