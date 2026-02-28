import bpy
from pathlib import Path

from .. import fn

def set_sidebar(area=None):
    """Open Sidebar and set storytools tab
    if no area can be found, use biggest viewport and set category toolbar to Storytools"""

    prefs = fn.get_addon_prefs()

    if not area:
        area = bpy.context.area

    context = bpy.context
    window = bpy.context.window

    if area == None:
        ## Return biggest 3D area
        areas_3d = [(w, a) for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type == 'VIEW_3D']
        if not areas_3d:
            print('Could not found area ! skip "set sidebar" operation')
            return
        areas_3d.sort(key=lambda x: x[1].width)
        window, area = areas_3d[-1]

        ## Return first found 3D area
        # window, area = next(((w, a) for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type == 'VIEW_3D'), (None,None))
        # if not area:
        #     print('Could not found area ! skip "set sidebar" operation')
        #     return

    sidebar = None

    ## Set sidebar visibility
    space_data = context.space_data
    if not space_data:
        space_data = area.spaces.active

    if prefs.show_sidebar != 'NONE':
        if space_data.show_region_ui and prefs.show_sidebar == 'HIDE':
            space_data.show_region_ui = False
        if not space_data.show_region_ui and prefs.show_sidebar == 'SHOW':
            space_data.show_region_ui = True

    ## Set sidebar panel tab
    if bpy.app.version >= (4,2,0) and prefs.set_sidebar_tab and space_data.show_region_ui:
        tab = prefs.sidebar_tab_target
        if not tab.strip():
            tab = 'Storytools'

        ## 'active_panel_category' is readonly at first (Then goes to false after operator has finished)
        ## Not working: Try to refresh UI to fix that once sidebar is opened
        # context.area.regions.update()
        # context.screen.update_tag()
        if sidebar := next((r for r in area.regions if r.type == 'UI'), None):
            with bpy.context.temp_override(window=window, area=area, region=sidebar):
                try:
                    # For now, just bypass the error, a second call works after full interface reload...
                    sidebar.active_panel_category = tab
                    sidebar.tag_redraw()
                    print('sidebar category set to:', tab)
                except AttributeError:
                    print('Could not set sidebar category (retry can work)')
                    pass

        # print('finished', sidebar)

""" Previous version
def set_sidebar(area=None):
    if not area:
        area = bpy.context.area
    prefs = fn.get_addon_prefs()
    context = bpy.context

    sidebar = None
    # with bpy.context.temp_override(area=area):
    ## Set sidebar visibility
    if prefs.show_sidebar != 'NONE':
        if context.space_data.show_region_ui and prefs.show_sidebar == 'HIDE':
            context.space_data.show_region_ui = False
            # context.area.spaces.update()
        if not context.space_data.show_region_ui and prefs.show_sidebar == 'SHOW':
            context.space_data.show_region_ui = True
            # context.area.spaces.update()

    ## Set sidebar panel tab
    if bpy.app.version >= (4,2,0) and prefs.set_sidebar_tab and context.space_data.show_region_ui:
        tab = prefs.sidebar_tab_target
        if not tab.strip():
            tab = 'Storytools'

        ## 'active_panel_category' is readonly at first (Then goes to false after operator has finished)
        ## Not working: Try to refresh UI to fix that once sidebar is opened
        # context.area.regions.update()
        # context.screen.update_tag()
        if sidebar := next((r for r in area.regions if r.type == 'UI'), None):
            with bpy.context.temp_override(window=bpy.context.window, area=bpy.context.area, region=sidebar):
                try:
                    # For now, just bypass the error, a second call works after full interface reload...
                    sidebar.active_panel_category = tab
                    sidebar.tag_redraw()
                    print('sidebar category set to:', tab)
                except AttributeError:
                    print('Could not set sidebar category (retry can work)')
                    pass
        # print('finished', sidebar)
 """

def get_storyboarding_startup_path():
    """Get the path of the startup file for storyboarding workspace"""

    ## Directly in system path:
    # Path(bpy.utils.resource_path('SYSTEM'), 'scripts', 'startup', 'bl_app_templates_system', 'Storyboarding', 'startup.blend')
    
    ## Over all valid path
    for template_root_path in bpy.utils.app_template_paths():
        template_path = Path(template_root_path, 'Storyboarding', 'startup.blend')
        if template_path.exists():
            return template_path

def activate_workspace(name='Storyboarding', filepath=None, context=None):
    """Activate workspace by workspace name
    filepath: if specified, fetch the workspace from this path
    """

    if context is None:
        context = bpy.context

    # if context.window.workspace.name == name:
    #     print(f'Already in {name} workspace')
    #     return

    if (searched_wkspace := bpy.data.workspaces.get(name)):
        context.window.workspace = searched_wkspace

    else:
        # Same name with spaces as underscore
        if filepath is None:    
            filepath = get_storyboarding_startup_path()
        
        ret = bpy.ops.workspace.append_activate(idname=name, filepath=str(filepath))
        if ret != {'FINISHED'}:
            print(f'Could not found "{name}" at {filepath}')
            message = [f'Could not found "{name}" workspace at:',
                    str(filepath)]
            fn.show_message_box(_message=message, _title='Workspace Not found', _icon='ERROR')

    return context.window.workspace

## Load directly a single workspace
class STORYTOOLS_OT_set_storyboard_workspace(bpy.types.Operator):
    bl_idname = "storytools.set_storyboard_workspace"
    bl_label = 'Set Storyboard Workspace'
    bl_description = "Set storyboarding workspace"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        # ret = bpy.ops.workspace.append_activate(idname=name, filepath=str(filepath))
        activate_workspace(context=context)

        ## Search in current screen
        # problem : after activating new workpace, the context is lost (or half voided)
        # areas_3d = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D']
        # if not areas_3d:
        #     return {"FINISHED"}
        # areas_3d.sort(key=lambda x: x.width)
        # set_sidebar(areas_3d[-1])
        # set_sidebar()

        bpy.app.timers.register(set_sidebar, first_interval=0.8)
        return {"FINISHED"}

classes = (STORYTOOLS_OT_set_storyboard_workspace,)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)