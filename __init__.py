# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Storytools - Storyboard Tools",
    "description": "Set of tools for Storyboarding",
    "author": "Samuel Bernou",
    "version": (1, 5, 0),
    "blender": (3, 3, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "https://github.com/Pullusb/storytools",
    "tracker_url": "https://github.com/Pullusb/storytools/issues",
    "category": "Object"}

import bpy

from . import OP_git_update
from . import properties
from . import preferences
from . import OP_story_palettes
from . import OP_camera_controls
from . import OP_camera_data
from . import OP_gp_objects
from . import GZ_toolbar
from . import OP_workspace_setup
from . import handles
from . import panels
from . import keymaps
from .fn import get_addon_prefs

modules = (
    OP_git_update,
    properties,
    preferences,
    OP_story_palettes,
    OP_gp_objects,
    OP_camera_controls,
    OP_camera_data,
    handles,
    GZ_toolbar,
    OP_workspace_setup,
    panels,
    keymaps,
)

def register():
    if bpy.app.background:
        return

    for mod in modules:
        mod.register()
    
    # Update panel name
    preferences.ui_in_sidebar_update(get_addon_prefs(), bpy.context)

def unregister():
    if bpy.app.background:
        return

    for mod in reversed(modules):
        mod.unregister()

if __name__ == "__main__":
    register()
