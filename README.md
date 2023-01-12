# Storytools - Storyboard Tools

Blender addon - Set of tool for storyboarding in Blender

## [Download latest](https://github.com/Pullusb/storytools/archive/master.zip)

**/!\ Alpha** - Work in progress

Sponsored by [**El Guiri Studios**](https://www.elguiristudios.com/)

<!-- https://github.com/Pullusb/storytools/archive/refs/heads/master.zip -->

 
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

Keep same mode accross object when selecting in this stack

### Special Behavior

When selecting a material, it "stick" to current active layer
(i.e: when selecting this layer again, it will switch back to this material)


### Bottom Toolbar

Action buttons to easily place object and camera

> Note: currently not all actions respects autokey

Objects Actions:

- Pan object
- Move object forward/backward
- Scale object
- Align object to camera 

Camera Actions:

- Pan camera
- Move camera forward/backward
- Toggle _Lock camera to view_
- Key camera position


<!-- ## TODO

-> Create a test storyboard template and check how to load

Modals
- Opt: For all modals, add icon warning if in autokey (same draw func call/stop for all) 

- 

Brush association

## IDEAS

- set different canvas grid color per object or according to depth
    - refreshed when changing object from dedicated UI list

- Set 1,2,3,4 buttons to brushes: Stroke, Fill, Negative Fill, Shadow
    - Need to create custom brushes (import from a blend or create from scratch)
    - Also need change to chosen layer (need to have association choice somewhere).
    - 

- Overview: obj/cam pan and depth move : Show corner minimap... (Big work!)

-->