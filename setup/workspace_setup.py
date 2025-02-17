import bpy
from pathlib import Path
from typing import List, Sequence, Tuple
from .. constants import APP_TEMPLATES_DIR, STORYBOARD_TEMPLATE_BLEND, DUAL_STORYBOARD_TEMPLATE_BLEND
from bpy.types import (
    Window,
    WindowManager,
)

from .. import fn

def set_sidebar(area=None):
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

def activate_workspace(name='Storyboard', filepath=None, context=None):
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
        # return True
    else:
        # Same name with spaces as underscore
        if filepath is None:    
            ## use name
            dir_name = name.replace(' ', '_')
            filepath = APP_TEMPLATES_DIR / dir_name / 'startup.blend'
        
        ret = bpy.ops.workspace.append_activate(idname=name, filepath=str(filepath))
        if ret != {'FINISHED'}:
            print(f'Could not found "{name}" at {filepath}')
            message = [f'Could not found "{name}" workspace at:',
                    str(filepath)]
            fn.show_message_box(_message=message, _title='Workspace Not found', _icon='ERROR')
            # return False

    ## Get biggest viewport and set category toolbar to Storytools:
    return context.window.workspace

## Load directly a single workspace
class STORYTOOLS_OT_set_storyboard_workspace(bpy.types.Operator):
    bl_idname = "storytools.set_storyboard_workspace"
    bl_label = 'Set Storyboard Workspace'
    bl_description = "Set storyboard workspace, import if needed"
    bl_options = {'REGISTER', 'INTERNAL'}

    # workspace_name : bpy.props.BoolProperty(name='Storyboard', default=False)

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

class STORYTOOLS_OT_set_storyboard_dual_window_workspace(bpy.types.Operator):
    bl_idname = "storytools.set_storyboard_dual_window_workspace"
    bl_label = 'Set Storyboard Dual Window Workspace'
    bl_description = "Set Dual Window storyboard workspace to be able to work with storypencil"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        # name = "Board"
        # filepath = str(DUAL_STORYBOARD_TEMPLATE_BLEND)
        
        # ret = bpy.ops.workspace.append_activate(idname=name, filepath=filepath)
        # if ret != {'FINISHED'}:
        #     print(f'Could not found "{name}" at {filepath}')
        #     message = [f'Could not found "{name}" workspace at:',
        #             str(filepath)]
        #     fn.show_message_box(_message=message, _title='Workspace Not found', _icon='ERROR')
        #     # return False

        ## Setup current window workspace (Storyboard)
        activate_workspace(context=context)
        bpy.app.timers.register(set_sidebar, first_interval=0.8)

        current_win = context.window
        current_win_id = current_win.as_pointer()
        
        ## Get or create secondary window
        if len(context.window_manager.windows) == 1:
            bpy.ops.wm.window_new_main()
            ## new window not active

        ## Activate Sequencer on secondary window
        if secondary_win := next((w for w in context.window_manager.windows if w.as_pointer() != current_win_id), None):
            with context.temp_override(window=secondary_win):
                ## load from storyboard template
                activate_workspace('Sequencer', filepath=STORYBOARD_TEMPLATE_BLEND)
                ## Can add some spark setup here (as option if an arg ops is passed)

        return {"FINISHED"}

## UNUSED CURRENTLY
# -------------------------------------------------------------
#  Setup Spark (spa sequencer) session (WIP, broken), better to integrate in aboce operator
#
# -------------------------------------------------------------

"""
class STORYTOOLS_OT_setup_spark(bpy.types.Operator):
    bl_idname = "storytools.setup_spark"
    bl_label = "Setup Dual Workspace For Spark"
    bl_description = "Configure settings for a storyboard session using spark (spa-sequencer) for shot management"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def get_workspace(self, type):
        for wrk in bpy.data.workspaces:
            if wrk.name == type:
                return wrk

        return None

    def execute(self, context):
        scene_base = context.scene

        wk_storyboard = activate_workspace(name='Storyboard', context=context)
        wk_sequencer = activate_workspace(name='Sequencer', context=context)
        # Create Workspace
        ## Add video editing
        # template_path = None
        # if "Video Editing" not in bpy.data.workspaces:
        #     template_path = next(bpy.utils.app_template_paths(), None)
        #     filepath = str(Path(template_path, "Video_Editing", "startup.blend"))
        #     bpy.ops.workspace.append_activate(
        #         idname="Video Editing", filepath=filepath)
        
        # Get/Create New scene

        ## Using data
        scene_edit = bpy.data.scenes.get('EDIT')
        if not scene_edit:
            scene_edit = bpy.data.scenes.get('Edit')
        if not scene_edit:
            scene_edit = bpy.data.scenes.new('EDIT')

        # scene_edit.storypencil_edit_workspace = self.get_workspace("Storyboard")
        bpy.app.timers.register(set_workpaces_on_dual_window_spark, first_interval=1.5)
        return {"FINISHED"}
"""

