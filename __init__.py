# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Storytools - Storyboard Tools",
    "description": "Set of tools for Storyboarding",
    "author": "Samuel Bernou",
    "version": (0, 8, 3),
    "blender": (3, 3, 0),
    "location": "View3D",
    "warning": "Alpha",
    "doc_url": "https://github.com/Pullusb/storytools",
    "category": "Object"}

from pathlib import Path

from . import OP_git_update
from . import properties
from . import preferences
from . import OP_story_palettes
from . import OP_camera_controls
from . import OP_gp_objects
from . import GZ_toolbar
from . import handles
from . import panels
# from . import keymaps

import bpy

modules = (
    OP_git_update,
    properties,
    preferences,
    OP_story_palettes,
    OP_gp_objects,
    OP_camera_controls,
    handles,
    GZ_toolbar,
    panels,
)

def register():
    if bpy.app.background:
        return
    for mod in modules:
        mod.register()

def unregister():
    if bpy.app.background:
        return
    for mod in modules:
        mod.unregister()

if __name__ == "__main__":
    register()
