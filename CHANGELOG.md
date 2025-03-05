# Changelog

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

2.8.0

- added: Exclude objects or collections from camera view:
  - located in camera subpanel
  - affect hide viewport and render toggle
  - refresh on active camera change
  - object listed by other cameras but not in current are restore (need to see if behavior is ok)

2.7.0

- added: add place new GP button on Minimap with overlays
- fixed: error on drawing setup
- changed: tiny improvement on map-frame ops when there is no GP (frame all)

2.6.1

- added: Minimap button toolbar (gizmos)
- added: `Map view roll` button in minimap toolbar:
  - Drag left right to rotate the top view
  - Single click to reset to -Y world up
- added: minimap toolbar button to reframe map to see camera and all GP object
- added: minimap toolbar button to popup panel with different view framing choices

2.6.0

- added: overlay line hint when tweaking camera shift, show position of the un-shifted frame in grey lines 
- added: snap on half view-frame using Alt during shift the transform

2.5.0

- added: Adjust focal length or orthographic scale with `Ctrl + Drag` on camera depth move button
- added: Adjust camera shift x/y with `Ctrl + Drag` on camera pan button (auto-lock on `Ctrl` is achieved then by releasing then pressing it again)

2.4.1

- fixed: workspace loading, now load properly with sidebar set.
- added: workspace in new menu for dual window storyboard mode

2.4.0

- added: new feature `Scale figure` overlay:
  - Toggle and options are located in GP overlay popover
  - Default mode display a ruler with a customizable size and subdivision
  - Alternatively can show silhouette of human male/female or cat
  - possible to convert as GP layers on active object to further customize silhouette

2.3.1

- fixed: error relative to asset brush in 4.4: use asset_activate ops instead of deprecated `context.scene.tool_settings.gpencil_paint.brush = br`

2.3.0

- added: Autokey gizmo button (special behavior : set the same autokey state in all scenes)

2.2.0

- added: `Annotate` layer in top of default stack (synced with `line_red` material)
- added: new tool-preset to select Pen tool > "Annotate" layer > line red material.

2.1.2

- fixed: error with 4.4
- fixed: workspace load
- fixed: error when loading toolsettings

2.1.0

- added: Snap cursor gizmo button:
  - `Click`: Cursor to selected
  - `Shift + Click`: Send Selection to cursor
  - `Click-Drag`: Cursor on GP drawing plane or geometry

2.0.0

- Most feature are now ready for gpv3 4.3+ (still wip)
- changed: in camera `Rotate gizmo` button reset rotation on single click (Previously double click)
- changed: when out of camera `Rotate gizmo` button now affect free view (view roll)
  - note: if `Grease pencil tools` addon (on extension platform) is active, use it's custom `rotate canvas` feature 
  - allow to reset free view rotation on single click + fixed angle rotation on `shift`

GPV3

---

1.20.0

- added: Preferences for GP settings behavior.
- added: Control bar pop-up menu on button to change `frame add` and `frame jump` behavior (synced from preferences by default, but can be localized per scene).

1.19.6

- fixed: Transforms on object using child-of constraints

1.19.5

- added: Default placement and orientation preferences to set when creating a new object

1.19.4

- added: initial minimap preferences + improve minimap view 

1.19.3

- added: New options for frame jump gizmo ops:
    - no modifier: jump on keys of active layer
    - +ctrl: jump on keys of visible layers
    - +shift: jump on keys of visible and unlocked layers
    - +ctrl+shift: keys of all layers

1.19.1

- changed: `Align to view` is now z-facing lights, speaker and empty-image objects (previoulsy z-facing text objects)
- fixed: problem with bottom bar alignment

1.19.0

- changed: Lock orbit navigation moved in the camera group, as it is related to view in general

1.18.1

- added: Navigate GP frame button. active layer by default, all accessible (visible and unlocked) when pressing shift
- fixed: bug when using camera zoom with orbit lock

1.17.3

- changed: GP (drawing) object visibility icon show when there is a viewport-rendering conflict
- changed: Better display of camera properties in list
- added: info-hint in drawing's displays toggle channel

