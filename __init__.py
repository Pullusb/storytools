# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Storytools - Storyboard Tools",
    "description": "Set of tools for Storyboarding",
    "author": "Samuel Bernou",
    "version": (1, 14, 5),
    "blender": (3, 3, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "https://github.com/Pullusb/storytools",
    "tracker_url": "https://github.com/Pullusb/storytools/issues",
    "category": "Object"}

import bpy

from . import properties
from . import tool_presets
from . import preferences
from . import setup
from . import camera_ops
from . import object_ops
from . import gizmos_objects
from . import gizmos_camera
from . import gizmo_toolbar
from . import map
from . import handles
from . import panels
from . import keymaps
from .fn import get_addon_prefs

modules = (
    setup,
    properties,
    tool_presets,
    preferences,
    camera_ops,
    handles,
    object_ops,
    gizmos_objects,
    gizmos_camera,
    gizmo_toolbar,
    # map,
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
