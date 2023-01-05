import bpy
from pathlib import Path

def activate_workspace(workspace_name = 'Storyboard', context=None):
    if context is None:
        context = bpy.context

    if context.window.workspace.name == workspace_name:
        print(f'Already in {workspace_name} workspace')
        return

    if (render_wkspace := bpy.data.workspaces.get(workspace_name)):
        context.window.workspace = render_wkspace
        return True

    workspace_filepath = Path(__file__).parent / 'workspaces' / 'startup.blend'
    ret = bpy.ops.workspace.append_activate(idname=workspace_name, filepath=str(workspace_filepath))
    if ret != {'FINISHED'}:
        print(f'Could not found {workspace_name} at {workspace_filepath}')
        return False

    return True

class STORYTOOLS_OT_set_storyboard_workspace(bpy.types.Operator):
    bl_idname = "storytools.set_storyboard_workspace"
    bl_label = 'Set Storyboard Workspace'
    bl_description = "Set story board workspace, import if needed"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        activate_workspace(context=context)
        return {"FINISHED"}

classes=(
    STORYTOOLS_OT_set_storyboard_workspace,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)