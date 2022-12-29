# Changelog

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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