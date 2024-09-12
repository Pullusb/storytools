# SPDX-License-Identifier: GPL-3.0-or-later

# Gizmo doc

import bpy
from bpy.types import (
    Operator,
    GizmoGroup,
    Gizmo
    )

from mathutils import Matrix, Vector
from gpu_extras.batch import batch_for_shader

from . import fn


class STORYTOOLS_GGT_toolpreset_bar(GizmoGroup):
    # bl_idname = "STORYTOOLS_GGT_toolbar"
    bl_label = "Story Tool Preset Bar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    @classmethod
    def poll(cls, context):
        # return 'GPENCIL' in context.mode and not fn.is_minimap_viewport(context)
        return context.object and context.object.type == 'GPENCIL' and not fn.is_minimap_viewport(context)

    def setup(self, context):

        self.tool_preset_gizmos = []

        ## Object Pan
        user_keymaps = bpy.context.window_manager.keyconfigs.user.keymaps
        # km = user_keymaps['Grease Pencil Stroke Paint Mode']

        from .keymaps import addon_keymaps

        ## TODO: reorder keymap item from "properties.order"

        for akm in set([kms[0] for kms in addon_keymaps]):
            km = user_keymaps.get(akm.name)
            if not km:
                continue
            for kmi in reversed(km.keymap_items):
                if kmi.idname == 'storytools.set_draw_tool':
                    props = kmi.properties

                    gz = self.gizmos.new("GIZMO_GT_button_2d")
                    fn.set_gizmo_settings(gz, icon=props.icon, alpha=0, alpha_highlight=0.2)
                    op = gz.target_set_operator("storytools.set_draw_tool")
                    op.name = props.name
                    op.mode = props.mode
                    op.tool = props.tool
                    op.layer = props.layer
                    op.material = props.material
                    op.brush = props.brush
                    op.description = props.description
                    self.tool_preset_gizmos.append(gz)

    def draw_prepare(self, context):
        prefs = fn.get_addon_prefs()
        settings = context.scene.storytools_settings
        
        # icon_size = prefs.toolbar_icon_bounds
        gap_size = prefs.toolbar_gap_size
        backdrop_size = 20 # prefs.toolbar_backdrop_size
        
        section_separator = 20
        px_scale = context.preferences.system.ui_scale

        for gz in self.gizmos:
            gz.hide = not settings.show_session_toolbar
        if not settings.show_session_toolbar:
            return
        
        region = context.region
        count = len(self.gizmos)

        ## Using only direct offset
        self.bar_width = (count - 1) * (gap_size * px_scale) + (section_separator * 2) * px_scale
        
        ## Need to set upper margin
        vertical_pos = region.height - ((prefs.toolbar_margin * px_scale) / 2) - fn.get_header_margin(context, bottom=False, overlap=False)
        left_pos = region.width / 2 - self.bar_width / 2
        next_pos = gap_size * px_scale

        for i, gz in enumerate(self.tool_preset_gizmos):
            gz.scale_basis = backdrop_size
            gz.color = (0.4, 0.4, 0.4)
            gz.color_highlight = (0.5, 0.5, 0.5)

            ## Matrix world is readonly
            gz.matrix_basis = Matrix.Translation((left_pos + (i * next_pos), vertical_pos, 0))


classes=(
    STORYTOOLS_GGT_toolpreset_bar,
)

def register():
    # if not fn.get_addon_prefs().active_toolbar:
    #     return
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    # if not fn.get_addon_prefs().active_toolbar:
    #     return
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
