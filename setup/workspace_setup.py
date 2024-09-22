import bpy
from pathlib import Path
from typing import List, Sequence, Tuple
from bpy.types import (
    Context,
    MetaSequence,
    Operator,
    PropertyGroup,
    SceneSequence,
    Window,
    WindowManager,
)

from .. import fn

def activate_workspace(name='Storyboard', context=None):
    if context is None:
        context = bpy.context

    if context.window.workspace.name == name:
        print(f'Already in {name} workspace')
        return

    if (render_wkspace := bpy.data.workspaces.get(name)):
        context.window.workspace = render_wkspace
        return True
    
    # Same name with spaces as underscore
    dir_name = name.replace(' ', '_')
    filepath = Path(__file__).parent / 'templates' / dir_name / 'startup.blend'
    
    ret = bpy.ops.workspace.append_activate(idname=name, filepath=str(filepath))
    if ret != {'FINISHED'}:
        print(f'Could not found "{name}" at {filepath}')
        message = [f'Could not found "{name}" workspace at:',
                   str(filepath)]
        fn.show_message_box(_message=message, _title='Workspace Not found', _icon='ERROR')

        return False

    ## Get biggest viewport and set category toolbar to Storytools:
    viewports = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D']
    if viewports:
        vp_area = viewports.sort(key=lambda x: x.width)
        if sidebar := next((r for r in vp_area.regions if r.type == 'UI'), None):
            sidebar.active_panel_category = 'Storytools'

    return context.window.workspace

class STORYTOOLS_OT_set_storyboard_workspace(bpy.types.Operator):
    bl_idname = "storytools.set_storyboard_workspace"
    bl_label = 'Set Storyboard Workspace'
    bl_description = "Set story board workspace, import if needed"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        activate_workspace(context=context)
        return {"FINISHED"}


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
        wk_sequencer = activate_workspace(name='Sequencer', context=context)

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
    STORYTOOLS_OT_setup_storypencil,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)