1.17.2

- changed: move workspace related operator in a new popup menu in header corner
- added: `Quick reset draw settings` (in workspace panel) button with related section in preferences

1.17.1

- added: GP buttons color preferences with new default color
- fixed: GP Buttons placement
- changed: Partial compatibility with 4.3 (need breaking change for full compatibility)

1.17.0

- added: Extend the control bar with new Grease pencil operators buttons:
 - `New GP frame` : Create new empty GP frame at position. jump forward if a frame exists at cursor. Ctrl + Click apply offset to all subsequent editable frames
 - `New GP frame copy` : Same behavior but copy content of currently active frame 
- added: addon preferences `Default Autolock Layers` set autolock state on new Grease pencils (enabled by default)
- added: addon preferences `Default Layer Use Light` to set Use light state on new created object (disabled by default)
- added: addon preferences `Grease Pencil Frame Offset` interval when offsetting key at creation (if already on a key) or when applying offset to subsequent frames

1.16.4

- fixed: bottom control bar toggle was not disabled correctly by preferences

1.16.3

- added: tool presets `Add` and `Reload UI` in addon preferences with infos

1.16.2

- added: Responsive control bar
- changed: reduced default 'Icon Backdrop Size' and Spreading

1.16.1

- added: submenu for GP settings in list
- changed: More compact and responsive UI for camera list and object list

1.16.0

- added: Origin displayed as cross on move and rotate controls, with previous position as ghost for easier placement
- fixed: Console error when using depth control

1.15.3

- added: addon preferences hide toggle for tool presets bar
- added: addon preferences customize margin and spreading of tool presets bar
- added: add shortcut info in tool presets tooltip

1.15.2

- fixed: Tool preset tab in preferences

1.15.1

- changed: better description for tool presets
- changed: using tool preset add undo step

1.15.0

- added: Upper tool-preset bar to selected existing preset in keymap (WIP)
- removed: experimental tool preset UI in preferences

1.14.2

- added: Button to remove active camera in camera drop-down menu
- fixed: UI properties highlight changing for camera or GP list when adding / removing objects

1.14.1

- fixed: allow object and camera creation on multiple scene

1.14.0

- added: View and tool Setting presets

1.13.0

- added: first version of quick settings restore

1.12.2

- changed: GP list do not show linked datablock infos by default (can be activated in drop down menu)

1.12.1

- fixed: bug when active object is hidden
- added: UI button to select camera target

1.12.0

- added: Custom Camera creation operator
    - choose if new is active (may be removed in future version)
    - choose to add a camera-bound timeline marker
