# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Storytools - Storyboard Tools",
    "description": "Set of tools for Storyboarding",
    "author": "Samuel Bernou",
    "version": (0, 2, 0),
    "blender": (3, 3, 0),
    "location": "View3D",
    "warning": "Alpha",
    "doc_url": "https://github.com/Pullusb/storytools",
    "category": "Object" }

from . import properties
from . import preferences
from . import GZ_toolbar
from . import OP_story_palettes
from . import OP_gp_objects
from . import panels
# from . import keymaps

import bpy

modules = (
    properties,
    preferences,
    GZ_toolbar,
    OP_story_palettes,
    OP_gp_objects,
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
