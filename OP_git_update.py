import bpy
import shutil
import subprocess
from pathlib import Path
import os

def git_update(folder: str) -> str:
    ''' Try to git pull fast foward only in passed folder and return console output'''
    os.chdir(folder)
    name = Path(folder).name
    print(f'Pulling in {name}')
    pull_cmd = ['git', 'pull', '--ff-only'] # git pull --ff-only
    pull_ret = subprocess.check_output(pull_cmd)
    return pull_ret.decode()

class STORYTOOLS_OT_git_pull(bpy.types.Operator):
    bl_idname = "storytools.git_pull"
    bl_label = "Git Pull Update"
    bl_description = "Update addon using 'git pull --ff-only'"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def invoke(self, context, event):
        if not shutil.which('git'):
            self.report({'ERROR'}, 'Git not found in path, if just installed, restart Blender/Computer')
            return {'CANCELLED'}
        
        ret = git_update(Path(__file__).parent.as_posix())
        print(ret)

        if 'Already up to date' in ret:
            self.report({'INFO'}, 'Already up to date')
            self.message = ret.rstrip('\n').split('\n')
        elif 'Fast-forward' in ret and 'Updating' in ret:
            self.report({'INFO'}, 'Updated ! Restart Blender')
            self.message = ['Updated! Restart Blender.'] + ret.rstrip('\n').split('\n')
        else:
            self.report({'WARNING'}, 'Problem trying to git pull addon')
            self.message = ['Problem checking git pull (see console)'] + ret.rstrip('\n').split('\n')

        return context.window_manager.invoke_props_dialog(self, width=350)
        # return context.window_manager.invoke_props_popup(self, event) # execute on change
        # return self.execute(context)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        for line in self.message:
            col.label(text=line)

    def execute(self, context):
        return {'FINISHED'}

def register():
    if bpy.app.background:
        return
    bpy.utils.register_class(STORYTOOLS_OT_git_pull)

def unregister():
    if bpy.app.background:
        return
    bpy.utils.unregister_class(STORYTOOLS_OT_git_pull)