- changed: UI:
    - show GP grid in Layer header
    - removed button to toggle bottom bar (have it's own button)

1.11.0

- added: Easy track to constraints from camera menu

1.10.1

- changed: code refactor

1.10.0

- added: new alternate behavior on `Cam lock to view` switch gizmo, to control view in cam:
  - `Ctrl` : Fit view to camera bounds (CBB state)
  - `Shift` : Zoom 1:1 (full resolution)

1.9.0

- added: `Align to view` has a better redo panel and `bring objects in view` handle multi-object (based on origins)

1.8.12

- added: `Camera rotation` reset using double click on gizmo button
- added: `Shift + Click` on `Align-to-view` bring objects in front of camera

1.8.11

- added: `Camera Depth move` + `Alt` to lock Z axis
- added: Camera rotation gizmo

1.8.10

- changed: draw button swap between object and draw mode when a GP is active

1.8.9

- added: `Translate` and `Depth` moves, pressing `Alt` lock Z world, can help placing on ground

1.8.8

- added: add a "fill_mask" holdout material in default palette 
- changed: set autolock on newly created GP object
- changed: add first keyframe on current frame when creating object (as native behavior)
- fixed: add undo step at draw object creation
- fixed: refresh all viewport areas when toggling toolbar
- fixed: prevent listing GP drawing object prefixed with a dot

1.8.7

- added: choice to use depth move visual hint colors and color personnalisation in preferences

1.8.6

- added: object pan-move lock axis, with `Ctrl` to autolock on direction, same as camera pan

1.8.5

- changed: Better and more standard precision mode for all transforms (keep relative position when swapping Shift key)

1.8.4

- added: Depth visual hint when using `Forward/backward move` on object

1.8.3

- added: dropdown menu for camera settings with focal length tweak and presets (hardcoded for now)
- fixed: better display of lens value in camera UI list

1.8.2

- changed: centered toolbar switch
- fixed: toolbar position with region overlap preferences off

1.8.1

- fixed: margin when headers or asset shelf are at bottom
- added: preference option to change color of active gizmo buttons

1.8.0

- added: `Navigation Lock` (expose native toggle as gizmo button to lock orbit in active viewport)
- added: Alternative shortcuts to use user's _orbits_ shortcuts as secondary _Pan_ during `Navigation Lock`.
- fixed: Camera pan openGL locking lines (API changed in blender 4.0)
 
1.7.0

- added: Object rotate modal operator and gizmo
    - Rotate active object on view axis by dragging left/right from gizmo
    - Shift for precision rotation
    - Ctrl to Snap on 15degrees angle from initial rotation

1.6.2

- changed: more compact bottom bar

1.6.1

- changed: standard shape for bottom bar toggle

1.6.0

- added: long button under bottom bar to toggle it (design will probably change)
- changed: margin from border do not depend on UI scale anymore

1.5.0

- added: GP native panels for Brush, Colors and Palettes appended as subpanels (code from _Nacho de Andrés_)

1.4.0

- changed: UI use subpanels for ability to collapse elements individually

1.3.3

- fixed: preferences keymap display and unreliable restore keymap item

1.3.2

- added: Possibility to add a "Track to" constraint pointing at camera when creating object

1.3.1

- changed: Text objects are aligned "Y up" (rotated 90° on X Axis) using `Align to view` tool. 

1.3.0

- added: Customizable operator shortcut to change tool, brush, layer and material at once with a single key in Grease pencil paint mode.
- added: 6 predefined shortcuts (change in addon prefs):
    - 1: tool=Draw, layer=Sketch
    - 2: tool=Draw, layer=Line
    - 3: tool=Fill, layer=Color
    - 4: tool=Draw, layer=Color
    - 5: tool=Erase, brush=Eraser Point
    - 6: tool=Erase, brush=Eraser Stroke
- added: "line_red" material to the base palette for in-object notes

1.2.2

- added: GP object's list options in a dropdown menu to show/hide objects informations (to let more room for Name when sidebar is used thin)
- changed: rename `Objects` label to `Drawings` (Same name as the automatically created collection)

1.2.1

- changed: changing gp object in Object mode select only active object

1.2.0

- added: (beta) hardcoded shortcuts switch tool / layer / (material) with one key
    - 1: Draw tool, layer Sketch
    - 2: Bucket tool, layer Color
    - 3: Draw tool, layer Color
    - 4: Eraser

1.1.1

- added: Camera uilist can be hided. Allow more space when working on a shot with only one camera
- added: In-front property toggle in object list

1.1.0

- added: Possibility to disable sidebar panel in preferences, some people just need the toolbar. (For now, it also disable Layer/material Synchronisation)
- added: Possibility to rename category tab in preferences

1.0.1

- fixed: camera passepartout sync with draw cam system
- added: Enter in cam view when clicking

1.0.0

- added: camera selection panel with following features:
    - add new camera (add at current view)
    - change active camera on single click
    - show focal length editable/keyable property (with toggle)
    - show passepartout toggle and alpha
    - transfer passepartout values when switching cam
    - full `Draw cam` system support when gp_toolbox is enabled:
        - set draw acam
        - back to main cam
        - reset rotation to main cam

0.9.4

- added: addon-prefs toolbar options:
    - hide bottom toolbar
    - bottom toolbar margin
    - clickable backdrop size
    - distance between buttons
    - button colors
- added: Toolbar toggle at scene level (for quick toggle)
- changed: Calculation to a display buttons
- removed: _Alpha_ statement in bl_info (addon is considered stable and usable in production)

0.9.3

- fixed: wrong UI scaling

0.9.2

- added: Button to activate native `grease pencil tools`
- added: Show `grease pencil tools` main panel at the bottom.
- removed: Experimental dual window setup

0.9.1

- added: Button to key object transform at current time
- fixed: Pan action not respecting auto-key

0.9.0

- fixed: Viewport UI with high-res screens (i.e: retina display)
- fixed: Active object not being selected when changing with GP objects panel
- changed: Depth move apply on whole selection only in object mode (else only active object)
- changed: Color of buttons to grey and dark-grey instead of orange and blue

0.8.7

- changed: More compact UI for object options
- added: Bring back side buttons for layers and materials

0.8.6

- added: Button to load bundled `Storyboard` workspace (show up if not in "Storyboard" tab)
- added: (Experimental) Button to load storypencil setup (show up if storypencil addon is enabled and only one window is opened)

0.8.5

- added: filter to set layer/material sync per object or across all objects (default individual)

0.8.4

- fixed: Layer / material Sync not working
- fixed: Layer / material needing restart after first addon activation

0.8.3

- added: "Lock cam to view" become "Go to Camera view" when out of camera.

0.8.2

- added: Error message when transforms are locked (avoid unwanted transformation)

0.8.1

- added: Camera pan show X/Y lock axis lines when constrained

0.8.0

- added: Update addon from prefs using git when addon is cloned as git repository and OS has git installed

0.7.0

- added: Button in sidebar to Attach/Detach object to/from camera
- added: UI _chain_ icon to show when object is parented in object stack
- added: UI show _grid overlay_ toggle (often used)
- added: when doing moving actions, key object/cam (respect autokey button settinggizmo ). 

0.6.0

- added: Camera forward backward move modal operator and gizmo button
    - Slide left to right to move active forward and backward
    - Shift: Slower move
- added: UI:button colors, bigger buttons backdrop and space.

0.5.0

- added: Object depth move modal operator and gizmo button
    - Ctrl : Adjust Scale (Retain same size in camera framing) 
    - 'M' key: switch between "distance" and "proportional" mode (only useful when pushing multiple objects)

0.4.2

- added: Object pan modal operator and gizmo
- added: Object visibility toggle, auto-sync 3 hide parameters `viewlayer`, `viewport`, `render` (WYSIWYG approach)
- added: Setup for layer-material association at object creation (hardcoded with current default palette)
- added: Object can be renamed on double click in object sidebar stack
- changed: Camera pan modal operator complete rewrite (mode independent):
    - 'X' / 'Y' key to lock on axis during pan
    - Ctrl continuous press : autolock on major Axis
    - Shift continuous press : Precision Pan (Slower)

0.4.1

- added: associate selected material with active layers
- fixed: viewport button gap not adjusting to UI scale 

0.4.0

- added: gizmo button to pan camera
- added: gizmo button to scale active object
- added: gizmo button to realign object
- added: Ctrl + Click on align button to realign keeping world Up

0.3.3

- added: Custom Object list
    - filter to show only GP object 
    - switch object upon selection
    - keep mode across objects
    - Display data user when objects is a linked duplicate 
- added: Layer list
- added: Material list


0.3.2

- added: Reset location and orientation (GP tool settings) when adding a new object
- added: Object creation: choice to use cursor location 
- fixed: Prevent alignement of camera (avoid potential user error when camera is selected)

0.3.0

- added: camera key location/rotation gizmo

0.2.0

- added: Create aligned object operator with config popup
- added: Load default palette (only one currently)
- added: Super basic UI, mostly for testing purposes
- added: properties and preferences for object creation
- added: Realign to view operator
- added: toolbar: gyzmo button "lock camera to view" (only in camera view)

0.1.0

- initial commit


<!--
Added: for new features.
Changed: for changes in existing functionality.
Deprecated: for soon-to-be removed features.
Removed: for now removed features.
Fixed: for any bug fixes.
Security: in case of vulnerabilities.
-->