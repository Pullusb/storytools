# Storytools - Storyboard Tools

Blender addon - Set of tool for storyboarding in Blender

Sponsored by [**El Guiri Studios**](https://www.elguiristudios.com/)


**/!\ Alpha** - Work in progress

**[Download latest](https://github.com/Pullusb/storytools/archive/master.zip)**

<!-- https://github.com/Pullusb/storytools/archive/refs/heads/master.zip -->

 
---  

## Description

Quick usage description

Add a `storytools` Tab in viewport sidebar 


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

When select object in stack, keep same mode as previous object


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

Create a test storyboard template 

Object list (UIlist)
- Object are created stored in a `GP` / `Gpencil` / `Drawings` collection (user can manually create sub-collection if needed)

Palette list (Material UIlist + buttons)
- Possibility to move materials

Brush association

## IDEAS

- set canvas grid color according to depth (or based on other information)
    - refreshed when changing object from dedicated UI list

- Set 1,2,3,4 buttons to brushes: Stroke, Fill, Negative Fill, Shadow
    - Need to create custom brushes (import from a blend or create from scratch)
    - Also need change to chosen layer (need to have association choice somewhere).
    - 

- 

-->