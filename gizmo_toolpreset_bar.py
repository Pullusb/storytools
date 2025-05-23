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
        # return 'GREASEPENCIL' in context.mode and not fn.is_minimap_viewport(context)
        return context.object and context.object.type == 'GREASEPENCIL' and not fn.is_minimap_viewport(context)

    def setup(self, context):

        self.tool_preset_gizmos = []

        ## Object Pan
        user_keymaps = bpy.context.window_manager.keyconfigs.user.keymaps
        # km = user_keymaps['Grease Pencil Paint Mode']

        ## Only display addon keymap :
        # from .keymaps import addon_keymaps
        # for akm in set([kms[0] for kms in addon_keymaps]):
        #     km = user_keymaps.get(akm.name)
        #     if not km:
        #         continue
        
        ## List available icons to use fallback
        # available_icons = [i.identifier for i in bpy.types.UILayout.bl_rna.functions['prop'].parameters['icon'].enum_items]

        ## List all set_draw_tools keymap
        toolpreset_kmis = fn.get_tool_presets_keymap()

        # for km in user_keymaps:
        #     for kmi in reversed(km.keymap_items):
        #         if kmi.idname == 'storytools.set_draw_tool':

        for _km, kmi in toolpreset_kmis:
            props = kmi.properties
            if not kmi.active or not props.show:
                continue
            gz = self.gizmos.new("GIZMO_GT_button_2d")
            fn.set_gizmo_settings(gz, icon=props.icon, alpha=0, alpha_highlight=0.6) # , alpha=0.4, alpha_highlight=0.5

            op = gz.target_set_operator("storytools.set_draw_tool")
            op.name = props.name
            # op.mode = props.mode # Default Keymap currently limited to Paint mode
            op.tool = props.tool
            op.layer = props.layer
            op.material = props.material
            op.brush = props.brush
            op.description = props.description
            op.shortcut = kmi.to_string() # Shortcut text for description
            self.tool_preset_gizmos.append(gz)

    def draw_prepare(self, context):
        prefs = fn.get_addon_prefs()
        settings = context.scene.storytools_settings
        
        # icon_size = prefs.toolbar_icon_bounds
        gap_size = prefs.presetbar_gap_size
        backdrop_size = prefs.presetbar_backdrop_size
        
        section_separator = 20
        px_scale = context.preferences.system.ui_scale

        ## Toggle on/off with same session as bottom control bar
        for gz in self.gizmos:
            gz.hide = not settings.show_session_toolbar
        if not settings.show_session_toolbar:
            return
        
        region = context.region
        count = len(self.gizmos)

        ## Using only direct offsetn
        self.bar_width = (count - 1) * (gap_size * px_scale) + (section_separator * 2) * px_scale
        # self.bar_width = (count - 1) * (gap_size * px_scale)
        
        ## Need to set upper margin
        vertical_pos = region.height - (prefs.presetbar_margin * px_scale) - fn.get_header_margin(context, bottom=False, overlap=False)
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
    if not fn.get_addon_prefs().active_presetbar:
        return
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    if not fn.get_addon_prefs().active_presetbar:
        return
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
