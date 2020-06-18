bl_info = {
    'name': '3D Comic Toolkit',
    'author': 'Bay Raitt',
    'version': (0, 4),
    'blender': (2, 80, 0),
    "description": "3D Comic Toolkit - requires factory addons: Bool Tool to be activated!! ",
    'category': 'Import-Export',
    'location': 'Spiraloid > 3D Comic',
    'wiki_url': ''
    }

import bpy
import os
import os.path
from bpy_extras.io_utils import ImportHelper
from platform import system
from distutils.dir_util import copy_tree
import glob

from bpy.props import *
import subprocess

import warnings
import re
from itertools import count, repeat
from collections import namedtuple
import math
from math import pi

from bpy.types import Operator
from mathutils import Vector
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    CollectionProperty,
)
from bpy.types import (Panel,
                       PropertyGroup,
                       AddonPreferences
                       )

import bmesh
#------------------------------------------------------

def getCurrentSceneIndex():
    currScene =  bpy.context.scene
    for currSceneIndex in range(0,len(bpy.data.scenes)):
        if bpy.data.scenes[currSceneIndex].name == currScene.name:
            return currSceneIndex

def getCurrentPanelNumber():
    scene_name = bpy.context.window.scene.name
    currSceneIndex = getCurrentSceneIndex()
    panels = []
    for scene in bpy.data.scenes:
        if "p." in scene.name:
            panels.append(scene.name)
    for panel in panels :
        for i in range(len(bpy.data.scenes)):
            if bpy.data.scenes[currSceneIndex].name == panel:
                stringFragments = panel.split('.')
                panel_number = stringFragments[1]
    return panel_number


def getCurrentExportCollection():
    numString = getCurrentPanelNumber()
    export_collection_name = "Export." + numString
    export_collection = bpy.data.collections.get(export_collection_name)
    return export_collection


def getCurrentLetterGroup():
    numString = getCurrentPanelNumber()
    letters_group_name = "Letters_eng." + numString
    letters_group = bpy.data.collections.get(letters_group_name)
    for ob in bpy.data.objects: 
        if ob.name == letters_group_name: 
            return ob
        # else:
        #     report({'ERROR'}, 'No Letters named ' + letters_group_name + ' found under camera') 



def renameAllScenesAfter():
    currScene = getCurrentSceneIndex()

        # panels = []
        # for scene in bpy.data.scenes:
        #     if "p." in scene.name:
        #         panels.append(scene.name)

    for currSceneIndex in range(len(bpy.data.scenes),currScene, -1 ):
        m = currSceneIndex - 1
        if m > currScene:
            if "p." in bpy.data.scenes[m].name:
                scene = bpy.data.scenes[m]
                n = currSceneIndex
                nn = currSceneIndex - 1

                sceneNumber = "%04d" % n
                oldSceneNumber = "%04d" % nn
                scene.name = 'p.'+ str(sceneNumber) + ".w100h100"

                scene_objects = scene.objects
                for obj in scene_objects:
                    if oldSceneNumber in obj.name:
                        obj.name = obj.name.replace(oldSceneNumber, sceneNumber)

                scene_collections = scene.collection.children
                for col in scene_collections:
                    if oldSceneNumber in col.name:
                        col.name = col.name.replace(oldSceneNumber, sceneNumber)

                scene_cameras = scene.collection.children
                for col in scene_collections:
                    if oldSceneNumber in col.name:
                        col.name = col.name.replace(oldSceneNumber, sceneNumber)


    return {'FINISHED'}

def validateComicAssetNames():
    for scene in bpy.data.scenes:
        if "p." in scene.name:
            panels.append(scene.name)
    for panel in panels :
        for i in range(0,len(panels)):
            if bpy.data.scenes[currSceneIndex].name == panel:
                stringFragments = panel.split('.')
                panel_number = stringFragments[1]
            self.report({'INFO'}, 'Panel Names Validated!')
    return {'FINISHED'}



def scene_mychosenobject_poll(self, object):
    return object.type == 'MESH'

def load_resource(blendFileName):
    currSceneIndex = getCurrentSceneIndex()
    scene_collections = bpy.data.scenes[currSceneIndex].collection.children

    user_dir = os.path.expanduser("~")
    common_subdir = "2.90/scripts/addons/3DComicToolkit/Resources/"
    if system() == 'Linux':
        addon_path = "/.config/blender/" + common_subdir
    elif system() == 'Windows':
        addon_path = (
            "\\AppData\\Roaming\\Blender Foundation\\Blender\\"
            + common_subdir.replace("/", "\\")
        )
        # os.path.join()
    elif system() == 'Darwin':
        addon_path = "/Library/Application Support/Blender/" + common_subdir
    addon_dir = user_dir + addon_path
    filepath = addon_dir + blendFileName

    context = bpy.context
    scenes = []
    resourceSceneIndex = 0
    mainCollection = context.scene.collection
    with bpy.data.libraries.load(filepath ) as (data_from, data_to):
        for name in data_from.scenes:
            scenes.append({'name': name})
        action = bpy.ops.wm.append
        action(directory=filepath + "/Scene/", files=scenes, use_recursive=True)
        scenes = bpy.data.scenes[-len(scenes):]

    resourceSceneIndex = -len(scenes)
    if resourceSceneIndex != 0 :
        nextScene =  bpy.data.scenes[resourceSceneIndex]
        loaded_scene_collections = bpy.data.scenes[resourceSceneIndex].collection.children
        
        for coll in loaded_scene_collections:
            bpy.ops.object.make_local(type='ALL')
            bpy.ops.object.select_all(action='DESELECT')
            for obj in coll.all_objects:
                bpy.context.collection.objects.link(obj)  
                obj.select_set(state=True)
                bpy.context.view_layer.objects.active = obj
        bpy.data.scenes.remove(nextScene)


        # for scene in scenes:
        #     for coll in scene.collection.children:
        #         bpy.ops.object.select_all(action='DESELECT')
        #         for obj in coll.all_objects:
        #             bpy.context.collection.objects.link(obj)  
        #             obj.select_set(state=True)
        #             bpy.context.view_layer.objects.active = obj
        #     bpy.data.scenes.remove(scene)

    return {'FINISHED'}

def operator_exists(idname):
    names = idname.split(".")
    print(names)
    a = bpy.ops
    for prop in names:
        a = getattr(a, prop)
    try:
        name = a.__repr__()
    except Exception as e:
        print(e)
        return False
    return True


    return {'FINISHED'}

def automap(mesh_objects, decimate_ratio):
    # UV map target_object if no UV's present


    for mesh_object in mesh_objects:
        if mesh_object.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            bpy.ops.object.select_all(action='DESELECT')
            mesh_object.select_set(state=True)
            bpy.context.view_layer.objects.active = mesh_object
            if not len( mesh_object.data.uv_layers ):
                bpy.ops.mesh.uv_texture_add()
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02, user_area_weight=0.75, use_aspect=True, stretch_to_bounds=True)
                bpy.ops.uv.seams_from_islands()
                bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
                bpy.ops.uv.minimize_stretch(iterations=1024)
                bpy.ops.uv.average_islands_scale()

                # area = bpy.context.area
                # old_type = area.type
                # if bakemesh.data.uv_layers:
                    # area.type = 'IMAGE_EDITOR'
                    # if operator_exists("uvpackmaster2"):
                    #     bpy.context.scene.uvp2_props.pack_to_others = False
                    #     bpy.context.scene.uvp2_props.margin = 0.015
                    #     bpy.ops.uvpackmaster2.uv_pack()
                # if old_type != "":
                    # area.type = old_type
            
            if (decimate_ratio != 1):
                    # bpy.ops.mesh.bisect(plane_co=(0, 0, 0), plane_no=(1, 0, 0), xstart=mesh_object.dimensions[1], xend=mesh_object.dimensions[1], ystart=mesh_object.dimensions[2], yend=mesh_object.dimensions[2])
                    # bpy.ops.mesh.mark_seam(clear=False)
                    # bpy.ops.mesh.select_all(action='SELECT')
                    # bpy.ops.mesh.bisect(plane_co=(0, 0, 0), plane_no=(0, 1, 0), xstart=mesh_object.dimensions[1], xend=mesh_object.dimensions[1], ystart=mesh_object.dimensions[2], yend=mesh_object.dimensions[2])
                    # bpy.ops.mesh.mark_seam(clear=False)
                    # bpy.ops.mesh.select_all(action='SELECT')
                    # bpy.ops.mesh.bisect(plane_co=(0, 0, 0), plane_no=(0, 0, 1), xstart=mesh_object.dimensions[1], xend=mesh_object.dimensions[1], ystart=mesh_object.dimensions[2], yend=mesh_object.dimensions[2])
                    # bpy.ops.mesh.mark_seam(clear=False)
                    # bpy.ops.mesh.select_all(action='SELECT')

                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    bpy.ops.object.modifier_add(type='DECIMATE')
                    bpy.context.object.modifiers["Decimate"].decimate_type = 'DISSOLVE'
                    bpy.context.object.modifiers["Decimate"].angle_limit = 0.0523599
                    bpy.context.object.modifiers["Decimate"].delimit = {'UV'}
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

                    bpy.ops.object.modifier_add(type='TRIANGULATE')
                    bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
                    bpy.context.object.modifiers["Triangulate"].quad_method = 'FIXED'
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Triangulate")


                    bpy.ops.object.modifier_add(type='DECIMATE')
                    bpy.context.object.modifiers["Decimate"].ratio = decimate_ratio
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")


        #select all meshes and pack into one UV set together
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.select_all(action='DESELECT')
        for mesh_object in mesh_objects:
            mesh_object.select_set(state=True)
            bpy.context.view_layer.objects.active = mesh_object

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(margin=0.017)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # raise Exception('stopping script')

    return {'FINISHED'} 


def add_ao(self, context, objects):
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)                
    selected_objects = objects 
    if selected_objects is not None :
        # ob = bpy.context.view_layer.objects.active
        for ob in selected_objects:
            if ob.type == 'MESH':
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = ob
                if ob.active_material is not None:
                    mat =  ob.active_material
                    mat.use_nodes = True
                    ao_group_name = 'AO group'

                    gnodes = [n for n in mat.node_tree.nodes if n.name == ao_group_name]
                    print(gnodes)
                    for g in gnodes:
                        g.select = True
                        matnodes.active = g
                        bpy.ops.node.delete_reconnect()


                    mat_output = mat.node_tree.nodes.get('Material Output')
                    shader_node = mat_output.inputs[0].links[0].from_node


                    group = bpy.data.node_groups.new(type="ShaderNodeTree", name= ao_group_name)

                    #Creating Group Input
                    group.inputs.new("NodeSocketShader", "Input1")
                    group.inputs.new("NodeSocketInterfaceFloat", "AO Intensity")
                    input_node = group.nodes.new("NodeGroupInput")
                    input_node.location = (0, 0)



                    #Creating Group Output
                    group.outputs.new("NodeSocketShader", "Output1")
                    output_node = group.nodes.new("NodeGroupOutput")
                    output_node.location = (500, 0)


                    # Creating Principled bsdf Node
                    #You can create any node here which you think are required to be in the group as these will be created automatically in a group


                    # ao_group = mat.node_tree.nodes.new('ShaderNodeGroup')


                    # # ao_group.name = ao_group_name
                    # ao_group.node_tree = bpy.data.node_groups[mat.node_tree.name] 
                    # # ao_group.node_tree = bpy.data.node_groups['BASE SKP']
                    # D.node_groups['NodeGroup'].nodes['Group Input']
                    
                    # #  relink everything
                    # mat.node_tree.links.new(shader_node.outputs[0], ao_group.inputs[0])
                    # mat.node_tree.links.new(ao_group.outputs[0], mat_output.inputs[0])

                    # # ao_group_input = mat.node_tree.nodes.new('NodeGroupInput')
                    # # ao_group_output = mat.node_tree.nodes.new('NodeGroupOutput')

                    ao = group.nodes.new(type='ShaderNodeAmbientOcclusion')
                    black = group.nodes.new(type='ShaderNodeEmission')
                    mix = group.nodes.new(type='ShaderNodeMixShader')
                    gamma = group.nodes.new(type='ShaderNodeGamma')

                    ao.samples = 4
                    ao.inputs[1].default_value = 0.5

                    black.inputs[0].default_value = (0, 0, 0, 1)


                    mat_output = mat.node_tree.nodes.get('Material Output')
                    existing_shader = mat_output.inputs[0].links[0].from_node


                    group.links.new(ao.outputs[0], gamma.inputs[0])
                    group.links.new(gamma.outputs[0], mix.inputs[0])
                    group.links.new(black.outputs[0], mix.inputs[1])
                    # group.links.new(existing_shader.outputs[0], mix.inputs[2])
                    group.links.new(input_node.outputs[0], mix.inputs[2])
                    group.links.new(mix.outputs[0], mat_output.inputs[0])


                    #creating links between nodes in group
                    group.links.new(input_node.outputs[1], gamma.inputs[1])
                    group.links.new(mix.outputs[0], output_node.inputs[0])

                    # Putting Node Group to the node editor
                    tree = bpy.context.object.active_material.node_tree
                    group_node = tree.nodes.new("ShaderNodeGroup")
                    group_node.node_tree = group
                    group_node.location = (-40,0)

                    #connections bewteen node group to output 
                    links = tree.links    
                    link = links.new(group_node.outputs[0], mat_output.inputs[0])
                    link = links.new(shader_node.outputs[0], group_node.inputs[0])

                    #setup material slider ranges
                    group.inputs[1].name = "AO Intensity"
                    group.inputs[1].default_value = 3
                    group.inputs[1].min_value = 0
                    group.inputs[1].max_value = 50
                # else:
                #     self.report({'ERROR'}, 'You must have a material assigned first!')
                    
        for ob in selected_objects:
            ob.select_set(state=True)
            bpy.context.view_layer.objects.active = ob
    return {'FINISHED'}

