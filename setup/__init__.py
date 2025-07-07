from . import (
    workspace_setup,
    reset_draw_settings,
    viewport_options,
    story_palettes,
    git_update,
    create_static_storyboard,
    render_to_pdf,
    # generate_marker_animatic,
    ui,
)

modules = (
    workspace_setup,
    reset_draw_settings,
    viewport_options,
    story_palettes,
    git_update,
    create_static_storyboard,
    render_to_pdf,
    # generate_marker_animatic,
    ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
