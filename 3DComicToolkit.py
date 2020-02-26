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
from bpy_extras.io_utils import ImportHelper
import os.path
import bpy, os
from platform import system

from bpy.props import *
import subprocess

import os
import warnings
import re
from itertools import count, repeat
from collections import namedtuple
from math import pi

import bpy
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



class BR_OT_spiraloid_3d_comic_workshop(bpy.types.Operator):
    """Visit the spiraloid workshop for updates and goodies!"""
    bl_idname = "view3d.spiraloid_3d_comic_workshop"
    bl_label = "Visit Workshop..."
    def execute(self, context):                
        subprocess.Popen('start '+ 'http://www.spiraloid.net')
        return {'FINISHED'}

def scene_mychosenobject_poll(self, object):
    return object.type == 'MESH'


def load_resource(blendFileName):
    user_dir = os.path.expanduser("~")
    common_subdir = "2.82/scripts/addons/3DComicToolkit/Resources/"
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
    mainCollection = context.scene.collection
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        for name in data_from.scenes:
            scenes.append({'name': name})
        action = bpy.ops.wm.append
        action(directory=filepath + "/Scene/", files=scenes)
        scenes = bpy.data.scenes[-len(scenes):]
    for scene in scenes:
        for coll in scene.collection.children:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in coll.all_objects:
                bpy.context.collection.objects.link(obj)  
                obj.select_set(state=True)
                bpy.context.view_layer.objects.active = obj
        bpy.data.scenes.remove(scene)

    return {'FINISHED'}


class BakePanelSettings(bpy.types.PropertyGroup):
    target_automesh : bpy.props.BoolProperty(name="Automesh", description="Generate a new mesh to recieve textures", default=True)
    target_existing : bpy.props.BoolProperty(name="Existing", description="Use an existing UV mapped mesh to recieve textures", default=True)
    target_clone : bpy.props.BoolProperty(name="Clone", description="Duplicate objects in collection to recieve textures", default=True)

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
            ("target_clone","Duplicate", "Duplicate", 1),
            ("target_existing", "Existing","Existing", 2),
            ("target_automesh", "Automesh","Automesh", 3),
            },
        default="target_automesh"
    )

    bakeSize : bpy.props.EnumProperty(
        name="Size", 
        description="Width in pixels for baked texture size", 
        items={
            ("size_128", "128","128 pixels", 1),
            ("size_512", "512","512 pixels", 2),
            ("size_1024","1024", "1024 pixels", 3),
            ("size_2048", "2048","2048 pixels", 4),
            ("size_4096", "4096","4096 pixels", 5),
            ("size_8192", "8192","8192 pixels", 6),
            },
        default="size_1024"
    )
    bake_distance : bpy.props.FloatProperty(name="Bake Distance Scale",  description="raycast is largest dimension * this value ", min=0, max=3, default=0.02 )
    bake_to_unlit : bpy.props.BoolProperty(name="Bake Lightmap", description="Bake Collection to new mesh with lightmap texture and unlit shader", default=True)
    bake_albedo : bpy.props.BoolProperty(name="Bake Albedo", description="Bake Collection to mesh with Albedo Texture", default=False)
    bake_normal : bpy.props.BoolProperty(name="Bake Normal", description="Bake Collection to mesh with Normal Texture", default=False)
    bake_metallic : bpy.props.BoolProperty(name="Bake Metallic", description="Bake Collection to mesh with Metallic Texture", default=False)
    bake_roughness : bpy.props.BoolProperty(name="Bake Roughness", description="Bake Collection to mesh with Roughness Texture", default=False)
    bake_emission : bpy.props.BoolProperty(name="Bake Emission", description="Bake Collection to mesh with Emission Texture", default=False)
    bake_opacity : bpy.props.BoolProperty(name="Bake Opacity", description="Bake Collection to mesh with Opacity Texture", default=False)
    bake_ao : bpy.props.BoolProperty(name="Bake AO", description="Bake Collection to mesh with Ambient Occlusion Texture", default=False)
    bake_w_decimate : bpy.props.BoolProperty(name="Decimate", description="Bake and Emission Textures", default=True)
    bake_w_decimate_ratio : bpy.props.FloatProperty(name="Decimate Ratio",  description="Amount to decimate target mesh", min=0, max=1, default=0.5 )
    bake_outline : bpy.props.BoolProperty(name="Outline", description="Add ink outline to bake mesh", default=True)
    bake_background : bpy.props.BoolProperty(name="Background", description="Bake all but collection to skyball", default=True)

