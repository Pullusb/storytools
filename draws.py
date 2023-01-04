import bpy
import blf

## Not used yet
def text_draw_callback_px(self, context):
    font_id = 0
    color = [0.8, 0.1, 0.2]
    blf.color(0, *color, 1)
    blf.position(font_id, 15, 100, 0)
    blf.size(font_id, 25, 72)
    # blf.draw(font_id, self.message)
    blf.draw(font_id, 'Test draw')


## Not used yet
def ob_lock_location_cam_draw_panel(self, context):
    '''Display object location settings'''
    layout = self.layout
    layout.use_property_split = True
    col = layout.column()
    row = col.row(align=True)
    row.prop(self.ob, "location")
    row.use_property_decorate = False
    row.prop(self.ob, "lock_location", text="", emboss=False, icon='DECORATE_UNLOCKED')