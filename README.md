# Storytools - Storyboard Tools

Blender addon - Set of tools for storyboarding in Blender

### Available on extension platform for Blender 5+ ([extension page](https://extensions.blender.org/add-ons/storytools/))

⬇️ Install directly from Blender: Edit > Preferences > Get Extension > search "Storytools" and click install 

#### [Documentation](https://pullusb.github.io/storytools-docs/)

---

## Links for 4.2 to 4.5 version and latest dev

Latest stable for Blender 5 and above is on the extension platform

#### [Download latest dev version (manual install for Blender 5+) ](https://github.com/Pullusb/storytools/archive/master.zip)

> /!\ Important notes:
> - the releases available on release pages are only for older version (below 5.0), see link below
> - the gpv2 branch (blender 4.0 to 4.2) is no longer maintained.
> - bl42to45 branch (blender 4.3 to 4.5) is no longer maintained.
> - version below 4.0 are not supported.


#### [Downloads for Blender 4.0 to 4.2 and 4.3 to 4.5 are listed in release page](https://github.com/Pullusb/storytools/releases)

---

![Storytools v1 UI](https://raw.githubusercontent.com/Pullusb/images_repo/master/storytools_ui_demo.jpg)


Sponsored by:
- **Samuel Bernou** (Maintainer)

Previous sponsors:
- [**CNC**](https://www.cnc.fr/)
- [**Autour de Minuit**](https://blog.autourdeminuit.com/)
- [**El Guiri Studios**](https://www.elguiristudios.com/)

---  

## Description

Add a `storytools` Tab in viewport sidebar

> After installation, restart blender once to enable material association handler


For a complete user guide, head to the [documentation](https://pullusb.github.io/storytools-docs/)

### Create New Drawing

Popup choices to Add a new grease pencil object in facing camera

Multiple Choice:

- At cursor position or right in front of camera
- Parented to camera
- Tweak distance directly (in meters)

When creating a new object:

- A default palette for storyboard is automatically loaded
- Draw mode is auto-reset to `Origin - Front Axis`

### Drawing Objects Stack

Keep same mode across object when selecting in this stack

### Special Behavior

When selecting a material, it "stick" to current active layer
(i.e: when selecting this layer again, it will switch back to this material)


## Bottom Control bar

Action gizmo buttons to easily place object and camera
All transform actions respect autokey

Objects Actions:

- Pan object
- Move object forward/backward
- Rotate object on camera view axis (Ctrl to snap on 15 degrees angles)
- Scale object
- Align object to camera: rotate object to have front axis face view (`-Y` direction)
- key object transform at current time (note: object, not GP frame)

Camera Actions:

- Pan camera
- Move camera forward/backward
- Toggle _Lock camera to view_
- Key camera position


## Top Tool preset bar

The tool presets are combos or customizables button + shortcut.  
Each set Blender tool with options, like a Macro.  
Defined through a shortcut and appear as button in the `Tool preset topbar` at the top of the viewport.


<!-- ## TODO
-> Add UI to better view and customize tools presets (icon selector, pre-entered names for builtin brush category, can use old code from "presets as collection"

-> How or when to fine tune settings of bucket fill (need to add lenght)
-> Probably need another brush with special settings for negative fill (auto-create new brushes)

-> Check if tool presets can handle multiple modes with bypass on main default shortcuts depending on each contexts

Modals
- Opt: For all modals, add icon warning if in autokey (same draw func call/stop for all) 

## Custom actions: Map Select could be overriden by custom action (while letting most of usual action valid)
pro:
    - allow to swap selection whatever the mode
    - would allow custom action on specific zone. like pointing camera at something.
cons:
    - Break default click action from blender
---

##Gizmo API tests

# prop tester
gz.use_draw_scale = True # already True
for att in ['group',
            'matrix_offset',
            'use_draw_value',
            'use_grab_cursor',
            'use_tooltip',
            'line_width']:
    print(att, getattr(gz, att))

alpha
alpha_highlight
bl_idname
color
color_highlight
group
hide
hide_keymap
hide_select
is_highlight
is_modal
line_width
matrix_basis
matrix_offset
matrix_space
matrix_world
properties
rna_type
scale_basis
select
select_bias
use_draw_hover
use_draw_modal
use_draw_offset_scale
use_draw_scale
use_draw_value
use_event_handle_all
use_grab_cursor
use_operator_tool_properties
use_select_background
use_tooltip


## Note for gizmoGroup

    # matrix_offset seem to affect only backdrop
    ## Note: instead of compose_matrix, use Matrix.LocRotScale(None, None, Vector((2,2,2)))
    # gz.matrix_offset = fn.compose_matrix(Vector((0,0,0)), Matrix().to_quaternion(), Vector((2,2,2)))
    
    # gz.scale_basis = 40 # same as tweaking matrix_basis scale
    
    ## changing matrix size does same thing as gz.scale_basis
    # gz.matrix_basis = fn.compose_matrix(
    #     Vector((left_pos + (i * next_pos), vertical_pos, 0)),
    #     Matrix().to_quaternion(), # Matrix.Rotation(0, 4, 'X'),
    #     Vector((1,1,1))
    # )

    # gz.matrix_basis = Matrix.Scale((1, 1, 1)) # takes at least 2 arguments (1 given)

## ! Not working : self.gz_lock_cam.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'

-->