class BR_OT_bake_panel(bpy.types.Operator):
    """Merge all meshes in active collection, unwrap and bake lighting and textures into a new "Export" collection"""
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
        layout.separator()
        layout.prop(bake_panel_settings, "bake_albedo")
        layout.prop(bake_panel_settings, "bake_normal")
        layout.prop(bake_panel_settings, "bake_metallic")
        layout.prop(bake_panel_settings, "bake_roughness")
        layout.prop(bake_panel_settings, "bake_emission")
        layout.prop(bake_panel_settings, "bake_opacity")
        layout.prop(bake_panel_settings, "bake_ao")
        layout.separator()
        layout.prop(bake_panel_settings, "bake_w_decimate")
        layout.prop(bake_panel_settings, "bake_w_decimate_ratio")
        layout.separator()
        layout.prop(bake_panel_settings, "bake_outline")
        layout.separator()
        layout.prop(bake_panel_settings, "bake_background")
        layout.separator()


    def execute(self, context):
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        # manage export collection 
        layer_collection = bpy.context.view_layer.layer_collection
        current_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
        current_collection = bpy.data.collections.get(current_collection_name)
        scene_collection = bpy.context.view_layer.layer_collection



        if current_collection is None :
            if context.view_layer.objects.active is not None :
                collections =  context.view_layer.objects.active.users_collection
                if len(collections) > 0:
                    bpy.context.view_layer.active_layer_collection = collections()
                    current_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
                    current_collection = bpy.data.collections.get(current_collection_name)
                else:
                    current_collection = scene_collection
                    self.report({'ERROR'}, 'You must select a collection!')
                    return {'FINISHED'} 

        # bake_collection_name = ("Lightmap Bake " + current_collection.name )
        bake_collection_name = ("Export")

        bake_mesh_name = ("BakeMesh  " + current_collection.name )


        obj = bpy.context.object
        # print ("::::::::::::::::::::::::::::::::::::::::::::::")

        # for area in bpy.context.screen.areas:
        #     if area.type == 'VIEW_3D':
        #         if bpy.context.selected_objects:
        #             bpy.ops.object.mode_set(mode='OBJECT', toggle=False)   
        bpy.ops.object.select_all(action='DESELECT')

        # cleanup previous bake collection 
        if bpy.data.collections.get(bake_collection_name) : 

            # bpy.context.view_layer.layer_collection.children[bake_collection_name].exclude = False
            # bake_collection = bpy.data.collections.get(bake_collection_name)
            # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[bake_collection_name]
            # bpy.ops.outliner.collection_delete(hierarchy=True)
            # bpy.context.scene.collection_delete(hierarchy=True)
            cc = bpy.context.view_layer.layer_collection.children[bake_collection_name].collection
            for o in cc.objects:
                bpy.data.objects.remove(o)
            bpy.context.scene.collection.children.unlink(cc)
            for c in bpy.data.collections:
                if not c.users:
                    bpy.data.collections.remove(c)


            for image in bpy.data.images:
                if bake_mesh_name in image.name:
                    bpy.data.images.remove(image)
                    self.report({'WARNING'}, 'Deleted previous bake images!')

            for mat in bpy.data.materials:
                if bake_mesh_name in mat.name:
                    bpy.data.materials.remove(mat)

            for tex in bpy.data.textures:
                if bake_mesh_name in tex.name:
                    bpy.data.textures.remove(tex)

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

                self.report({'WARNING'}, 'Deleted all previous bake data from scene!')






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
        if  settings.bakeSize == "size_512":
            width = 512
            height = 512
        if  settings.bakeSize == "size_1024":
            width = 1024
            height = 1024
        if  settings.bakeSize == "size_2048":
            width = 2048
            height = 2048
        if  settings.bakeSize == "size_4096":
            width = 4096
            height = 4096
        if  settings.bakeSize == "size_8192":
            width = 8192
            height = 8192

        bake_to_unlit = settings.bake_to_unlit
        bake_albedo = settings.bake_albedo
        bake_normal = settings.bake_normal
        bake_metallic = settings.bake_metallic
        bake_roughness = settings.bake_roughness
        bake_emission = settings.bake_emission
        bake_opacity = settings.bake_opacity
        bake_ao = settings.bake_ao
        decimate = settings.bake_w_decimate
        ratio = settings.bake_w_decimate_ratio
        bake_distance = settings.bake_distance
        bake_background = settings.bake_background
        bake_outline = settings.bake_outline

        # Setup Targets and Collections
        bpy.ops.object.select_all(action='DESELECT')
        for ob in current_collection.objects :
            if ob.type == 'MESH' : 
                print (ob.name)
                ob.select_set(state=True)
                bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        bakemeshes = []

        if settings.target_strategy == "target_automesh":
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((-4.37114e-08, -1, 0), (1, -4.37114e-08, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":True, "use_proportional_edit":False, "proportional_edit_falloff":'INVERSE_SQUARE', "proportional_size":0.101089, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            bpy.ops.object.booltool_auto_union()
            bm = bpy.context.object
            bakemeshes.append(bm)

        if settings.target_strategy == "target_existing":
            bakemesh = bpy.context.object
            bakemeshes.append(bm)

        if settings.target_strategy == "target_clone":
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((-4.37114e-08, -1, 0), (1, -4.37114e-08, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":True, "use_proportional_edit":False, "proportional_edit_falloff":'INVERSE_SQUARE', "proportional_size":0.101089, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            bakemeshes = bpy.context.selected_objects


        for bakemesh in bakemeshes :

            if bake_to_unlit :
                ## old collection logic
                # layer_collection = bpy.context.view_layer.layer_collection
                # current_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
                # current_collection = bpy.data.collections.get(current_collection_name)
                # scene_collection = bpy.context.view_layer.layer_collection
                # if current_collection is None :
                #     if context.view_layer.objects.active is not None :
                #         collections =  context.view_layer.objects.active.users_collection
                #         if len(collections) > 0:
                #             bpy.context.view_layer.active_layer_collection = collections()
                #             current_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
                #             current_collection = bpy.data.collections.get(current_collection_name)
                #         else:
                #             current_collection = scene_collection
                #             self.report({'ERROR'}, 'You must select a collection!')
                #             return {'FINISHED'} 

                # bake_collection_name = ("Lightmap Bake " + current_collection.name )
                # bake_mesh_name = ("Lightmap BakeMesh  " + current_collection.name )




                # bake_to_unlit = True
                # decimate = True



                # # verify all objects have UV's, if not create some.
                # bpy.ops.object.select_all(action='DESELECT')
                # for ob in current_collection.objects :
                #     if ob.type == 'MESH' : 
                #         print (ob.name)
                #         ob.select_set(state=True)
                #         bpy.context.view_layer.objects.active = ob
                #         if not len( ob.data.uv_layers ):
                #             bpy.ops.uv.smart_project()
                #             bpy.ops.uv.smart_project(angle_limit=66)
                #             bpy.ops.uv.smart_project(island_margin=0.05, user_area_weight=0)

                if target_strategy == "target_automesh" or target_strategy == "target_clone" :




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
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.select_all(action='SELECT')
                    # if bakemesh.data.uv_layers:
                        # area.type = 'IMAGE_EDITOR'
                    bpy.ops.uv.seams_from_islands()

                    bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.05)
                    bpy.ops.uv.minimize_stretch(iterations=1024)

                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    
                    # if old_type != "":
                        # area.type = old_type
                    # area.type = 'INFO'

                bakemesh.name = bake_mesh_name

                bpy.ops.object.select_all(action='DESELECT')
                bakemesh.select_set(state=True)
                bpy.context.view_layer.objects.active = bakemesh
                selected_objects = bpy.context.selected_objects
                # nuke_flat_texture(selected_objects, self.width, self.height)

                for ob in selected_objects:
                    if ob.type == 'MESH':
                        if ob.active_material is not None:
                            ob.active_material.node_tree.nodes.clear()
                            for i in range(len(ob.material_slots)):
                                bpy.ops.object.material_slot_remove({'object': ob})
                        bpy.ops.object.shade_smooth()

                        assetName = ob.name
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
                        if ob.data.materials:
                            ob.data.materials[0] = mat
                        else:
                            ob.data.materials.append(mat)  





                bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name= bake_collection_name)
                # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[current_collection_name]
                # bpy.context.view_layer.active_layer_collection.exclude = False

                bpy.ops.object.select_all(action='DESELECT')
                for ob in current_collection.objects :
                    if ob.type == 'MESH' : 
                        ob.select_set(state=True)

                bakemesh.select_set(state=True)
                bpy.context.view_layer.objects.active = bakemesh

                #bake the textures
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

                matnodes = bpy.context.active_object.material_slots[0].material.node_tree.nodes
                imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']

                for n in imgnodes:
                    if n.image.name == bake_mesh_name + "_lightmap":
                        n.select = True
                        matnodes.active = n
                        if os.path.exists(file_dir):
                            if os.path.exists(materials_dir):
                                outBakeFileName = n.image.name+".png"
                                outRenderFileName = materials_dir+outBakeFileName
                                n.image.file_format = 'PNG'
                                n.image.filepath = outRenderFileName
                                bpy.ops.object.bake(type='COMBINED', filepath=outRenderFileName, save_mode='EXTERNAL')
                                n.image.save()
                                self.report({'INFO'},"Baked lightmap texture saved to: " + outRenderFileName )
                        else:
                            bpy.ops.object.bake(type='COMBINED')
                            n.image.pack()




                # bpy.ops.object.bake('INVOKE_DEFAULT', type='COMBINED')
                # bpy.ops.object.bake("INVOKE_SCREEN", type='COMBINED')
                
                # bpy.context.view_layer.layer_collection.children[bake_collection_name].exclude = False
                # bpy.context.view_layer.layer_collection.children[current_collection_name].exclude = True


                bpy.context.view_layer.layer_collection.children[bake_collection_name].exclude = True
                bpy.context.view_layer.layer_collection.children[current_collection_name].exclude = False
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[current_collection_name]

            if bake_albedo or bake_normal or bake_roughness or bake_metallic or bake_emission or bake_opacity or bake_ao:

                layer_collection = bpy.context.view_layer.layer_collection
                current_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
                current_collection = bpy.data.collections.get(current_collection_name)
                scene_collection = bpy.context.view_layer.layer_collection
                if current_collection is None :
                    current_collection = scene_collection
                    self.report({'ERROR'}, 'You must select a collection!')
                    return {'FINISHED'} 

                bake_collection_name = ("BSDF Bake " + current_collection.name )
                bake_mesh_name = ("BakeMesh " + current_collection.name )
                # bake_to_unlit = True
                # decimate = True
                obj = bpy.context.object
                # print ("::::::::::::::::::::::::::::::::::::::::::::::")

                # for area in bpy.context.screen.areas:
                #     if area.type == 'VIEW_3D':
                #         if bpy.context.selected_objects:
                #             bpy.ops.object.mode_set(mode='OBJECT', toggle=False)   
                bpy.ops.object.select_all(action='DESELECT')
                # cleanup previous bake collection 
                if bpy.data.collections.get(bake_collection_name) : 

                    # bpy.context.view_layer.layer_collection.children[bake_collection_name].exclude = False
                    # bake_collection = bpy.data.collections.get(bake_collection_name)
                    # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[bake_collection_name]
                    # bpy.ops.outliner.collection_delete(hierarchy=True)
                    # bpy.context.scene.collection_delete(hierarchy=True)
                    cc = bpy.context.view_layer.layer_collection.children[bake_collection_name].collection
                    for o in cc.objects:
                        bpy.data.objects.remove(o)
                    bpy.context.scene.collection.children.unlink(cc)
                    for c in bpy.data.collections:
                        if not c.users:
                            bpy.data.collections.remove(c)


                    for image in bpy.data.images:
                        if bake_mesh_name in image.name:
                            bpy.data.images.remove(image)
                            self.report({'WARNING'}, 'Deleted previous bake images!')

                    for mat in bpy.data.materials:
                        if bake_mesh_name in mat.name:
                            bpy.data.materials.remove(mat)

                    for tex in bpy.data.textures:
                        if bake_mesh_name in tex.name:
                            bpy.data.textures.remove(tex)

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

                        self.report({'WARNING'}, 'Deleted all previous bake data from scene!')

                # if bakemesh is None:

                #     # verify all objects have UV's, if not create some.
                #     bpy.ops.object.select_all(action='DESELECT')
                #     for ob in current_collection.objects :
                #         if ob.type == 'MESH' : 
                #             bpy.ops.object.select_all(action='DESELECT')
                #             print (ob.name)
                #             ob.select_set(state=True)
                #             bpy.context.view_layer.objects.active = ob
                #             if not len( ob.data.uv_layers ):
                #                 bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                #                 bpy.ops.mesh.select_all(action='SELECT')
                #                 # bpy.ops.uv.smart_project()
                #                 # bpy.ops.uv.smart_project(angle_limit=66)
                #                 bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.01, user_area_weight=0.75)
                #                 bpy.ops.uv.average_islands_scale()

                #                 # select all faces
                #                 # bpy.ops.mesh.select_all(action='SELECT')
                #                 bpy.ops.uv.pack_islands(margin=0.017)

                #                 # bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.1)
                #                 bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                #                 # bpy.ops.uv.seams_from_islands()




                bpy.ops.object.select_all(action='DESELECT')
                print (ob.name)
                ob.select_set(state=True)
                bpy.context.view_layer.objects.active = ob
                if not len( ob.data.uv_layers ):
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.select_all(action='SELECT')
                    # bpy.ops.uv.smart_project()
                    # bpy.ops.uv.smart_project(angle_limit=66)
                    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.01, user_area_weight=0.75)
                    bpy.ops.uv.average_islands_scale()

                    # select all faces
                    # bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.uv.pack_islands(margin=0.017)

                    # bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.1)
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)



                    # select all objects and the bake mesh to prepare for bake
                    bpy.ops.object.select_all(action='DESELECT')
                    for ob in current_collection.objects :
                        if ob.type == 'MESH' : 
                            print (ob.name)
                            ob.select_set(state=True)
                            bpy.context.view_layer.objects.active = ob
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)



                    # this duplicates meshes and puts them in the new collection but it doesn't deal w instances well. perhaps duplicate collection might be a better way to go here...
                    # we need to make all instances real before joining    
                    # bpy.ops.object.select_all(action='SELECT')
                    # bpy.ops.object.duplicates_make_real()
                    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((-4.37114e-08, -1, 0), (1, -4.37114e-08, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":True, "use_proportional_edit":False, "proportional_edit_falloff":'INVERSE_SQUARE', "proportional_size":0.101089, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})


                    bpy.ops.object.booltool_auto_union()

                    bakemesh = bpy.context.object

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
                        bpy.context.object.modifiers["Decimate"].ratio = ratio
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

                    # area = bpy.context.area
                    # old_type = area.type
                    # area.type = 'VIEW_3D'
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.select_all(action='SELECT')
                    # if bakemesh.data.uv_layers:
                        # area.type = 'IMAGE_EDITOR'
                    bpy.ops.uv.seams_from_islands()

                    # bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.001)
                    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)

                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    
                    # if old_type != "":
                        # area.type = old_type
                    # area.type = 'INFO'
                bakemesh.name = bake_mesh_name

                bpy.ops.object.select_all(action='DESELECT')
                bakemesh.select_set(state=True)
                bpy.context.view_layer.objects.active = bakemesh
                selected_objects = bpy.context.selected_objects
                # nuke_bsdf_textures(selected_objects, self.width, self.height)

                for ob in selected_objects:
                        if ob.type == 'MESH':
                            if ob.active_material is not None:
                                ob.active_material.node_tree.nodes.clear()
                                for i in range(len(ob.material_slots)):
                                    bpy.ops.object.material_slot_remove({'object': ob})
                            bpy.ops.object.shade_smooth()
                            bpy.context.object.data.use_auto_smooth = False
                            bpy.ops.mesh.customdata_custom_splitnormals_clear()

                            assetName = ob.name
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
                            bpy.ops.object.shade_smooth()
                            mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                            shader = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
                            shader.inputs[0].default_value = (1, 1, 1, 1)
                            mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])

                            if bake_albedo:
                                bpy.context.scene.render.bake.use_pass_direct = False
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_color = True
                                texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                                texture.image = bpy.data.images.new(texName_albedo,  width=width, height=height)
                                mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])

                            # if bake_opacity:


                            if bake_ao:
                                texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                                texture.image = bpy.data.images.new(texName_ao,  width=width, height=height)
                                mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])



                            if bake_roughness:
                                bpy.context.scene.render.bake.use_pass_direct = False
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_color = False
                                texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                                texture.image = bpy.data.images.new(texName_roughness,  width=width, height=height)
                                mat.node_tree.links.new(texture.outputs[0], shader.inputs[7])

                            if bake_metallic:
                                bpy.context.scene.render.bake.use_pass_direct = False
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_color = True
                                texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                                texture.image = bpy.data.images.new(texName_metal,  width=width, height=height)
                                mat.node_tree.links.new(texture.outputs[0], shader.inputs[4])

                            if bake_emission:
                                bpy.context.scene.render.bake.use_pass_direct = False
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_color = True
                                texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                                texture.image = bpy.data.images.new(texName_emission,  width=width, height=height)
                                mat.node_tree.links.new(texture.outputs[0], shader.inputs[17])

                            if bake_normal:
                                bpy.context.scene.render.bake.use_pass_direct = False
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_color = False
                                texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                                texture.image = bpy.data.images.new(texName_normal, width=width, height=height)
                                texture.image.colorspace_settings.name = 'Non-Color'
                                bump = mat.node_tree.nodes.new(type='ShaderNodeNormalMap')
                                mat.node_tree.links.new(texture.outputs[0], bump.inputs[1])
                                mat.node_tree.links.new(bump.outputs[0], shader.inputs[19])

                            # Assign it to object
                            if ob.data.materials:
                                ob.data.materials[0] = mat
                            else:
                                ob.data.materials.append(mat)             






                bpy.context.scene.render.tile_x =  width
                bpy.context.scene.render.tile_y =  height
                bpy.context.scene.cycles.max_bounces = 4
                bpy.context.scene.cycles.diffuse_bounces = 4
                bpy.context.scene.cycles.glossy_bounces = 4
                bpy.context.scene.cycles.transparent_max_bounces = 4
                bpy.context.scene.cycles.transmission_bounces = 4
                bpy.context.scene.cycles.volume_bounces = 0




                bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name= bake_collection_name)

                # bake_collection = bpy.data.collections.get(bake_collection_name)
                # bpy.context.view_layer.active_layer_collection = bake_collection
                # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[current_collection_name]

                # bpy.context.view_layer.active_layer_collection.exclude = False

                bpy.ops.object.select_all(action='DESELECT')
                for ob in current_collection.objects :
                    if ob.type == 'MESH' : 
                        ob.select_set(state=True)

                bakemesh.select_set(state=True)
                bpy.context.view_layer.objects.active = bakemesh

                #bake the textures
                bpy.context.scene.render.engine = 'CYCLES'
                matnodes = bpy.context.active_object.material_slots[0].material.node_tree.nodes
                imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']

                for n in imgnodes:
                    if n.image.name == bake_mesh_name + "_albedo":
                        n.select = True
                        matnodes.active = n
                        bpy.context.scene.cycles.bake_type = 'DIFFUSE'
                        bpy.context.scene.render.image_settings.color_depth = '8'
                        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
                        bpy.context.scene.render.image_settings.file_format = 'PNG'
                        bpy.context.scene.render.bake.use_pass_indirect = False
                        bpy.context.scene.render.bake.use_pass_direct = False
                        bpy.context.scene.render.bake.use_pass_color = True
                        bpy.context.scene.render.bake.use_selected_to_active = True
                        bpy.context.scene.render.bake.use_cage = True
                        ray_length = bakemesh.dimensions[1] * bake_distance
                        bpy.context.scene.render.bake.cage_extrusion = ray_length
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

                for n in imgnodes:
                    if n.image.name == bake_mesh_name + "_normal":
                        n.select = True
                        matnodes.active = n
                        bpy.context.scene.cycles.bake_type = 'NORMAL'
                        bpy.context.scene.render.image_settings.color_depth = '16'
                        bpy.context.scene.render.image_settings.color_mode = 'RGB'
                        bpy.context.scene.render.image_settings.file_format = 'PNG'
                        bpy.context.scene.render.bake.use_selected_to_active = True
                        bpy.context.scene.render.bake.use_cage = True
                        ray_length = bakemesh.dimensions[1] * bake_distance
                        bpy.context.scene.render.bake.cage_extrusion = ray_length
                        if os.path.exists(file_dir):
                            if os.path.exists(materials_dir):
                                outBakeFileName = n.image.name+".png"
                                outRenderFileName = materials_dir+outBakeFileName
                                n.image.file_format = 'PNG'
                                n.image.filepath = outRenderFileName
                                bpy.ops.object.bake(type='NORMAL', filepath=outRenderFileName, save_mode='EXTERNAL')
                                n.image.save()
                                self.report({'INFO'},"Baked normal texture saved to: " + outRenderFileName )
                        else:
                            bpy.ops.object.bake(type='NORMAL')
                            n.image.pack()

                for n in imgnodes:
                    if n.image.name == bake_mesh_name + "_metal":
                        n.select = True
                        matnodes.active = n
                        bpy.context.scene.cycles.bake_type = 'GLOSSY'
                        bpy.context.scene.render.image_settings.color_depth = '8'
                        bpy.context.scene.render.image_settings.color_mode = 'BW'
                        bpy.context.scene.render.image_settings.file_format = 'PNG'
                        bpy.context.scene.render.bake.use_pass_indirect = False
                        bpy.context.scene.render.bake.use_pass_direct = False
                        bpy.context.scene.render.bake.use_pass_color = True
                        bpy.context.scene.render.bake.use_selected_to_active = True
                        bpy.context.scene.render.bake.use_cage = True
                        ray_length = bakemesh.dimensions[1] * bake_distance
                        bpy.context.scene.render.bake.cage_extrusion = ray_length
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

                        bpy.ops.object.bake(type='GLOSSY')

                for n in imgnodes:
                    if n.image.name == bake_mesh_name + "_roughness":
                        n.select = True
                        matnodes.active = n
                        bpy.context.scene.cycles.bake_type = 'ROUGHNESS'
                        bpy.context.scene.render.image_settings.color_depth = '8'
                        bpy.context.scene.render.image_settings.color_mode = 'BW'
                        bpy.context.scene.render.image_settings.file_format = 'PNG'
                        bpy.context.scene.render.bake.use_selected_to_active = True
                        bpy.context.scene.render.bake.use_cage = True
                        ray_length = bakemesh.dimensions[1] * bake_distance
                        bpy.context.scene.render.bake.cage_extrusion = ray_length
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

                for n in imgnodes:
                    if n.image.name == bake_mesh_name + "_emission":
                        n.select = True
                        matnodes.active = n
                        bpy.context.scene.cycles.bake_type = 'EMIT'
                        bpy.context.scene.render.image_settings.color_depth = '8'
                        bpy.context.scene.render.image_settings.color_mode = 'BW'
                        bpy.context.scene.render.image_settings.file_format = 'PNG'
                        bpy.context.scene.render.bake.use_selected_to_active = True
                        bpy.context.scene.render.bake.use_cage = True
                        ray_length = bakemesh.dimensions[1] * bake_distance
                        bpy.context.scene.render.bake.cage_extrusion = ray_length
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

                for n in imgnodes:
                    if n.image.name == bake_mesh_name + "_ao":
                        n.select = True
                        matnodes.active = n
                        bpy.context.scene.cycles.bake_type = 'AO'
                        bpy.context.scene.render.image_settings.color_depth = '8'
                        bpy.context.scene.render.image_settings.color_mode = 'BW'
                        bpy.context.scene.render.image_settings.file_format = 'PNG'
                        bpy.context.scene.render.bake.use_selected_to_active = True
                        bpy.context.scene.render.bake.use_cage = True
                        ray_length = bakemesh.dimensions[1] * bake_distance
                        bpy.context.scene.render.bake.cage_extrusion = ray_length
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




                # bpy.context.scene.cycles.bake_type = 'NORMAL'
                # bpy.context.scene.cycles.bake_type = 'AO'
                # bpy.context.scene.cycles.bake_type = 'ROUGHNESS'
                # bpy.context.scene.cycles.bake_type = 'GLOSSY'
                # if self.bake_emmision :
                #     bpy.context.scene.cycles.bake_type = 'EMIT'
                

                # for image in bpy.data.images:
                #     if (bake_mesh_name + "_albedo") in image.name:
                #         image.pack()

                bpy.context.view_layer.layer_collection.children[bake_collection_name].exclude = False
                bpy.context.view_layer.layer_collection.children[current_collection_name].exclude = True
                bpy.context.scene.render.engine = 'BLENDER_EEVEE'




        if bake_background :
            active_camera = bpy.context.scene.camera
            bpy.context.scene.render.engine = 'CYCLES'



            if active_camera is not None :
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
            bpy.data.scenes[0].render.resolution_x = 4096
            bpy.data.scenes[0].render.resolution_y = 4096
            bpy.data.scenes[0].render.resolution_percentage = 100
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

            bpy.ops.object.select_all(action='DESELECT')
            skyball_objects[0].select_set(state=True)
            skyball_warp_objects[0].select_set(state=True)
            bpy.context.view_layer.objects.active = skyball_warp_objects[0]

            #bake the textures
            bpy.context.scene.render.tile_x =  width
            bpy.context.scene.render.tile_y =  height
            bpy.context.scene.cycles.max_bounces = 4
            bpy.context.scene.cycles.diffuse_bounces = 4
            bpy.context.scene.cycles.glossy_bounces = 4
            bpy.context.scene.cycles.transparent_max_bounces = 4
            bpy.context.scene.cycles.transmission_bounces = 4
            bpy.context.scene.cycles.volume_bounces = 0

            bpy.context.scene.render.engine = 'CYCLES'
            matnodes = bpy.context.active_object.material_slots[0].material.node_tree.nodes
            imgnodes = [n for n in matnodes if n.type == 'TEX_IMAGE']

            for n in imgnodes:
                n.select = True
                matnodes.active = n
                bpy.context.scene.cycles.bake_type = 'DIFFUSE'
                bpy.context.scene.render.image_settings.color_depth = '8'
                bpy.context.scene.render.image_settings.color_mode = 'RGBA'
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

            bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name= bake_collection_name)
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[current_collection_name]


        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class BR_OT_new_3d_comic(bpy.types.Operator):
    """Start a new 3D Comic from scratch"""
    bl_idname = "view3d.spiraloid_3d_comic_new_3d_comic"
    bl_label ="New 3D Comic..."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}
    

