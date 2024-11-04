# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from .. import fn
# from pprint import pprint as pp

## -*- setup drawing settings *-*
## Set lasso as selection tool
## Reset edit line opacity to prefs default on all GP

## Set same data name as object name (only if single user) ?
## Set opacity at 1.0 and disable pressure ?
## Disable Use light on all GP (at object and Layer level) ?

class STORYTOOLS_OT_setup_drawing(bpy.types.Operator):
    bl_idname = "storytools.setup_drawing"
    bl_label = 'Setup Drawing'
    bl_description = 'Quick setup for drawing-ready experience'
    bl_options = {'REGISTER', 'UNDO'} 

    # def invoke(self, context, event):
    #     self.force = event.ctrl
    #     self.set_world = event.shift
    #     return self.execute(context)

    def execute(self, context):
        scn = context.scene
        prefs = fn.get_addon_prefs()
        # pp(dir(context.tool_settings))
        # print('====')

        # for i in dir(context.tool_settings.gpencil_paint.brush):
        #     if 'brush' in i.lower(): print(i)

        # return {'FINISHED'} # for test mode

        ## Reset edit lines opacity on all GP
        if prefs.set_edit_line_opacity:
            # Iterate in gp datas
            for gp in bpy.data.grease_pencils:
                if not gp.is_annotation:
                    ## Set edit line opacity to 0 on all GP
                    gp.edit_line_color[3] = prefs.default_edit_line_opacity

                ## Disable use light at layer level (need separate prefs)
                # for l in gp.layers:
                #     l.use_lights = False


        ## Set select tool (in edit / sculpt)
        if (tool_id := prefs.set_selection_tool) != 'NONE':
            if context.mode in ("EDIT_GREASE_PENCIL", "SCULPT_GREASE_PENCIL", "EDIT_GREASE_PENCIL", "SCULPT_GREASE_PENCIL"):
                if bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False).idname != tool_id:
                    bpy.ops.wm.tool_set_by_id(name=tool_id)
        
        ## Show sidebar
        if prefs.show_sidebar != 'NONE':
            if context.space_data.show_region_ui and prefs.show_sidebar == 'HIDE':
                context.space_data.show_region_ui = False
                # context.area.spaces.update()
            if not context.space_data.show_region_ui and prefs.show_sidebar == 'SHOW':
                context.space_data.show_region_ui = True
                # context.area.spaces.update()

        ## Set sidebar panel
        if bpy.app.version >= (4,2,0) and prefs.set_sidebar_tab and context.space_data.show_region_ui:
            tab = prefs.sidebar_tab_target
            if not tab.strip():
                tab = 'Storytools'
            
            ## 'active_panel_category' is readonly at first (Then goes to false after operator has finished)
            ## Not working: Try to refresh UI to fix that once sidebar is opened
            # context.area.regions.update()
            # context.screen.update_tag()
            if sidebar := next((r for r in context.area.regions if r.type == 'UI'), None):
                # sidebar.tag_redraw()
                try:
                    # for now, just by pass the error, a second call works...
                    sidebar.active_panel_category = tab
                except AttributeError:
                    pass


        ## Set opacity at 1.0 and disable pressure on current pen (better to create or load specific brushes)
        # br = context.tool_settings.gpencil_paint.brush
        # br.gpencil_settings.use_strength_pressure = False
        # br.gpencil_settings.pen_strength = 1.0

        # Iterate in objects
        # for o in scn.objects:
        #     ## Disable use light at object level
        #     if o.type == 'GREASEPENCIL':
        #         o.use_grease_pencil_lights = False

        ## Set data name from object name if single user ?
        # for obj in bpy.data.objects:
        #     if obj.type in ('GREASEPENCIL', 'GREASEPENCIL'):
        #         gpd = obj.data
        #         if gpd.users == 1 and gpd.name != gp.name:
        #             gpd.name = gp.name

        ## Set Draw mode if current object is selected
        # if context.object.type == 'GREASEPENCIL':
        #     if self.force:
        #         if context.mode != "PAINT_GREASE_PENCIL":
        #             bpy.ops.object.mode_set(mode='PAINT_GREASE_PENCIL')
        
        ## Set Draw tool
        # if context.mode == "PAINT_GREASE_PENCIL":
        #     tool = 'builtin_brush.Draw'
        #     if bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False).idname != tool:
        #         # print('Set lasso tool')
        #         bpy.ops.wm.tool_set_by_id(name=tool)

        # if self.set_world:
        #     world = scn.world
        #     if not world:
        #         world = scn.world = bpy.data.worlds.new('World')
        #     world.use_nodes = True
            
        #     if (bg := world.node_tree.nodes.get("Background")):
        #         bg.inputs[0].default_value = (0.5, 0.5, 0.5, 1.0)

        return {'FINISHED'}


classes = (STORYTOOLS_OT_setup_drawing,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
