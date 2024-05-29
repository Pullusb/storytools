# Storytools - Storyboard Tools

Blender addon - Set of tool for storyboarding in Blender

## [Download latest](https://github.com/Pullusb/storytools/archive/master.zip)


<!-- https://github.com/Pullusb/storytools/archive/refs/heads/master.zip -->

![Storytools UI](https://github.com/Pullusb/images_repo/blob/master/storytools_ui_demo.jpg)

Version 1.0 sponsored by [**El Guiri Studios**](https://www.elguiristudios.com/)

---  

## Description

Add a `storytools` Tab in viewport sidebar

> After installation, restart blender once to enable material association handler

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


## Bottom Toolbar

Action gizmo buttons to easily place object and camera
All transform actions respect autokey

<!-- > Note: currently not all actions respects autokey -->

Objects Actions:

- Pan object
- Move object forward/backward
- Rotate object on camera view axis (Ctrl to snap on 15 degrees angles)
- Scale object
- Align object to camera: rotate object to have front axis face view (`-Y` direction)
- key object tranform at current time (note: object, not GP frame)

Camera Actions:

- Pan camera
- Move camera forward/backward
- Toggle _Lock camera to view_
- Key camera position



<!-- ## TODO

-> Create a test storyboard template and check how to load

Modals
- Opt: For all modals, add icon warning if in autokey (same draw func call/stop for all) 

## Ideas
Change Objects canvas colors (very optional)
Set different canvas grid color per object, at generation pick a new color 
Or change it according to depth ? Refreshed when changing object from dedicated UI list

## Map

#### TODO
- [ ] Set 2D openGL draw instead of 3D
- [ ] Hide storytoolbar in map
- [ ] Find a way to enable/disable map mode, should be available in both
- [ ] Create a nav gyzmo for the minimzp
- [ ] opt: Custom Gizmo ? Rotate object (same), rotate/orbit camera (? orbit need point)

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