def outline(mesh_objects):
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='DESELECT')

    # UV map target_object if no UV's present
    for mesh_object in mesh_objects:
        ink_thickness = mesh_object.dimensions[1] * -0.07
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.select_all(action='DESELECT')
        mesh_object.select_set(state=True)
        bpy.context.view_layer.objects.active = mesh_object
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.select_all(action='SELECT')
        ink_thickness_vgroup_name = "Ink_Thickness"
        mesh_object.vertex_groups.new(name = ink_thickness_vgroup_name)
        ink_thickness_vgroup = mesh_object.vertex_groups[-1]
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        bpy.ops.object.select_all(action='DESELECT')
        mesh_object.select_set(state=True)
        bpy.context.view_layer.objects.active = mesh_object


        ink_thick_tex_name = "InkThickness"
        ink_thick_tex_slot = bpy.data.textures.new(ink_thick_tex_name, type='CLOUDS')
        ink_thick_tex = bpy.data.textures[ink_thick_tex_name]
        ink_thick_tex.noise_type = 'SOFT_NOISE'
        ink_thick_tex.noise_scale = 0.15
        ink_thick_tex.noise_depth = 0
        ink_thick_tex.nabla = 0.001

        ink_thick_mod = mesh_object.modifiers.new(name = 'InkThickness', type = 'VERTEX_WEIGHT_EDIT')
        ink_thick_mod.vertex_group = ink_thickness_vgroup.name
        ink_thick_mod.default_weight = 0
        ink_thick_mod.normalize = False
        ink_thick_mod.falloff_type = 'STEP'
        ink_thick_mod.invert_falloff = True
        ink_thick_mod.mask_constant = 1
        ink_thick_mod.mask_texture = ink_thick_tex
        ink_thick_mod.mask_tex_use_channel = 'INT'
        ink_thick_mod.mask_tex_mapping = 'LOCAL'


        white_outline_mod = mesh_object.modifiers.new(name = 'WhiteOutline', type = 'SOLIDIFY')
        white_outline_mod.use_flip_normals = True
        white_outline_mod.thickness = ink_thickness / 3.2
        white_outline_mod.offset = -1
        white_outline_mod.material_offset = 2
        white_outline_mod.vertex_group = ink_thickness_vgroup.name
        white_outline_mod.show_in_editmode = False

        black_outline_mod = mesh_object.modifiers.new(name = 'BlackOutline', type = 'SOLIDIFY')
        black_outline_mod.use_flip_normals = True
        black_outline_mod.thickness = ink_thickness 
        black_outline_mod.offset = -1
        black_outline_mod.material_offset = 1
        black_outline_mod.vertex_group = ink_thickness_vgroup.name
        black_outline_mod.show_in_editmode = False



        # bpy.context.object.material_slots[1].link = 'DATA'
        # bpy.ops.object.material_slot_add()
        if mesh_object.active_material is None:
            assetName = mesh_object.name
            matName = (assetName + "Mat")
            mat = bpy.data.materials.new(name=matName)
            mat.use_nodes = True
            mat_output = mat.node_tree.nodes.get('Material Output')
            shader = mat_output.inputs[0].links[0].from_node
            nodes = mat.node_tree.nodes
            for node in nodes:
                if node.type != 'OUTPUT_MATERIAL': # skip the material output node as we'll need it later
                    nodes.remove(node) 

            shader = mat.node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')
            shaderToRGB_A = mat.node_tree.nodes.new(type='ShaderNodeShaderToRGB')
            shaderToRGB_B = mat.node_tree.nodes.new(type='ShaderNodeShaderToRGB')
            shaderToRGB_C = mat.node_tree.nodes.new(type='ShaderNodeShaderToRGB')
            ramp_A = mat.node_tree.nodes.new(type='ShaderNodeValToRGB')
            ramp_B = mat.node_tree.nodes.new(type='ShaderNodeValToRGB')
            ramp_C = mat.node_tree.nodes.new(type='ShaderNodeValToRGB')
            light_path = mat.node_tree.nodes.new(type='ShaderNodeLightPath')
            mix_shader = mat.node_tree.nodes.new(type='ShaderNodeMixShader')


            shader.inputs[0].default_value = (1, 1,1, 1) # base color
            ramp_A.color_ramp.elements[0].position = 0.00
            ramp_A.color_ramp.elements[1].position = 0.09
            ramp_A.color_ramp.interpolation = 'CONSTANT'
            ramp_B.color_ramp.elements[0].position = 0.00
            ramp_B.color_ramp.elements[1].position = 0.09
            ramp_B.color_ramp.interpolation = 'CONSTANT'
            ramp_C.color_ramp.elements[0].position = 0.00
            ramp_C.color_ramp.elements[1].position = 0.09
            ramp_C.color_ramp.interpolation = 'CONSTANT'



            mat.node_tree.links.new(shader.outputs[0], shaderToRGB_A.inputs[0])
            mat.node_tree.links.new(shaderToRGB_A.outputs[0], ramp_C.inputs[0])
            mat.node_tree.links.new(ramp_C.outputs[0], mix_shader.inputs[2])
            mat.node_tree.links.new(light_path.outputs[0], mix_shader.inputs[0])
            mat.node_tree.links.new(mix_shader.outputs[0], shaderToRGB_B.inputs[0])
            mat.node_tree.links.new(shaderToRGB_B.outputs[0], ramp_A.inputs[0])
            mat.node_tree.links.new(ramp_A.outputs[0], shaderToRGB_C.inputs[0])
            mat.node_tree.links.new(shaderToRGB_C.outputs[0], ramp_B.inputs[0])
            mat.node_tree.links.new(ramp_B.outputs[0], mat_output.inputs[0])

            # Assign it to object
            if mesh_object.data.materials:
                mesh_object.data.materials[0] = mat
            else:
                mesh_object.data.materials.append(mat)




        OutlineMatName = "BlackOutline"
        matName = (OutlineMatName + "Mat")
        mat = bpy.data.materials.new(name=matName)
        mesh_object.data.materials.append(mat)             
        mat.use_nodes = True
        mat_output = mat.node_tree.nodes.get('Material Output')
        shader = mat_output.inputs[0].links[0].from_node
        nodes = mat.node_tree.nodes
        for node in nodes:
            if node.type != 'OUTPUT_MATERIAL': # skip the material output node as we'll need it later
                nodes.remove(node) 
        shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
        shader.name = "Background"
        shader.label = "Background"
        shader.inputs[0].default_value = (0, 0, 0, 1)
        mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])

        mat.use_backface_culling = True
        mat.shadow_method = 'NONE'

        OutlineMatName = "WhiteOutline"
        matName = (OutlineMatName + "Mat")
        mat = bpy.data.materials.new(name=matName)
        mesh_object.data.materials.append(mat)             
        mat.use_nodes = True
        mat_output = mat.node_tree.nodes.get('Material Output')
        shader = mat_output.inputs[0].links[0].from_node
        nodes = mat.node_tree.nodes
        for node in nodes:
            if node.type != 'OUTPUT_MATERIAL': # skip the material output node as we'll need it later
                nodes.remove(node) 
        shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
        shader.name = "Background"
        shader.label = "Background"
        shader.inputs[0].default_value = (1, 1, 1, 1)
        mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])
        mat.use_backface_culling = True
        mat.shadow_method = 'NONE'


        # add custom property
        mesh_object["is_toon_shaded"] = 1





        # raise Exception('stopping script')

        return {'FINISHED'} 

def empty_trash(self, context):
    for block in bpy.data.collections:
        if not block.users:
            bpy.data.collections.remove(block)

    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)

    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)

    for block in bpy.data.actions:
        if block.users == 0:
            bpy.data.actions.remove(block)

    for block in bpy.data.lights:
        if block.users == 0:
            bpy.data.lights.remove(block)

    for block in bpy.data.curves:
        if block.users == 0:
            bpy.data.curves.remove(block)

    for block in bpy.data.cameras:
        if block.users == 0:
            bpy.data.cameras.remove(block)

    for block in bpy.data.grease_pencils:
        if block.users == 0:
            bpy.data.grease_pencils.remove(block)

    for block in bpy.data.texts:
        if block.users == 0:
            bpy.data.texts.remove(block)

    for block in bpy.data.fonts:
        if block.users == 0:
            bpy.data.fonts.remove(block)

    for block in bpy.data.libraries:
        if block.users == 0:
            bpy.data.libraries.remove(block)


    return {'FINISHED'}

#------------------------------------------------------


def reset_blender():
    return {'FINISHED'}



class ComicPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    assets_folder = StringProperty(
            name="Assets Folder",
            subtype='DIR_PATH',
            )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Location for Spiraloid Template Assets")
        layout.prop(self, "assets_folder")


class BR_OT_new_3d_comic(bpy.types.Operator):
    """Start a new 3D Comic from scratch"""
    bl_idname = "view3d.spiraloid_new_3d_comic"
    bl_label = "New 3D Comic..."
    bl_options = {'REGISTER', 'UNDO'}

    # bpy.ops.wm.read_homefile('INVOKE_DEFAULT')


    def execute(self, context):
        bpy.ops.wm.read_homefile(use_empty=True)
        # load_resource("comic_default.blend")
        # context.window.scene = scene

        currScene = getCurrentSceneIndex()
        bpy.data.scenes[currScene].name = "Back Stage"

        # panels = []
        # for scene in bpy.data.scenes:
        #     if "p." in scene.name:
        #         panels.append(scene.name)

        # for panel in panels :
        #     for i in range(len(bpy.data.scenes)):
        #         if bpy.data.scenes[i].name == panel:
        #             m = currSceneIndex - 1
        #             if m > currSceneIndex:
        #                 sceneNumber = "%04d" % m
        #                 bpy.data.scenes[m].name = 'p.'+ str(sceneNumber)


        #create scene collection
        shared_assets_collection_name = "Shared Assets"
        shared_assets_collection = bpy.data.collections.new(shared_assets_collection_name)
        bpy.context.scene.collection.children.link(shared_assets_collection)  

        #create subcollection
        cname = "Actors"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Creatures"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Figurines"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Items"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Lights"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Materials"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Places"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Props"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Sounds"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Vehicles"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "Vfx"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)
        cname = "World_Props"
        c = bpy.data.collections.new(cname)
        shared_assets_collection.children.link(c)


        angle=math.radians(90.0)
        bpy.ops.object.camera_add(enter_editmode=False, align='WORLD', location=(0, -12, 1.52), rotation=(angle, 0, 0), scale=(1, 1, 1))
        
        # firstPanelName = 'p.0001'
        # newScene = bpy.ops.scene.new(type='NEW')
        # firstPanelSceneIndex = getCurrentSceneIndex()
        # bpy.data.scenes[firstPanelSceneIndex].name = firstPanelName

        # this crashes for some unknown reasion
        # BR_OT_insert_comic_scene.execute(self, context)


        return {'FINISHED'}

class BR_OT_first_panel_scene(bpy.types.Operator):
    """make first panel scene the active scene"""
    bl_idname = "view3d.spiraloid_3d_comic_first_panel"
    bl_label ="First"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.window.scene = bpy.data.scenes[0]
        return {'FINISHED'}

class BR_OT_last_panel_scene(bpy.types.Operator):
    """make last panel scene the active scene"""
    bl_idname = "view3d.spiraloid_3d_comic_last_panel"
    bl_label ="Last"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        totalScenes = len(bpy.data.scenes) - 1
        bpy.context.window.scene = bpy.data.scenes[totalScenes]
        return {'FINISHED'}

class BR_OT_next_panel_scene(bpy.types.Operator):
    """make next panel scene the active scene"""
    bl_idname = "view3d.spiraloid_3d_comic_next_panel"
    bl_label ="Next"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        index = 0
        totalScenes = len(bpy.data.scenes)
        currScene = getCurrentSceneIndex()
        nextScene = currScene + 1

        # print ('totalScenes is : ', totalScenes)
        print ('currScene is : ', currScene)
        print ('nextScene is : ', nextScene)
        
        if nextScene == totalScenes:
            index = 0
        else:
            index = nextScene
        # print ('index is : ',  index)
        bpy.context.window.scene = bpy.data.scenes[index]


        return {'FINISHED'}

class BR_OT_previous_panel_scene(bpy.types.Operator):
    """make previous panel scene the active scene"""
    bl_idname = "view3d.spiraloid_3d_comic_previous_panel"
    bl_label ="Previous"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        index = 0
        totalScenes = len(bpy.data.scenes)
        currScene = getCurrentSceneIndex()
        prevScene = currScene -1

        print ('totalScenes is : ', totalScenes)
        print ('currScene is : ', currScene)
        
        if currScene == 0:
            index = totalScenes -1
        else:
            index = prevScene
            print ('index is : ',  index)
        bpy.context.window.scene = bpy.data.scenes[index]

        return {'FINISHED'}

# class BR_OT_clone_comic_scene(bpy.types.Operator):
#     """ Insert a new panel scene after the currently active panel scene, copying contents"""
#     bl_idname = "view3d.spiraloid_3d_comic_clone_panel"
#     bl_label ="Clone"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#         currSceneIndex = getCurrentSceneIndex()
#         panels = []
#         for scene in bpy.data.scenes:
#             if "p." in scene.name:
#                 panels.append(scene.name)

#         for panel in panels :
#             for i in range(len(bpy.data.scenes)):
#                 if bpy.data.scenes[i].name == panel:
#                     m = currSceneIndex - 1
#                     if m > currSceneIndex:
#                         sceneNumber = "%04d" % n
#                         bpy.data.scenes[m].name = 'p.'+ str(sceneNumber)

#         resourceSceneIndex = currSceneIndex + 1
#         resourceSceneIndexPadded = "%04d" % resourceSceneIndex
#         targetSceneName = 'p.'+ str(resourceSceneIndexPadded)
#         newScene = bpy.ops.scene.new(type='FULL_COPY')
#         bpy.data.scenes[newSceneIndex].name = targetSceneName
#         bpy.context.window.scene = bpy.data.scenes[resourceSceneIndex]
#         BR_OT_panel_init.execute(self, context)


#         return {'FINISHED'}


class BR_OT_clone_comic_scene(bpy.types.Operator):
    """ Insert a new panel scene after the currently active panel scene, copying contents"""
    bl_idname = "view3d.spiraloid_3d_comic_clone_panel"
    bl_label ="Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currSceneIndex = getCurrentSceneIndex()
        renameAllScenesAfter()
        newSceneIndex = currSceneIndex + 1
        sceneNumber = "%04d" % newSceneIndex
        newSceneName = 'p.'+ str(sceneNumber) + ".w100h100"
        newScene = bpy.ops.scene.new(type='FULL_COPY')
        bpy.context.scene.name = newSceneName
        
        # BR_OT_panel_init.execute(self, context)

        bpy.ops.object.select_all(action='DESELECT')

        currScene =  bpy.data.scenes[newSceneIndex]
        currsceneName = currScene.name
        panelSceneName = 'p.'+ str(sceneNumber) + ".w100h100"

        export_collection_name = "Export." + str(sceneNumber) 
        wip_collection_name = "Wip." + str(sceneNumber) 
        lighting_collection_name = "Lighting." + str(sceneNumber) 
        scene_collections = bpy.data.scenes[newSceneIndex].collection.children

        for c in scene_collections:
            if "Export." in c.name:
                export_collection = c
                c.name = export_collection_name
            if "Wip." in c.name:
                wip_collection = c
                c.name = wip_collection_name
            if "Lighting." in c.name:
                c.name = lighting_collection_name

        # export_collection =  bpy.data.collections.get(export_collection_name)
        # if not export_collection:
        #     export_collection =  bpy.data.collections.new(export_collection_name)
        #     bpy.context.scene.collection.children.link(export_collection)

        # wip_collection = bpy.data.collections.get(wip_collection_name)
        # if not wip_collection:
        #     wip_collection = bpy.data.collections.new(wip_collection_name)
        #     bpy.context.scene.collection.children.link(wip_collection)

        objects = export_collection.objects
        for obj in objects:
            if "Camera." in obj.name:
                bpy.context.scene.camera = bpy.data.objects[obj.name]
                obj.name = 'Camera.'+ str(sceneNumber)
            if "Camera_aim." in obj.name:
                obj.name = 'Camera_aim.'+ str(sceneNumber)
            if "Letters_eng." in obj.name:
                obj.name = 'Letters_eng.'+ str(sceneNumber)
            if "Lighting." in obj.name:
                obj.name = 'Lighting.'+ str(sceneNumber)

        bpy.context.scene.cursor.location[2] = 1.52


        return {'FINISHED'}



class BR_OT_insert_comic_scene(bpy.types.Operator):
    """ Insert a new panel scene after the currently active panel scene"""
    bl_idname = "view3d.spiraloid_3d_comic_create_panel"
    bl_label ="Insert New..."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currSceneIndex = getCurrentSceneIndex()
        renameAllScenesAfter()
        # panels = []
        # for scene in bpy.data.scenes:
        #     if "p." in scene.name:
        #         panels.append(scene.name)

        # for panel in panels :
        #     for i in range(len(bpy.data.scenes)):
        #         if bpy.data.scenes[i].name == panel:
        #             m = currSceneIndex - 1
        #             if m > currSceneIndex:
        #                 sceneNumber = "%04d" % m
        #                 bpy.data.scenes[m].name = 'p.'+ str(sceneNumber)

        newSceneIndex = currSceneIndex + 1
        newSceneIndexPadded = "%04d" % newSceneIndex
        newSceneName = 'p.'+ str(newSceneIndexPadded) + ".w100h100"
        newScene = bpy.ops.scene.new(type='NEW')
        bpy.context.scene.name = newSceneName
        BR_OT_panel_init.execute(self, context)


        return {'FINISHED'}

class BR_OT_delete_comic_scene(bpy.types.Operator):
    """ Delete currently active panel scene"""
    bl_idname = "view3d.spiraloid_3d_comic_delete_panel"
    bl_label ="Delete"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currScene = getCurrentSceneIndex()
        bpy.ops.scene.delete()
        for currSceneIndex in range(len(bpy.data.scenes) + 1):
            if currSceneIndex > currScene:
                m = currSceneIndex - 1
                sceneNumber = "%04d" % m
                bpy.data.scenes[m].name = 'Scene_'+ str(sceneNumber)
        return {'FINISHED'}

class BR_OT_reorder_scene_later(bpy.types.Operator):
    """Shift current scene later, changing the read order of panel scenes"""
    bl_idname = "view3d.spiraloid_3d_comic_reorder_scene_later"
    bl_label ="Shift Scene Later"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currSceneIndex = getCurrentSceneIndex()
        panels = []
        for scene in bpy.data.scenes:
            if "p." in scene.name:
                panels.append(scene.name)

        for panel in panels :
            for i in range(len(bpy.data.scenes)):
                if bpy.data.scenes[i].name == panel:
                    swapSceneIndex == currSceneIndex + 1
                    if i == swapSceneIndex :
                        bpy.data.scenes[currSceneIndex].name = "foo"
                        sceneNumber = "%04d" % currSceneIndex
                        bpy.data.scenes[i].name = 'p.'+ str(sceneNumber)


        # for sceneIndex in range(len(panels),currScene, -1 ):
        #     if sceneIndex > currScene:
        #         n = sceneIndex
        #         sceneNumber = "%04d" % n
        #         bpy.data.scenes[sceneIndex].name = 'p.'+ str(sceneNumber)
            # if m == currScene + 1:
            #     sceneNumber = "%04d" % m
            #     currentSceneNumber = "%04d" % currScene
            #     bpy.data.scenes[currScene].name = "tmp"
            #     bpy.data.scenes[m].name = 'p.'+ str(currentSceneNumber)
            #     bpy.data.scenes[currScene].name = 'p.'+ str(sceneNumber)

        return {'FINISHED'}

class BR_OT_reorder_scene_earlier(bpy.types.Operator):
    """Shift current scene Earlier, changing the read order of panel scenes"""
    bl_idname = "view3d.spiraloid_3d_comic_reorder_scene_earlier"
    bl_label ="Shift Scene Earlier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}

