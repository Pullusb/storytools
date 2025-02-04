from pathlib import Path
LAYERMAT_PREFIX = 'mat--'

MODULE_DIR = Path(__file__).parent
APP_TEMPLATES_DIR = MODULE_DIR / 'templates'
STORYBOARD_TEMPLATE = APP_TEMPLATES_DIR / 'Storyboard' / 'startup.blend'
SEQUENCE_TEMPLATE = APP_TEMPLATES_DIR / 'Sequencer' / 'startup.blend'