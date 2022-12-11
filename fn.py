# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import json
import os
from pathlib import Path

def load_palette(context, filepath, ob=None):
    with open(filepath, 'r') as fd:
        mat_dic = json.load(fd)
    # from pprint import pprint
    # pprint(mat_dic)
    
    if ob is None:
        ob = context.object

    for mat_name, attrs in mat_dic.items():
        curmat = bpy.data.materials.get(mat_name)
        if curmat:
            # exists
            if curmat.is_grease_pencil:
                if curmat not in ob.data.materials[:]: # add only if it's not already there
                    ob.data.materials.append(curmat)
                continue
            else:
                mat_name = mat_name + '.01' # rename to avoid conflict

        ## Create a GP mat
        mat = bpy.data.materials.new(name=mat_name)
        bpy.data.materials.create_gpencil_data(mat)
        
        ob.data.materials.append(mat)
        for attr, value in attrs.items():
            setattr(mat.grease_pencil, attr, value)