class BR_OT_add_next_panel_scene(bpy.types.Operator):
    """make next panel scene the active scene"""
    bl_idname = "view3d.spiraloid_3d_comic_next_panel"
    bl_label ="Next"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}

class BR_OT_add_previous_panel_scene(bpy.types.Operator):
    """make previous panel scene the active scene"""
    bl_idname = "view3d.spiraloid_3d_comic_previous_panel"
    bl_label ="Previous"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}

class BR_OT_add_comic_scene(bpy.types.Operator):
    """ Insert a new panel scene after the currently active panel scene"""
    bl_idname = "view3d.spiraloid_3d_comic_create_panel"
    bl_label ="Create"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}

class BR_OT_delete_comic_scene(bpy.types.Operator):
    """ Delete currently active panel scene"""
    bl_idname = "view3d.spiraloid_3d_comic_delete_panel"
    bl_label ="Remove"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}

class BR_OT_reorder_panel_scenes(bpy.types.Operator):
    """Change the read order of panel scenes"""
    bl_idname = "view3d.spiraloid_3d_comic_reorder_panels"
    bl_label ="Reorder..."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}



class BR_OT_add_letter_caption(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_caption"
    bl_label ="Add Caption"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        load_resource("letter_caption.blend")
        return {'FINISHED'}

class BR_OT_add_letter_wordballoon(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_wordballoon"
    bl_label ="Add Wordballoon"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        load_resource("letter_wordballoon.blend")

        return {'FINISHED'}

class BR_OT_add_letter_sfx(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_sfx"
    bl_label ="Add Sfx"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        load_resource("letter_sfx.blend")

        return {'FINISHED'}

    
class BR_OT_build_3d_comic(bpy.types.Operator):
    """Build and export 3D Comic"""
    bl_idname = "view3d.spiraloid_build_3d_comic"
    bl_label ="Export 3D Comic"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}

class BR_OT_regenerate_3d_comic_preview(bpy.types.Operator):
    """remake video sequencer scene strip from all scenes"""
    bl_idname = "view3d.spiraloid_3d_comic_preview"
    bl_label = "Generate Comic Movie"
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


def populate_coll(scene):
    bpy.app.handlers.scene_update_pre.remove(populate_coll)
    scene.coll.clear()
    for identifier, name, description in enum_items:
        scene.coll.add().name = name

def menu_draw_bake(self, context):
    self.layout.operator("view3d.spiraloid_bake_panel", 
        text="Bake Panel...")

    bpy.ops.object.dialog_operator('INVOKE_DEFAULT')


#------------------------------------------------------

class BR_MT_3d_comic_menu(bpy.types.Menu):
    bl_idname = "INFO_HT_3d_comic_menu"
    bl_label = "3D Comics"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.spiraloid_3d_comic_new_3d_comic")
        layout.separator()
        layout.menu(BR_MT_3d_comic_submenu_panels.bl_idname, icon="VIEW_ORTHO")
        layout.menu(BR_MT_3d_comic_submenu_letters.bl_idname, icon="OUTLINER_OB_FONT")
        layout.separator()
        layout.operator("view3d.spiraloid_3d_comic_preview")
        layout.separator()
        layout.operator("view3d.spiraloid_bake_panel")
        layout.separator()
        layout.operator("view3d.spiraloid_build_3d_comic")

class BR_MT_3d_comic_submenu_panels(bpy.types.Menu):
    bl_idname = 'view3d.spiraloid_3d_comic_submenu_panels'
    bl_label = 'Panels'

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.spiraloid_3d_comic_next_panel", icon="TRIA_RIGHT")
        layout.operator("view3d.spiraloid_3d_comic_previous_panel", icon="TRIA_LEFT")
        layout.separator()
        layout.operator("view3d.spiraloid_3d_comic_create_panel")
        layout.operator("view3d.spiraloid_3d_comic_delete_panel")
        layout.operator("view3d.spiraloid_3d_comic_reorder_panels")


class BR_MT_3d_comic_submenu_letters(bpy.types.Menu):
    bl_idname = 'view3d.spiraloid_3d_comic_submenu_letters'
    bl_label = 'Letters'

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.spiraloid_3d_comic_add_letter_caption")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_wordballoon")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_sfx")



def draw_item(self, context):
    layout = self.layout
    layout.menu(BR_MT_3d_comic_menu.bl_idname)


def register():
    bpy.utils.register_class(BR_MT_3d_comic_menu)
    bpy.utils.register_class(BR_MT_3d_comic_submenu_panels)
    bpy.utils.register_class(BR_MT_3d_comic_submenu_letters)
    bpy.utils.register_class(BR_OT_spiraloid_3d_comic_workshop)

    bpy.utils.register_class(BR_OT_bake_panel)
    bpy.utils.register_class(BR_OT_new_3d_comic) 
    bpy.utils.register_class(BR_OT_add_next_panel_scene)      
    bpy.utils.register_class(BR_OT_add_previous_panel_scene)      
    bpy.utils.register_class(BR_OT_add_comic_scene)      
    bpy.utils.register_class(BR_OT_add_letter_caption) 
    bpy.utils.register_class(BR_OT_add_letter_wordballoon) 
    bpy.utils.register_class(BR_OT_add_letter_sfx) 
    bpy.utils.register_class(BR_OT_reorder_panel_scenes)
    bpy.utils.register_class(BR_OT_regenerate_3d_comic_preview) 
    bpy.utils.register_class(BR_OT_delete_comic_scene)      
    bpy.utils.register_class(BR_OT_build_3d_comic) 
    bpy.utils.register_class(BakePanelSettings)
    

    bpy.utils.register_class(ComicPreferences)

    bpy.types.Scene.bake_panel_settings = bpy.props.PointerProperty(type=BakePanelSettings)
    
    bpy.types.TOPBAR_MT_editor_menus.append(draw_item)

def unregister():
    bpy.utils.unregister_class(BR_MT_3d_comic_menu)
    bpy.utils.unregister_class(BR_MT_3d_comic_submenu_panels)
    bpy.utils.unregister_class(BR_MT_3d_comic_submenu_letters)
    bpy.utils.unregister_class(BR_OT_spiraloid_3d_comic_workshop) 
    
    bpy.utils.unregister_class(BR_OT_bake_panel) 
    bpy.utils.unregister_class(BR_OT_new_3d_comic)
    bpy.utils.unregister_class(BR_OT_add_next_panel_scene)      
    bpy.utils.unregister_class(BR_OT_add_previous_panel_scene)       
    bpy.utils.unregister_class(BR_OT_add_comic_scene)      
    bpy.utils.unregister_class(BR_OT_add_letter_caption) 
    bpy.utils.unregister_class(BR_OT_add_letter_wordballoon) 
    bpy.utils.unregister_class(BR_OT_add_letter_sfx) 
    bpy.utils.unregister_class(BR_OT_reorder_panel_scenes)
    bpy.utils.unregister_class(BR_OT_regenerate_3d_comic_preview) 
    bpy.utils.unregister_class(BR_OT_delete_comic_scene)      
    bpy.utils.unregister_class(BR_OT_build_3d_comic) 
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