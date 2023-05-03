# Changelog

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- added: when doing moving actions, key object/cam (respect autokey setting)

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