class BR_OT_add_letter_caption(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_caption"
    bl_label ="Add Caption"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        export_collection = getCurrentExportCollection()
        active_camera = bpy.context.scene.camera
        if active_camera is not None :
            active_camera_name = active_camera.name
        else:
            self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)

        bpy.ops.object.select_all(action='DESELECT')
        # load_resource("letter_wordballoon.blend")
        load_resource("letter_caption.blend")
        # load_resource("letter_sfx.blend")

        objects = bpy.context.selected_objects
        if objects is not None :
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        letter = objects[0]
        letter_group = getCurrentLetterGroup()

        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        letter_group.select_set(state=True)
        bpy.context.view_layer.objects.active = letter_group
        # bpy.ops.object.parent_set()
        bpy.ops.object.parent_no_inverse_set()

        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        bpy.context.view_layer.objects.active = letter
        bpy.ops.object.origin_clear()

        camera_position = active_camera.matrix_world.to_translation()

        for obj in objects:
            export_collection.objects.link(obj)
            bpy.context.collection.objects.unlink(obj) 

        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        bpy.context.view_layer.objects.active = letter

        return {'FINISHED'}

class BR_OT_add_letter_wordballoon(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_wordballoon"
    bl_label ="Add Wordballoon"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        export_collection = getCurrentExportCollection()
        active_camera = bpy.context.scene.camera
        if active_camera is not None :
            active_camera_name = active_camera.name
        else:
            self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)

        bpy.ops.object.select_all(action='DESELECT')
        load_resource("letter_wordballoon.blend")
        # load_resource("letter_caption.blend")
        # load_resource("letter_sfx.blend")

        objects = bpy.context.selected_objects
        if objects is not None :
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        letter = objects[0]
        letter_group = getCurrentLetterGroup()

        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        letter_group.select_set(state=True)
        bpy.context.view_layer.objects.active = letter_group
        # bpy.ops.object.parent_set()
        bpy.ops.object.parent_no_inverse_set()

        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        bpy.context.view_layer.objects.active = letter
        bpy.ops.object.origin_clear()

        camera_position = active_camera.matrix_world.to_translation()

        for obj in objects:
            export_collection.objects.link(obj)
            bpy.context.collection.objects.unlink(obj) 

        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        bpy.context.view_layer.objects.active = letter

        return {'FINISHED'}

