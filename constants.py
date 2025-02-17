from pathlib import Path

LAYERMAT_PREFIX = 'mat--'

MODULE_DIR = Path(__file__).parent

APP_TEMPLATES_DIR = MODULE_DIR / 'templates'

STORYBOARD_TEMPLATE_BLEND = APP_TEMPLATES_DIR / 'Storyboard' / 'startup.blend'

DUAL_STORYBOARD_TEMPLATE_BLEND = APP_TEMPLATES_DIR / 'Storyboard_Dual_Window' / 'startup.blend'