## UNUSED CURRENTLY
# -------------------------------------------------------------
#  Setup code from Storypencil addon (Modified)
#
# -------------------------------------------------------------

def window_id(window: Window) -> str:
    """ Get Window's ID.

    :param window: the Window to consider
    :return: the Window's ID
    """
    return str(window.as_pointer())


def get_window_from_id(wm: WindowManager, win_id: str) -> Window:
    """Get a Window object from its ID (serialized ptr).

    :param wm: a WindowManager holding Windows
    :param win_id: the ID of the Window to get
    :return: the Window matching the given ID, None otherwise
    """
    return next((w for w in wm.windows if w and window_id(w) == win_id), None)


def get_main_windows_list(wm: WindowManager) -> Sequence[Window]:
    """Get all the Main Windows held by the given WindowManager `wm`"""
    return [w for w in wm.windows if w and w.parent is None]


def join_win_ids(ids: List[str]) -> str:
    """Join Windows IDs in a single string"""
    return ";".join(ids)


def split_win_ids(ids: str) -> List[str]:
    """Split a Windows IDs string into individual IDs"""
    return ids.split(";")

def get_secondary_window_indices(wm: WindowManager) -> List[str]:
    """Get secondary Windows indices as a list of IDs

    :param wm: the WindowManager to consider
    :return: the list of secondary Windows IDs
    """
    return split_win_ids(wm.storypencil_settings.secondary_windows_ids)


def is_secondary_window(window_manager: WindowManager, win_id: str) -> bool:
    """Return wether the Window identified by 'win_id' is a secondary window.

    :return: whether this Window is a sync secondary
    """
    return win_id in get_secondary_window_indices(window_manager)


def enable_secondary_window(wm: WindowManager, win_id: str):
    """Enable the secondary status of a Window.

    :param wm: the WindowManager instance
    :param win_id: the id of the window
    """
    secondary_indices = get_secondary_window_indices(wm)
    win_id_str = win_id
    # Delete old indice if exist
    if win_id_str in secondary_indices:
        secondary_indices.remove(win_id_str)

    # Add indice
    secondary_indices.append(win_id_str)

    # rebuild the whole list of valid secondary windows
    secondary_indices = [
        idx for idx in secondary_indices if get_window_from_id(wm, idx)]

    wm.storypencil_settings.secondary_windows_ids = join_win_ids(secondary_indices)


def toggle_secondary_window(wm: WindowManager, win_id: str):
    """Toggle the secondary status of a Window.

    :param wm: the WindowManager instance
    :param win_id: the id of the window
    """
    secondary_indices = get_secondary_window_indices(wm)
    win_id_str = win_id
    if win_id_str in secondary_indices:
        secondary_indices.remove(win_id_str)
    else:
        secondary_indices.append(win_id_str)

    # rebuild the whole list of valid secondary windows
    secondary_indices = [
        idx for idx in secondary_indices if get_window_from_id(wm, idx)]

    wm.storypencil_settings.secondary_windows_ids = join_win_ids(secondary_indices)


def get_main_window(wm: WindowManager) -> Window:
    """Get the Window used to drive the synchronization system

    :param wm: the WindowManager instance
    :returns: the main Window or None
    """
    return get_window_from_id(wm=wm, win_id=wm.storypencil_settings.main_window_id)


def get_secondary_window(wm: WindowManager) -> Window:
    """Get the first secondary Window

    :param wm: the WindowManager instance
    :returns: the Window or None
    """
    for w in wm.windows:
        win_id = window_id(w)
        if is_secondary_window(wm, win_id):
            return w

    return None


def get_not_main_window(wm: WindowManager) -> Window:
    """Get the first not main Window

    :param wm: the WindowManager instance
    :returns: the Window or None
    """
    for w in wm.windows:
        win_id = window_id(w)
        if win_id != wm.storypencil_settings.main_window_id:
            return w

    return None