class BR_OT_add_letter_sfx(bpy.types.Operator):
    """Add a new sfx with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_sfx"
    bl_label ="Add Sfx"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        export_collection = getCurrentExportCollection()
        active_camera = bpy.context.scene.camera
        if active_camera is not None :
            active_camera_name = active_camera.name
        else:
            self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)

        bpy.ops.object.select_all(action='DESELECT')
        # load_resource("letter_wordballoon.blend")
        # load_resource("letter_caption.blend")
        load_resource("letter_sfx.blend")

        objects = bpy.context.selected_objects
        if objects is not None :
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        letter = objects[0]
        letter_group = getCurrentLetterGroup()

        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        letter_group.select_set(state=True)
        bpy.context.view_layer.objects.active = letter_group
        # bpy.ops.object.parent_set()
        bpy.ops.object.parent_no_inverse_set()

        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        bpy.context.view_layer.objects.active = letter
        bpy.ops.object.origin_clear()

        camera_position = active_camera.matrix_world.to_translation()

        for obj in objects:
            export_collection.objects.link(obj)
            bpy.context.collection.objects.unlink(obj) 

        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        bpy.context.view_layer.objects.active = letter

        return {'FINISHED'}



class BR_OT_panel_init(bpy.types.Operator):
    """Add a new ground disc with falloff"""
    bl_idname = "view3d.spiraloid_3d_comic_panel_init"
    bl_label ="Initialize"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currSceneIndex = getCurrentSceneIndex()
        sceneNumber = "%04d" % currSceneIndex
        bpy.ops.object.select_all(action='DESELECT')

        # panels = []
        # for scene in bpy.data.scenes:
        #     if "p." in scene.name:
        #         panels.append(scene.name)

        # for panel in panels :
        #     for i in range(len(bpy.data.scenes)):
        #         if bpy.data.scenes[i].name == panel:
        #             m = currSceneIndex - 1
        #             if m > currSceneIndex:
        #                 sceneNumber = "%04d" % m
        #                 bpy.data.scenes[m].name = 'p.'+ str(sceneNumber)


        currScene =  bpy.data.scenes[currSceneIndex]
        currsceneName = currScene.name
        panelSceneName = 'p.'+ str(sceneNumber) + ".w100h100"

        # if panelSceneName != currsceneName:
        bpy.data.scenes[currSceneIndex].name = panelSceneName
        # currsceneName = currScene.name

        # for c in bpy.data.collections:
        #     if c.name is export_collection_name:


        wip_collection_name = "Wip." + sceneNumber
        export_collection_name = "Export." + sceneNumber
        scene_collections = bpy.data.scenes[currSceneIndex].collection.children

        for c in scene_collections:
            if c.name == export_collection_name:
                print ("Removing existing export collection")
                bpy.data.scenes[currSceneIndex].collection.children.unlink(c)
                bpy.data.collections.remove(c)
                bpy.ops.outliner.orphans_purge()


        wip_collection = bpy.data.collections.new(wip_collection_name)
        export_collection =  bpy.data.collections.new(export_collection_name)
        bpy.context.scene.collection.children.link(wip_collection)
        bpy.context.scene.collection.children.link(export_collection)
        # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[wip_collection_name]

        # load selected scene
        load_resource("panel_default.blend")

        # link imported collection to scene so it shows up in outliner
        loaded_export_collection_name =  "Export.TEMPLATE"
        loaded_export_collection = bpy.data.collections.get(loaded_export_collection_name)

        # bpy.data.scenes[currSceneIndex].collection.children.link(export_collection_name)

        objects = bpy.context.selected_objects
        # objects = loaded_export_collection.all_objects
        for obj in objects:
            # try :
            #     # loaded_export_collection.objects.unlink(obj)
            #     bpy.data.collections[loaded_export_collection_name].objects.unlink(obj)
            # except:
            #     pass
            try:
                bpy.context.scene.collection.objects.unlink(obj)
            except:
                pass
            
            for c in bpy.data.collections:
                try:
                    c.objects.unlink(obj)
                except:
                    pass
            export_collection.objects.link(obj)   
            # bpy.data.collections[export_collection_name].objects.link(obj)
        objects = export_collection.objects
        for obj in objects:
            if "Camera." in obj.name:
                bpy.context.scene.camera = bpy.data.objects[obj.name]
                obj.name = 'Camera.'+ str(sceneNumber)
            if "Camera_aim." in obj.name:
                obj.name = 'Camera_aim.'+ str(sceneNumber)
            if "Letters_eng." in obj.name:
                obj.name = 'Letters_eng.'+ str(sceneNumber)

    
    



        # library = bpy.data.libraries['panel_default.blend']
        # for usid in  library.users_id:
        #     usid.user_clear()

        # for library in bpy.data.libraries:
        #     bpy.data.libraries.

        bpy.context.scene.frame_start = 1 
        bpy.context.scene.frame_end = 72
        bpy.context.scene.cursor.location[2] = 1.52


        return {'FINISHED'}


class BR_OT_panel_init_workshop_lighting(bpy.types.Operator):
    """initialize with workshop lighting"""
    bl_idname = "view3d.spiraloid_3d_comic_init_workshop_lighting"
    bl_label ="Lightkit"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currSceneIndex = getCurrentSceneIndex()
        sceneNumber = "%04d" % currSceneIndex

        bpy.ops.object.select_all(action='DESELECT')

        lighting_collection_name =  "Lighting." + str(sceneNumber) 
        lighting_collection = bpy.data.collections.get(lighting_collection_name)
        if lighting_collection:
            bpy.data.collections.remove(lighting_collection)
            empty_trash(self, context)

        lighting_collection = bpy.data.collections.new(lighting_collection_name)
        bpy.context.scene.collection.children.link(lighting_collection)


        active_camera = bpy.context.scene.camera
        if active_camera:
            active_camera_name = active_camera.name

        # load_resource("lighting_workshop.blend")

        # if objects is not None :
        #     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # letter = objects[0]
        # letter_group = getCurrentLetterGroup()


        lighting_group_name = "Lighting." + str(sceneNumber)

        keylight_name = "Key." + str(sceneNumber)
        rim_name = "Rim." + str(sceneNumber)
        back_name = "Back." + str(sceneNumber)
        fill_name = "Fill." + str(sceneNumber)
        bouncelight_name = "Bounce." + str(sceneNumber)
        sky_name = "Sky." + str(sceneNumber)


        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.scenes[currSceneIndex].objects:
            if lighting_group_name in obj.name: 
                bpy.ops.object.select_all(action='DESELECT')
                obj.select = True
                for c in obj.children:
                    c.select = True
                bpy.ops.object.delete(use_global=False)
                empty_trash(self, context)
                self.report({'INFO'}, 'Deleted Previous Lighting!')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add(type='SPHERE', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
        lighting_group = bpy.context.active_object
        lighting_group.name = lighting_group_name

        lighting_group.show_in_front = True
        lighting_group.empty_display_size = 0.1

        if active_camera:
            active_camera.select_set(state=True)
            bpy.context.view_layer.objects.active = active_camera
            bpy.ops.object.parent_no_inverse_set()
        lighting_collection.objects.link(lighting_group)
        bpy.context.collection.objects.unlink(lighting_group)

        bpy.ops.object.select_all(action='DESELECT')
        lighting_group.select_set(state=True)

        for obj in bpy.data.scenes[currSceneIndex].objects:
            if "Camera_aim." in obj.name:
                lighting_group.select_set(state=True)
                bpy.context.view_layer.objects.active = lighting_group
                constraint = bpy.ops.object.constraint_add(type='COPY_LOCATION')
                bpy.context.object.constraints["Copy Location"].target = bpy.data.objects[obj.name]


        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.light_add(type='SUN', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
        keylight = bpy.context.active_object
        keylight.name = keylight_name
        lighting_group.select_set(state=True)
        bpy.context.view_layer.objects.active = lighting_group
        bpy.ops.object.parent_no_inverse_set()
        keylight.rotation_euler[0] = -3.5
        keylight.rotation_euler[1] = -3.5
        keylight.rotation_euler[2] = 3.5
        keylight.data.energy = 1
        keylight.data.color = (1, 1, 1)
        lighting_collection.objects.link(keylight)
        bpy.context.collection.objects.unlink(keylight) 

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.light_add(type='SUN', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
        rim = bpy.context.active_object
        rim.name = rim_name
        lighting_group.select_set(state=True)
        bpy.context.view_layer.objects.active = lighting_group
        bpy.ops.object.parent_no_inverse_set()
        rim.rotation_euler[0] = -3.50811
        rim.rotation_euler[1] = -5.93412
        rim.rotation_euler[2] = 2.96706
        rim.data.energy = 5
        rim.data.specular_factor = 3
        rim.data.color = (0.132868, 0.367247, 1)
        lighting_collection.objects.link(rim)
        bpy.context.collection.objects.unlink(rim) 


        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.light_add(type='SUN', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
        back = bpy.context.active_object
        back.name = back_name
        lighting_group.select_set(state=True)
        bpy.context.view_layer.objects.active = lighting_group
        bpy.ops.object.parent_no_inverse_set()
        back.rotation_euler[0] = -3.49066
        back.rotation_euler[1] = -6.28319
        back.rotation_euler[2] = 5.06145
        back.data.energy = 0.6
        back.data.specular_factor = 1
        back.data.color = (0.955095, 0.669994, 0.399015)
        lighting_collection.objects.link(back)
        bpy.context.collection.objects.unlink(back) 



        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.light_add(type='SUN', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
        fill = bpy.context.active_object
        fill.name = fill_name
        lighting_group.select_set(state=True)
        bpy.context.view_layer.objects.active = lighting_group
        bpy.ops.object.parent_no_inverse_set()
        fill.rotation_euler[0] = -6.73697
        fill.rotation_euler[1] = -5.95157
        fill.rotation_euler[2] = 7.45256
        fill.data.energy = 0.1
        fill.data.color = (1, 1, 1)
        lighting_collection.objects.link(fill)
        bpy.context.collection.objects.unlink(fill) 


        # #unparent light kit
        # bpy.ops.object.select_all(action='DESELECT')
        # lighting_group.select_set(state=True)
        # bpy.context.view_layer.objects.active = lighting_group
        # bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        if active_camera:
            active_camera.select_set(state=True)
        else:
            lighting_group.rotation_euler[1] = 0
            lighting_group.rotation_euler[0] = 1.36136
            lighting_group.rotation_euler[2] = 0.331613

        

        # set viewport display
        for area in  bpy.context.screen.areas:  # iterate through areas in current screen
            if area.type == 'VIEW_3D':
                for space in area.spaces:  # iterate through spaces in current VIEW_3D area
                    if space.type == 'VIEW_3D':  # check if space is a 3D view
                        space.shading.type = 'MATERIAL'  # set the viewport shading to material
                        space.shading.use_scene_world = True
                        space.shading.use_scene_lights = True

                        space.overlay.show_floor = False
                        space.overlay.show_axis_x = False
                        space.overlay.show_axis_y = False
                        space.overlay.show_cursor = False
                        space.overlay.show_relationship_lines = False
                        space.overlay.show_bones = False
                        space.overlay.show_motion_paths = False
                        space.overlay.show_object_origins = False
                        space.overlay.show_annotation = False
                        space.overlay.show_text = False
                        space.overlay.show_text = False
                        space.overlay.show_outline_selected = False
                        space.overlay.show_extras = False
                        space.overlay.show_overlays = True
                        space.show_gizmo = False
                        space.overlay.wireframe_threshold = 1

        scene = bpy.data.scenes[currSceneIndex]
        if scene.world is None:
            # create a new world
            new_world = bpy.data.worlds.new(sky_name)
            scene.world = new_world
            
            new_world.use_nodes = True
            new_world.node_tree.nodes["Background"].inputs[0].default_value = (0.00393594, 0.00393594, 0.00393594, 1)


        # bpy.ops.object.light_add(type='SUN', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
        # keylight = bpy.context.active_object
        # keylight.name = "Keylight"

        # bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)



        # keylight.rotation_euler[0] = -2.00713
        # keylight.rotation_euler[1] = -2.61799
        # keylight.rotation_euler[2] = 3.66519
        # keylight.data.energy = 1
        # keylight.data.color = (1, 1, 1)

        # bpy.ops.outliner.item_activate(extend=True, deselect_all=True)




        return {'FINISHED'}

class BR_OT_panel_init_ink_lighting(bpy.types.Operator):
    """initialize with workshop lighting"""
    bl_idname = "view3d.spiraloid_3d_comic_init_ink_lighting"
    bl_label ="Ink"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currSceneIndex = getCurrentSceneIndex()
        sceneNumber = "%04d" % currSceneIndex

        bpy.ops.object.select_all(action='DESELECT')
        lighting_collection_name =  "Lighting." + str(sceneNumber) 
        lighting_collection = bpy.data.collections.get(lighting_collection_name)
        if lighting_collection:
            bpy.data.collections.remove(lighting_collection)
            empty_trash(self, context)

        lighting_collection = bpy.data.collections.new(lighting_collection_name)
        bpy.context.scene.collection.children.link(lighting_collection)


        active_camera = bpy.context.scene.camera
        if active_camera:
            active_camera_name = active_camera.name

        lighting_group_name = "Lighting." + str(sceneNumber)

        keylight_name = "Key." + str(sceneNumber)
        rim_name = "Rim." + str(sceneNumber)
        back_name = "Back." + str(sceneNumber)
        fill_name = "Fill." + str(sceneNumber)
        bouncelight_name = "Bounce." + str(sceneNumber)
        sky_name = "Sky." + str(sceneNumber)


        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.scenes[currSceneIndex].objects:
            if lighting_group_name in obj.name: 
                bpy.ops.object.select_all(action='DESELECT')
                obj.select = True
                for c in obj.children:
                    c.select = True
                bpy.ops.object.delete(use_global=False)
                empty_trash(self, context)
                self.report({'INFO'}, 'Deleted Previous Lighting!')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add(type='SPHERE', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
        lighting_group = bpy.context.active_object
        lighting_group.name = lighting_group_name

        lighting_group.show_in_front = True
        lighting_group.empty_display_size = 0.1

        active_camera.select_set(state=True)
        bpy.context.view_layer.objects.active = active_camera
        bpy.ops.object.parent_no_inverse_set()
        lighting_collection.objects.link(lighting_group)
        bpy.context.collection.objects.unlink(lighting_group)

        bpy.ops.object.select_all(action='DESELECT')
        lighting_group.select_set(state=True)

        for obj in bpy.data.scenes[currSceneIndex].objects:
            if "Camera_aim." in obj.name:
                lighting_group.select_set(state=True)
                bpy.context.view_layer.objects.active = lighting_group
                constraint = bpy.ops.object.constraint_add(type='COPY_LOCATION')
                bpy.context.object.constraints["Copy Location"].target = bpy.data.objects[obj.name]


        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.light_add(type='SUN', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
        keylight = bpy.context.active_object
        keylight.name = keylight_name
        lighting_group.select_set(state=True)
        bpy.context.view_layer.objects.active = lighting_group
        bpy.ops.object.parent_no_inverse_set()
        # keylight.rotation_euler[0] = -3.5
        # keylight.rotation_euler[1] = -3.5
        # keylight.rotation_euler[2] = 3.5

        keylight.rotation_euler[0] = -3.31613
        keylight.rotation_euler[1] = -3.83972
        keylight.rotation_euler[2] = 4.18879

        keylight.data.energy = 1
        keylight.data.color = (1, 1, 1)
        keylight.data.use_contact_shadow = True
        keylight.data.contact_shadow_distance = 10
        keylight.data.shadow_buffer_bias = 0.001
        keylight.data.contact_shadow_bias = 0.001
        keylight.data.angle = 0

        lighting_collection.objects.link(keylight)
        bpy.context.collection.objects.unlink(keylight) 

        # bpy.ops.object.select_all(action='DESELECT')
        # bpy.ops.object.light_add(type='SUN', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
        # rim = bpy.context.active_object
        # rim.name = rim_name
        # lighting_group.select_set(state=True)
        # bpy.context.view_layer.objects.active = lighting_group
        # bpy.ops.object.parent_no_inverse_set()
        # rim.rotation_euler[0] = -3.50811
        # rim.rotation_euler[1] = -5.93412
        # rim.rotation_euler[2] = 2.96706
        # rim.data.energy = 5
        # rim.data.specular_factor = 3
        # rim.data.color = (0.132868, 0.367247, 1)
        # export_collection.objects.link(rim)
        # bpy.context.collection.objects.unlink(rim) 




        # #unparent light kit
        # bpy.ops.object.select_all(action='DESELECT')
        # lighting_group.select_set(state=True)
        # bpy.context.view_layer.objects.active = lighting_group
        # bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        if active_camera:
            active_camera.select_set(state=True)
        else:
            lighting_group.rotation_euler[1] = 0
            lighting_group.rotation_euler[0] = 1.36136
            lighting_group.rotation_euler[2] = 0.331613
        

        # set viewport display
        for area in  bpy.context.screen.areas:  # iterate through areas in current screen
            if area.type == 'VIEW_3D':
                for space in area.spaces:  # iterate through spaces in current VIEW_3D area
                    if space.type == 'VIEW_3D':  # check if space is a 3D view
                        space.shading.type = 'MATERIAL'  # set the viewport shading to material
                        space.shading.use_scene_world = True
                        space.shading.use_scene_lights = True

                        space.overlay.show_floor = False
                        space.overlay.show_axis_x = False
                        space.overlay.show_axis_y = False
                        space.overlay.show_cursor = False
                        space.overlay.show_relationship_lines = False
                        space.overlay.show_bones = False
                        space.overlay.show_motion_paths = False
                        space.overlay.show_object_origins = False
                        space.overlay.show_annotation = False
                        space.overlay.show_text = False
                        space.overlay.show_text = False
                        space.overlay.show_outline_selected = False
                        space.overlay.show_extras = False
                        space.overlay.show_overlays = True
                        space.show_gizmo = False
                        space.overlay.wireframe_threshold = 1
                        # if space.local_view is not None:
                        #     bpy.ops.view3d.localview()

        scene = bpy.data.scenes[currSceneIndex]
        if scene.world is not None:
            scene.world.node_tree.nodes.clear
            empty_trash(self, context)


        # create a new world
        mat_world = bpy.data.worlds.new(sky_name)
        scene.world = mat_world
        
        mat_world.use_nodes = True
        mat_world.node_tree.nodes["Background"].inputs[0].default_value = (0.00393594, 0.00393594, 0.00393594, 1)
        world_output = mat_world.node_tree.nodes.get('World Output')
        background_shader = world_output.inputs[0].links[0].from_node
        background_color = mat_world.node_tree.nodes.new(type='ShaderNodeRGB')
        light_path = mat_world.node_tree.nodes.new(type='ShaderNodeLightPath')
        mix_shader = mat_world.node_tree.nodes.new(type='ShaderNodeMixShader')

        mat_world.node_tree.links.new(background_color.outputs[0], background_shader.inputs[0])
        mat_world.node_tree.links.new(background_shader.outputs[0], mix_shader.inputs[2])
        mat_world.node_tree.links.new(light_path.outputs[0], mix_shader.inputs[0])
        mat_world.node_tree.links.new(mix_shader.outputs[0], world_output.inputs[0])

        background_color.outputs[0].default_value = (1, 1, 1, 1)



        visible_objects = []
        for obj in bpy.context.scene.objects:
            if obj.visible_get and  obj.type == 'MESH':
                visible_objects.append(obj)
        outline(visible_objects)

        # shader_to_rgb_A = mat_world.node_tree.nodes.new(type='ShaderNodeShaderToRGB')
        # shader_to_rgb_B = mat_world.node_tree.nodes.new(type='ShaderNodeShaderToRGB')
        # ramp_A = mat.node_tree.nodes.new(type='ShaderNodeValToRGB')
        # ramp_B = mat.node_tree.nodes.new(type='ShaderNodeValToRGB')
        # ramp_A.color_ramp.elements[0].position = 0.00
        # ramp_A.color_ramp.elements[1].position = 0.2
        # ramp_A.color_ramp.interpolation = 'CONSTANT'
        # ramp_B.color_ramp.elements[0].position = 0.00
        # ramp_B.color_ramp.elements[1].position = 0.2
        # ramp_B.color_ramp.interpolation = 'CONSTANT'

        # bpy.context.scene.cycles.max_bounces = 0
        # bpy.context.scene.cycles.preview_start_resolution = 1024




        return {'FINISHED'}


class BR_OT_add_ground(bpy.types.Operator):
    """Add a new ground disc with falloff"""
    bl_idname = "view3d.spiraloid_3d_comic_add_ground"
    bl_label ="Add Ground Disc"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.select_all(action='DESELECT')
        load_resource("ground_disc.blend")
        selected_objects = bpy.context.selected_objects
        for ob in selected_objects:
            ob.hide_select = True

        return {'FINISHED'}

class BR_OT_add_outline(bpy.types.Operator):
    """create a polygon outline for selected objects."""
    bl_idname = "view3d.spiraloid_3d_comic_outline"
    bl_label = "Outline Selected"
    bl_options = {'REGISTER', 'UNDO'}
    

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        selected_objects = bpy.context.selected_objects
        outline(selected_objects)

        return {'FINISHED'}

class BR_OT_regenerate_3d_comic_preview(bpy.types.Operator):
    """remake video sequencer scene strip from all scenes"""
    bl_idname = "view3d.spiraloid_3d_comic_preview"
    bl_label = "Generate Comic Video"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        main_scene = bpy.context.scene
        count = 0
        original_type = bpy.context.area.type

        for a in bpy.context.screen.areas:
            if a.type == 'SEQUENCE_EDITOR':
                if a.spaces[0].view_type == 'SEQUENCER':  
                    bpy.context.area.type ="SEQUENCE_EDITOR"
                    for scene in bpy.data.scenes :
                        if scene is not main_scene :
                            bpy.ops.sequencer.scene_strip_add(frame_start=count, channel=1, scene=bpy.data.scenes[count].name)
                            activeStrip = bpy.context.scene.sequence_editor.active_strip            
                            bpy.context.scene.sequence_editor.sequences_all[activeStrip.name].frame_final_duration = 1
                        count = count + 1
                    bpy.context.area.type = original_type
        return {'FINISHED'}

class BR_OT_spiraloid_3d_comic_workshop(bpy.types.Operator):
    """Visit the spiraloid workshop for updates and goodies!"""
    bl_idname = "view3d.spiraloid_3d_comic_workshop"
    bl_label = "Visit Workshop..."
    def execute(self, context):                
        subprocess.Popen('start '+ 'http://www.spiraloid.net')
        return {'FINISHED'}

#------------------------------------------------------

class BuildComicSettings(bpy.types.PropertyGroup):
    comic_name : bpy.props.StringProperty(name="Comic Name", description="Name of 3D Comic Site", default=True)
    panel_bake_all : bpy.props.BoolProperty(name="Panel Bake All", description="Bake each scene into an Export Collection, with every mesh lightmapped w unlit shader", default=True)

    # bake_distance : bpy.props.FloatProperty(name="Bake Distance Scale",  description="raycast is largest dimension * this value ", min=0, max=3, default=0.02 )
    # bakeSize : bpy.props.EnumProperty(
    #     name="Size", 
    #     description="Width in pixels for baked texture size", 
    #     items={
    #         ("size_128", "128","128 pixels", 1),
    #         ("size_512", "512","512 pixels", 2),
    #         ("size_1024","1024", "1024 pixels", 3)
    #         },
    #     default="size_1024"
    # )
    # bakeTargetObject : bpy.props.PointerProperty(
    #     type=bpy.types.Object,
    #     poll=scene_mychosenobject_poll,
    #     name="Target Mesh",         
    #     description="If no target mesh specified, a new automesh will be created from all meshes in collection"
    # )

class BR_OT_build_3d_comic(bpy.types.Operator):
    """Export all 3D Comic panels and start a local server.  Existing panels will be overwritten"""
    bl_idname = "view3d.spiraloid_build_3d_comic"
    bl_label ="Export 3D Comic"
    bl_options = {'REGISTER', 'UNDO'}
    config: bpy.props.PointerProperty(type=BuildComicSettings)

    def draw(self, context):
        # bpy.types.Scene.bake_panel_settings = bpy.props.CollectionProperty(type=BakePanelSettings)
        # scene = bpy.data.scene[0]
        layout = self.layout
        scene = context.scene
        bake_panel_settings = scene.build_comic_settings


    def execute(self, context):
        if bpy.data.is_dirty:
            self.report({'WARNING'}, "You must save your file first!")
        else:



            # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            startFrame = 1
            endFrame = 72

            # path to the folder
            file_path = bpy.data.filepath
            file_name = bpy.path.display_name_from_filepath(file_path)
            file_ext = '.blend'
            file_dir = file_path.replace(file_name+file_ext, '')
            basefilename = os.path.splitext(file_name)[0]
            tmp_path_to_file = (os.path.join(file_dir, basefilename))
            js_file_path = (file_dir + "files.js")
            bat_file_path = (file_dir + "Read_Local.bat")
            drive_letter = os.path.splitext(file_name)[0]
            # export all scenes
            i = 0



            # delete existing panel.glb fils.
            for panel_files in glob.glob(file_dir+'*.glb'):
                print('os.remove(', panel_files, ')')
                os.remove(panel_files)


            # begin writing the javascript file for the comic
            js_file = open(js_file_path, "w")
            js_file.write('var files = [' +'\n')
            js_file.write('      "./header.w100h50.glb",' +'\n')  
            js_file.write('      "./black.w100h200.glb",' +'\n')  






            panels = []
            for scene in bpy.data.scenes:
                bpy.context.window.scene = scene                

                if "p." in scene.name:
                    panels.append(scene)
                # turn off all collections.
                scene_collections = scene.collection.children
                for col in scene_collections:
                    col_name = col.name
                    bpy.context.view_layer.layer_collection.children[col_name].exclude = True
                bpy.ops.object.select_all(action='DESELECT')

                startFrame = bpy.context.scene.frame_start
                endFrame = bpy.context.scene.frame_end
                bpy.context.scene.frame_current = startFrame

            for scene in panels:
                bpy.context.window.scene = scene 
                # activate export collection.
                export_collection = getCurrentExportCollection()

                if not export_collection:
                    self.report({'WARNING'}, "Export Collection " + export_collection.name + "was not found in scene, skipping export of" + scene.name)
                else:
                    export_collection_name = export_collection.name
                    bpy.context.view_layer.layer_collection.children[export_collection_name].exclude = False
                    child_collections = bpy.context.view_layer.layer_collection.children[export_collection_name].collection.children
                    for col in child_collections:
                        col_name = col.name
                        bpy.context.view_layer.layer_collection.children[export_collection_name].children[col_name].exclude = False

                    meshes = []
                    for obj in export_collection.objects:
                        if obj.visible_get and  obj.type == 'GPENCIL':
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(state=True)
                            bpy.context.view_layer.objects.active = obj

                            # set a temporary context to poll correctly
                            context = bpy.context.copy()
                            for area in bpy.context.screen.areas:
                                if area.type == 'VIEW_3D':
                                    for region in area.regions:
                                        if region.type == 'WINDOW':
                                            context['area'] = area
                                            context['region'] = region
                                            break
                                    break
                            bpy.ops.gpencil.convert(context, type='CURVE', use_timing_data=True)
                            
                            selected_objects = bpy.context.selected_objects
                            gp_mesh = selected_objects[1]
                            bpy.ops.object.select_all(action='DESELECT')
                            bpy.context.view_layer.objects.active =  gp_mesh
                            gp_mesh.select_set(state=True)
                            gp_mesh.data.bevel_depth = 0.005
                            gp_mesh.data.bevel_resolution = 0

                            pmesh = bpy.ops.object.convert(target='MESH')
                            bpy.ops.object.select_all(action='DESELECT')
                            gp_mesh.select_set(state=True)
                            bpy.context.view_layer.objects.active = gp_mesh
                            bpy.ops.object.modifier_add(type='DECIMATE')
                            gp_mesh.modifiers["Decimate"].decimate_type = 'DISSOLVE'
                            gp_mesh.modifiers["Decimate"].angle_limit = 0.0610865
                            bpy.ops.object.modifier_add(type='DECIMATE')
                            gp_mesh.modifiers["Decimate.001"].ratio = 0.2
                            matName = (gp_mesh.name + "Mat")
                            mat = bpy.data.materials.new(name=matName)
                            mat.use_nodes = True
                            mat.node_tree.nodes.clear()
                            mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                            shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                            shader.inputs[0].default_value =  [0, 0, 0, 1]
                            shader.name = "Background"
                            shader.label = "Background"
                            mat_output = mat.node_tree.nodes.get('Material Output')
                            mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])
                            # Assign it to object
                            if gp_mesh.data.materials:
                                gp_mesh.data.materials[0] = mat
                            else:
                                gp_mesh.data.materials.append(mat)  

                        if obj.visible_get and  obj.type == 'MESH':
                            meshes.append(obj)

                        if "Camera." in obj.name:
                            bpy.context.scene.frame_current = startFrame
                            obj.keyframe_insert(data_path="location", frame=startFrame)
                            bpy.context.scene.frame_current = endFrame
                            obj.keyframe_insert(data_path="location", frame=endFrame)

                        if "Camera_aim." in obj.name:
                            bpy.context.scene.frame_current = startFrame
                            obj.keyframe_insert(data_path="location", frame=startFrame)
                            bpy.context.scene.frame_current = endFrame
                            obj.keyframe_insert(data_path="location", frame=endFrame)

                    # meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']

                    # get the minimum coordinate in scene
                    if meshes:
                        minV = Vector((min([min([co[0] for co in m.bound_box]) for m in meshes]),
                                    min([min([co[1] for co in m.bound_box]) for m in meshes]),
                                    min([min([co[2] for co in m.bound_box]) for m in meshes])))
                        maxV = Vector((max([max([co[0] for co in m.bound_box]) for m in meshes]),
                                    max([max([co[1] for co in m.bound_box]) for m in meshes]),
                                    max([max([co[2] for co in m.bound_box]) for m in meshes])))
                        scene_bounds = (minV[0] + maxV[0])*50
                    else:
                        scene_bounds = 100

                    # process meshes 
                    if meshes:
                        for obj in meshes:
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(state=True)
                            bpy.context.view_layer.objects.active = obj
                            for mod in [m for m in obj.modifiers]:
                                bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)     

                    # cam_ob = bpy.context.scene.camera
                    # if cam_ob is None:
                    #     self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)
                    # elif cam_ob.type == 'CAMERA':
                    #     # cam_ob.data.clip_end = scene_bounds
                    #     cam_ob.data.clip_end = 200

                    # process camera
                    active_camera = bpy.context.scene.camera
                    if active_camera is not None :
                        bpy.ops.object.select_all(action='DESELECT')
                        active_camera.select_set(state=True)
                        bpy.context.view_layer.objects.active = active_camera

                        bpy.ops.nla.bake(frame_start=startFrame, frame_end=endFrame, visual_keying=True, clear_constraints=True, bake_types={'OBJECT'})
                    else:
                        self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)





                    # process letters
                    letters = [o for o in bpy.context.scene.objects if o.type == 'FONT']
                    for text in letters:
                        bpy.ops.object.select_all(action='DESELECT')
                        text.select_set(state=True)
                        bpy.context.view_layer.objects.active = text
                        bpy.ops.object.convert(target='MESH')
                        # mod = text.modifiers.new(name = 'Decimate', type = 'DECIMATE')
                        # mod.ratio = 0.5

                    # process world_nodes 
                    # world_nodes = bpy.data.worlds[bpy.context.scene.world.name].node_tree.nodes
                    world_nodes = bpy.context.scene.world
                    if world_nodes:
                        if world_nodes.use_nodes:
                            background_node = world_nodes.node_tree.nodes.get('Background')
                            background_node_color_input = background_node.inputs[0].links[0].from_node
                            if background_node_color_input:
                                # if "RGB" in background_node_color_input.name:
                                background_color = background_node_color_input.outputs[0].default_value
                            else:
                                background_color = background_node.inputs[0].default_value

                            bpy.ops.object.select_all(action='DESELECT')
                            load_resource("skyball.blend")
                            ob = bpy.context.selected_objects[0]
                            bpy.context.view_layer.objects.active = ob
                            ob.select_set(state=True)

                            if ob.active_material is not None:
                                for i in range(len(ob.material_slots)):
                                    bpy.ops.object.material_slot_remove({'object': ob})
                            bpy.ops.object.shade_smooth()

                            assetName = ob.name
                            matName = (assetName + "Mat")
                            mat = bpy.data.materials.new(name=matName)
                            mat.use_nodes = True
                            mat.node_tree.nodes.clear()
                            mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                            shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                            shader.inputs[0].default_value =  [background_color[0], background_color[1], background_color[2], 1]
                            mat.use_backface_culling = True
                            shader.name = "Background"
                            shader.label = "Background"


                            mat_output = mat.node_tree.nodes.get('Material Output')
                            mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])
                            # Assign it to object
                            if ob.data.materials:
                                ob.data.materials[0] = mat
                            else:
                                ob.data.materials.append(mat)  




                    path_to_export_file = (file_dir + scene.name +".glb")
                    bpy.ops.export_scene.gltf(
                        export_nla_strips=True,  # <-- Set False will crash or produce duplicate actions
                        export_apply=False, # <-- Set true will crash        
                        export_format='GLB', 
                        ui_tab='GENERAL', 
                        export_copyright="Bay Raitt", 
                        export_image_format='AUTO', 
                        export_texture_dir="", 
                        export_texcoords=True, 
                        export_normals=True, 
                        export_draco_mesh_compression_enable=False, 
                        export_draco_mesh_compression_level=6, 
                        export_draco_position_quantization=14, 
                        export_draco_normal_quantization=10, 
                        export_draco_texcoord_quantization=12, 
                        export_draco_generic_quantization=12, 
                        export_tangents=False, 
                        export_materials=True, 
                        export_colors=False, 
                        export_cameras=True, 
                        export_selected=False, 
                        use_selection=False, 
                        export_extras=True, 
                        export_yup=True, 
                        export_animations=True, 
                        export_frame_range=True, 
                        export_frame_step=1, 
                        export_force_sampling=True, 
                        export_def_bones=False, 
                        export_current_frame=False, 
                        export_skins=False, 
                        export_all_influences=False, 
                        export_morph=False, 
                        export_morph_normal=False, 
                        export_morph_tangent=False, 
                        export_lights=True, 
                        export_displacement=False, 
                        will_save_settings=False,  
                        filepath=(path_to_export_file), 
                        check_existing=True, 
                        filter_glob="*.glb;*.gltf")
                    # write the line for this file into the javascript file. 
                    js_file.write('      "./' + scene.name + '.glb",' +'\n')  

                    # rehide this collection so it's not in the next export.  
                    bpy.context.view_layer.layer_collection.children[export_collection_name].exclude = True


                        # export_copyright="Bay Raitt", 
                        # filepath=(path_to_export_file), 
                        # use_selection=False, 
                        # export_format='GLB', 
                        # export_image_format='JPEG', 
                        # export_yup=True, 
                        # export_apply=True, 
                        # export_cameras=True, 
                        # export_animations=True, 
                        # export_frame_range=True, 
                        # export_frame_step=1, 
                        # export_force_sampling=True, 
                        # export_nla_strips=False, 
                        # export_def_bones=True, 
                        # export_current_frame=False, 
                        # export_skins=True, 
                        # export_all_influences=False,
                        # export_materials=True, 
                        # export_colors=True
                        # )

                        # export_morph=True, 
                        # export_morph_normal=True, 
                        # export_morph_tangent=False
                        # export_texture_dir="", 
                        # export_texcoords=True, 
                        # export_normals=True, 
                        # export_draco_mesh_compression_enable=False, 
                        # export_draco_mesh_compression_level=6, 
                        # export_draco_position_quantization=14, 
                        # export_draco_normal_quantization=10, 
                        # export_draco_texcoord_quantization=12, 
                        # export_draco_generic_quantization=12, 
                        # export_tangents=False, 
                        # export_selected=False, 
                        # export_extras=False, 
                        # export_lights=False 

                    # will_save_settings=False,
                    # check_existing=True
                    # export_texture_dir="Materials", 
                    # export_draco_mesh_compression_enable=False, 
                    # export_draco_mesh_compression_level=6, 
                    # export_draco_position_quantization=14, 
                    # export_draco_normal_quantization=10, 
                    # export_draco_texcoord_quantization=12, 
                    # export_draco_generic_quantization=12, 
                    # bpy.ops.export_scene.obj(   filepath = path_to_export_file, use_selection   =   True )
                    i = i + 1

            # finish writing the javascript file
            js_file.write('      "./black.w100h200.glb",' +'\n')  
            js_file.write('      "./footer.w100h50.glb",' +'\n')  
            js_file.write('];' +'\n')
            js_file.close()


            # create local server bat file (windows only)
            bat_file = open(bat_file_path, "w")
            stringFragments = file_dir.split(':')
            drive_letter = stringFragments[0] + ":"


            bat_file.write(drive_letter +'\n')  
            bat_file.write('cd ' + file_dir +'\n')  
            bat_file.write('start http://localhost:8008/' +'\n')  
            bat_file.write('python -m SimpleHTTPServer 8008' +'\n')
            bat_file.close()


            # copy 3D Comic Html
            user_dir = os.path.expanduser("~")
            common_subdir = "2.90/scripts/addons/3DComicToolkit/Resources/Reader"
            if system() == 'Linux':
                addon_path = "/.config/blender/" + common_subdir
            elif system() == 'Windows':
                addon_path = (
                    "\\AppData\\Roaming\\Blender Foundation\\Blender\\"
                    + common_subdir.replace("/", "\\")
                )
                # os.path.join()
            elif system() == 'Darwin':
                addon_path = "/Library/Application Support/Blender/" + common_subdir
            addon_dir = user_dir + addon_path
            copy_tree(addon_dir, file_dir)



            ## reopen scene from before build comic
            bpy.ops.wm.open_mainfile(filepath=file_path)
            self.report({'INFO'}, 'Exported Comic!')
            # subprocess.Popen('explorer '+ file_dir)
            # subprocess.Popen(bat_file_path)
            BR_OT_read_3d_comic.execute(self, context)






        return {'FINISHED'}

pythonServerSubprocess = ""

class BR_OT_read_3d_comic(bpy.types.Operator):
    """Build and export 3D Comic"""
    bl_idname = "view3d.spiraloid_read_3d_comic"
    bl_label ="Read 3D Comic"
    bl_options = {'REGISTER', 'UNDO'}
    # config: bpy.props.PointerProperty(type=BuildComicSettings)

    # def draw(self, context):
    #     # bpy.types.Scene.bake_panel_settings = bpy.props.CollectionProperty(type=BakePanelSettings)
    #     # scene = bpy.data.scene[0]
    #     layout = self.layout
    #     scene = context.scene
    #     bake_panel_settings = scene.build_comic_settings


    def execute(self, context):
        global pythonServerSubprocess

        # path to the folder
        file_path = bpy.data.filepath
        file_name = bpy.path.display_name_from_filepath(file_path)
        file_ext = '.blend'
        file_dir = file_path.replace(file_name+file_ext, '')
        bat_file_path = (file_dir + "Read_Local.bat")
        index_file_path = (file_dir + "index.html")

        if os.path.isfile(index_file_path):
            if not os.path.isfile(bat_file_path):
                bat_file = open(bat_file_path, "w")
                bat_file.write('cd ' + file_dir +'\n')  
                bat_file.write('start http://localhost:8002/' +'\n')  
                bat_file.write('python -m SimpleHTTPServer 8002' +'\n')
                bat_file.close()

            # subprocess.Popen('explorer '+ file_dir)
            if pythonServerSubprocess:
                pythonServerSubprocess.terminate()
            cmd = bat_file_path
            pythonServerSubprocess = subprocess.Popen(cmd)
            # subprocess.Popen(bat_file_path)
        else:
            self.report({'ERROR'}, 'No 3D Comic found next to .blend file!  Try Export 3D Comic first.' + bpy.context.scene.name)



        return {'FINISHED'}


class BR_OT_spiraloid_3d_comic_workshop(bpy.types.Operator):
    """Visit the spiraloid workshop for updates and goodies!"""
    bl_idname = "view3d.spiraloid_3d_comic_workshop"
    bl_label = "Get More..."
    def execute(self, context):                
        subprocess.Popen('start '+ 'http://www.spiraloid.net')
        return {'FINISHED'}

#------------------------------------------------------

class BakePanelSettings(bpy.types.PropertyGroup):
    target_automesh : bpy.props.BoolProperty(name="Automesh", description="Generate a new mesh to recieve textures", default=True)
    target_existing : bpy.props.BoolProperty(name="Existing", description="Use an existing UV mapped mesh to recieve textures", default=True)
    target_duplicate : bpy.props.BoolProperty(name="Duplicate", description="Duplicate objects in collection to recieve textures", default=True)

    bakeTargetObject : bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=scene_mychosenobject_poll,
        name="Target Mesh",         
        description="If no target mesh specified, a new automesh will be created from all meshes in collection"
    )
    
    target_strategy : bpy.props.EnumProperty(
        name="Target", 
        description="Type of object to recieve baked textures", 
        items={
            ("target_automesh", "Combined","Automesh", 0),
            ("target_duplicate","Duplicate", "Duplicate", 1),
            ("target_existing", "Existing Mesh","Existing", 2),
            },
        default="target_automesh"
    )

    bakeSize : bpy.props.EnumProperty(
        name="Size", 
        description="Width in pixels for baked texture size", 
        items={
            ("size_128", "128","128 pixels", 0),
            ("size_128", "256","256 pixels", 1),
            ("size_512", "512","512 pixels", 2),
            ("size_1024","1024", "1024 pixels", 3),
            ("size_2048", "2048","2048 pixels", 4),
            ("size_4096", "4096","4096 pixels", 5),
            ("size_8192", "8192","8192 pixels", 6),
            },
        default="size_1024"
    )
    bake_distance : bpy.props.FloatProperty(name="Bake Distance Scale",  description="raycast is largest dimension * this value ", min=0, max=3, default=0.02 )
    bake_to_unlit : bpy.props.BoolProperty(name="Bake Lighting", description="Bake Collection to new mesh with lightmap texture and unlit shader", default=True)
    # bake_to_pbr : bpy.props.BoolProperty(name="Bake PBR", description="Bake Collection to new mesh with a Principled BSDF shader", default=False)
    bake_albedo : bpy.props.BoolProperty(name="Bake Albedo", description="Bake Collection to mesh with Albedo Texture", default=True)
    bake_normal : bpy.props.BoolProperty(name="Bake Normal", description="Bake Collection to mesh with Normal Texture", default=True)
    bake_metallic : bpy.props.BoolProperty(name="Bake Metallic*", description="Bake Collection to mesh with Metallic Texture", default=True)
    bake_roughness : bpy.props.BoolProperty(name="Bake Roughness", description="Bake Collection to mesh with Roughness Texture", default=True)
    bake_emission : bpy.props.BoolProperty(name="Bake Emission*", description="Bake Collection to mesh with Emission Texture", default=False)
    bake_opacity : bpy.props.BoolProperty(name="Bake Transparency*", description="Bake Collection to mesh with Opacity Texture", default=False)
    bake_ao : bpy.props.BoolProperty(name="Bake AO", description="Bake Collection to mesh with Ambient Occlusion Texture", default=False)
    bake_ao_LoFi : bpy.props.BoolProperty(name="Use Output Mesh", description="Use target for Ambient Occlusion, otherwise use source meshes (slower).", default=True)
    bake_ao_applied : bpy.props.BoolProperty(name="Apply", description="Composite Ambient Occlusion into Albedo Texture", default=True)
    bake_curvature : bpy.props.BoolProperty(name="Curvature*", description="Bake Collection to mesh with Curvature Texture", default=True)
    bake_curvature_applied : bpy.props.BoolProperty(name="Apply", description="Bake Curvature into Albedo Texture", default=True)
    bake_cavity : bpy.props.BoolProperty(name="Cavity*", description="Bake Collection to mesh with Cavity Texture", default=True)
    bake_cavity_applied : bpy.props.BoolProperty(name="Apply", description="Bake Cavity into Albedo Texture", default=True)
    bake_w_decimate : bpy.props.BoolProperty(name="Decimate", description="Bake and Emission Textures", default=True)
    bake_w_decimate_ratio : bpy.props.FloatProperty(name="Decimate Ratio",  description="Amount to decimate target mesh", min=0, max=1, default=0.5 )
    bake_outline : bpy.props.BoolProperty(name="Outline", description="Add ink outline to bake mesh", default=False)
    bake_background : bpy.props.BoolProperty(name="Background", description="Bake all but collection to skyball", default=False)

class BR_OT_bake_panel(bpy.types.Operator):
    """Merge all meshes in active collection, unwrap and toggle_workmodeing and textures into a new "Export" collection"""
    bl_idname = "view3d.spiraloid_bake_panel"
    bl_label = "Bake Collection..."
    bl_options = {'REGISTER', 'UNDO'}
    config: bpy.props.PointerProperty(type=BakePanelSettings)

    def draw(self, context):
        # bpy.types.Scene.bake_panel_settings = bpy.props.CollectionProperty(type=BakePanelSettings)
     
        # scene = bpy.data.scene[0]

        layout = self.layout
        scene = context.scene
        bake_panel_settings = scene.bake_panel_settings

        strategy_row = layout.row(align=True)

        layout.prop(bake_panel_settings, "target_strategy")

        row = layout.row(align=True)
        row.prop(bake_panel_settings, "bakeTargetObject" )


        if bake_panel_settings.target_strategy == "target_existing":
            row.enabled = True
        else :
            row.enabled = False


        layout.prop(bake_panel_settings, "bakeSize")
        layout.prop(bake_panel_settings, "bake_distance")
        layout.separator()
        layout.prop(bake_panel_settings, "bake_to_unlit")
        layout.prop(bake_panel_settings, "bake_albedo")
        layout.prop(bake_panel_settings, "bake_metallic")
        layout.prop(bake_panel_settings, "bake_roughness")
        layout.prop(bake_panel_settings, "bake_normal")
        normal_cavity_row = layout.row(align=True)
        normal_curvature_row = layout.row(align=True)
        if bake_panel_settings.bake_normal:
            normal_curvature_row.enabled = True
            normal_curvature_row.prop(bake_panel_settings, "bake_curvature")
            normal_curvature_row.prop(bake_panel_settings, "bake_curvature_applied")
            normal_cavity_row.enabled = True
            normal_cavity_row.prop(bake_panel_settings, "bake_cavity")
            normal_cavity_row.prop(bake_panel_settings, "bake_cavity_applied")
        layout.prop(bake_panel_settings, "bake_emission")
        layout.prop(bake_panel_settings, "bake_opacity")
        layout.prop(bake_panel_settings, "bake_ao")
        ao_row = layout.row(align=True)
        if bake_panel_settings.bake_ao:
            ao_row.enabled = True
            ao_row.prop(bake_panel_settings, "bake_ao_LoFi")
            ao_row.prop(bake_panel_settings, "bake_ao_applied")
        else:
            ao_row.enabled = False



        layout.separator()
        layout.prop(bake_panel_settings, "bake_w_decimate")
        pbr_row = layout.row(align=True)
        if bake_panel_settings.bake_w_decimate:
            pbr_row.enabled = True
            layout.prop(bake_panel_settings, "bake_w_decimate_ratio")
        else :
            pbr_row.enabled = False

        layout.separator()
        layout.prop(bake_panel_settings, "bake_outline")
        layout.separator()
        layout.prop(bake_panel_settings, "bake_background")
        layout.separator()





    def execute(self, context):  
        if bpy.data.is_dirty:
            self.report({'WARNING'}, "You must save your file first!")
        else:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
            scene_name = bpy.context.window.scene.name
            currSceneIndex = getCurrentSceneIndex()
            export_collection_name = "Export"
            panel_number = "0000"
            panels = []

            for scene in bpy.data.scenes:
                if "p." in scene.name:
                    panels.append(scene.name)
            for panel in panels :
                for i in range(len(bpy.data.scenes)):
                    if bpy.data.scenes[currSceneIndex].name == panel:
                        stringFragments = panel.split('.')
                        export_collection_name = "Export." + stringFragments[1]
                        panel_number = stringFragments[1]

            if bpy.data.collections.get(export_collection_name) is None :
                e_collection = bpy.data.collections.new(export_collection_name)
                bpy.context.scene.collection.children.link(e_collection)  

            export_collection = bpy.data.collections.get(export_collection_name)

            layer_collection = bpy.context.view_layer.layer_collection
            source_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
            source_collection = bpy.data.collections.get(source_collection_name)
            scene_collection = bpy.context.view_layer.layer_collection
            bake_collection_name =  (scene_name + "_" + source_collection_name  + "_baked")
            bake_mesh_name = (scene_name + "_" + source_collection_name  + "_baked")

            hasMultires = False



            if source_collection is None :
                selected_objects = bpy.context.selected_objects
                if len(selected_objects) > 0:
                    source_collection = selected_objects[0].users_collection[0]            
                    source_collection_name = source_collection.name  
                else:
                    # source_collection = scene_collection
                    collections =  context.view_layer.objects.active.users_collection          
                    if len(collections) > 2:
                        self.report({'ERROR'}, 'You must select a collection!')
                return {'FINISHED'} 


            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode='OBJECT')



            # cleanup previous bake collection 
            if bpy.data.collections.get(bake_collection_name) : 
                old_bake_collection = bpy.data.collections.get(bake_collection_name)
                bpy.context.view_layer.active_layer_collection = export_collection.children[bake_collection_name]
                bpy.data.collections.remove(old_bake_collection)
                empty_trash(self, context)
                self.report({'INFO'}, 'Deleted Previous Export collection!')


            # manage export collection 
            layer_collection = bpy.context.view_layer.layer_collection
            source_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
            source_collection = bpy.data.collections.get(source_collection_name)
            scene_collection = bpy.context.view_layer.layer_collection
            bake_collection = bpy.data.collections.new(bake_collection_name)
            export_collection.children.link(bake_collection)
            obj = bpy.context.object
            # print ("::::::::::::::::::::::::::::::::::::::::::::::")

            # bpy.ops.object.select_all(action='DESELECT')

            # path to the folder
            file_path = bpy.data.filepath
            file_name = bpy.path.display_name_from_filepath(file_path)
            file_ext = '.blend'
            file_dir = file_path.replace(file_name+file_ext, '')
            # materials_dir = file_dir+"\Materials\"
            materials_dir = file_dir+"\\Materials\\"
            if not os.path.exists(materials_dir):
                os.makedirs(materials_dir)
            
            settings = context.scene.bake_panel_settings

            if settings.bakeSize == "size_128":
                width = 128
                height = 128
                pixelMargin = 2
            if settings.bakeSize == "size_256":
                width = 256
                height = 256
                pixelMargin = 2
            if  settings.bakeSize == "size_512":
                width = 512
                height = 512
                pixelMargin = 4
            if  settings.bakeSize == "size_1024":
                width = 1024
                height = 1024
                pixelMargin = 8
            if  settings.bakeSize == "size_2048":
                width = 2048
                height = 2048
                pixelMargin = 8
            if  settings.bakeSize == "size_4096":
                width = 4096
                height = 4096
                pixelMargin = 8
            if  settings.bakeSize == "size_8192":
                width = 8192
                height = 8192
                pixelMargin = 8


            bake_to_unlit = settings.bake_to_unlit
            bake_albedo = settings.bake_albedo
            bake_normal = settings.bake_normal
            bake_metallic = settings.bake_metallic
            bake_roughness = settings.bake_roughness
            bake_emission = settings.bake_emission
            bake_opacity = settings.bake_opacity
            bake_ao = settings.bake_ao
            bake_ao_applied = settings.bake_ao_applied
            bake_curvature = settings.bake_curvature
            bake_curvature_applied = settings.bake_curvature_applied
            bake_cavity = settings.bake_cavity
            bake_cavity_applied = settings.bake_cavity_applied            
            bake_ao_LoFi = settings.bake_ao_LoFi
            decimate = settings.bake_w_decimate
            ratio = settings.bake_w_decimate_ratio
            bake_distance = settings.bake_distance
            bake_background = settings.bake_background
            bake_outline = settings.bake_outline

            wm = context.window_manager
            tot = 1000
            wm.progress_begin(0,tot)       
            progress_current = 0.0
            process_count =  bake_to_unlit + bake_albedo + bake_normal + bake_roughness + bake_metallic + bake_emission +  bake_opacity + bake_ao + bake_outline + bake_background
            progress_step = tot/process_count
            progress_current += progress_step
            wm.progress_update(progress_current)
            # for i in range(tot):
            #     wm.progress_update(i)

            visible_objects = []
            for obj in bpy.context.scene.objects:
                if obj.visible_get :
                    visible_objects.append


            # # select all source meshes
            # bpy.ops.object.select_all(action='DESELECT')
            # for ob in source_collection.objects :
            #     if ob.type == 'MESH' : 
            #         print (ob.name)
            #         ob.select_set(state=True)
            #         bpy.context.view_layer.objects.active = ob
            # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            # source_meshes = bpy.context.selected_objects

            # select all source meshes
            source_meshes = []
            for ob in source_collection.objects :
                if ob.type == 'MESH' : 
                    print (ob.name)
                    source_meshes.append(ob)


            bake_meshes = []
            tmp_meshes = []

            if settings.bake_w_decimate :
                ratio = settings.bake_w_decimate_ratio
            else:
                ratio = 1


            if settings.target_strategy == "target_automesh":
                # duplicate all collection objects and put into one collection.
                for ob in source_meshes :
                    bpy.ops.object.select_all(action='DESELECT')
                    ob.select_set(state=True)
                    bpy.context.view_layer.objects.active = ob
                    bpy.ops.object.duplicate_move()
                    target_object = bpy.context.selected_objects[0]
                    bpy.data.collections[source_collection_name].objects.unlink(target_object)
                    bpy.data.collections[bake_collection_name].objects.link(target_object)
                    tmp_meshes.append(target_object)

                #apply all modifiers
                for tmp_ob in tmp_meshes:
                    bpy.ops.object.select_all(action='DESELECT')
                    tmp_ob.select_set(state=True)
                    bpy.context.view_layer.objects.active = tmp_ob
                    for mod in [m for m in tmp_ob.modifiers]:
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)            

                # # UV maps any objects that do not have UV's
                automap(tmp_meshes, ratio)

                #boolean objects into one mesh
                bpy.ops.object.select_all(action='DESELECT')
                for ob in tmp_meshes :
                    ob.select_set(state=True)
                    bpy.context.view_layer.objects.active = ob
                bpy.ops.object.booltool_auto_union()           
                bm = bpy.context.object
                bm.name = bake_mesh_name
                bake_meshes.append(bm)

                # Triangulate
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')
                bpy.ops.mesh.select_all(action='TOGGLE')
                bpy.ops.mesh.quads_convert_to_tris(quad_method='FIXED', ngon_method='BEAUTY')
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)





            # if settings.target_strategy == "target_duplicate":



            # duplicate and move to bake collection
            if settings.target_strategy == "target_duplicate":
                for source_object in source_meshes :
                    bpy.ops.object.select_all(action='DESELECT')
                    source_object.select_set(state=True)
                    bpy.context.view_layer.objects.active = source_object
                    target_object_name = source_object.name + "_baked"
                    

                    bpy.ops.object.duplicate_move()
                    automap(bpy.context.selected_objects, ratio)
                    target_object = bpy.context.selected_objects[0]
                    target_object.name = target_object_name

                    # UV maps any objects if it does not have UV's

                    bpy.data.collections[source_collection_name].objects.unlink(target_object)
                    bpy.data.collections[bake_collection_name].objects.link(target_object)
                    bake_meshes.append(target_object)


                    # self.report({'ERROR'}, '======================================================')

            if settings.target_strategy == "target_existing":
                # bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((-4.37114e-08, -1, 0), (1, -4.37114e-08, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":True, "use_proportional_edit":False, "proportional_edit_falloff":'INVERSE_SQUARE', "proportional_size":0.101089, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
                # bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name=bake_collection_name)
                # bakemesh = bpy.context.object
                # bake_mesh_name = bm.name
                # bake_meshes.append(bm)
                # target_object = settings.bakeTargetObject
                bake_meshes.append(settings.bakeTargetObject)



                # bpy.ops.object.duplicate_move()
                # target_object = bpy.context.selected_objects[0]
                # target_object.name = target_object_name
                # bpy.data.collections[source_collection_name].objects.unlink(target_object)
                # bpy.data.collections[bake_collection_name].objects.link(target_object)

            if settings.target_strategy == "target_automesh":
                # bake_mesh_name = ("BakeMesh  " + source_collection.name )
                # bakemesh.name = bake_mesh_name
                target_object = bake_meshes[0]
                # bakemesh = bake_meshes[0]



            if bake_to_unlit :
                ## old collection logic
                # layer_collection = bpy.context.view_layer.layer_collection
                # source_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
                # source_collection = bpy.data.collections.get(source_collection_name)
                # scene_collection = bpy.context.view_layer.layer_collection
                # if source_collection is None :
                #     if context.view_layer.objects.active is not None :
                #         collections =  context.view_layer.objects.active.users_collection
                #         if len(collections) > 0:
                #             bpy.context.view_layer.active_layer_collection = collections()
                #             source_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
                #             source_collection = bpy.data.collections.get(source_collection_name)
                #         else:
                #             source_collection = scene_collection
                #             self.report({'ERROR'}, 'You must select a collection!')
                #             return {'FINISHED'} 

                # bake_collection_name = ("Lightmap Bake " + source_collection.name )
                # bake_mesh_name = ("Lightmap BakeMesh  " + source_collection.name )




                # bake_to_unlit = True
                # decimate = True



                # # verify all objects have UV's, if not create some.
                # bpy.ops.object.select_all(action='DESELECT')
                # for ob in source_collection.objects :
                #     if ob.type == 'MESH' : 
                #         print (ob.name)
                #         ob.select_set(state=True)
                #         bpy.context.view_layer.objects.active = ob
                #         if not len( ob.data.uv_layers ):
                #             bpy.ops.uv.smart_project()
                #             bpy.ops.uv.smart_project(angle_limit=66)
                #             bpy.ops.uv.smart_project(island_margin=0.05, user_area_weight=0)

                if settings.target_strategy == "target_automesh" or settings.target_strategy == "target_duplicate" :


                    if decimate:

                        bpy.ops.object.modifier_add(type='DECIMATE')
                        bpy.context.object.modifiers["Decimate"].decimate_type = 'DISSOLVE'
                        bpy.context.object.modifiers["Decimate"].angle_limit = 0.0523599
                        bpy.context.object.modifiers["Decimate"].delimit = {'UV'}
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

                        bpy.ops.object.modifier_add(type='TRIANGULATE')
                        bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
                        bpy.context.object.modifiers["Triangulate"].quad_method = 'FIXED'
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Triangulate")

                        bpy.ops.object.modifier_add(type='DECIMATE')
                        print (ratio)
                        bpy.context.object.modifiers["Decimate"].ratio = ratio
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

                    # area = bpy.context.area
                    # old_type = area.type
                    # area.type = 'VIEW_3D'

                    
                    # if old_type != "":
                        # area.type = old_type
                    # area.type = 'INFO'







                # bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name= bake_collection_name)

                # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]
                
                
                # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[source_collection_name]
                
                
                # bpy.context.view_layer.active_layer_collection.exclude = False

                automap(bake_meshes, ratio)


                for bakemesh in bake_meshes :


                    bpy.ops.object.select_all(action='DESELECT')
                    bakemesh.select_set(state=True)
                    bpy.context.view_layer.objects.active = bakemesh
                    # selected_objects = bpy.context.selected_objects

                    # nuke_flat_texture(selected_objects, width, height)

                    if bakemesh.active_material is not None:
                        # bakemesh.active_material.node_tree.nodes.clear()
                        for i in range(len(bakemesh.material_slots)):
                            bpy.ops.object.material_slot_remove({'object': ob})
                    bpy.ops.object.shade_smooth()

                    assetName = bakemesh.name
                    matName = (assetName + "Mat")
                    texName_lightmap = (assetName + "_lightmap")
                    mat = bpy.data.materials.new(name=matName)
                    mat.use_nodes = True
                    mat.node_tree.nodes.clear()
                    mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                    shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                    texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                    texture.image = bpy.data.images.new(texName_lightmap, width=width, height=height)

                    mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])

                    shader.name = "Background"
                    shader.label = "Background"

                    mat_output = mat.node_tree.nodes.get('Material Output')
                    mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])



                    # Assign it to object
                    if bakemesh.data.materials:
                        bakemesh.data.materials[0] = mat
                    else:
                        bakemesh.data.materials.append(mat)  


                    # Select Objects for Bake
                    bpy.ops.object.select_all(action='DESELECT')
                    for ob in source_meshes :
                        ob.select_set(state=True)
                        bpy.context.view_layer.objects.active = ob
                    bakemesh.select_set(state=True)
                    bpy.context.view_layer.objects.active = bakemesh

                    #set Redner bake settings
                    bpy.context.scene.render.engine = 'CYCLES'
                    bpy.context.scene.render.tile_x =  width
                    bpy.context.scene.render.tile_y =  height
                    bpy.context.scene.cycles.max_bounces = 4
                    bpy.context.scene.cycles.diffuse_bounces = 4
                    bpy.context.scene.cycles.glossy_bounces = 4
                    bpy.context.scene.cycles.transparent_max_bounces = 4
                    bpy.context.scene.cycles.transmission_bounces = 4
                    bpy.context.scene.cycles.volume_bounces = 0

                    bpy.context.scene.cycles.bake_type = 'COMBINED'
                    bpy.context.scene.render.bake.use_selected_to_active = True
                    bpy.context.scene.render.bake.use_cage = True
                    ray_length = bakemesh.dimensions[1] * bake_distance
                    bpy.context.scene.render.bake.cage_extrusion = ray_length
                    bpy.context.scene.render.bake.use_pass_direct = True
                    bpy.context.scene.render.bake.use_pass_indirect = True
                    bpy.context.scene.cycles.samples = 256  

                    #select the output texture node and bake
                    matnodes = bpy.context.active_object.material_slots[0].material.node_tree.nodes
                    imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']
                    for n in imgnodes:
                        if n.image.name == texName_lightmap:
                            n.select = True
                            matnodes.active = n
                            # if os.path.exists(file_dir) and os.path.exists(materials_dir):
                            #         outBakeFileName = n.image.name+".png"
                            #         outRenderFileName = materials_dir+outBakeFileName
                            #         n.image.file_format = 'PNG'
                            #         n.image.filepath = outRenderFileName
                            #         bpy.ops.object.bake(type='COMBINED', filepath=outRenderFileName, save_mode='EXTERNAL')
                            #         n.image.save()
                            #         self.report({'INFO'},"Baked lightmap texture saved to: " + outRenderFileName )
                            # else:
                            bpy.ops.object.bake(type='COMBINED')
                            n.image.pack()




                    # bpy.ops.object.bake('INVOKE_DEFAULT', type='COMBINED')
                    # bpy.ops.object.bake("INVOKE_SCREEN", type='COMBINED')
                    
                    # bpy.context.view_layer.layer_collection.children[bake_collection_name].exclude = False
                    # bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = True


                    bpy.context.view_layer.layer_collection.children[export_collection_name].exclude = False
                    bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = False
                    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[source_collection_name]

                progress_current += progress_step
                wm.progress_update(progress_current)


            if bake_albedo or bake_normal or bake_roughness or bake_metallic or bake_emission or bake_opacity or bake_ao:
                for target_object in bake_meshes :
                    if target_object is not None:
                            
                        # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        bpy.ops.object.select_all(action='DESELECT')
                        target_object.select_set(state=True)
                        bpy.context.view_layer.objects.active = target_object

                        # # UV if none exist
                        # if not len(source_object.data.uv_layers):
                        #     bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        #     bpy.ops.mesh.select_all(action='SELECT')
                        #     # bpy.ops.uv.smart_project()
                        #     # bpy.ops.uv.smart_project(angle_limit=66)
                        #     bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.01, user_area_weight=0.75)
                        #     bpy.ops.uv.average_islands_scale()

                        #     # select all faces
                        #     # bpy.ops.mesh.select_all(action='SELECT')
                        #     bpy.ops.uv.pack_islands(margin=0.017)

                        #     # bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.1)
                        #     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                        #     if decimate:
                        #         bpy.ops.object.modifier_add(type='DECIMATE')
                        #         bpy.context.object.modifiers["Decimate"].decimate_type = 'DISSOLVE'
                        #         bpy.context.object.modifiers["Decimate"].angle_limit = 0.0523599
                        #         bpy.context.object.modifiers["Decimate"].delimit = {'UV'}
                        #         bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

                        #         bpy.ops.object.modifier_add(type='TRIANGULATE')
                        #         bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
                        #         bpy.context.object.modifiers["Triangulate"].quad_method = 'FIXED'
                        #         bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Triangulate")

                        #         bpy.ops.object.modifier_add(type='DECIMATE')
                        #         bpy.context.object.modifiers["Decimate"].ratio = ratio
                        #         bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

                        #     # area = bpy.context.area
                        #     # old_type = area.type
                        #     # area.type = 'VIEW_3D'
                        #     bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        #     bpy.ops.mesh.select_all(action='SELECT')
                        #     # if bakemesh.data.uv_layers:
                        #         # area.type = 'IMAGE_EDITOR'
                        #     bpy.ops.uv.seams_from_islands()

                        #     # bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.001)
                        #     bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)

                        #     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                            
                        #     # if old_type != "":
                        #         # area.type = old_type
                        #     # area.type = 'INFO'


                        # bpy.ops.object.select_all(action='DESELECT')
                        # bakemesh.select_set(state=True)
                        # bpy.context.view_layer.objects.active = bakemesh




                        # selected_objects = bpy.context.selected_objects
                        # nuke_bsdf_textures(selected_objects, self.width, self.height)

                        # for ob in selected_objects:
                        #         if ob.type == 'MESH':


                        if target_object.active_material is not None:
                            for i in range(len(target_object.material_slots)):
                                bpy.ops.object.material_slot_remove()

                        # raise Exception('stopping script')

                        # bpy.ops.object.shade_smooth()
                        # bpy.context.object.data.use_auto_smooth = False
                        # bpy.ops.mesh.customdata_custom_splitnormals_clear()

                        assetName = target_object.name
                        matName = (assetName + "Mat")
                        mat = bpy.data.materials.new(name=matName)
                        
                        mat.use_nodes = True
                        texName_albedo = (assetName + "_albedo")
                        texName_roughness = (assetName + "_roughness")
                        texName_metal = (assetName + "_metallic")
                        texName_emission = (assetName + "_emission")
                        texName_normal = (assetName + "_normal") 
                        texName_ao = (assetName + "_ao") 
                        # texName_orm = (assetName + "_orm")

                        mat.node_tree.nodes.clear()
                        # bpy.ops.object.shade_smooth()
                        mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                        shader = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
                        shader.inputs[0].default_value = (1, 1, 1, 1)
                        mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])



                        if bake_albedo:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_albedo,  width=width, height=height)
                            mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])


                        if bake_ao:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_ao,  width=width, height=height)
                            mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])

                        if bake_roughness:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_roughness,  width=width, height=height)
                            mat.node_tree.links.new(texture.outputs[0], shader.inputs[7])

                        if bake_metallic:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_metal,  width=width, height=height)
                            mat.node_tree.links.new(texture.outputs[0], shader.inputs[4])

                        if bake_emission:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_emission,  width=width, height=height)
                            mat.node_tree.links.new(texture.outputs[0], shader.inputs[17])

                        if bake_normal:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_normal, width=width, height=height)
                            texture.image.colorspace_settings.name = 'Non-Color'
                            bump = mat.node_tree.nodes.new(type='ShaderNodeNormalMap')
                            mat.node_tree.links.new(texture.outputs[0], bump.inputs[1])
                            mat.node_tree.links.new(bump.outputs[0], shader.inputs[19])
                            bpy.ops.object.shade_smooth()
                            bpy.context.object.data.use_auto_smooth = False
                            bpy.ops.mesh.customdata_custom_splitnormals_clear()


                        # Assign it to object
                        if target_object.data.materials:
                            target_object.data.materials[0] = mat
                        else:
                            target_object.data.materials.append(mat)             

                        bpy.context.scene.render.tile_x =  width
                        bpy.context.scene.render.tile_y =  height
                        bpy.context.scene.cycles.max_bounces = 4
                        bpy.context.scene.cycles.diffuse_bounces = 4
                        bpy.context.scene.cycles.glossy_bounces = 4
                        bpy.context.scene.cycles.transparent_max_bounces = 4
                        bpy.context.scene.cycles.transmission_bounces = 4
                        bpy.context.scene.cycles.volume_bounces = 0

                        # bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name= bake_collection_name)

                        # bake_collection = bpy.data.collections.get(bake_collection_name)
                        # bpy.context.view_layer.active_layer_collection = bake_collection
                        # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

                        # bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = False
                        # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[source_collection_name]

                        # bpy.context.view_layer.active_layer_collection.exclude = False

                        bpy.ops.object.select_all(action='DESELECT')
                        if (settings.target_strategy == "target_automesh") or (settings.target_strategy == "target_duplicate") :
                            for ob in source_collection.objects :
                                if ob.type == 'MESH' : 
                                    bpy.context.view_layer.objects.active = ob
                                    ob.select_set(state=True)
                        target_object.select_set(state=True)                       
                        bpy.context.view_layer.objects.active = target_object

                        #bake the textures
                        bpy.context.scene.render.engine = 'CYCLES'

                        # if not len(target_object.material_slots):
                        #     bpy.ops.object.material_slot_add()

                        # if target_object.material_slots[0].material is None:
                        #     bpy.ops.material.new()

                        # matName = (target_object_name + "Mat")
                        # texName_lightmap = (target_object_name + "_lightmap")
                        # mat = bpy.data.materials.new(name=matName)
                        # mat.use_nodes = True
                        # mat.node_tree.nodes.clear()
                        # mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                        # shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                        # texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                        # texture.image = bpy.data.images.new(texName_lightmap, width=width, height=height)

                        # mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])

                        # shader.name = "Background"
                        # shader.label = "Background"

                        # mat_output = mat.node_tree.nodes.get('Material Output')
                        # mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])

                        matnodes = target_object.material_slots[0].material.node_tree.nodes
                        imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']


                        for n in imgnodes:
                            if n.image.name == texName_ao:
                                n.select = True
                                matnodes.active = n
                                bpy.context.scene.cycles.bake_type = 'AO'
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'BW'
                                if bake_ao_LoFi :
                                    bpy.context.scene.render.bake.use_selected_to_active = False
                                    bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = True
                                else :
                                    bpy.context.scene.render.bake.use_selected_to_active = True
                                    bpy.context.scene.render.bake.use_cage = True
                                    ray_length = target_object.dimensions[1] * bake_distance
                                    bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 256
                                bpy.context.scene.render.bake.margin = pixelMargin
                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='AO', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Ambient Oclusion texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='AO')
                                    n.image.pack()
                                
                                bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = False
                                progress_current += progress_step
                                wm.progress_update(int(progress_current))




                        if bake_ao_applied and bake_ao and bake_albedo:
                            if os.path.exists(file_dir):
                                if os.path.exists(materials_dir):
                                    outBakeFileName = (texName_albedo + "_w_ao")
                                    outRenderFileName = outBakeFileName

                                    # switch on nodes and get reference
                                    bpy.context.scene.use_nodes = True
                                    tree = bpy.context.scene.node_tree

                                    #clear default nodes
                                    for node in tree.nodes:
                                            tree.nodes.remove(node)
                                    
                                    for image in bpy.data.images:
                                        if (texName_ao) in image.name:
                                            ao_image = image
                                            ao_image_node = tree.nodes.new('CompositorNodeImage')
                                            ao_image_node.image = ao_image

                                        if (texName_albedo) in image.name:
                                            albedo_image = image
                                            albedo_image_node = tree.nodes.new('CompositorNodeImage')
                                            albedo_image_node.image = albedo_image


                                    # image = bpy.data.images.load(filepath= albedo_image)
                                    # viewer_node = bpy.context.scene.node_tree.nodes.new('CompositorNodeViewer')
                                    comp_node = tree.nodes.new('CompositorNodeComposite')   
                                    output_node = tree.nodes.new("CompositorNodeOutputFile")


                                    mix_node =  bpy.context.scene.node_tree.nodes.new("CompositorNodeMixRGB")
                                    mix_node.blend_type = 'MULTIPLY'


                                    gamma_node =  bpy.context.scene.node_tree.nodes.new("CompositorNodeGamma")
                                    gamma_node.inputs[1].default_value = 2
                                    tree.links.new(ao_image_node.outputs['Image'], gamma_node.inputs[0])
                                    tree.links.new(gamma_node.outputs['Image'], mix_node.inputs[1])
                                    tree.links.new(albedo_image_node.outputs['Image'], mix_node.inputs[2])


                                    # bpy.context.scene.node_tree.links.new(mix_node.outputs[0], viewer_node.inputs[0])

                                    # baked_ao_image = bpy.data.images.new(texName_albedo + "_w_ao",  width=width, height=height)


                                    output_node.base_path =  materials_dir
                                    output_node.file_slots[0].path = outBakeFileName
                                    output_node.format.file_format = 'PNG'
                                    output_node.format.color_mode = 'RGB'

                                    tree.links.new(mix_node.outputs[0], output_node.inputs[0])
                                    tree.links.new(mix_node.outputs[0], comp_node.inputs[0])

                                    bpy.context.scene.render.use_file_extension = True

                                    bpy.ops.render.render(animation=False, write_still=True)


                                    outRenderFileNamePadded = materials_dir+outBakeFileName+"0001.png"
                                    outRenderFileName = materials_dir+outBakeFileName+".png"
                                    if os.path.exists(outRenderFileName):
                                        os.remove(outRenderFileName)
                                    os.rename(outRenderFileNamePadded, outRenderFileName)

                                    bpy.ops.node.save_image_file_node()


                                    # image = bpy.data.images['Viewer Node']
                                    # image.save_render(outRenderFileName, scene=None)

                                    self.report({'INFO'},"Composited texture saved to: " + outRenderFileName )

                                    texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                                    try:
                                        img = bpy.data.images.load(outRenderFileName)
                                        texture.image = img
                                        mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])
                                    except:
                                        raise NameError("Cannot load image %s" % path)

                                    # baked_ao_image.image.pack()





                        for n in imgnodes:
                            if n.image.name == texName_albedo:
                                n.select = True
                                matnodes.active = n
                                bpy.context.scene.cycles.bake_type = 'DIFFUSE'
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'RGBA'
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_direct = False
                                bpy.context.scene.render.bake.use_pass_color = True
                                bpy.context.scene.render.bake.use_selected_to_active = True
                                bpy.context.scene.render.bake.use_cage = True
                                ray_length = target_object.dimensions[1] * bake_distance
                                bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 8
                                bpy.context.scene.render.bake.margin = pixelMargin
                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='DIFFUSE', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked albedo texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='DIFFUSE')
                                    n.image.pack()
                                progress_current += progress_step
                                wm.progress_update(int(progress_current))


                        for n in imgnodes:
                            if n.image.name == texName_normal:
                                n.select = True
                                matnodes.active = n
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '16'
                                bpy.context.scene.render.image_settings.color_mode = 'RGB'
                                bpy.context.scene.cycles.samples = 64
                                bpy.context.scene.render.bake.margin = pixelMargin

                                for mod in [m for m in target_object.modifiers if m.type == 'MULTIRES']:
                                    hasMultires = True
                                    mod.levels = 0
                                
                                if not hasMultires :
                                    # bpy.context.scene.render.use_bake_multires = True
                                    # bpy.context.scene.render.bake_type = 'NORMALS'
                                    # bpy.context.view_layer.objects.active = target_object
                                # else :
                                    bpy.context.scene.render.use_bake_multires = False
                                    bpy.context.scene.cycles.bake_type = 'NORMAL'
                                    bpy.context.scene.render.bake.use_selected_to_active = True
                                    bpy.context.scene.render.bake.use_cage = True
                                    ray_length = target_object.dimensions[1] * bake_distance
                                    bpy.context.scene.render.bake.cage_extrusion = ray_length

                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        if hasMultires :
                                            # error here because the soruce meshes might not have UV's   the logic should probably not have them selected.
                                            bpy.ops.object.bake(type='NORMAL', filepath=outRenderFileName, save_mode='EXTERNAL', use_selected_to_active=False)
                                        else:
                                            bpy.ops.object.bake(type='NORMAL', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked normal texture saved to: " + outRenderFileName )
                                else:
                                    if hasMultires :
                                        bpy.ops.object.bake(type='NORMAL', use_selected_to_active=False)
                                    else :
                                        bpy.ops.object.bake(type='NORMAL')
                                    n.image.pack()

                                # apply modifiers
                                for mod in [m for m in target_object.modifiers if m.type == 'MULTIRES']:
                                    mod.levels = 0
                                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)     
                                # for mod in [m for m in target_object.modifiers]:

                                progress_current += progress_step
                                wm.progress_update(int(progress_current))

                        for n in imgnodes:
                            if n.image.name == texName_metal:
                                n.select = True
                                matnodes.active = n
                                existing_albedo_color = (0, 0, 0, 1)
                                existing_metal_color = (0, 0, 0, 1)

                                bpy.context.scene.cycles.bake_type = 'Diffuse'
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'BW'
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_direct = False
                                bpy.context.scene.render.bake.use_pass_color = True
                                bpy.context.scene.render.bake.use_selected_to_active = True
                                bpy.context.scene.render.bake.use_cage = True
                                ray_length = target_object.dimensions[1] * bake_distance
                                bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 4
                                bpy.context.scene.render.bake.margin = pixelMargin

                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for mat in tmp_src.data.materials:
                                            tmp_src.active_material = mat
                                            shadernodes = [n for n in matnodes if n.type == 'ShaderNodeBsdfPrincipled']
                                            for n in shadernodes:

                                                # get albedo input
                                                if not n.inputs[0].links:
                                                    existing_albedo_color = n.inputs[0].default_value
                                                else:
                                                    existing_albedo_color_input = n.inputs[0].links[0].from_node

                                                # get metallic input
                                                if not n.inputs[4].links:
                                                    existing_metal_color = n.inputs[4].default_value
                                                else:
                                                    existing_metal_color_input = n.inputs[4].links[0].from_node

                                                # link metallic connection to albedo
                                                if existing_metal_color:
                                                    n.inputs[0].default_value = existing_metal_color
                                                if existing_metal_color_input:
                                                    mat.node_tree.links.new(existing_metal_color_input.outputs[0], n.inputs[0])




                                                # restore albedo connection
                                                if existing_metal_color:
                                                    n.inputs[0].default_value = existing_albedo_color
                                                if existing_metal_color_input:
                                                    mat.node_tree.links.new(shader.inputs[0], existing_albedo_color_input.outputs[0])

                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='GLOSSY', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked metal texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='GLOSSY')
                                    n.image.pack()
                                progress_current += progress_step
                                wm.progress_update(int(progress_current))


                                #create tmp shader and connect texture to it.
                                for sob in source_meshes:
                                    if ob.data.materials:
                                        for mat in ob.data.materials:
                                            ob.active_material = mat
                                            shadernodes = [n for n in matnodes if n.type == 'ShaderNodeBsdfPrincipled']
                                            for n in shadernodes:
                                                existing_shader_color_input = n.inputs[0].links[0].from_node
                                                mat.node_tree.links.new(shader.inputs[0], existing_shader_color_input.outputs[0])

                                            tmpshader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                                            mat.node_tree.links.new(tmpshader.outputs[0], mat_output.inputs[0])


                                            #cleanup.
                                            mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])
                                            mat.node_tree.nodes.remove(tmpshader)



                        for n in imgnodes:
                            if n.image.name == texName_roughness:
                                n.select = True
                                matnodes.active = n
                                bpy.context.scene.cycles.bake_type = 'ROUGHNESS'
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'BW'
                                bpy.context.scene.render.bake.use_selected_to_active = True
                                bpy.context.scene.render.bake.use_cage = True
                                ray_length = target_object.dimensions[1] * bake_distance
                                bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 64
                                bpy.context.scene.render.bake.margin = pixelMargin
                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='ROUGHNESS', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked roughness texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='ROUGHNESS')
                                    n.image.pack()
                                progress_current += progress_step
                                wm.progress_update(int(progress_current))

                        for n in imgnodes:
                            if n.image.name == texName_emission:
                                n.select = True
                                matnodes.active = n
                                bpy.context.scene.cycles.bake_type = 'EMIT'
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'BW'
                                bpy.context.scene.render.bake.use_selected_to_active = True
                                bpy.context.scene.render.bake.use_cage = True
                                ray_length = target_object.dimensions[1] * bake_distance
                                bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 64
                                bpy.context.scene.render.bake.margin = pixelMargin
                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='EMIT', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked emission texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='EMIT')
                                    n.image.pack()
                                progress_current += progress_step
                                wm.progress_update(int(progress_current))


                        # bpy.context.scene.cycles.bake_type = 'NORMAL'
                        # bpy.context.scene.cycles.bake_type = 'AO'
                        # bpy.context.scene.cycles.bake_type = 'ROUGHNESS'
                        # bpy.context.scene.cycles.bake_type = 'GLOSSY'
                        # if self.bake_emmision :
                        #     bpy.context.scene.cycles.bake_type = 'EMIT'
                        

                        # for image in bpy.data.images:
                        #     if (bake_mesh_name + "_albedo") in image.name:
                        #         image.pack()

            bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = True
            bpy.context.view_layer.layer_collection.children[export_collection_name].children[bake_collection_name].exclude = False
            
            # export_collection.children[bake_collection_name].exclude = False
            bpy.context.scene.render.engine = 'BLENDER_EEVEE'


            if bake_outline :
                outline(bake_meshes)
                progress_current += progress_step
                wm.progress_update(int(progress_current))



            if bake_background :
                active_camera = bpy.context.scene.camera
                skyball_cam = bpy.context.scene.camera
                skyball_cam_object = bpy.context.selected_objects[0]
                bpy.context.scene.render.engine = 'CYCLES'



                if active_camera is not None :
                    camera_collection = active_camera.users_collection[0]
                    if camera_collection is not export_collection:
                        export_collection.objects.link(active_camera)
                    bpy.ops.object.select_all(action='DESELECT')
                    active_camera.select_set(state=True)
                    bpy.context.view_layer.objects.active = active_camera
                else :
                    skyball_cam = bpy.data.cameras.new("MirrorBallCamera")
                    skyball_cam_object = bpy.data.objects.new("MirrorBallCamera",skyball_cam)
                    bpy.context.scene.collection.objects.link(skyball_cam_object)
                    bpy.ops.object.select_all(action='DESELECT')
                    skyball_cam_object.select_set(state=True)
                    bpy.context.view_layer.objects.active = skyball_cam_object

                bpy.context.scene.camera = skyball_cam_object
                bpy.context.object.data.type = 'PANO'
                bpy.context.object.data.cycles.panorama_type = 'MIRRORBALL'
                bpy.context.object.rotation_euler[0] = 1.5708
                # bpy.context.object.rotation_euler[2] = 3.14159 #180
                bpy.context.object.rotation_euler[2] = 0

                skyball_cam_object.location[2] = 1.61
                bpy.context.scene.render.resolution_x = 4096
                bpy.context.scene.render.resolution_y = 4096
                bpy.context.scene.render.resolution_percentage = 100
                bpy.context.scene.cycles.samples = 32
                bpy.ops.render.render( animation=False, write_still=False )

                img_name = "skyball.png"

                # Render to Packed image.
                file_path = bpy.data.filepath
                file_name = bpy.path.display_name_from_filepath(file_path)
                file_ext = '.blend'
                file_dir = file_path.replace(file_name+file_ext, '')
                outRenderFileName = file_dir + "/" + img_name

                if os.path.exists(outRenderFileName):
                    os.remove(outRenderFileName)

                bpy.data.images['Render Result'].save_render(outRenderFileName)

                if os.path.exists(outRenderFileName):
                    bpy.ops.image.open(filepath = outRenderFileName)
                    bpy.data.images[img_name].pack()
                    os.remove(outRenderFileName)

                bpy.context.view_layer.layer_collection.children[export_collection_name].children[bake_collection_name].exclude = False


                #reset active camera
                bpy.context.scene.camera = active_camera
                bpy.ops.object.select_all(action='DESELECT')
                skyball_cam_object.select_set(state=True)
                bpy.context.view_layer.objects.active = skyball_cam_object
                bpy.ops.object.delete(use_global=False)

                bpy.ops.object.select_all(action='DESELECT')
                load_resource("skyball.blend")
                skyball_objects = bpy.context.selected_objects
                for ob in skyball_objects:
                    if ob.type == 'MESH':
                        if ob.active_material is not None:
                            ob.active_material.node_tree.nodes.clear()
                            for i in range(len(ob.material_slots)):
                                bpy.ops.object.material_slot_remove({'object': ob})
                        bpy.ops.object.shade_smooth()

                        assetName = ob.name
                        matName = (assetName + "Mat")
                        mat = bpy.data.materials.new(name=matName)
                        mat.use_nodes = True
                        mat.node_tree.nodes.clear()
                        mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                        shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                        texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                        texture.image = bpy.data.images[img_name]

                        mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])

                        shader.name = "Background"
                        shader.label = "Background"

                        mat_output = mat.node_tree.nodes.get('Material Output')
                        mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])



                        # Assign it to object
                        if ob.data.materials:
                            ob.data.materials[0] = mat
                        else:
                            ob.data.materials.append(mat)
                        export_collection.objects.link(ob)
                        bpy.context.scene.collection.objects.unlink(ob)



                        

                bpy.ops.object.select_all(action='DESELECT')
                load_resource("skyball_warp.blend")
                skyball_warp_objects = bpy.context.selected_objects
                for ob in skyball_warp_objects:
                    if ob.type == 'MESH':
                        if ob.active_material is not None:
                            ob.active_material.node_tree.nodes.clear()
                            for i in range(len(ob.material_slots)):
                                bpy.ops.object.material_slot_remove({'object': ob})
                        bpy.ops.object.shade_smooth()

                        assetName = ob.name
                        matName = (assetName + "Mat")
                        mat = bpy.data.materials.new(name=matName)
                        mat.use_nodes = True
                        mat.node_tree.nodes.clear()
                        mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                        shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                        texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                        texture.image = bpy.data.images.new("skyball_warp.png", width=width, height=height)

                        mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])

                        shader.name = "Background"
                        shader.label = "Background"

                        mat_output = mat.node_tree.nodes.get('Material Output')
                        mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])



                        # Assign it to object
                        if ob.data.materials:
                            ob.data.materials[0] = mat
                        else:
                            ob.data.materials.append(mat)
                        export_collection.objects.link(ob)
                        bpy.context.scene.collection.objects.unlink(ob)
                        

                bpy.ops.object.select_all(action='DESELECT')
                skyball_objects[0].select_set(state=True)
                skyball_warp_objects[0].select_set(state=True)
                bpy.context.view_layer.objects.active = skyball_warp_objects[0]

                #bake the textures
                bpy.context.scene.render.tile_x =  width
                bpy.context.scene.render.tile_y =  height
                bpy.context.scene.cycles.max_bounces = 1
                bpy.context.scene.cycles.diffuse_bounces = 1
                bpy.context.scene.cycles.glossy_bounces = 1
                bpy.context.scene.cycles.transparent_max_bounces = 1
                bpy.context.scene.cycles.transmission_bounces = 1
                bpy.context.scene.cycles.volume_bounces = 0

                bpy.context.scene.render.engine = 'CYCLES'
                bpy.context.scene.cycles.samples = 1

                matnodes = bpy.context.active_object.material_slots[0].material.node_tree.nodes
                imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']

                for n in imgnodes:
                    n.select = True
                    matnodes.active = n
                    bpy.context.scene.cycles.bake_type = 'COMBINED'
                    bpy.context.scene.render.image_settings.color_depth = '8'
                    bpy.context.scene.render.image_settings.color_mode = 'RGB'
                    bpy.context.scene.render.image_settings.file_format = 'PNG'
                    bpy.context.scene.render.bake.use_pass_indirect = False
                    bpy.context.scene.render.bake.use_pass_direct = False
                    bpy.context.scene.render.bake.use_pass_color = True
                    bpy.context.scene.render.bake.use_selected_to_active = True
                    bpy.context.scene.render.bake.use_cage = True
                    ray_length = skyball_warp_objects[0].dimensions[1] * bake_distance
                    bpy.context.scene.render.bake.cage_extrusion = ray_length
                    if os.path.exists(file_dir):
                        if os.path.exists(materials_dir):
                            outBakeFileName = n.image.name+".png"
                            outRenderFileName = materials_dir+outBakeFileName
                            n.image.file_format = 'PNG'
                            n.image.filepath = outRenderFileName
                            bpy.ops.object.bake(type='COMBINED', filepath=outRenderFileName, save_mode='EXTERNAL')
                            n.image.save()
                            self.report({'INFO'},"Baked skyball texture saved to: " + outRenderFileName )
                    else:
                        bpy.ops.object.bake(type='COMBINED')
                        n.image.pack()
                    progress_current += progress_step
                    wm.progress_update(int(progress_current))


                # bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name= bake_collection_name)
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[source_collection_name]

            wm.progress_end()

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

#------------------------------------------------------

def populate_coll(scene):
    bpy.app.handlers.scene_update_pre.remove(populate_coll)
    scene.coll.clear()
    for identifier, name, description in enum_items:
        scene.coll.add().name = name

def menu_draw_bake(self, context):
    self.layout.operator("view3d.spiraloid_bake_panel", 
        text="Bake Panel...")

    bpy.ops.object.dialog_operator('INVOKE_DEFAULT')

class BR_MT_3d_comic_menu(bpy.types.Menu):
    bl_idname = "INFO_HT_3d_comic_menu"
    bl_label = "3D Comics"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.spiraloid_new_3d_comic")
        layout.separator()
        layout.menu(BR_MT_3d_comic_submenu_panels.bl_idname, icon="VIEW_ORTHO")
        layout.menu(BR_MT_3d_comic_submenu_letters.bl_idname, icon="OUTLINER_OB_FONT")
        layout.menu(BR_MT_3d_comic_submenu_assets.bl_idname, icon="GHOST_ENABLED")
        layout.menu(BR_MT_3d_comic_submenu_lighting.bl_idname, icon="LIGHT_SUN")
        layout.separator()
        layout.menu(BR_MT_3d_comic_submenu_utilities.bl_idname, icon="PREFERENCES")
        layout.separator()
        layout.operator("view3d.spiraloid_3d_comic_preview", icon= "FILE_MOVIE")
        layout.separator()
        layout.operator("view3d.spiraloid_build_3d_comic", icon="RENDER_RESULT")
        layout.separator()
        layout.operator("view3d.spiraloid_read_3d_comic", icon="HIDE_OFF")

class BR_MT_3d_comic_submenu_panels(bpy.types.Menu):
    bl_idname = 'view3d.spiraloid_3d_comic_submenu_panels'
    bl_label = 'Panels'

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.spiraloid_3d_comic_first_panel", icon="TRIA_UP")
        layout.operator("view3d.spiraloid_3d_comic_next_panel", icon="TRIA_RIGHT")
        layout.operator("view3d.spiraloid_3d_comic_previous_panel", icon="TRIA_LEFT")
        layout.operator("view3d.spiraloid_3d_comic_last_panel", icon="TRIA_DOWN")
        layout.separator()
        layout.operator("view3d.spiraloid_3d_comic_create_panel")
        layout.operator("view3d.spiraloid_3d_comic_clone_panel")
        layout.operator("view3d.spiraloid_3d_comic_delete_panel")
        layout.operator("view3d.spiraloid_3d_comic_reorder_scene_earlier")
        layout.operator("view3d.spiraloid_3d_comic_reorder_scene_later")
        layout.separator()
        layout.operator("view3d.spiraloid_3d_comic_panel_init")

class BR_MT_3d_comic_submenu_letters(bpy.types.Menu):
    bl_idname = 'view3d.spiraloid_3d_comic_submenu_letters'
    bl_label = 'Letters'

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.spiraloid_3d_comic_add_letter_wordballoon")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_caption")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_sfx")

class BR_MT_3d_comic_submenu_assets(bpy.types.Menu):
    bl_idname = 'view3d.spiraloid_3d_comic_submenu_assets'
    bl_label = 'Assets'

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.spiraloid_3d_comic_add_ground")
        layout.operator("view3d.spiraloid_3d_comic_workshop")



class BR_MT_3d_comic_submenu_utilities(bpy.types.Menu):
    bl_idname = 'view3d.spiraloid_3d_comic_submenu_utilities'
    bl_label = 'Utilities'

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.spiraloid_3d_comic_outline")
        layout.operator("view3d.spiraloid_bake_panel", icon="TEXTURE_DATA")




class BR_MT_3d_comic_submenu_lighting(bpy.types.Menu):
    bl_idname = 'view3d.spiraloid_3d_comic_submenu_lighting'
    bl_label = 'Filter'

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.spiraloid_3d_comic_init_workshop_lighting")
        layout.operator("view3d.spiraloid_3d_comic_init_ink_lighting")
        # layout.operator("view3d.spiraloid_3d_comic_init_vehicle_lighting")
        # layout.operator("view3d.spiraloid_3d_comic_init_magic_hour_lighting")




def draw_item(self, context):
    layout = self.layout
    layout.menu(BR_MT_3d_comic_menu.bl_idname)

#------------------------------------------------------

def register():
    bpy.utils.register_class(BR_OT_panel_init)
    bpy.utils.register_class(BR_MT_3d_comic_menu)
    bpy.utils.register_class(BR_MT_3d_comic_submenu_panels)
    bpy.utils.register_class(BR_MT_3d_comic_submenu_letters)
    bpy.utils.register_class(BR_OT_spiraloid_3d_comic_workshop)
    bpy.utils.register_class(BR_OT_add_outline)

    bpy.utils.register_class(BR_OT_bake_panel)
    bpy.utils.register_class(BR_OT_new_3d_comic) 

    bpy.utils.register_class(BR_OT_next_panel_scene)      
    bpy.utils.register_class(BR_OT_previous_panel_scene)
    bpy.utils.register_class(BR_OT_first_panel_scene)
    bpy.utils.register_class(BR_OT_last_panel_scene)

    bpy.utils.register_class(BR_OT_panel_init_workshop_lighting)
    bpy.utils.register_class(BR_OT_panel_init_ink_lighting)
    bpy.utils.register_class(BR_MT_3d_comic_submenu_lighting)
    bpy.utils.register_class(BR_MT_3d_comic_submenu_utilities)

    bpy.utils.register_class(BR_OT_reorder_scene_later)   
    bpy.utils.register_class(BR_OT_reorder_scene_earlier)   
    bpy.utils.register_class(BR_OT_insert_comic_scene)       
    bpy.utils.register_class(BR_OT_clone_comic_scene)       
    bpy.utils.register_class(BR_OT_add_letter_caption) 
    bpy.utils.register_class(BR_OT_add_letter_wordballoon) 
    bpy.utils.register_class(BR_OT_add_letter_sfx) 

    bpy.utils.register_class(BR_OT_add_ground) 
    bpy.utils.register_class(BR_MT_3d_comic_submenu_assets) 


    bpy.utils.register_class(BR_OT_regenerate_3d_comic_preview) 
    bpy.utils.register_class(BR_OT_delete_comic_scene)      
    bpy.utils.register_class(BR_OT_build_3d_comic) 
    bpy.utils.register_class(BR_OT_read_3d_comic) 

    bpy.utils.register_class(BakePanelSettings)
    

    bpy.utils.register_class(ComicPreferences)

    bpy.types.Scene.bake_panel_settings = bpy.props.PointerProperty(type=BakePanelSettings)
    
    bpy.types.TOPBAR_MT_editor_menus.append(draw_item)

def unregister():
    bpy.utils.unregister_class(BR_OT_panel_init)
    bpy.utils.unregister_class(BR_MT_3d_comic_menu)
    bpy.utils.unregister_class(BR_MT_3d_comic_submenu_panels)
    bpy.utils.unregister_class(BR_MT_3d_comic_submenu_letters)
    bpy.utils.unregister_class(BR_OT_spiraloid_3d_comic_workshop) 
    bpy.utils.unregister_class(BR_OT_add_outline) 
    
    bpy.utils.unregister_class(BR_OT_bake_panel) 
    bpy.utils.unregister_class(BR_OT_new_3d_comic)
    bpy.utils.unregister_class(BR_OT_next_panel_scene)      
    bpy.utils.unregister_class(BR_OT_previous_panel_scene)  
    bpy.utils.unregister_class(BR_OT_first_panel_scene)
    bpy.utils.unregister_class(BR_OT_last_panel_scene)

    bpy.utils.unregister_class(BR_OT_panel_init_workshop_lighting)
    bpy.utils.unregister_class(BR_OT_panel_init_ink_lighting)
    bpy.utils.unregister_class(BR_MT_3d_comic_submenu_lighting)
    bpy.utils.unregister_class(BR_MT_3d_comic_submenu_utilities)
    
    bpy.utils.unregister_class(BR_OT_reorder_scene_later)   
    bpy.utils.unregister_class(BR_OT_reorder_scene_earlier)   

    bpy.utils.unregister_class(BR_OT_insert_comic_scene)      
    bpy.utils.unregister_class(BR_OT_clone_comic_scene)      
    bpy.utils.unregister_class(BR_OT_add_letter_caption) 
    bpy.utils.unregister_class(BR_OT_add_letter_wordballoon) 
    bpy.utils.unregister_class(BR_OT_add_letter_sfx) 

    bpy.utils.unregister_class(BR_OT_add_ground) 
    bpy.utils.unregister_class(BR_MT_3d_comic_submenu_assets) 

    bpy.utils.unregister_class(BR_OT_regenerate_3d_comic_preview) 
    bpy.utils.unregister_class(BR_OT_delete_comic_scene)      
    bpy.utils.unregister_class(BR_OT_build_3d_comic) 
    bpy.utils.unregister_class(BR_OT_read_3d_comic) 
    bpy.utils.unregister_class(BakePanelSettings)

    bpy.utils.unregister_class(ComicPreferences)
    
    bpy.types.TOPBAR_MT_editor_menus.remove(draw_item)

    if __name__ != "__main__":
        bpy.types.TOPBAR_MT_editor_menus.remove(menu_draw_bake)
#    bpy.types.SEQUENCER_MT_add.remove(add_object_button)

if __name__ == "__main__":
    register()

    # The menu can also be called from scripts
#bpy.ops.wm.call_menu(name=BR_MT_3d_comic_menu.bl_idname)

#debug console
#__import__('code').interact(local=dict(globals(), **locals()))
# pauses wherever this line is:
# code.interact