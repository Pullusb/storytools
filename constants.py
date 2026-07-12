from pathlib import Path

LAYERMAT_PREFIX = 'mat--'

## Default layer stack for new GP objects: (layer name + default associated material)
DEFAULT_LAYER_STACK = (
    ('Annotate', 'Red'),
    ('Sketch', 'Black'),
    ('Line', 'Black'),
    ('Color', 'White'),
)

DEFAULT_ACTIVE_LAYER = 'Sketch'

## Default material stack for new GP objects
## same_color bool: use the stroke color for both stroke and fill
## holdout bool: Activate holdout for this material
DEFAULT_MATERIAL_STACK = (
    {'name': 'Black', 'stroke_color': (0.0, 0.0, 0.0, 1.0), 'fill_color': (0.0, 0.0, 0.0, 1.0), 'same_color': True, 'holdout': False},
    {'name': 'White', 'stroke_color': (1.0, 1.0, 1.0, 1.0), 'fill_color': (1.0, 1.0, 1.0, 1.0), 'same_color': True, 'holdout': False},
    {'name': 'Grey_light', 'stroke_color': (0.630757, 0.630757, 0.630757, 1.0), 'fill_color': (0.630757, 0.630757, 0.630757, 1.0), 'same_color': True, 'holdout': False},
    {'name': 'Grey_mid', 'stroke_color': (0.361307, 0.361307, 0.361307, 1.0), 'fill_color': (0.361307, 0.361307, 0.361307, 1.0), 'same_color': True, 'holdout': False},
    {'name': 'Grey_dark', 'stroke_color': (0.102242, 0.102242, 0.102242, 1.0), 'fill_color': (0.102242, 0.102242, 0.102242, 1.0), 'same_color': True, 'holdout': False},
    {'name': 'Red', 'stroke_color': (0.7, 0.0, 0.0, 1.0), 'fill_color': (0.7, 0.0, 0.0, 1.0), 'same_color': True, 'holdout': False},
    {'name': 'Blue', 'stroke_color': (0.051, 0.646, 1.0, 1.0), 'fill_color': (0.051, 0.646, 1.0, 1.0), 'same_color': True, 'holdout': False},
    {'name': 'Mask', 'stroke_color': (0.0, 0.0, 0.0, 1.0), 'fill_color': (0.0, 0.0, 0.0, 1.0), 'same_color': True, 'holdout': True},
)

MODULE_DIR = Path(__file__).parent

RESOURCES_DIR = MODULE_DIR / 'resources'

FONT_DIR = RESOURCES_DIR / 'fonts'

PRESETS_DIR = RESOURCES_DIR / 'presets'

IMAGES_DIR = RESOURCES_DIR / 'images'