def set_workspace_on_dual_window(context=None):
    context = context or bpy.context
    wm = context.window_manager

    main_window = get_main_window(wm)
    print('main_window: ', main_window, main_window.workspace.name)
    with context.temp_override(window=main_window, scene=bpy.data.scenes['Scene']):
        activate_workspace(name='Storyboard')
        set_sidebar()

    ## Works, go to edit as planned
    secondary_window = get_secondary_window(wm)
    print('secondary_window: ', secondary_window, secondary_window.workspace.name)
    with context.temp_override(window=secondary_window, scene=bpy.data.scenes['Edit']):
        activate_workspace(name='Sequencer')
    
    ## ! no good !
    # non_set_win = next((w for w in set(bpy.context.window_manager.windows[:]) if w.workspace.name not in ('Storyboard','Sequencer')), None)
    # print('non_set_win: ', non_set_win)
    # if non_set_win:
    #     print('non_set_workspace: ', non_set_win.workspace.name)
    #     print('Storyboard', bpy.data.workspaces.get('Storyboard'))
    #     non_set_win.workspace = bpy.data.workspaces.get('Storyboard')

    
    ## method 2.
    # main_window = get_main_window(wm)
    # wk_sequencer = bpy.data.workspaces.get('Sequencer')
    # if wk_sequencer:
    #     main_window.workspace = wk_sequencer
    # else:
    #     print('Sequencer workspace not found')

    # secondary_window = get_secondary_window(wm)
    # wk_storyboard = bpy.data.workspaces.get('Storyboard')
    # if wk_storyboard:
    #     secondary_window.workspace = wk_storyboard
    # else:
    #     print('Storyboard workspace not found')

class STORYTOOLS_OT_setup_storypencil(bpy.types.Operator):
    bl_idname = "storytools.setup_storypencil"
    bl_label = "Setup Workspace"
    bl_description = "Configure settings for a storyboard session"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def get_workspace(self, type):
        for wrk in bpy.data.workspaces:
            if wrk.name == type:
                return wrk

        return None

    def execute(self, context):
        scene_base = context.scene
        
        # Append custom workspaces
        wk_storyboard = activate_workspace(name='Storyboard', context=context)
        wk_sequencer = activate_workspace(name='Sequencer', filepath=STORYBOARD_TEMPLATE_BLEND, context=context)

        # Create Workspace
        template_path = None
        if "Video Editing" not in bpy.data.workspaces:
            template_path = next(bpy.utils.app_template_paths(), None)
            filepath = str(Path(template_path, "Video_Editing", "startup.blend"))
            bpy.ops.workspace.append_activate(
                idname="Video Editing", filepath=filepath)
        
        # Create New scene
        # bpy.ops.scene.new()
        # scene_edit = context.scene
        # scene_edit.name = 'Edit'
        
        ## Using data
        scene_edit = bpy.data.scenes.get('Edit')
        if not scene_edit:
            scene_edit = bpy.data.scenes.new('Edit')

        # Rename original base scene
        scene_base.name = 'Base'
        
        # Setup Edit scene settings
        scene_edit.storypencil_main_workspace = self.get_workspace(
            "Video Editing")
        scene_edit.storypencil_main_scene = scene_edit
        scene_edit.storypencil_base_scene = scene_base

        # scene_edit.storypencil_edit_workspace = self.get_workspace("2D Animation")
        scene_edit.storypencil_edit_workspace = self.get_workspace("Storyboard")

        ## Setup Dual Window ?
        # if len(bpy.context.window_manager.windows) == 1:
        #     # Extract a window and switch it to Sequencer
        #     main_window = bpy.context.window_manager.windows[0]
        #     bpy.ops.wm.window_new()
        #     edit_window = bpy.context.window_manager.windows[-1]
        #     edit_window.screen.areas[0].type = 'SEQUENCE_EDITOR'
        
        # Add a new strip (need set the area context)
        context.window.scene = scene_edit
        area_prv = context.area.ui_type
        context.area.ui_type = 'SEQUENCE_EDITOR'
        prv_frame = scene_edit.frame_current

        scene_edit.frame_current = scene_edit.frame_start
        vse = scene_edit.sequence_editor
        if not vse or next((s for s in vse.sequences if s.type == 'SCENE'), None) is None:
            with context.temp_override(scene=scene_edit):
                bpy.ops.storypencil.new_scene()

        context.area.ui_type = area_prv
        scene_edit.frame_current = prv_frame

        scene_edit.update_tag()
        with context.temp_override(scene=scene_edit):
            bpy.ops.sequencer.reload()

            ## Set dual monitor
            scene_edit.storypencil_use_new_window = True
            bpy.ops.storypencil.sync_set_main()

        bpy.app.timers.register(set_workspace_on_dual_window, first_interval=1.5)
        return {"FINISHED"}


classes=(
    STORYTOOLS_OT_set_storyboard_workspace,
    STORYTOOLS_OT_set_storyboard_dual_window_workspace, # wip broken
    # STORYTOOLS_OT_setup_spark, # wip broken
    # STORYTOOLS_OT_setup_storypencil,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)