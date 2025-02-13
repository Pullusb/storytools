import bpy
from mathutils import Vector, Matrix
from .figure_shapes import build_scale_figure_shape
from .draw_scale_figure import get_canvas_scale_figure_matrix
import numpy as np
### --- Create as GP layer

def split_vector_chains(vectors):
    """
    Split a sequence of Vector objects into chains where consecutive pairs form connected segments.
    
    Args:
        vectors: A list of Vector objects representing segment endpoints
    
    Returns:
        List of lists, where each sublist contains a chain of connected vectors
    """
    # Check if we have enough vectors to form at least one segment
    if len(vectors) < 2 or len(vectors) % 2 != 0:
        raise ValueError("Vectors list must contain complete segments (pairs of vectors)")
    
    # Convert into pairs of vectors (segments)
    segments = []
    for i in range(0, len(vectors)-1, 2):  # Step by 2 to get pairs
        start_vector = vectors[i]
        end_vector = vectors[i+1]
        segments.append((start_vector, end_vector))
    
    if not segments:
        return []
    
    chains = []
    current_chain = [segments[0][0], segments[0][1]]  # Start first chain with first segment
    
    # Process remaining segments
    for i in range(1, len(segments)):
        start_vector = segments[i][0]
        end_vector = segments[i][1]
        
        # If current segment starts where previous ended
        if start_vector == current_chain[-1]:
            current_chain.append(end_vector)
        else:
            # Start new chain
            chains.append(current_chain)
            current_chain = [start_vector, end_vector]
    
    # Add last chain
    chains.append(current_chain)
    
    return chains

def scale_figure_as_layer():
    """Apply scale figure with current settings as grease pencil layer on active object"""
    # add key at current frame or at timeline start ?)

    ## Get scale figure settings
    settings = bpy.context.scene.storytools_settings
    
    ## Get strokes points
    points = build_scale_figure_shape()
    
    ## Apply canvas matrix and convert to object local coordinates
    canvas_matrix = get_canvas_scale_figure_matrix(bpy.context)
    points = [bpy.context.object.matrix_world.inverted() @ canvas_matrix @ v for v in points]

    obj = bpy.context.object
    if not obj:
        return
    
    gp = obj.data
    if not (layer := gp.layers.get('ScaleFigure')):
        layer = gp.layers.new('ScaleFigure', set_active=False)
        ## Set color and opacity
        layer.tint_factor = 1.0
        layer.tint_color = settings.scale_figure_color[:3]
        layer.opacity = max(settings.scale_figure_opacity, 0.1) # ensure visible
        ## To the bottom of the stack
        gp.layers.move_bottom(layer)

    if not (frame := layer.current_frame()):
        frame = layer.frames.new(bpy.context.scene.frame_current)
    
    # frame.strokes.clear() # clear existing strokes ?    

    # Create the subsegments groups
    chains = split_vector_chains(points)
    
    ## chains is list of point sequence   [[vec3, vec3, vec3, ...], [vec3, vec3, ...]]
    
    ## Add strokes with right number of points
    chains_individual_pt_count = [len(chain) for chain in chains]
    # print('chains_individual_pt_count: ', chains_individual_pt_count)
    
    drawing = frame.drawing
    drawing.add_strokes(chains_individual_pt_count)


    ## Examples
    # slice a range you can just use the slice syntax in python, e.g. positions[start:end] where positions is the numpy array of positions
    # start = drawing.curve_offsets[curve_i]
    # end = drawing.curve_offsets[curve_i + 1]
    # the length of the curve offsets is always one greater than the number of curves so you don't need to do any checks

    ### Set points positions

    # Create the flat list
    ## Directly apply positions on attribute using slice of the point array... (WIP)
    flat_positions = sum(chains, []) # list of vec3
    # length of the curve offsets is always one greater than the number of curves
    start = drawing.curve_offsets[len(drawing.strokes) - len(chains)].value
    end = drawing.curve_offsets[len(drawing.strokes)].value
    for i in range(start, end):
        drawing.attributes['position'].data[i].vector = flat_positions[i-start]
    
    ## Classic loop method on strokes (Works)
    # for i in range(1, len(chains) + 1):
    #     ## iterate from the end to affect only strokes at the end of the stack
    #     idx = -i
    #     chain = chains[idx]
    #     stroke = drawing.strokes[idx]
    #     for pt, coord in zip(stroke.points, chain):
    #         print(coord)
    #         pt.position = coord

    return layer

class STORYTOOLS_OT_bake_scale_figure_as_layer(bpy.types.Operator):
    bl_idname = "storytools.bake_scale_figure_as_layer"
    bl_label = "Bake Scale Figure As Grease Pencil Layer"
    bl_description = "Apply scale figure with current settings as grease pencil layer on active object"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    def execute(self, context):        
        scale_figure_as_layer()
        return {"FINISHED"}


def register():
    bpy.utils.register_class(STORYTOOLS_OT_bake_scale_figure_as_layer)

def unregister():
    bpy.utils.unregister_class(STORYTOOLS_OT_bake_scale_figure_as_layer)
