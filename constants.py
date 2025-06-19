from pathlib import Path

LAYERMAT_PREFIX = 'mat--'

MODULE_DIR = Path(__file__).parent

RESOURCES_DIR = MODULE_DIR / 'resources'

APP_TEMPLATES_DIR = RESOURCES_DIR / 'templates'

FONT_DIR = RESOURCES_DIR / 'fonts'

PRESETS_DIR = RESOURCES_DIR / 'presets'

STORYBOARD_TEMPLATE_BLEND = APP_TEMPLATES_DIR / 'Storyboard' / 'startup.blend'

DUAL_STORYBOARD_TEMPLATE_BLEND = APP_TEMPLATES_DIR / 'Storyboard_Dual_Window' / 'startup.blend'
