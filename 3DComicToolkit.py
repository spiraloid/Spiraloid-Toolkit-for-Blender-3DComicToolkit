bl_info = {
    'name': '3D Comic Toolkit',
    'author': 'Bay Raitt',
    'version': (0, 5),
    'blender': (2, 93, 0),
    "description": "3D Comic Toolkit - requires factory addons: Bool Tool to be activated!! ",
    'category': 'Import-Export',
    'location': 'Spiraloid > 3D Comic',
    'wiki_url': ''
    }

import bpy
import os
import shutil
import os.path
from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import ExportHelper

from bpy_extras.object_utils import AddObjectHelper, object_data_add

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
import random

from bpy.types import Operator
from mathutils import *
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
# import bpy.utils.previews
# from bpy.app.handlers import persistent


#------------------------------------------------------
# addon preferences

# class ComicPreferences(AddonPreferences):
#     # this must match the addon name, use '__package__'
#     # when defining this in a submodule of a python package.
#     bl_idname = __name__

#     assets_folder = StringProperty(
#             name="Assets Folder",
#             subtype='DIR_PATH',
#             )

#     def draw(self, context):
#         layout = self.layout
#         layout.label(text="Location for Spiraloid Template Assets")
#         layout.prop(self, "assets_folder")



#------------------------------------------------------
# global variables

developer_mode = False
backstage_collection_name = ""
localHostIsRunning = False
last_applied_pose_index = 0
isChildLock = False
previous_sky_color_index = 0
previous_random_int = 0 
isWorkmodeToggled = True
isWireframe = False
previous_toolbar_state = False
previous_region_ui_state = False
previous_mode = 'EDIT'
previous_selection = ""
active_language_abreviated = "en"
active_language = "english"
working_folder = ""
ink_swatch_object = ""
issue_folder = ""
localComicServerProcess = False


#------------------------------------------------------
# utilities

def warn_not_saved(self, context):
    self.layout.label(text= "You must save your file first!")

def warn_folder_exists(self, context):
    self.layout.label(text= "Folder Already Exists!")

def warn_language_set(self, context):
    scene = context.scene
    language = scene.panel_settings.s3dc_language
    self.layout.label(text= "Language set to " + language + " for all scenes")

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

def to_hex(c):
    if c < 0.0031308:
        srgb = 0.0 if c < 0.0 else c * 12.92
    else:
        srgb = 1.055 * math.pow(c, 1.0 / 2.4) - 0.055

    return hex(max(min(int(srgb * 255 + 0.5), 255), 0))

def toHex(r,g,b):
    rgb = [r,g,b]
    result = ""
    i=0
    while i < 3:
        val = str(to_hex(rgb[i]))
        val = val[2:]
        if len(val) == 1:
            val += val
        result+=val
        i+=1
    return result

def scene_mychosenobject_poll(self, object):
    return object.type == 'MESH'

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

    for block in bpy.data.worlds:
        if block.users == 0:
            bpy.data.worlds.remove(block)
            

    for block in bpy.data.particles:
        if block.users == 0:
            bpy.data.particles.remove(block)

    try:
        bpy.ops.outliner.orphans_purge()
    except:
        pass
    try:
        bpy.ops.outliner.orphans_purge()
    except:
        pass
    try:
        bpy.ops.outliner.orphans_purge()
    except:
        pass

    return {'FINISHED'}

## track changed objects and update scene after -- dangerous
# def scene_update_handler(scene):
#     updated_objects = []
#     for o in scene.objects:
#         is_cycler = o.get("Suzanne")
#         if is_cycler:
#             updated_objects.append(o)
#     if(len(updated_objects) > 0):
#         print("updated objects: " + updated_objects[0].name)

#------------------------------------------------------
# mesh tools 

def NormalInDirection( normal, direction, limit = 0.5 ):
    return direction.dot( normal ) > limit

def GoingUp( normal, limit = 0.5):
    return NormalInDirection( normal, Vector( (0, 0, 1 ) ), limit )

def GoingDown( normal, limit = 0.5):
    return NormalInDirection( normal, Vector( (0, 0, -1 ) ), limit )

def GoingSide( normal, limit = 0.5):
    return GoingUp( normal, limit ) == False and GoingDown( normal, limit ) == False

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
                # bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02, area_weight=0.75, correct_aspect=True, scale_to_bounds=True)
                # bpy.ops.uv.seams_from_islands()
                # bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
                # bpy.ops.uv.minimize_stretch(iterations=1024)
                # bpy.ops.uv.average_islands_scale()

                bpy.ops.uv.cube_project(cube_size=10, scale_to_bounds=True)

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
                    bpy.ops.object.modifier_apply( modifier="Decimate")

                    bpy.ops.object.modifier_add(type='TRIANGULATE')
                    bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
                    bpy.context.object.modifiers["Triangulate"].quad_method = 'FIXED'
                    bpy.ops.object.modifier_apply( modifier="Triangulate")


                    bpy.ops.object.modifier_add(type='DECIMATE')
                    bpy.context.object.modifiers["Decimate"].ratio = decimate_ratio
                    bpy.ops.object.modifier_apply( modifier="Decimate")

                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.delete_loose()
                    bpy.ops.mesh.dissolve_degenerate()
                    bpy.ops.mesh.remove_doubles()
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)



    #select all meshes and pack into one UV set together
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='DESELECT')
    for mesh_object in mesh_objects:
        mesh_object.select_set(state=True)
        bpy.context.view_layer.objects.active = mesh_object

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    C=bpy.context
    old_area_type = C.area.type
    C.area.type='IMAGE_EDITOR'
    C.area.ui_type = 'UV'
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.uv.select_all(action='SELECT')
    # bpy.ops.uv.minimize_stretch(override, iterations=100)
    if operator_exists("uvpackmaster2"):
        bpy.context.scene.uvp2_props.pack_to_others = False
        bpy.context.scene.uvp2_props.margin = 0.01
        bpy.context.scene.uvp2_props.rot_step = 5
        bpy.ops.uvpackmaster2.uv_measure_area()
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(margin=0.005)
        bpy.ops.uvpackmaster2.uv_pack()
    else:
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(margin=0.005)
    C.area.type=old_area_type


    # bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    # for area in bpy.context.screen.areas:
    #         if area.type == 'IMAGE_EDITOR':
    #             for region in area.regions:
    #                 if region.type == 'WINDOW':
    #                     override = {'area': area, 'region': region, 'edit_object': bpy.context.edit_object}
    #                     bpy.context.scene.tool_settings.use_uv_select_sync = True
    #                     bpy.ops.uv.select_all(action='SELECT')
    #                     bpy.ops.mesh.select_all(action='SELECT')
    #                     # bpy.ops.uv.minimize_stretch(override, iterations=100)
    #                     if operator_exists("uvpackmaster2"):
    #                         bpy.context.scene.uvp2_props.pack_to_others = False
    #                         bpy.context.scene.uvp2_props.margin = 0.01
    #                         bpy.context.scene.uvp2_props.rot_step = 5
    #                         bpy.ops.uvpackmaster2.uv_measure_area()
    #                         bpy.ops.uv.average_islands_scale()
    #                         bpy.ops.uv.pack_islands(override , margin=0.005)
    #                         bpy.ops.uvpackmaster2.uv_pack()
    #                     else:
    #                         bpy.ops.uv.average_islands_scale(override)
    #                         bpy.ops.uv.pack_islands(override , margin=0.005)





        # bpy.ops.mesh.select_all(action='SELECT')
        # C=bpy.context
        # old_area_type = C.area.type
        # C.area.type='IMAGE_EDITOR'
        # bpy.ops.uv.pack_islands(margin=0.017)
        # C.area.type=old_area_type


    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='DESELECT')
    for mesh_object in mesh_objects:
        mesh_object.select_set(state=True)
        bpy.context.view_layer.objects.active = mesh_object


        # raise Exception('stopping script')

    return {'FINISHED'} 


#------------------------------------------------------
# drop tools

def get_align_matrix(location, normal):
    up = Vector((0,0,1))
    angle = normal.angle(up)
    axis = up.cross(normal)
    mat_rot = Matrix.Rotation(angle, 4, axis)
    mat_loc = Matrix.Translation(location)
    mat_align = mat_rot @ mat_loc
    return mat_align

def transform_ground_to_world(layer, ground):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    object_eval = ground.evaluated_get(depsgraph)
    tmpMesh = bpy.data.meshes.new_from_object(object_eval)        
    tmpMesh.transform(ground.matrix_world)
    tmp_ground = bpy.data.objects.new(name='tmpGround', object_data=tmpMesh)
    layer.objects.link(tmp_ground)
    layer.objects.update()
    return tmp_ground

def get_lowest_world_co_from_mesh(ob, mat_parent=None):
    bme = bmesh.new()
    bme.from_mesh(ob.data)
    mat_to_world = ob.matrix_world.copy()
    if mat_parent:
        mat_to_world = mat_parent @ mat_to_world
    lowest=None
    #bme.verts.index_update() #probably not needed
    for v in bme.verts:
        if not lowest:
            lowest = v
        if (mat_to_world @ v.co).z < (mat_to_world @ lowest.co).z:
            lowest = v
    lowest_co = mat_to_world @ lowest.co
    bme.free()
    return lowest_co

def get_lowest_world_co(context, ob, mat_parent=None):
    if ob.type == 'MESH':
        return get_lowest_world_co_from_mesh(ob)

    elif ob.type == 'EMPTY' and ob.dupli_type == 'GROUP':
        if not ob.dupli_group:
            return None

        else:
            lowest_co = None
            for ob_l in ob.dupli_group.objects:
                if ob_l.type == 'MESH':
                    lowest_ob_l = get_lowest_world_co_from_mesh(ob_l, ob.matrix_world)
                    if not lowest_co:
                        lowest_co = lowest_ob_l
                    if lowest_ob_l.z < lowest_co.z:
                        lowest_co = lowest_ob_l

            return lowest_co

 #------------------------------------------------------
   
def drop_objects(self, context, use_origin, align):
    ground = context.object
    # ground_collection_name = bpy.context.object.users_collection[0].name
    ground.select_set(state=False)
    # bpy.context.view_layer.objects.active = context.selected_objects[0]

    obs = context.selected_objects
    # obs.remove(ground)
    tmp_ground = transform_ground_to_world(context.scene.collection, ground)
    down = Vector((0, 0, -10000))

    for ob in obs:
        if use_origin:
            lowest_world_co = ob.location
        else:
            lowest_world_co = get_lowest_world_co(context, ob)
        if not lowest_world_co:
            print(ob.type, 'is not supported. Failed to drop', ob.name)
            continue
        is_hit, hit_location, hit_normal, hit_index = tmp_ground.ray_cast(lowest_world_co, down)
        if not is_hit:
            print(ob.name, 'didn\'t hit the ground')
            continue

        # simple drop down
        to_ground_vec =  hit_location - lowest_world_co
        ob.location += to_ground_vec

        # drop with align to hit normal
        if align:
            to_center_vec = ob.location - hit_location #vec: hit_loc to origin
            # rotate object to align with face normal
            mat_normal = get_align_matrix(hit_location, hit_normal)
            rot_euler = mat_normal.to_euler()
            mat_ob_tmp = ob.matrix_world.copy().to_3x3()
            mat_ob_tmp.rotate(rot_euler)
            mat_ob_tmp = mat_ob_tmp.to_4x4()
            ob.matrix_world = mat_ob_tmp
            # move_object to hit_location
            ob.location = hit_location
            # move object above surface again
            to_center_vec.rotate(rot_euler)
            ob.location += to_center_vec


    #cleanup
    bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.active_object.select_set(state=True)
    # bpy.ops.object.delete('EXEC_DEFAULT')
    for ob in obs:
        ob.select_set(state=True)
    bpy.data.objects.remove(bpy.data.objects[tmp_ground.name], do_unlink=True)
    empty_trash(self, context)


class OBJECT_OT_drop_to_ground(Operator):
    """Drop selected objects on active object"""
    bl_idname = "object.drop_on_active"
    bl_label = "Drop to Ground"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Drop selected objects on active object"

    align : BoolProperty(
            name="Align to ground",
            description="Aligns the object to the ground",
            default=True)
    use_origin : BoolProperty(
            name="Use Center",
            description="Drop to objects origins",
            default=False)

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 2

    ##### EXECUTE #####
    def execute(self, context):
        print('\nDropping Objects')
        drop_objects(self, context)
        return {'FINISHED'}

#------------------------------------------------------
# gets

def getCurrentSceneIndex():
    currScene =  bpy.context.scene
    for currSceneIndex in range(0,len(bpy.data.scenes)):
        if bpy.data.scenes[currSceneIndex].name == currScene.name:
            return currSceneIndex

def getCurrentPanelNumber(padded):
    scene_name = bpy.context.window.scene.name
    currSceneIndex = getCurrentSceneIndex()
    panels = []
    pi = 0
    panel_number = pi
    if (currSceneIndex > 0):
        for scene in bpy.data.scenes:
            if "p." in scene.name:
                panels.append(scene.name)        
        for panel in panels :
            for i in range(0,len(bpy.data.scenes)):
                if bpy.data.scenes[currSceneIndex].name == panel:
                    pi = currSceneIndex - 1
                    panel_number = pi
    else:
        panel_number = 0

    if padded:
        paddedNumString = "%04d" % panel_number
        return paddedNumString
    else:
        return panel_number

def getCurrentLetterGroup():
    #make sure letter collection is active
    getCurrentLettersCollection()
    language = bpy.context.scene.panel_settings.s3dc_language
    paddedNumString = getCurrentPanelNumber(True)
    letters_group_name = "Letters_" + language + "." + paddedNumString
    letters_group = bpy.data.collections.get(letters_group_name)
    for ob in bpy.data.objects: 
        if ob.name == letters_group_name: 
            return ob
        # else:
        #     report({'ERROR'}, 'No Letters named ' + letters_group_name + ' found under camera') 

def getCurrentActiveCollection(self, context):
    try:
        active_collection = bpy.context.collection
    except:
        pass 
    if active_collection:
        return active_collection
    else:
        self.report({'INFO'}, 'No active Collection found !')

def getCurrentExportCollection(self, context):
    currSceneIndex = getCurrentSceneIndex()
    currScene =  bpy.context.scene
    numString = getCurrentPanelNumber(False)
    paddedNumString = "%04d" % numString
    export_collection_name = "Export." + paddedNumString
    # export_collection = bpy.data.collections.get(export_collection_name)

    try:
        active_collection = bpy.context.collection
        # active_collection_children = active_collection.children
    except:
        pass 

    export_collection_name =  "Export." + str(paddedNumString) 

    export_collection = bpy.data.collections.get(export_collection_name)        
    if export_collection:
        return export_collection
    else:
        if active_collection:
            # active_collection = bpy.context.collection
            # active_collection_children = active_collection.children
            active_collection.name = export_collection_name
            self.report({'INFO'}, 'No Export Collection found, using active collection!')
            return active_collection
        else:
            self.report({'INFO'}, 'No active or Export Collection named ' + export_collection_name + 'found in ' + currScene.name + '!')

def getCurrentBackstageCollectionName():
    # toonfill_use_global = bpy.context.scene.panel_settings.s3dc_toonfill_use_global

    # if toonfill_use_global:
    #     backstage_collection_name = "Backstage.Global"
    # else:
    currSceneIndex = getCurrentSceneIndex()
    currScene =  bpy.context.scene
    if currSceneIndex != 0:
        paddedNumString = getCurrentPanelNumber(True)
        backstage_collection_name = "Backstage." + paddedNumString
    else:
        backstage_collection_name = "Backstage.Global"
    return backstage_collection_name

def getCurrentBackstageCollection():
    # toonfill_use_global = bpy.context.scene.s3dc_toonfill_use_global
    toonfill_use_global = bpy.context.scene.panel_settings.s3dc_toonfill_use_global

    currSceneIndex = getCurrentSceneIndex()
    backstage_collection_name = getCurrentBackstageCollectionName()
    backstage_collection = ""

    # if toonfill_use_global:
        # scene_collections = bpy.data.scenes[0].collection.children
        # backstage_collection = bpy.data.scenes[0].collection.children['Backstage.Global']
    # else:
    scene_collections = bpy.data.scenes[currSceneIndex].collection.children
    for col in scene_collections:
        if backstage_collection_name in col.name:
            backstage_collection = bpy.data.collections.get(backstage_collection_name)
    # try:
    #     active_collection = bpy.context.collection
    #     # active_collection_children = active_collection.children
    # except:
    #     pass 
    return backstage_collection


def getCurrentLightingCollection(self, context):
    currSceneIndex = getCurrentSceneIndex()
    currScene =  bpy.context.scene
    numString = getCurrentPanelNumber(False)
    paddedNumString = "%04d" % numString
    lighting_collection_name = "Lighting." + paddedNumString
    scene_collections = bpy.data.scenes[currSceneIndex].collection.children
    scene_cameras = currScene.collection.children

    all_collections = []
    coll = bpy.context.scene.collection
    for c in traverse_tree(coll):
        all_collections.append(c)


    for col in all_collections:
        if lighting_collection_name in col.name:
            lighting_collection = bpy.data.collections.get(lighting_collection_name)
            if lighting_collection:
                return lighting_collection
            else:
                report({'INFO'}, 'No lighting Collection found!')

def getCurrentLettersCollection():
    currScene =  bpy.context.scene
    numString = getCurrentPanelNumber(False)
    paddedNumString = "%04d" % numString
    letters_collection_name = "Letters." + paddedNumString
    letters_collection = bpy.data.collections.get(letters_collection_name)
    if letters_collection:
        bpy.context.view_layer.layer_collection.children[letters_collection_name].exclude = False
        return letters_collection
    # else:
    #     report({'ERROR'}, 'No Export Collection named ' + export_collection_name + 'found in ' + currScene.name + '!')

def loop_children_recursively(obj, children=[], reset=True):
    """returns all object child objects"""
    if reset:
        children = []
    for child in obj.children:
        isnt_root = not (child.type == 'EMPTY')
        if isnt_root and child not in children:
            children.append(child)
            children = loop_children_recursively(child, children, False)
    return children

def get_all_children(parent_object):
    tmp_child_objects = []
    child_objects = loop_children_recursively(parent_object, tmp_child_objects, False)
    return child_objects

def traverse_tree(t):
    yield t
    for child in t.children:
        yield from traverse_tree(child)

def parent_lookup(coll):
    parent_lookup = {}
    for coll in traverse_tree(coll):
        for c in coll.children.keys():
            parent_lookup.setdefault(c, coll.name)
    return parent_lookup

def get_parent_collection(coll):
    coll_name = coll.name
    C = bpy.context
    coll_scene = C.scene.collection
    coll_parents = parent_lookup(coll_scene)
    parent_collection_name = coll_parents.get(coll_name)
    parent_collection = bpy.data.collections.get(parent_collection_name)        
    return parent_collection

def getCurrentMaterialSwatch():
    panel_number = getCurrentPanelNumber(True)
    
    global ink_swatch_object
    ink_swatch_object_name = "Materials.Global"
    toonfill_use_global = bpy.context.scene.panel_settings.s3dc_toonfill_use_global
    if not toonfill_use_global:
        ink_swatch_object_name = "Materials." + panel_number
    backstage_collection = getCurrentBackstageCollection()
    if backstage_collection:
            # bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = False
            backstage_objects = backstage_collection.objects
            for mobj in backstage_objects:
                if ink_swatch_object_name in mobj.name:
                    ink_swatch_object = mobj
                    # bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = True
    return ink_swatch_object

def getMaterialSwatch(isGlobal):
    if isGlobal:
        ink_swatch_object_name = "Materials.Global"
    else:
        panel_number = getCurrentPanelNumber(True)
        ink_swatch_object_name = "Materials." + panel_number
    backstage_collection = getCurrentBackstageCollection()
    if backstage_collection:
            backstage_objects = backstage_collection.objects
            for mobj in backstage_objects:
                if ink_swatch_object_name in mobj.name:
                    ink_swatch_object = mobj
    return ink_swatch_object




#------------------------------------------------------
# scene tools

def set_active_language(self, context): 
    current_scene = bpy.context.scene
    currSceneIndex = getCurrentSceneIndex()
    current_scene_name = bpy.data.scenes[currSceneIndex].name
    active_language_index = current_scene["panel_settings"]["s3dc_language"]
    active_language = bpy.context.scene.panel_settings.s3dc_language
    if not active_language:
        current_scene["panel_settings"]["language"] = 0
    print(active_language)
    panels = []
    for scene in bpy.data.scenes:
        if "p." in scene.name:
            panels.append(scene.name)
            # scene["panel_settings"]["language"] = active_language_index
            scene["panel_settings"]["language"] = active_language_index

    for panel in panels :
        for i in range(len(bpy.data.scenes)):
            if bpy.data.scenes[i].name == panel:
                bpy.context.window.scene = bpy.data.scenes[i]
                letters_collection = getCurrentLettersCollection()
                objects = letters_collection.objects
                for obj in objects:
                    if "Letters_" in obj.name and active_language not in obj.name:
                        bpy.ops.object.select_all(action='DESELECT')
                        objects = get_all_children(obj)
                        for c in objects:
                            c.hide_set(True)
                            c.hide_viewport = True


                    if "Letters_" in obj.name and active_language in obj.name:
                        # is_hidden = obj.hide_get()
                        # if is_hidden:
                        #     obj.hide_set(False)
                        #     obj.hide_viewport = False
                        bpy.ops.object.select_all(action='DESELECT')
                        objects = get_all_children(obj)
                        for c in objects:
                            c.hide_set(False)
                            c.hide_viewport = False


    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.window.scene = bpy.data.scenes[currSceneIndex]
    bpy.context.window_manager.popup_menu(warn_language_set, title="SUCCESS", icon='ERROR')
    return {'None'} 

def renameAllScenesAfter(self, context):
    startingSceneIndex = getCurrentSceneIndex()
    backstage_collection = getCurrentBackstageCollection()

    # panels = []
    # for scene in bpy.data.scenes:
    #     if "p." in scene.name:
    #         panels.append(scene.name)
    for iSceneIndex in range(len(bpy.data.scenes) -1,startingSceneIndex, -1 ):        
        if "p." in bpy.data.scenes[iSceneIndex].name:
            scene = bpy.data.scenes[iSceneIndex]
            oldSceneIndex = iSceneIndex - 1
            newPanelNumber = "%04d" % iSceneIndex
            oldPanelNumber = "%04d" % oldSceneIndex

            stringFragments = bpy.data.scenes[iSceneIndex].name.split('.')
            x_stringFragments = stringFragments[2]
            xx_stringFragments = x_stringFragments.split('h')
            current_panel_height = xx_stringFragments[1]
            xxx_stringFragments = xx_stringFragments[0].split('w')
            current_panel_width = xxx_stringFragments[1]
            scene.name = 'p.'+ str(newPanelNumber) + '.w' + str(current_panel_width) + 'h' + str(current_panel_height)

            # print("=======DEBUG: " + scene.name)
            # raise KeyboardInterrupt()


        # m = currSceneIndex -1
        # if m > currScene:
        #     if "p." in bpy.data.scenes[m].name:
        #         scene = bpy.data.scenes[m]
        #         n = currSceneIndex
        #         nn = currSceneIndex - 1

        #         sceneNumber = "%04d" % n
        #         oldSceneNumber = "%04d" % nn




        #         # scene.name = 'p.'+ str(sceneNumber) + ".w100h100"

        #         stringFragments = bpy.data.scenes[m].name.split('.')
        #         x_stringFragments = stringFragments[2]
        #         xx_stringFragments = x_stringFragments.split('h')
        #         current_panel_height = xx_stringFragments[1]
        #         xxx_stringFragments = xx_stringFragments[0].split('w')
        #         current_panel_width = xxx_stringFragments[1]


            scene.name = 'p.'+ str(newPanelNumber) + '.w' + str(current_panel_width) + 'h' + str(current_panel_height)

            if backstage_collection:
                bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = False

            scene_objects = scene.objects
            for obj in scene_objects:
                if newPanelNumber in obj.name:
                    obj.name = obj.name.replace(oldPanelNumber, newPanelNumber)

            scene_collections = scene.collection.children
            for col in scene_collections:
                if oldPanelNumber in col.name:
                    col.name = col.name.replace(oldPanelNumber, newPanelNumber)

            scene_cameras = scene.collection.children
            for col in scene_collections:
                if oldPanelNumber in col.name:
                    col.name = col.name.replace(oldPanelNumber, newPanelNumber)

        if backstage_collection:
            bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = True

    return {'FINISHED'}

def load_resource(self, context, blendFileName, is_random):
    global previous_random_int
    if bpy.context.object:
        if "OBJECT" not in bpy.context.object.mode:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
            bpy.ops.object.select_all(action='DESELECT')

    currSceneIndex = getCurrentSceneIndex()
    export_collection = getCurrentExportCollection(self, context)
    if export_collection:
        export_collection_name = export_collection.name
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[export_collection_name]
    else:
        panelNumber = getCurrentPanelNumber(True)
        export_collection_name = "Export." + panelNumber
        export_collection =  bpy.data.collections.new(export_collection_name)
        bpy.context.scene.collection.children.link(export_collection)

    scene_collections = bpy.data.scenes[currSceneIndex].collection.children
    # objects = context.selected_objects
    # if objects is not None :
    #     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    #     bpy.ops.object.select_all(action='DESELECT')

    user_dir = os.path.expanduser("~")
    # common_subdir = "2.90/scripts/addons/3DComicToolkit/Resources/"   this fails on github installs because the name is Spiraloid-
    # common_subdir = "2.90/scripts/addons/Spiraloid-Toolkit-for-Blender-3DComicToolkit/Resources/"
    # if system() == 'Linux':
    #     addon_path = "/.config/blender/" + common_subdir
    # elif system() == 'Windows':
    #     addon_path = (
    #         "\\AppData\\Roaming\\Blender Foundation\\Blender\\"
    #         + common_subdir.replace("/", "\\")
    #     )
    #     # os.path.join()
    # elif system() == 'Darwin':
    #     addon_path = "/Library/Application Support/Blender/" + common_subdir
    # addon_dir = user_dir + addon_path


    # user = bpy.utils.user_resource('SCRIPTS', "addons\\test2\\")
    scripts_dir = bpy.utils.user_resource('SCRIPTS', "addons")

    addon_resources_subdir = "/Spiraloid-Toolkit-for-Blender-3DComicToolkit-master/Resources/"        
    addon_dir = scripts_dir + addon_resources_subdir



    if is_random:
        stringFragments = blendFileName.split('.')
        index = []     
        for file in os.listdir(addon_dir):
            if file.startswith(stringFragments[0]+"."):
                if not file.endswith(".blend1"):
                    index.append(file)
        i = len(index) -1
        if i >= 0:
            random_int = random.randint(0, i)
            while (random_int == previous_random_int):
                random_int = random.randint(0, i)
                if (random_int != previous_random_int):
                    break
        else:
            random_int = 0
        padded_random_int = "%03d" % random_int
        filepath = addon_dir + stringFragments[0] + "." + padded_random_int + ".blend"
        previous_random_int = random_int

    else:
        filepath = addon_dir + blendFileName


    context = bpy.context
    resourceSceneIndex = 0
    scenes = []
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

def load_shared_resource(self, context, blendFileName, is_random):
    global previous_random_int
    shared_asset_filepath = ""
    if bpy.context.object:
        if "OBJECT" not in bpy.context.object.mode:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
            bpy.ops.object.select_all(action='DESELECT')

    currSceneIndex = getCurrentSceneIndex()
    export_collection = getCurrentExportCollection(self, context)
    if export_collection:
        export_collection_name = export_collection.name
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[export_collection_name]
    else:
        panelNumber = getCurrentPanelNumber(True)
        export_collection_name = "Export." + panelNumber
        export_collection =  bpy.data.collections.new(export_collection_name)
        bpy.context.scene.collection.children.link(export_collection)

    scene_collections = bpy.data.scenes[currSceneIndex].collection.children
    user_dir = os.path.expanduser("~")

    scripts_dir = bpy.utils.user_resource('SCRIPTS', "addons")
    addon_resources_subdir = "/Spiraloid-Toolkit-for-Blender-3DComicToolkit-master/Resources/"        
    addon_dir = scripts_dir + addon_resources_subdir

    stringFragments = blendFileName.split('.')
    if is_random:
        index = []     
        for file in os.listdir(addon_dir):
            if file.startswith(stringFragments[0]+"."):
                if not file.endswith(".blend1"):
                    index.append(file)
        if (len(index) > 1):
            random_int = random.randint(0, len(index) -1)
            while (random_int == previous_random_int):
                random_int = random.randint(0, len(index) -1)
                if (random_int != previous_random_int):
                    break
        else:
            random_int = 0
        padded_random_int = "%03d" % random_int
        template_filepath = addon_dir + stringFragments[0] + "." + padded_random_int + ".blend"
        template_glb_filepath = addon_dir + stringFragments[0] + "." + padded_random_int + ".glb"
        previous_random_int = random_int
    else:
        template_filepath = addon_dir + blendFileName
        template_glb_filepath = addon_dir + stringFragments[0] + ".glb"


    if os.path.exists(template_filepath):
        root_folder = os.path.dirname(bpy.data.filepath)
        shared_assets_folder = root_folder + '\\shared\\'
        template_basefilename = os.path.basename(template_filepath) 
        shared_asset_filepath = shared_assets_folder + template_basefilename
        
        if not os.path.exists(shared_asset_filepath):
            shutil.copy(template_filepath, shared_asset_filepath)

    if os.path.exists(template_glb_filepath):
        template_glb_basefilename = os.path.basename(template_glb_filepath) 
        file_dir = os.path.dirname(os.path.dirname(bpy.data.filepath))
        shared_glb_path = (os.path.join(file_dir, "panels\\shared\\"))
        if os.path.exists(shared_glb_path):
            shared_asset_glb_filepath = (shared_glb_path + template_glb_basefilename)
            shutil.copy(template_glb_filepath, shared_asset_glb_filepath)
        else:
            self.report({'ERROR'}, "No Comic folders Found")

    if os.path.exists(shared_asset_filepath):
        context = bpy.context
        resourceSceneIndex = 0
        # scenes = []
        with bpy.data.libraries.load(shared_asset_filepath, link=True, relative=True ) as (data_from, data_to):
            data_to.collections = data_from.collections

        for new_coll in data_to.collections:
            if stringFragments[0] in new_coll.name:
                # instance = bpy.data.collections.new(new_coll.name )
                # instance.instance_type = 'COLLECTION'
                # instance.instance_collection = new_coll
                export_collection.children.link(new_coll)
                new_coll_name = new_coll.name
                # for obj in new_coll.all_objects:
                obj = new_coll.all_objects[0]
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(state=True)
                bpy.context.view_layer.objects.active = obj
                # if obj.type == 'ARMATURE':
                #     bpy.ops.object.make_override_library(collection=new_coll_name)
                # # raise KeyboardInterrupt()
                #     # export_collection.children.link(linked_override)

                #     bpy.data.collections.remove(new_coll)
                #     linked_override_collection = bpy.context.selected_objects[0].users_collection[0]
                #     export_collection.children.link(linked_override_collection)
                #     bpy.data.scenes[currSceneIndex].collection.children.unlink(linked_override_collection)
                # else:
                    # raise KeyboardInterrupt()
                bpy.ops.object.make_override_library(collection=new_coll_name)
                bpy.data.collections.remove(new_coll)
                linked_override_collection = bpy.context.selected_objects[0].users_collection[0]
                export_collection.children.link(linked_override_collection)
                bpy.data.scenes[currSceneIndex].collection.children.unlink(linked_override_collection)
                obj["shared_asset_filepath"] = shared_asset_filepath


            # for name in data_from.scenes:
            #     scenes.append({'name': name})
            # action = bpy.ops.wm.link
            # action(directory=filepath + "/Collection/" + stringFragments[0], files=scenes )
            # scenes = bpy.data.scenes[-len(scenes):]

        # resourceSceneIndex = -len(scenes)
        # if resourceSceneIndex != 0 :
        #     nextScene =  bpy.data.scenes[resourceSceneIndex]
        #     loaded_scene_collections = bpy.data.scenes[resourceSceneIndex].collection.children
        #     shared_asset_collections = bpy.data.collections.get("Shared Assets")
            
        #     for coll in loaded_scene_collections:
        #         bpy.ops.object.make_local(type='ALL')
        #         bpy.ops.object.select_all(action='DESELECT')
        #         for obj in coll.all_objects:
        #             bpy.context.collection.objects.link(obj)  
        #             obj.select_set(state=True)
        #             bpy.context.view_layer.objects.active = obj

        #             for shared_c in shared_asset_collections.children:
        #                 if category_name in shared_c.name:
        #                     shared_c.objects.link(obj)  

        #     bpy.data.scenes.remove(nextScene)




    return {'FINISHED'}

def validate_naming(self, context):
        currSceneIndex = getCurrentSceneIndex()
        currScene =  bpy.data.scenes[currSceneIndex]
        paddedSceneNumber = getCurrentPanelNumber(True)
        current_scene_name = bpy.data.scenes[currSceneIndex].name
        stringFragments = current_scene_name.split('.')
        x_stringFragments = stringFragments[2]
        xx_stringFragments = x_stringFragments.split('h')
        current_panel_height = xx_stringFragments[1]
        xxx_stringFragments = xx_stringFragments[0].split('w')
        current_panel_width = xxx_stringFragments[1]
        # panelSceneName = 'p.'+ str(paddedSceneNumber) + ".w100h100"
        panelSceneName = 'p.'+ str(paddedSceneNumber) + '.w' + str(current_panel_width) + 'h' + str(current_panel_height)
        bpy.data.scenes[currSceneIndex].name = panelSceneName
        # renameAllScenesAfter(self, context)

        scene_collections = bpy.data.scenes[currSceneIndex].collection.children
        for c in scene_collections:
            if "Export." in c.name:
                export_collection = c
                c.name = "Export." + str(paddedSceneNumber) 
            if "Wip." in c.name:
                wip_collection = c
                c.name = "Wip." + str(paddedSceneNumber) 
            if "Lighting." in c.name:
                c.name = "Lighting." + str(paddedSceneNumber) 
            if "Letters." in c.name:
                c.name = "Letters." + str(paddedSceneNumber) 




        export_collection = getCurrentExportCollection(self, context)
        if export_collection:
            for c in export_collection.children:
                if "Lighting." in c.name:
                    c.name = "Lighting." + str(paddedSceneNumber) 

            objects = export_collection.objects
            for obj in objects:
                if "Camera." in obj.name:
                    bpy.context.scene.camera = bpy.data.objects[obj.name]
                    obj.name = 'Camera.'+ str(paddedSceneNumber)
                if "Camera_aim." in obj.name:
                    obj.name = 'Camera_aim.'+ str(paddedSceneNumber)
                if "Lighting." in obj.name:
                    obj.name = 'Lighting.'+ str(paddedSceneNumber)

            letters_collection = getCurrentLettersCollection()
            letters_objects = letters_collection.objects
            for obj in letters_objects:

                has_letters_english = False
                has_letters_spanish = False
                has_letters_japanese = False
                has_letters_korean = False
                has_letters_german = False
                has_letters_french = False
                has_letters_dutch = False

                if "Letters_spanish." in obj.name:
                    obj.name = 'Letters_spanish.'+ str(paddedSceneNumber)
                    has_letters_spanish = True
                    active_language_abreviated = 'es'
                if "Letters_japanese." in obj.name:
                    obj.name = 'Letters_japanese.'+ str(paddedSceneNumber)
                    has_letters_japanese = True
                    active_language_abreviated = 'ja'
                if "Letters_korean." in obj.name:
                    obj.name = 'Letters_korean.'+ str(paddedSceneNumber)  
                    has_letters_korean = True
                    active_language_abreviated = 'ko'

                if "Letters_german." in obj.name:
                    obj.name = 'Letters_german.'+ str(paddedSceneNumber)
                    has_letters_german = True
                    active_language_abreviated = 'de'

                if "Letters_french." in obj.name:
                    obj.name = 'Letters_french.'+ str(paddedSceneNumber)  
                    has_letters_french = True
                    active_language_abreviated = 'fr'

                if "Letters_dutch." in obj.name:
                    obj.name = 'Letters_dutch.'+ str(paddedSceneNumber)  
                    has_letters_dutch = True
                    active_language_abreviated = 'da'

                if "Letters_eng." in obj.name:
                    obj.name = 'Letters_english.'+ str(paddedSceneNumber)

                if "Letters_english." in obj.name:
                    obj.name = 'Letters_english.'+ str(paddedSceneNumber)
                    has_letters_english = True
                    active_language_abreviated = 'en-US'

                    # if not has_letters_spanish:
                    #     bpy.ops.object.select_all(action='DESELECT')
                    #     obj.select_set(state=True)
                    #     bpy.context.view_layer.objects.active = obj
                    #     ob = obj.copy()
                    #     object_collection = obj.users_collection[0].name
                    #     bpy.data.collections[object_collection].objects.link(ob)
                    #     ob.name = 'Letters_spanish.'+ str(paddedSceneNumber)

                    # if not has_letters_japanese:
                    #     bpy.ops.object.select_all(action='DESELECT')
                    #     obj.select_set(state=True)
                    #     bpy.context.view_layer.objects.active = obj
                    #     ob = obj.copy()
                    #     object_collection = obj.users_collection[0].name
                    #     bpy.data.collections[object_collection].objects.link(ob)
                    #     ob.name = 'Letters_japanese.'+ str(paddedSceneNumber)

                    # if not has_letters_korean:
                    #     bpy.ops.object.select_all(action='DESELECT')
                    #     obj.select_set(state=True)
                    #     bpy.context.view_layer.objects.active = obj
                    #     ob = obj.copy()
                    #     object_collection = obj.users_collection[0].name
                    #     bpy.data.collections[object_collection].objects.link(ob)
                    #     ob.name = 'Letters_korean.'+ str(paddedSceneNumber)

                    # if not has_letters_german:
                    #     bpy.ops.object.select_all(action='DESELECT')
                    #     obj.select_set(state=True)
                    #     bpy.context.view_layer.objects.active = obj
                    #     ob = obj.copy()
                    #     object_collection = obj.users_collection[0].name
                    #     bpy.data.collections[object_collection].objects.link(ob)
                    #     ob.name = 'Letters_german.'+ str(paddedSceneNumber)

                    # if not has_letters_french:
                    #     bpy.ops.object.select_all(action='DESELECT')
                    #     obj.select_set(state=True)
                    #     bpy.context.view_layer.objects.active = obj
                    #     ob = obj.copy()
                    #     object_collection = obj.users_collection[0].name
                    #     bpy.data.collections[object_collection].objects.link(ob)
                    #     ob.name = 'Letters_french.'+ str(paddedSceneNumber)
        else:
            self.report({'ERROR'}, 'No Export Collection Found!  Scene Must be reinitialized')

def toggle_workmode(self, context, rendermode):
    global isWorkmodeToggled
    global currentSubdLevel
    global previous_mode
    global previous_selection
    global isWireframe
    global previous_toolbar_state
    global previous_region_ui_state

    if rendermode:
        isWorkmodeToggled = True        

    if bpy.context.mode == 'OBJECT':
        previous_mode =  'OBJECT'
    if bpy.context.mode == 'EDIT_MESH':
        previous_mode =  'EDIT'
        bpy.context.space_data.overlay.show_overlays = False
    if bpy.context.mode == 'POSE':
        previous_mode =  'POSE'
        bpy.context.space_data.overlay.show_bones = True
    if bpy.context.mode == 'SCULPT':
        previous_mode =  'SCULPT'
    if bpy.context.mode == 'PAINT_VERTEX':
        previous_mode =  'VERTEX_PAINT'
    if bpy.context.mode == 'WEIGHT_PAINT':
        previous_mode =  'WEIGHT_PAINT'
    if bpy.context.mode == 'TEXTURE_PAINT':
        previous_mode =  'TEXTURE_PAINT'

    my_areas = bpy.context.workspace.screens[0].areas
    for area in my_areas:
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                my_shading = 'WIREFRAME'  # 'WIREFRAME' 'SOLID' 'MATERIAL' 'RENDERED'
                space.overlay.show_overlays = True
                space.overlay.show_floor = True
                space.overlay.show_axis_x = True
                space.overlay.show_axis_y = True
                space.overlay.show_outline_selected = True
                space.overlay.show_cursor = True
                space.overlay.show_extras = True
                space.overlay.show_relationship_lines = True
                space.overlay.show_bones = True
                space.overlay.show_motion_paths = True
                space.overlay.show_object_origins = True
                space.overlay.show_annotation = True
                space.overlay.show_text = True
                space.overlay.show_stats = True
                previous_toolbar_state = space.show_region_toolbar
                previous_region_ui_state = space.show_region_ui


                if isWorkmodeToggled:
                    previous_selection = bpy.context.selected_objects
                    space.overlay.show_overlays = True
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
                    space.overlay.show_stats = False
                    space.overlay.show_outline_selected = False
                    space.overlay.show_extras = False
                    space.show_gizmo = False
                    space.overlay.show_text = False
                    space.overlay.show_stats = False
                    space.show_region_toolbar = previous_toolbar_state
                    space.show_region_ui = previous_region_ui_state
                    # space.show_region_header = False



                    selected_objects = bpy.context.selected_objects
                    if not selected_objects:
                        space.overlay.show_outline_selected = True


                    space.overlay.wireframe_threshold = 1
                    if space.overlay.show_wireframes:
                        isWireframe = True
                        space.overlay.show_outline_selected = True
                        space.overlay.show_extras = True
                        space.overlay.show_overlays = True
                        space.overlay.show_text = True
                        space.overlay.show_stats = True


                        # bpy.context.space_data.overlay.show_cursor = True
                    else:
                        isWireframe = False
                        # bpy.context.space_data.overlay.show_outline_selected = False
                        # bpy.context.space_data.overlay.show_extras = False

                    # bpy.context.space_data.overlay.show_wireframes = False

                    if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                        # bpy.context.scene.eevee.use_bloom = True
                        # bpy.context.scene.eevee.use_ssr = True
                        my_shading =  'MATERIAL'

                        lights = [o for o in bpy.context.scene.objects if o.type == 'LIGHT']
                        if (lights):
                            space.shading.use_scene_lights = True
                            space.shading.use_scene_world = True
                        else:
                            space.shading.use_scene_lights = True
                            space.shading.use_scene_world = False

                        if bpy.context.scene.world:
                            space.shading.use_scene_world = True
                        else:
                            space.shading.use_scene_world = False


                    if bpy.context.scene.render.engine == 'CYCLES':
                        my_shading =  'RENDERED'
                        lights = [o for o in bpy.context.scene.objects if o.type == 'LIGHT']
                        # if (lights):
                        #     bpy.context.space_data.shading.use_scene_lights_render = True
                        # else:
                        #     bpy.context.space_data.shading.use_scene_lights = False
                        #     bpy.context.space_data.shading.studiolight_intensity = 1


                        if bpy.context.scene.world is None:
                            if (lights):
                                space.shading.use_scene_world_render = False
                                space.shading.studiolight_intensity = 0.01
                            else:
                                space.shading.use_scene_world_render = False
                                space.shading.studiolight_intensity = 1
                        else:
                            space.shading.use_scene_world_render = True
                            if (lights):
                                space.shading.use_scene_lights_render = True
                else:
                    space.overlay.show_overlays = True
                    space.overlay.show_cursor = True
                    space.overlay.show_floor = True
                    space.overlay.show_axis_x = True
                    space.overlay.show_axis_y = True
                    space.overlay.show_extras = True
                    space.overlay.show_relationship_lines = False
                    space.overlay.show_bones = True
                    space.overlay.show_motion_paths = True
                    space.overlay.show_object_origins = True
                    space.overlay.show_annotation = True
                    space.overlay.show_text = True
                    space.overlay.show_stats = True
                    space.overlay.wireframe_threshold = 1
                    space.show_gizmo = True
                    # space.show_region_header = True
                    space.show_region_toolbar = previous_toolbar_state
                    space.show_region_ui = previous_region_ui_state


                    if previous_mode == 'EDIT':
                        if not len(bpy.context.selected_objects):
                            bpy.ops.object.editmode_toggle()
                        # else:
                        #     for ob in previous_selection :
                        #         # if ob.type == 'MESH' : 
                        #         ob.select_set(state=True)
                        #         bpy.context.view_layer.objects.active = ob
                        #     bpy.ops.object.editmode_toggle()



                    if previous_mode == 'VERTEX_PAINT':
                        my_shading = 'SOLID'
                        space.shading.light = 'FLAT'


                    if previous_mode == 'SCULPT':
                        my_shading =  'SOLID'
                        space.shading.color_type = 'MATERIAL'
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

                    if previous_mode == 'EDIT' or previous_mode == 'OBJECT' or previous_mode == 'POSE':
                        my_shading = 'SOLID'
                        # for ob in bpy.context.scene.objects:
                        #     if ob.type == 'MESH':
                        #         if ob.data.vertex_colors:
                        #             bpy.context.space_data.shading.color_type = 'VERTEX'
                        #         else:
                        #             bpy.context.space_data.shading.color_type = 'RANDOM'


                    if isWireframe:
                        space.overlay.show_wireframes = True
                    else:
                        space.overlay.show_wireframes = False
                    space.shading.color_type = 'RANDOM'
                    space.shading.show_backface_culling = False
                    space.shading.show_shadows = True


    for obj in bpy.context.scene.objects:
        # if obj.visible_get and obj.type == 'MESH':
        if obj.visible_get :
            
            # for mod in [m for m in obj.modifiers if m.type == 'MULTIRES']:
            #     mod_max_level = mod.render_levels
            #     if isWorkmodeToggled:
            #         currentSubdLevel = mod.levels
            #         mod.levels = mod_max_level
            #         mod.sculpt_levels = mod_max_level
            #     if not isWorkmodeToggled:
            #         mod.levels = currentSubdLevel
            #         mod.sculpt_levels = currentSubdLevel
            #         if currentSubdLevel != 0:
            #             bpy.context.space_data.overlay.show_wireframes = False


            # for mod in [m for m in obj.modifiers if m.type == 'SUBSURF']:
            #     mod_max_level = mod.render_levels
            #     if isWorkmodeToggled:
            #         currentSubdLevel = mod.levels
            #         mod.levels = mod_max_level
            #     if not isWorkmodeToggled:
            #         mod.levels = currentSubdLevel
            #         if currentSubdLevel != 0:
            #             bpy.context.space_data.overlay.show_wireframes = False

            scene = bpy.context.scene
            if isWorkmodeToggled:
                is_toon_shaded = obj.get("is_toon_shaded")
                if is_toon_shaded:
                    for mod in obj.modifiers:
                        if 'InkThickness' in mod.name:
                            obj.modifiers["InkThickness"].show_viewport = True
                        if 'WhiteOutline' in mod.name:
                            obj.modifiers["WhiteOutline"].show_viewport = True
                        if 'BlackOutline' in mod.name:
                            obj.modifiers["BlackOutline"].show_viewport = True
            else:
                is_toon_shaded = obj.get("is_toon_shaded")
                if is_toon_shaded:
                    for mod in obj.modifiers:
                        if 'InkThickness' in mod.name:
                            obj.modifiers["InkThickness"].show_viewport = False
                        if 'WhiteOutline' in mod.name:
                            obj.modifiers["WhiteOutline"].show_viewport = False
                        if 'BlackOutline' in mod.name:
                            obj.modifiers["BlackOutline"].show_viewport = False
                     
        

                # bpy.ops.object.mode_set(mode=previous_mode, toggle=False)


            # for area in my_areas:
            #     for space in area.spaces:
            #         if space.type == 'VIEW_3D':
            #             space.shading.type = my_shading

    # set viewport display
    for area in  bpy.context.screen.areas:  # iterate through areas in current screen
        if area.type == 'VIEW_3D':
            for space in area.spaces:  # iterate through spaces in current VIEW_3D area
                if space.type == 'VIEW_3D':  # check if space is a 3D view
                    # space.shading.type = 'MATERIAL'  # set the viewport shading to material
                    space.shading.type = my_shading
                    try: 
                        if scene.world is not None:
                            space.shading.use_scene_world = True
                            space.shading.use_scene_lights = True
                    except:
                        pass

                            

    for image in bpy.data.images:
        image.reload()

    isWorkmodeToggled = not isWorkmodeToggled
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

def outline(self,context,mesh_objects, toonfill_mode ):
    # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    # bpy.ops.object.select_all(action='DESELECT')

    paddedNumString = getCurrentPanelNumber(True)
    backstage_collection = getCurrentBackstageCollection()
    if not backstage_collection:
        self.report({'INFO'}, 'No Backstage Collection found, initializng as 3D Comic Panel!')
        BR_OT_panel_init.execute(self, context)

    # ink_swatch_object = getCurrentMaterialSwatch()
    panel_material_swatch = getMaterialSwatch(False)
    global_material_swatch = getMaterialSwatch(True)
    export_collection = getCurrentExportCollection(self, context)
    backstage_collection = getCurrentBackstageCollection()
    backstage_collection_name = getCurrentBackstageCollectionName()
    toonfill_use_global_ink = bpy.context.scene.panel_settings.s3dc_toonfill_use_global_ink
    panel_number = getCurrentPanelNumber(True)

    if toonfill_use_global_ink:
        ink_swatch_object = global_material_swatch
    else:
        ink_swatch_object = panel_material_swatch


    if backstage_collection:
        try:
            bpy.context.view_layer.layer_collection.children[backstage_collection_name].exclude = False
        except:
            pass
    backstage_objects = backstage_collection.objects

    if bpy.context.mode != 'EDIT_MESH':
        for mesh_object in mesh_objects:
            is_toon_shaded = mesh_object.get("is_toon_shaded")
            if mesh_object.type == 'MESH' or mesh_object.type == 'CURVE' or mesh_object.type == 'FONT':
                if not is_toon_shaded:
                    is_insensitive = False

                    if "ink" in toonfill_mode and "toon" in toonfill_mode:
                        if mesh_object.active_material:
                            # mesh_object.active_material.use_nodes = True
                            # mesh_object.active_material.node_tree.nodes.clear()
                            for i in range(len(mesh_object.material_slots)):
                                bpy.ops.object.material_slot_remove({'object': mesh_object})
                        for mod in mesh_object.modifiers:
                            if 'InkThickness' in mod.name:
                                bpy.ops.object.modifier_remove(modifier=mod.name)
                            if 'WhiteOutline' in mod.name:
                                bpy.ops.object.modifier_remove(modifier=mod.name)
                            if 'BlackOutline' in mod.name:
                                bpy.ops.object.modifier_remove(modifier=mod.name)

                        for vgroup in mesh_object.vertex_groups:
                            if 'Ink_Thickness' in vgroup.name:
                                mesh_object.vertex_groups.remove(vgroup)

                        try:
                            drivers_data = mesh_object.animation_data.drivers
                            for dr in drivers_data:  
                                mesh_object.driver_remove(dr.data_path, -1)
                        except:
                            pass
                        
                        empty_trash(self, context)
                    if "ink" in toonfill_mode:
                        ink_thickness = mesh_object.dimensions[1] * 0.035
                        if bpy.context.object:
                            if "OBJECT" not in bpy.context.object.mode:
                                if "DRAW" in bpy.context.object.mode :
                                    bpy.ops.gpencil.paintmode_toggle(back=False)
                                    bpy.ops.object.select_all(action='DESELECT')
                                else:
                                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                                    bpy.ops.object.select_all(action='DESELECT')

                        mesh_object.select_set(state=True)
                        bpy.context.view_layer.objects.active = mesh_object
                        # if "EDIT" not in bpy.context.object.mode:
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        if mesh_object.type == 'MESH':
                            bpy.ops.mesh.select_all(action='SELECT')
                        # if mesh_object.type == 'CURVE':
                        #     bpy.ops.curve.select_all(action='TOGGLE')

                            ink_thickness_vgroup_name = "Ink_Thickness"
                            mesh_object.vertex_groups.new(name = ink_thickness_vgroup_name)
                            ink_thickness_vgroup = mesh_object.vertex_groups[-1]
                            bpy.ops.object.vertex_group_assign()

                            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = mesh_object

                            if not toonfill_use_global_ink:
                                ink_thick_tex_name = "L_InkThickness." + str(paddedNumString)
                                for itex in bpy.data.textures: 
                                    if ink_thick_tex_name in itex.name:
                                        ink_thick_tex = bpy.data.textures[ink_thick_tex_name]
                                    else:
                                        ink_thick_tex_name = ink_thick_tex_name
                                        ink_thick_tex_slot = bpy.data.textures.new(ink_thick_tex_name, type='CLOUDS')
                                        ink_thick_tex = bpy.data.textures[ink_thick_tex_name]
                                    
                                    # ink_thick_tex.noise_type = 'SOFT_NOISE'
                                    # ink_thick_tex.noise_depth = 0
                                    # ink_thick_tex.nabla = 0.001
                                    # ink_thick_tex.intensity = 0.99

                                    # if ink_swatch_object:
                                    #     objectInkSmoothnessDriver = ink_thick_tex.driver_add('noise_scale')
                                    #     objectInkSmoothnessDriver.driver.type = 'SUM'
                                    #     newVar = objectInkSmoothnessDriver.driver.variables.new()
                                    #     newVar.name = "ink_wobble"
                                    #     newVar.type = 'SINGLE_PROP'
                                    #     newVar.targets[0].id = ink_swatch_object 
                                    #     newVar.targets[0].data_path = '["OutlineWobble"]'
                                    #     objectInkSmoothnessDriver.driver.expression =  "ink_wobble"
                                    #     objectInkSmoothnessDriver = "ink_wobble"
                                    # else:
                                    #     ink_thick_tex.noise_scale = 0.3
                            else:
                                ink_thick_tex_name = "L_InkThickness.Global"
                                for itex in bpy.data.textures: 
                                    if ink_thick_tex_name in itex.name:
                                        ink_thick_tex = bpy.data.textures[ink_thick_tex_name]



                            ink_thick_mod = mesh_object.modifiers.new(name = 'InkThickness', type = 'VERTEX_WEIGHT_EDIT')
                            ink_thick_mod.vertex_group = ink_thickness_vgroup.name
                            ink_thick_mod.default_weight = 0
                            ink_thick_mod.use_add = True

                            ink_thick_mod.normalize = False
                            ink_thick_mod.falloff_type = 'STEP'
                            ink_thick_mod.invert_falloff = True
                            ink_thick_mod.mask_constant = 1
                            ink_thick_mod.mask_texture = ink_thick_tex
                            ink_thick_mod.mask_tex_use_channel = 'INT'
                            # ink_thick_mod.mask_tex_mapping = 'LOCAL'
                            ink_thick_mod.mask_tex_mapping = 'GLOBAL'

                        white_outline_mod = mesh_object.modifiers.new(name = 'WhiteOutline', type = 'SOLIDIFY')
                        white_outline_mod.use_flat_faces = True
                        white_outline_mod.use_flip_normals = True
                        white_outline_mod.thickness = -ink_thickness / 2
                        white_outline_mod.offset = -1
                        white_outline_mod.material_offset = 2
                        if mesh_object.type == 'MESH':
                            white_outline_mod.vertex_group = ink_thickness_vgroup.name
                        white_outline_mod.show_in_editmode = False
                        white_outline_mod.thickness_clamp = 0.5
                        white_outline_mod.thickness_vertex_group = 0.1


                        if not ink_swatch_object:
                            mesh_object["OutlineThickness"] = 0.5


                        objectInkThicknessDriver = white_outline_mod.driver_add('thickness')
                        objectInkThicknessDriver.driver.type = 'SCRIPTED'
                        newVar = objectInkThicknessDriver.driver.variables.new()
                        newVar.name = "ink_thickness"
                        newVar.type = 'SINGLE_PROP'
                        if ink_swatch_object:
                            newVar.targets[0].id = ink_swatch_object 
                        else:
                            newVar.targets[0].id = mesh_object 
                        newVar.targets[0].data_path = '["OutlineThickness"]'
                        objectInkThicknessDriver.driver.expression =  "ink_thickness  * -0.1"
                        objectInkThicknessDriver = "ink_thickness * -.1"

                        if ink_swatch_object:
                            objectInkSmoothnessDriver = white_outline_mod.driver_add('thickness_vertex_group')
                            objectInkSmoothnessDriver.driver.type = 'SUM'
                            newVar = objectInkSmoothnessDriver.driver.variables.new()
                            newVar.name = "ink_smooth"
                            newVar.type = 'SINGLE_PROP'
                            newVar.targets[0].id = ink_swatch_object 
                            newVar.targets[0].data_path = '["OutlineSmooth"]'
                            objectInkSmoothnessDriver.driver.expression =  "ink_smooth"
                            objectInkSmoothnessDriver = "ink_smooth"



                        black_outline_mod = mesh_object.modifiers.new(name = 'BlackOutline', type = 'SOLIDIFY')
                        black_outline_mod.use_flip_normals = True
                        black_outline_mod.use_flat_faces = True

                        # black_outline_mod.thickness = ink_thickness 

                        thicknessDriver = black_outline_mod.driver_add('thickness')
                        thicknessDriver.driver.type = 'SCRIPTED'
                        newVar = thicknessDriver.driver.variables.new()
                        newVar.name = "thickness"
                        newVar.type = 'SINGLE_PROP'
                        newVar.targets[0].id = mesh_object 
                        newVar.targets[0].data_path = 'modifiers["WhiteOutline"].thickness'
                        # thicknessDriver.driver.expression =  "(thickness  * 1.15) - .02"
                        # thicknessDriver.driver.expression =  "(thickness  * -1) - (thickness  * 1)"
                        thicknessDriver.driver.expression =  "thickness  * -1.5"

                        factorDriver = black_outline_mod.driver_add('thickness_vertex_group')
                        factorDriver.driver.type = 'SCRIPTED'
                        newVar = factorDriver.driver.variables.new()
                        newVar.name = "thickness_vertex_group"
                        newVar.type = 'SINGLE_PROP'
                        newVar.targets[0].id = mesh_object 
                        newVar.targets[0].data_path = 'modifiers["WhiteOutline"].thickness_vertex_group'
                        factorDriver.driver.expression =  "thickness_vertex_group"


                        black_outline_mod.offset = 1
                        black_outline_mod.material_offset = 1
                        if mesh_object.type == 'MESH':
                            black_outline_mod.vertex_group = ink_thickness_vgroup.name
                        black_outline_mod.show_in_editmode = False
                        black_outline_mod.thickness_clamp = 0
                        # black_outline_mod.thickness_vertex_group = 0.2

                        decimators = []
                        for i in range(len(mesh_object.modifiers)):
                            mod = mesh_object.modifiers[i]
                            if 'Decimate' in mod.name:
                                decimators.append(i)
                        if decimators:
                            firstDecimatorIndex = int(decimators[0])
                            ink_thick_mod_name = ink_thick_mod.name
                            white_outline_mod_name = white_outline_mod.name
                            black_outline_mod_name = black_outline_mod.name

                            # bpy.ops.object.modifier_move_to_index(modifier=black_outline_mod_name, index=firstDecimatorIndex)
                            # bpy.ops.object.modifier_move_to_index(modifier=white_outline_mod_name, index=firstDecimatorIndex)
                            # bpy.ops.object.modifier_move_to_index(modifier=ink_thick_mod_name, index=firstDecimatorIndex)

                        # bpy.ops.object.modifier_move_to_index(modifier=ink_thick_mod_name, firstDecimatorIndex)
                        # bpy.ops.object.modifier_move_to_index(modifier=white_outline_mod_name, firstDecimatorIndex)
                        # bpy.ops.object.modifier_move_to_index(modifier=black_outline_mod_name, firstDecimatorIndex)



                        # bpy.context.object.material_slots[1].link = 'DATA'
                        # bpy.ops.object.material_slot_add()
                    if "toon" in toonfill_mode:
                        hasVertexColor = False
                        if mesh_object.hide_select:
                            mesh_object.hide_select = False
                            is_insensitive = True

                        if backstage_collection:
                            # bpy.context.scene.collection.objects.link(mobj)
                            # bpy.ops.object.select_all(action='DESELECT')
                            # mesh_object.select_set(state=True)
                            # mobj.select_set(state=True)
                            # bpy.context.view_layer.objects.active = mobj
                            # bpy.ops.object.material_slot_copy()
                            # bpy.context.scene.collection.objects.unlink(mobj)
                            # bpy.ops.object.select_all(action='DESELECT')
                            # mesh_object.select_set(state=True)
                            # bpy.context.view_layer.objects.active = mesh_object

                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            ink_swatch_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = ink_swatch_object
                            bpy.ops.object.material_slot_copy()

                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = mesh_object
                            for i, mat in reversed(list(enumerate(mesh_object.data.materials))):
                                if "L_Toon." not in mat.name:
                                    # letter.data.materials.pop(index=i)
                                    mesh_object.active_material_index = i
                                    bpy.ops.object.material_slot_remove()

                            for p in mesh_object.data.polygons:
                                if p.material_index >= len(mesh_object.data.materials):
                                    p.material_index = -1
                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = mesh_object
                        else:
                            if mesh_object.active_material:
                                mesh_object.active_material.node_tree.nodes.clear()
                                for i in range(len(mesh_object.material_slots)):
                                    bpy.ops.object.material_slot_remove({'object': mesh_object})


                            if mesh_object.active_material is None:
                                if mesh_object.type == 'MESH':
                                    if mesh_object.data.vertex_colors:
                                        hasVertexColor = True

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

                                if (hasVertexColor):
                                    shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                                else:
                                    shader = mat.node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')

                                shaderToRGB_A = mat.node_tree.nodes.new(type='ShaderNodeShaderToRGB')
                                ramp_A = mat.node_tree.nodes.new(type='ShaderNodeValToRGB')
                                light_path = mat.node_tree.nodes.new(type='ShaderNodeLightPath')
                                mix_shader = mat.node_tree.nodes.new(type='ShaderNodeMixShader')


                                shader.inputs[0].default_value = (1, 1,1, 1) # base color
                                ramp_A.color_ramp.elements[0].position = 0.00
                                ramp_A.color_ramp.elements[1].position = 0.09
                                ramp_A.color_ramp.interpolation = 'CONSTANT'

                                mat.node_tree.links.new(shader.outputs[0], shaderToRGB_A.inputs[0])
                                mat.node_tree.links.new(shaderToRGB_A.outputs[0], ramp_A.inputs[0])
                                mat.node_tree.links.new(ramp_A.outputs[0], mix_shader.inputs[2])
                                mat.node_tree.links.new(light_path.outputs[0], mix_shader.inputs[0])
                                mat.node_tree.links.new(mix_shader.outputs[0], mat_output.inputs[0])

                                # for i in range(len(ob.material_slots)):
                                #     bpy.context.object.active_material_index = i
                                #     outline_mat = ob.active_material
                                #     if "WhiteOutline" in outline_mat.name:
                                #         for node in outline_mat.node_tree.nodes:
                                #             if "Background" in node.name: 
                                #                 shader = node

                                #             if "BSDF" in node.name: 
                                #                 shader = node
                                                
                                #             if shader:
                                #                 ncolorNode = outline_mat.node_tree.nodes.new('ShaderNodeAttribute')
                                #                 ncolorNode.attribute_name = vertexColorName
                                #                 outline_mat.node_tree.links.new(shader.inputs[0], ncolorNode.outputs[0])


                                if (hasVertexColor):
                                    vertexColorName = mesh_object.data.vertex_colors[0].name
                                    colorNode = mat.node_tree.nodes.new('ShaderNodeAttribute')
                                    colorNode.attribute_name = vertexColorName
                                    mat.node_tree.links.new(shader.inputs[0], colorNode.outputs[0])

                                mesh_object["is_gradient"] = True              
                                mesh_object["toon_color_light"] = [1.0,0.333,1.0,1.0]              
                                mesh_object["toon_color_dark"] = [0.33,0.1,0.0,1.0]              

                                if "ink" not in toonfill_mode:
                                    for mod in mesh_object.modifiers:
                                        if 'InkThickness' in mod.name:
                                            bpy.ops.object.modifier_remove(modifier="InkThickness")
                                        if 'WhiteOutline' in mod.name:
                                            bpy.ops.object.modifier_remove(modifier="WhiteOutline")
                                        if 'BlackOutline' in mod.name:
                                            bpy.ops.object.modifier_remove(modifier="BlackOutline")

                                # Assign it to object
                                if mesh_object.data.materials:
                                    mesh_object.data.materials[0] = mat
                                else:
                                    mesh_object.data.materials.append(mat)

                    if "ink" in toonfill_mode:
                        if backstage_collection:
                            # bpy.context.scene.collection.objects.link(mobj)
                            # bpy.ops.object.select_all(action='DESELECT')
                            # mesh_object.select_set(state=True)
                            # mobj.select_set(state=True)
                            # bpy.context.view_layer.objects.active = mobj
                            # bpy.ops.object.material_slot_copy()
                            # bpy.context.scene.collection.objects.unlink(mobj)
                            # bpy.ops.object.select_all(action='DESELECT')
                            # mesh_object.select_set(state=True)
                            # bpy.context.view_layer.objects.active = mesh_object

                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            ink_swatch_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = ink_swatch_object
                            bpy.ops.object.material_slot_copy()

                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = mesh_object
                            for i, mat in reversed(list(enumerate(mesh_object.data.materials))):
                                if "ink" in toonfill_mode and "toon" in toonfill_mode:
                                    if ("L_Toon." not in mat.name) and  ("L_OutlineNoShadowLight." not in mat.name) and  ("L_OutlineNoShadowDark." not in mat.name):
                                        mesh_object.active_material_index = i
                                        bpy.ops.object.material_slot_remove()
                                else:
                                    if ("L_Ink." not in mat.name) and  ("L_OutlineNoShadowLight." not in mat.name) and  ("L_OutlineNoShadowDark." not in mat.name):
                                        mesh_object.active_material_index = i
                                        bpy.ops.object.material_slot_remove()

                            for p in mesh_object.data.polygons:
                                if p.material_index >= len(mesh_object.data.materials):
                                    p.material_index = -1
                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = mesh_object


                        else:
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
                    mesh_object["is_toon_shaded"] = True


                    # bpy.types.Objects.toon_color_top = bpy.props.FloatVectorProperty(
                    #                                 name = "toon_color_top",
                    #                                 subtype = "COLOR",
                    #                                 size = 4,
                    #                                 min = 0.0,
                    #                                 max = 1.0,
                    #                                 default = (1,0.0,0.8,1.0)
                    #                                 )
                    # bpy.types.Objects.toon_color_bot = bpy.props.FloatVectorProperty(
                    #                                 name = "toon_color_bot",
                    #                                 subtype = "COLOR",
                    #                                 size = 4,
                    #                                 min = 0.0,
                    #                                 max = 1.0,
                    #                                 default = (0.25,0.3,0.7,1.0)
                    #                                 )

                    if is_insensitive:
                        mesh_object.hide_select = True



    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = True
    return {'FINISHED'} 


#------------------------------------------------------
# pose tools

def get_pose_index(obj, pose_name ):
    idx = 0
    for pm in obj.pose_library.pose_markers:
        if pose_name == pm.name:
            return idx
        idx += 1
    return None

def cycle_pose(self, objects, direction):
    global last_applied_pose_index
    objects = bpy.context.selected_objects
    if objects is not None :
        for obj in objects:
            starting_mode = bpy.context.object.mode
            if obj.type != 'ARMATURE':
                for mod in obj.modifiers:
                    if 'Skeleton' in mod.name:
                        armt = mod.object

            if obj.type == 'ARMATURE':
                    armt = obj

            if armt:                   
                is_hidden = armt.hide_get()
                if is_hidden:
                    armt.hide_set(False)
                    armt.hide_viewport = False
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                bpy.ops.object.select_all(action='DESELECT')
                armt.select_set(state=True)
                bpy.context.view_layer.objects.active = armt
                bpy.ops.object.mode_set(mode='POSE', toggle=False)
                # armt = obj.data
                # boneNames = armt.bones.keys()
                # myBones = armt.bones
                # bpy.ops.pose.select_all(action='DESELECT')
                # for poseBone in obj.pose.bones:
                #     poseBone.bone.select = True



                next_pose_index =  last_applied_pose_index
                if "POSE" in starting_mode:
                    selected_bones = bpy.context.selected_pose_bones

                active_pose_library = armt.pose_library
                if active_pose_library:
                    if next_pose_index is None:
                        print("pose %s not found." )
                    else:
                        pose_count = len(armt.pose_library.pose_markers)

                        if "next" in direction:
                            if next_pose_index < (pose_count -1):
                                next_pose_index = next_pose_index + 1  
                            else:
                                next_pose_index = 0

                        if "previous" in direction:
                            if next_pose_index > 0:
                                next_pose_index = next_pose_index - 1  
                            else:
                                next_pose_index = (pose_count -1)

                        if "OBJECT" in starting_mode:
                            bpy.ops.pose.select_all(action='SELECT')

                        if "POSE" in starting_mode:
                            bpy.ops.pose.select_all(action='DESELECT')
                            for bone in selected_bones:
                                poseBone = armt.pose.bones[bone.name]
                                poseBone.bone.select = True

                        bpy.ops.poselib.apply_pose(pose_index=next_pose_index) # add this line <<<<<<<<
                        last_applied_pose_index =  next_pose_index
                        last_pose_name = armt.pose_library.pose_markers[last_applied_pose_index].name
                        self.report({'INFO'}, 'Pose ' + last_pose_name +  ' applied!')


                else:
                    if "OBJECT" in starting_mode:
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(state=True)
                        bpy.context.view_layer.objects.active = obj

                    if is_hidden:
                        armt.hide_set(True)
                        # armt.hide_viewport = True
                    self.report({'INFO'}, 'Armature has no active pose library!')

def clean_poses(self):
    objects = bpy.context.selected_objects
    if objects is not None :
        for obj in objects:
            if obj.type == 'ARMATURE':
                armt = obj
            if armt:                   
                bpy.ops.object.mode_set(mode='POSE', toggle=False)
                active_pose_library = armt.pose_library    
                if active_pose_library:
                    bpy.ops.poselib.action_sanitize()
                    pose_count = range(0,len(armt.pose_library.pose_markers))
                    i = 0
                    for pose_index in armt.pose_library.pose_markers:
                        fcurves = bpy.data.actions[active_pose_library.name].fcurves
                        for fc in fcurves:
                            for key in fc.keyframe_points:
                                if key.co[0] == pose_index.frame:
                                    key.co[0] = i + 1
                                    fc.evaluate(i + 1)
                        i = i + 1
                    bpy.ops.poselib.action_sanitize()

def add_full_pose(self):
    global last_applied_pose_index
    objects = bpy.context.selected_objects
    if objects is not None :
        for obj in objects:
            if obj.type == 'ARMATURE':
                armt = obj
                print(armt.name)
            if armt:
                frame_max = 1                  
                frames = 0   
                count = 0               
                bpy.ops.object.mode_set(mode='POSE', toggle=False)
                active_pose_library = armt.pose_library    
                if active_pose_library:
                    selected_bones = bpy.context.selected_pose_bones
                    bpy.ops.pose.select_all(action='DESELECT')
                    for bone in selected_bones:
                        poseBone = armt.pose.bones[bone.name]
                        poseBone.bone.select = True

                    frames = [m.frame for m in armt.pose_library.pose_markers]
                    count = len(frames)
                    frame_max = max(frames) if len(frames) else 0
                    bpy.ops.poselib.pose_add(frame=frames[-1]+1, name='Pose.000')
                    bpy.ops.poselib.action_sanitize()
                    bpy.ops.pose.select_all(action='DESELECT')
                    for bone in selected_bones:
                        poseBone = armt.pose.bones[bone.name]
                        poseBone.bone.select = True
                    last_pose_name = armt.pose_library.pose_markers[count-1].name
                    bpy.ops.poselib.apply_pose(pose_index=count)
                    last_applied_pose_index = count
                    self.report({'INFO'}, 'Pose ' + last_pose_name +  ' added to pose library!')

def overwrite_full_pose(self):
    global last_applied_pose_index
    objects = bpy.context.selected_objects
    if objects is not None :
        for obj in objects:
            if obj.type == 'ARMATURE':
                armt = obj
                print(armt.name)
            if armt: 
                bpy.ops.object.mode_set(mode='POSE', toggle=False)
                active_pose_library = armt.pose_library    
                if active_pose_library:

                    #make sure inherit rotation is on.
                    for poseBone in armt.pose.bones:
                        bpy.ops.pose.select_all(action='DESELECT')
                        poseBone.bone.select = True
                        matrix_final = armt.matrix_world @ poseBone.matrix
                        bpy.ops.wm.context_collection_boolean_set(data_path_iter="selected_pose_bones", data_path_item="bone.use_inherit_rotation", type='ENABLE')
                        poseBone.matrix_world = matrix_final

                    selected_bones = bpy.context.selected_pose_bones
                    bpy.ops.pose.select_all(action='DESELECT')
                    for bone in selected_bones:
                        poseBone = armt.pose.bones[bone.name]
                        poseBone.bone.select = True
                    bpy.ops.poselib.pose_add(frame = last_applied_pose_index)
                    bpy.ops.poselib.action_sanitize()
                    bpy.ops.pose.select_all(action='DESELECT')
                    for bone in selected_bones:
                        poseBone = armt.pose.bones[bone.name]
                        poseBone.bone.select = True
                    self.report({'INFO'}, 'Pose added to pose library!')

def remove_full_pose(self):
    global last_applied_pose_index
    objects = bpy.context.selected_objects
    if objects is not None :
        for obj in objects:
            if obj.type == 'ARMATURE':
                armt = obj
                print(armt.name)
            if armt:                   
                bpy.ops.object.mode_set(mode='POSE', toggle=False)
                active_pose_library = armt.pose_library    
                if active_pose_library:
                    last_pose_name = armt.pose_library.pose_markers[last_applied_pose_index].name
                    bpy.ops.poselib.pose_remove(pose=last_pose_name)
                    last_applied_pose_index = last_applied_pose_index -1 
                    bpy.ops.poselib.apply_pose(pose_index=last_applied_pose_index)
                    self.report({'INFO'}, 'Pose removed ' + last_pose_name +  ' from pose library!')

#------------------------------------------------------
# export tools

def smart_anim_bake(obj): 
    try:
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    except:
        pass
    startFrame = bpy.context.scene.frame_start
    endFrame = bpy.context.scene.frame_end 
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    bpy.context.view_layer.objects.active = obj
    C=bpy.context
    old_area_type = C.area.type
    C.area.type='GRAPH_EDITOR'
        
    if obj.type != 'ARMATURE':
        bpy.ops.nla.bake(frame_start=startFrame, frame_end=endFrame, visual_keying=False, clear_constraints=True, bake_types={'OBJECT'})  

        # #types = {'VIEW_3D', 'TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'NLA_EDITOR', 'IMAGE_EDITOR', 'SEQUENCE_EDITOR', 'CLIP_EDITOR', 'TEXT_EDITOR', 'NODE_EDITOR', 'LOGIC_EDITOR', 'PROPERTIES', 'OUTLINER', 'USER_PREFERENCES', 'INFO', 'FILE_BROWSER', 'CONSOLE'}


        degp = bpy.context.evaluated_depsgraph_get()

        bpy.ops.graph.select_all(action='SELECT')
        bpy.ops.graph.decimate(mode='ERROR', remove_error_margin=0.1)
        bpy.ops.graph.interpolation_type(type='BEZIER')
        bpy.context.scene.frame_set(startFrame)
        obj.keyframe_insert(data_path="location", index=-1, frame=startFrame)
        bpy.context.scene.frame_set(endFrame)
        obj.keyframe_insert(data_path="location", index=-1, frame=endFrame)



        
        # bpy.ops.graph.decimate(mode='RATIO', remove_ratio=0.199732)
        # bpy.ops.graph.select_all(action='SELECT')
        # bpy.ops.graph.decimate(mode='ERROR', remove_error_margin=0.001)
        # bpy.ops.graph.interpolation_type(type='LINEAR')
        # ‘CONSTANT’, ‘LINEAR’, ‘BEZIER’, ‘SINE’, ‘QUAD’, ‘CUBIC’, ‘QUART’, ‘QUINT’, ‘EXPO’, ‘CIRC’, ‘BACK’, ‘BOUNCE’, ‘ELASTIC’


        # C.area.type='DOPESHEET_EDITOR'
        # bpy.ops.action.interpolation_type(type='BEZIER')
       
    C.area.type=old_area_type
    
def prep_cycler_instance_export(self, context):
    export_collection = getCurrentExportCollection(self, context)
    for obj in export_collection.all_objects:
        if obj.type == 'EMPTY':
            is_cycler = obj.get("is_cycler")
            if is_cycler:
                bpy.ops.object.select_all(action='DESELECT')
                for c in obj.children:
                    if not c.hide_viewport:
                        bpy.ops.object.select_all(action='DESELECT')
                        c.select_set(state=True)
                        bpy.context.view_layer.objects.active = c 
                        bpy.ops.object.duplicates_make_real()
                        real_instance_object = bpy.context.selected_objects[0]
                        bpy.ops.object.make_single_user(object=True, obdata=True, material=True, animation=False)
                        bpy.ops.object.select_all(action='DESELECT')
                        real_instance_object.select_set(state=True)
                        obj.select_set(state=True)                    
                        bpy.context.view_layer.objects.active = obj
                        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                        bpy.ops.object.select_all(action='DESELECT')
                        c.select_set(state=True)               
                        bpy.context.view_layer.objects.active = c                                        
                        bpy.ops.object.delete()
                    else:
                        objs = bpy.data.objects
                        objs.remove(objs[c.name], do_unlink=True)

def prep_letters_export(self, context, scene):
    C=bpy.context
    if (C):
        old_area_type = C.area.type
        C.area.type='VIEW_3D'

        # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        startFrame = 1
        endFrame = 72

        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        # bpy.context.window.scene = scene 
        # # activate export collection.
        # collections = scene.collection.children
        # for col in collections:
        #     col_name = col.name
        #     if "Letters." in col_name:
        #         bpy.context.view_layer.layer_collection.children[col_name].exclude = False

        startFrame = bpy.context.scene.frame_start
        endFrame = bpy.context.scene.frame_end
        bpy.context.scene.frame_current = startFrame


        export_collection = getCurrentExportCollection(self, context)
        export_collection_name = export_collection.name
        
        letters_collection = getCurrentLettersCollection()

        if not letters_collection:
            self.report({'WARNING'}, "Export Collection " + letters_collection.name + "was not found in scene, skipping export of" + scene.name)
        else:
            letters_collection_name = letters_collection.name
            bpy.context.view_layer.layer_collection.children[letters_collection_name].exclude = False
            # child_collections = bpy.context.view_layer.layer_collection.children[letters_collection_name].collection.children
            # for col in child_collections:
            #     col_name = col.name
            #     bpy.context.view_layer.layer_collection.children[letters_collection_name].children[col_name].exclude = False

        #     meshes = []

            # for obj in bpy.context.scene.objects:
            #     if obj is not None:
            #         if "Letters_" in obj.name:
            #             child_objects = get_all_children(obj)
            #             for c in child_objects:
            #                 c.hide_set(True)
            #                 c.hide_viewport = True
            #             obj.hide_set(True)
            #             obj.hide_viewport = True

            for obj in bpy.context.scene.objects:
                if obj is not None:
                    if "Letters_" in obj.name: 
                        # print(active_language)
                        # raise KeyboardInterrupt()
                        active_language = scene.panel_settings.s3dc_language
                        if active_language in obj.name:

                            bpy.ops.object.select_all(action='DESELECT')
                            # obj.select_set(state=True)
                            # bpy.context.view_layer.objects.active = obj
                            # bpy.ops.collection.objects_add_active(collection=export_collection_name)
                            # bpy.ops.collection.objects_remove(collection=letters_collection)

                            obj.hide_set(False)
                            obj.hide_viewport = False

                            if obj.animation_data:
                                if obj.type == 'OBJECT':
                                    print('>>>>> attempting to process: ' + obj.name)
                                    smart_anim_bake(obj)

                            child_objects = get_all_children(obj)
                            for c in child_objects:
                                c.hide_set(False)
                                c.hide_viewport = False

                                if c.type == 'FONT':
                                    bpy.ops.object.select_all(action='DESELECT')
                                    c.select_set(state=True)
                                    bpy.context.view_layer.objects.active = c
                                    bpy.ops.object.convert(target='MESH')
                                    mod = c.modifiers.new(name = 'Decimate', type = 'DECIMATE')
                                    mod.ratio = 0.5
                                    bpy.ops.object.modifier_apply(modifier=mod.name)

                                bpy.ops.object.select_all(action='DESELECT')
                                # c.select_set(state=True)
                                # bpy.context.view_layer.objects.active = c
                                # bpy.ops.collection.objects_add_active(collection=export_collection_name)
                                # bpy.ops.collection.objects_remove(collection=letters_collection)

                                export_collection.objects.link(c)
                                letters_collection.objects.unlink(c)

                            export_collection.objects.link(obj)
                            letters_collection.objects.unlink(obj)

                            is_toon_shaded = obj.get("is_toon_shaded")
                            if is_toon_shaded:
                                for mod in obj.modifiers:
                                    if 'InkThickness' in mod.name:
                                        obj.modifiers["InkThickness"].show_viewport = True
                                    if 'WhiteOutline' in mod.name:
                                        obj.modifiers["WhiteOutline"].show_viewport = True
                                    if 'BlackOutline' in mod.name:
                                        obj.modifiers["BlackOutline"].show_viewport = True

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
                                # bpy.ops.gpencil.convert(context, type='CURVE', use_normalize_weights=True, radius_multiplier=1.0, use_link_strokes=False, timing_mode='NONE', frame_range=100, start_frame=1, use_realtime=False, end_frame=250, gap_duration=0.0, gap_randomness=0.0, seed=0, use_timing_data=False)
                                bpy.ops.gpencil.convert(context, type='CURVE', bevel_depth=0.05, bevel_resolution=3, use_normalize_weights=False, radius_multiplier=0.1, use_link_strokes=False, start_frame=startFrame, end_frame=endFrame, use_timing_data=False)

                                # C=bpy.context
                                # old_area_type = C.area.type
                                # C.area.type='VIEW_3D'
                                # bpy.ops.gpencil.convert(context, type='CURVE', bevel_depth=0.0, bevel_resolution=0, use_normalize_weights=True, radius_multiplier=1.0, use_link_strokes=False, timing_mode='FULL', frame_range=100, start_frame=1, use_realtime=False, end_frame=250, gap_duration=0.0, gap_randomness=0.0, seed=0, use_timing_data=False)
                                # C.area.type=old_area_type
                                

                                selected_objects = bpy.context.selected_objects
                                gp_mesh = selected_objects[1]
                                bpy.ops.object.select_all(action='DESELECT')
                                bpy.context.view_layer.objects.active =  gp_mesh
                                gp_mesh.select_set(state=True)
                                gp_mesh.data.bevel_depth = 0.005
                                gp_mesh.data.bevel_resolution = 1

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

                            for mod in [m for m in obj.modifiers]:
                                mod.show_viewport = True
                                bpy.ops.object.modifier_apply(modifier=mod.name)     

            bpy.context.view_layer.layer_collection.children[letters_collection_name].exclude = True

    C.area.type=old_area_type

    return {'FINISHED'}

def export_panel(self, context, export_only_current, remove_skeletons):
    # if bpy.data.is_dirty:
    #     # self.report({'WARNING'}, "You must save your file first!")
    #     bpy.context.window_manager.popup_menu(warn_not_saved, title="Warning", icon='ERROR')
    bpy.context.scene.tool_settings.use_keyframe_insert_auto = False

    # else:
    if bpy.context.object:
        if "OBJECT" not in bpy.context.object.mode:
            if "DRAW" in bpy.context.object.mode :
                bpy.ops.gpencil.paintmode_toggle(back=False)
                bpy.ops.object.select_all(action='DESELECT')
            else:
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                bpy.ops.object.select_all(action='DESELECT')


    #make sure letter collection is active
    getCurrentLettersCollection()

    # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    startFrame = 1
    endFrame = 72

    # path to the folder
    file_path = bpy.data.filepath
    file_name = bpy.path.display_name_from_filepath(file_path)
    file_ext = '.blend'
    blend_file_dir = file_path.replace(file_name+file_ext, '')

    file_dir = os.path.dirname(os.path.dirname(file_path)) 
    episode_dir_name = os.path.basename(file_dir)
    basefilename = os.path.splitext(file_name)[0]
    tmp_path_to_file = (os.path.join(file_dir, basefilename))
    js_file_path = (os.path.join(file_dir, "files.js"))
    bat_file_path = (os.path.join(file_dir, "Read_Local.bat"))
    drive_letter = os.path.splitext(file_name)[0]

    currSceneIndex = getCurrentSceneIndex()
    current_scene_name = bpy.data.scenes[currSceneIndex].name

    active_language = bpy.context.scene.panel_settings.s3dc_language

    if "english" in active_language:
        active_language_abreviated = 'en'                    
    if "spanish" in active_language:
        active_language_abreviated = 'es'
    if "japanese." in active_language:
        active_language_abreviated = 'ja'
    if "korean." in active_language:
        active_language_abreviated = 'ko'
    if "german." in active_language:
        active_language_abreviated = 'de'
    if "french." in active_language:
        active_language_abreviated = 'fr'
    if "dutch." in active_language:
        active_language_abreviated = 'da'

    if not active_language_abreviated:
        self.report({'ERROR'}, "No Active Language!")



    # export all scenes
    i = 0


    # delete existing panels
    if os.path.exists(file_dir+'\\panels\\'):
        if not export_only_current:
            # delete existing panel.glb fils.
            for panel_files in glob.glob(file_dir+'\\panels\\*.' + active_language_abreviated +'.glb'):
                print('os.remove(', panel_files, ')')
                os.remove(panel_files)
        else:
            for panel_files in glob.glob(file_dir +'\\panels\\'+ current_scene_name + '.' + active_language_abreviated + '.glb'):
                print('os.remove(', panel_files, ')')
                os.remove(panel_files)
    else:
        os.mkdir(file_dir+'\\panels\\')

    if not os.path.exists(file_dir+'\\panels\\shared\\'):
        self.report({'ERROR'}, "No shared folder present near save location! 3D Comic directory needs to be rebuilt?")



    # copy template reader files
    if not export_only_current:            
        if not os.path.exists(file_dir+'\\index.html'):
            # # copy 3D Comic Html
            # user_dir = os.path.expanduser("~")
            # reader_subdir = "/Reader"
            # if system() == 'Linux':
            #     addon_path = "/.config/blender/" + common_subdir
            # elif system() == 'Windows':
            #     addon_path = (
            #         "\\AppData\\Roaming\\Blender Foundation\\Blender\\"
            #         + common_subdir.replace("/", "\\")
            #     )
            #     # os.path.join()
            # elif system() == 'Darwin':
            #     addon_path = "/Library/Application Support/Blender/" + common_subdir
            # addon_dir = user_dir + addon_path

            scripts_dir = bpy.utils.user_resource('SCRIPTS', "addons")
            addon_resources_subdir = "/Spiraloid-Toolkit-for-Blender-3DComicToolkit-master/Resources/"        
            addon_dir = scripts_dir + addon_resources_subdir
            addon_reader_dir = addon_dir + "/Reader"
            copy_tree(addon_reader_dir, file_dir)        


    if not export_only_current:
        # begin writing the javascript file for the comic
        js_file = open(js_file_path, "w")
        js_file.write('var files = [' +'\n')
        # js_file.write('      "./panels/header.w100h50.glb",' +'\n')  
        # js_file.write('      "./panels/black.w100h100.glb",' +'\n')  

    panels = []
    if export_only_current:
        panels.append(bpy.data.scenes[currSceneIndex])
    
    for scene in bpy.data.scenes:
        if not export_only_current:
            if "p." in scene.name:
                panels.append(scene)

    for scene in panels:
        # turn off all collections in every scene.
        for general_scene in bpy.data.scenes:
            bpy.context.window.scene = general_scene
            scene_collections = general_scene.collection.children
            for col in scene_collections:
                col_name = col.name
                bpy.context.view_layer.layer_collection.children[col_name].exclude = True
            bpy.ops.object.select_all(action='DESELECT')

        # initialize the scene
        bpy.context.window.scene = scene 
        startFrame = bpy.context.scene.frame_start
        endFrame = bpy.context.scene.frame_end
        bpy.context.scene.frame_current = startFrame
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        if bpy.context.object:
            starting_mode = bpy.context.object.mode
            if "OBJECT" not in starting_mode:
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                bpy.ops.object.select_all(action='DESELECT')
        toggle_workmode(self, context, True)

        # set the context to be the view_3d in object mode.
        C=bpy.context
        old_area_type = C.area.type
        C.area.type='VIEW_3D'

        # prepare the letters for export
        prep_letters_export(self, context, scene)

        # verify and activate export collection.
        export_collection = getCurrentExportCollection(self, context)
        if not export_collection:
            self.report({'WARNING'}, "Export Collection " + export_collection.name + "was not found in scene, skipping export of" + scene.name)
        else:
            linked_library_collections = []
            export_collection_name = export_collection.name
            bpy.context.view_layer.layer_collection.children[export_collection_name].exclude = False
            child_collections = bpy.context.view_layer.layer_collection.children[export_collection_name].collection.children
            for col in child_collections:
                col_name = col.name
                is_override_library = col.override_library
                if is_override_library:
                    col_objects = col.all_objects
                    # for cobj in col_objects:
                    #     if cobj is not None:
                    #         if bpy.context.object:
                    #             starting_mode = bpy.context.object.mode
                    #             if "OBJECT" not in starting_mode:
                    #                 bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                    #                 bpy.ops.object.select_all(action='DESELECT')
                    #         cobj.select_set(state=True)
                    #         bpy.context.view_layer.objects.active = cobj
                    #         bpy.ops.object.make_local(type='ALL')

                    ref_obj = col_objects[0]
                    ref_empty = bpy.data.objects.new('ref_' + ref_obj.name, None)  # Create new empty object
                    export_collection.objects.link(ref_empty)  # Link empty to the current object's collection
                    ref_empty.empty_display_type = 'PLAIN_AXES'
                    ref_empty.location = ref_obj.location

                    if ref_obj.type == 'ARMATURE':
                        ref_obj.make_local()
                        ch = [child for child in ref_obj.children if child.type == 'MESH' and child.find_armature()]
                        for ob in ch:
                            bpy.ops.object.select_all(action='DESELECT')
                            ob.select_set(state=True)
                            bpy.context.view_layer.objects.active = ob
                            bpy.data.objects.remove(bpy.data.objects[ob.name], do_unlink=True)

                        # print("=======DEBUG: " + str(currSceneIndex))
                        # raise KeyboardInterrupt()


                        # for mod in obj.modifiers:
                        #     if 'Skeleton' not in mod.name:
                        #         expiring_mod_name = mod.name 
                        #         bpy.ops.object.modifier_remove(modifier=expiring_mod_name)


                    # print("=======DEBUG: " + str(currSceneIndex))
                    # raise KeyboardInterrupt()

                    linked_library_blend_file_name = ref_obj.data.library.name
                    linked_library_stringFragments = linked_library_blend_file_name.split('.')
                    linked_library_filename = linked_library_stringFragments[0]
                    linked_folder_abspath = (os.path.join(file_dir, "panels\\shared\\"))
                    linked_glb_abspath_filename = (linked_folder_abspath + "\\" + linked_library_filename + ".glb")
                    linked_glb_relpath_filename = ("./shared/" + linked_library_filename + ".glb")

                    
                    if not os.path.exists(linked_glb_abspath_filename):
                        self.report({'ERROR'}, 'Cannot find shared asset :' + linked_glb_abspath_filename)

                    ref_empty["ref_filename"] = linked_glb_relpath_filename

                    # if ref_obj == 'ARMATURE':
                    #     for mod in obj.modifiers:
                    #         if 'Skeleton' not in mod.name:
                    #             expiring_mod_name = mod.name 
                    #             bpy.ops.object.modifier_remove(modifier=expiring_mod_name)
                    # else:
                    #     export_collection.children.unlink(col)

                    # bpy.data.scenes[currSceneIndex].collection.children.link(col)
                    # bpy.context.view_layer.layer_collection.children[col_name].exclude = True
                    linked_library_collections.append(col)                        
                else:
                    bpy.context.view_layer.layer_collection.children[export_collection_name].children[col_name].exclude = False

                # print("=======DEBUG: " + str(currSceneIndex))
                # raise KeyboardInterrupt()


            meshes = []
            armatures = []
            active_camera = bpy.context.scene.camera
            if active_camera is None :
                self.report({'ERROR'}, 'No Camera found in export collection of scene: ' + bpy.context.scene.name)



            # make all cycler collection instances real and delete the hidden ones.
            prep_cycler_instance_export(self, context)


            export_objects = export_collection.all_objects
            for obj in export_objects:
                if obj is not None:
                    if bpy.context.object:
                        starting_mode = bpy.context.object.mode
                        if "OBJECT" not in starting_mode:
                            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                            bpy.ops.object.select_all(action='DESELECT')



                    if "Camera." in obj.name:
                        if "Camera." in active_camera.name:
                            active_camera.select_set(state=True)
                            bpy.context.view_layer.objects.active = active_camera
                            export_camera = active_camera
                            bpy.context.scene.frame_set(startFrame)
                            obj.keyframe_insert(data_path="location", index=-1, frame=startFrame)
                            bpy.context.scene.frame_set(endFrame)
                            obj.keyframe_insert(data_path="location", index=-1, frame=endFrame)

                    if "Camera_aim." in obj.name:
                        bpy.context.scene.frame_set(startFrame)
                        obj.keyframe_insert(data_path="location", index=-1, frame=startFrame)
                        bpy.context.scene.frame_set(endFrame)
                        obj.keyframe_insert(data_path="location", index=-1, frame=endFrame)

                    # # make instances real                           
                    # bpy.ops.object.select_all(action='DESELECT')
                    # obj.select_set(state=True)
                    # bpy.context.view_layer.objects.active = obj
                    # bpy.ops.object.duplicates_make_real()

                    # freshly_deinstanced_selected_objects = bpy.context.selected_objects
                    # for ob in freshly_deinstanced_selected_objects:
                    #     if ob.type == 'MESH':
                    #         bpy.ops.object.select_all(action='DESELECT')
                    #         ob.select_set(state=True)
                    #         bpy.context.view_layer.objects.active = ob
                    #         bpy.ops.object.convert(target='MESH')



            objects = export_collection.all_objects
            for obj in objects:
                if obj is not None and obj.visible_get:
                    print (obj.name)

                    if obj.type == 'ARMATURE':
                        armatures.append(obj)

                    if obj.type == 'MESH':
                        if developer_mode:
                            if not obj.find_armature():
                                meshes.append(obj)
                        else:
                            meshes.append(obj)

                        if obj.animation_data:
                            # Collect places where animation/driver data possibly present.
                            keyable_list = [getattr(obj.data, 'shape_keys', None)]
                            for ms in obj.material_slots:
                                if not ms:
                                    continue
                                keyable_list.append(ms.material)
                            for ps in obj.particle_systems:
                                keyable_list.append(ps.settings)
                            keyable_list.append(obj)
                            keyable_list.append(obj.data)

                            # Print data paths of available animation/driver f-curves.
                            for keyable in keyable_list:
                                if not keyable or not keyable.animation_data:
                                    continue
                                action = keyable.animation_data.action
                                if action:
                                    for fc in action.fcurves:
                                        print(">>>>>> found animation on: " + obj.name + ", baking..." )
                                        smart_anim_bake(obj)
                                else:
                                    for fc in keyable.animation_data.drivers:
                                        print(">>>>>> found drivers on: " + obj.name + " " + fc.data_path)
                                        obj.animation_data_clear()
                                

                    is_toon_shaded = obj.get("is_toon_shaded")
                    if is_toon_shaded:
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(state=True)
                        bpy.context.view_layer.objects.active = obj

                        try:
                            # ToonDarkColor = obj.material_slots[0].material.node_tree.nodes["ColorRamp"].color_ramp.elements[0].color 
                            ToonLightColor = obj.material_slots[0].material.node_tree.nodes["ColorRamp"].color_ramp.elements[1].color 
                            ToonDarkColor = obj.material_slots[0].material.node_tree.nodes["ColorRamp"].color_ramp.elements[0].color 

                            # obj["ToonBlack"] = (Color((ToonDarkColor[0], ToonDarkColor[1], ToonDarkColor[2])))
                            # obj["ToonWhite"] = (Color((ToonLightColor[0], ToonLightColor[1], ToonLightColor[2])))


                            hex_color_light = toHex(ToonLightColor[0],ToonLightColor[1],ToonLightColor[2])
                            hex_color_dark = toHex(ToonDarkColor[0],ToonDarkColor[1],ToonDarkColor[2])



                            # obj.data["toon_color"] = (Color((ToonLightColor[0], ToonLightColor[1], ToonLightColor[2])))
                            # obj.data["toon_color"] = "0x" + hex_color
                            obj.data["toon_color_light"] = "#" + hex_color_light
                            obj.data["toon_color_dark"] = "#" + hex_color_dark
                        except:
                            pass

                        for mod in obj.modifiers:
                            if 'InkThickness' in mod.name:
                                obj.modifiers["InkThickness"].show_viewport = True
                            if 'WhiteOutline' in mod.name:
                                obj.modifiers["WhiteOutline"].show_viewport = True
                            if 'BlackOutline' in mod.name:
                                obj.modifiers["BlackOutline"].show_viewport = True

                    if obj.visible_get and  obj.type == 'GPENCIL':
                        # bpy.ops.gpencil.editmode_toggle(False)
                        # bpy.ops.object.mode_set(mode='OBJECT')

                        if "OBJECT" not in obj.mode:
                            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  

                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(state=True)
                        bpy.context.view_layer.objects.active = obj
                        if obj.active_material is not None:
                            gp_mat =  obj.active_material
                            gp_color = gp_mat.grease_pencil.color
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
                        bpy.ops.gpencil.convert(context, type='CURVE', use_normalize_weights=True, radius_multiplier=1.0, use_link_strokes=False, timing_mode='NONE', frame_range=100, start_frame=1, use_realtime=False, end_frame=250, gap_duration=0.0, gap_randomness=0.0, seed=0, use_timing_data=False)
                        selected_objects = bpy.context.selected_objects
                        gp_mesh = selected_objects[1]
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.context.view_layer.objects.active =  gp_mesh
                        gp_mesh.select_set(state=True)
                        gp_mesh.data.bevel_depth = 0.005
                        gp_mesh.data.bevel_resolution = 1

                        pmesh = bpy.ops.object.convert(target='MESH')
                        bpy.ops.object.select_all(action='DESELECT')
                        gp_mesh.select_set(state=True)
                        bpy.context.view_layer.objects.active = gp_mesh

                        if len(gp_mesh.data.polygons) >= 2000:
                            bpy.ops.object.modifier_add(type='DECIMATE')
                            gp_mesh.modifiers["Decimate"].decimate_type = 'DISSOLVE'
                            gp_mesh.modifiers["Decimate"].angle_limit = 0.0610865
                            bpy.ops.object.modifier_add(type='DECIMATE')
                            gp_mesh.modifiers["Decimate.001"].ratio = 0.5

                        matName = (gp_mesh.name + "Mat")
                        mat = bpy.data.materials.new(name=matName)
                        mat.use_nodes = True
                        mat.node_tree.nodes.clear()
                        mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                        shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                        if gp_mat:
                            shader.inputs[0].default_value =  gp_color
                        else:
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

                        bpy.context.collection.objects.unlink(gp_mesh) 
                        export_collection.objects.link(gp_mesh)
                        meshes.append(gp_mesh)
                        bpy.data.objects.remove(bpy.data.objects[obj.name], do_unlink=True)
                        # raise KeyboardInterrupt()
                        

                    # if obj.visible_get and  obj.type == 'FONT':
                    #     bpy.ops.object.select_all(action='DESELECT')
                    #     obj.select_set(state=True)
                    #     bpy.context.view_layer.objects.active = obj
                    #     bpy.ops.object.convert(target='MESH')
                    #     bpy.ops.object.select_all(action='DESELECT')


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
                for mesh in meshes:
                    bpy.ops.object.select_all(action='DESELECT')
                    mesh.select_set(state=True)
                    bpy.context.view_layer.objects.active = mesh
                    print('>>>>> Scene: ' + scene.name)
                    print('>>>>> Mesh: ' + mesh.name)
                    bpy.ops.object.make_local(type='ALL')
                    for mod in [m for m in mesh.modifiers]:
                        mod.show_viewport = True
                        try:
                            drivers_data = mesh.animation_data.drivers
                            for dr in drivers_data:  
                                mesh.driver_remove(dr.data_path, -1)
                        except:
                            pass
                        
                        if (mesh.type == 'MESH'):
                            bpy.ops.object.modifier_apply(modifier=mod.name)

                    # bpy.ops.object.convert(target='MESH')


                    if (mesh.type == 'CURVE'):
                        C=bpy.context
                        if (C):
                            old_area_type = C.area.type
                            C.area.type='VIEW_3D'
                            bpy.ops.object.convert(target='MESH')
                            C.area.type=old_area_type


                    objectConstraints = mesh.constraints
                    if (objectConstraints):
                        for const in objectConstraints:
                            bpy.ops.object.visual_transform_apply()
                            bpy.ops.constraint.delete(constraint=const.name, owner='OBJECT')
                            # mesh.constraints.remove(const)

                    is_toon_shaded = mesh.get("is_toon_shaded")
                    if is_toon_shaded:
                        if mesh.material_slots[0].material is not None:
                            matnodes = mesh.material_slots[0].material.node_tree.nodes
                            background_shader = matnodes.get('Background')
                            if not background_shader:
                                matnodes.clear()
                                mat_output = matnodes.new(type='ShaderNodeOutputMaterial')
                                shader = matnodes.new(type='ShaderNodeBsdfPrincipled')
                                mesh.material_slots[0].material.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])




            # # delete all the skeletons to reduce file size
            # if (remove_skeletons):
            #     if (armatures):
            #         for obj in armatures:
            #             ch = [child for child in obj.children if child.type == 'MESH' and child.find_armature()]
            #             for ob in ch:
            #                 if ob.visible_get: 
            #                     bpy.ops.object.select_all(action='DESELECT')
            #                     ob.select_set(state=True)
            #                     bpy.context.view_layer.objects.active = ob
            #                     bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

            #             bpy.ops.object.select_all(action='DESELECT')
            #             obj.select_set(state=True)
            #             bpy.context.view_layer.objects.active = obj
            #             override = bpy.context.copy()
            #             override['selected_objects'] = list(bpy.context.scene.objects)
            #             bpy.ops.object.delete(override)


            # cam_ob = bpy.context.scene.camera
            # if cam_ob is None:
            #     self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)
            # elif cam_ob.type == 'CAMERA':
            #     # cam_ob.data.clip_end = scene_bounds
            #     cam_ob.data.clip_end = 200

            # process camera

            # if active_camera is not None :
            #     for obj in objects:
            #         bpy.ops.object.select_all(action='DESELECT')
            #         if "Camera_aim." in obj.name:
            #             obj.select_set(state=True)
            #             bpy.context.view_layer.objects.active = obj
            #             bpy.ops.nla.bake(frame_start=startFrame, frame_end=endFrame, visual_keying=True, clear_constraints=True, bake_types={'OBJECT'})

            #     bpy.ops.object.select_all(action='DESELECT')
            #     active_camera.select_set(state=True)
            #     bpy.context.view_layer.objects.active = active_camera
            #     bpy.ops.nla.bake(frame_start=startFrame, frame_end=endFrame, visual_keying=True, clear_constraints=True, bake_types={'OBJECT'})
                
            #     # temp context switch
            #     #types = {'VIEW_3D', 'TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'NLA_EDITOR', 'IMAGE_EDITOR', 'SEQUENCE_EDITOR', 'CLIP_EDITOR', 'TEXT_EDITOR', 'NODE_EDITOR', 'LOGIC_EDITOR', 'PROPERTIES', 'OUTLINER', 'USER_PREFERENCES', 'INFO', 'FILE_BROWSER', 'CONSOLE'}
            #     C=bpy.context
            #     old_area_type = C.area.type
            #     C.area.type='GRAPH_EDITOR'
            #     bpy.ops.graph.decimate(mode='ERROR', remove_error_margin=0.001)

            #     C.area.type='DOPESHEET_EDITOR'
            #     bpy.ops.action.interpolation_type(type='BEZIER')
            #     C.area.type=old_area_type

            # else:
            #     self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)


                

                # if "Letters_eng." in obj.name:
                #     active_camera.select_set(state=True)
                #     bpy.context.view_layer.objects.active = active_camera
                # if "Lighting." in obj.name:
                #     active_camera.select_set(state=True)
                #     bpy.context.view_layer.objects.active = active_camera


                # for mod in obj.modifiers:
                #     if 'Skeleton' in mod.name:
                #         bpy.ops.object.modifier_apply( modifier="Skeleton")


            # selected_objects = bpy.context.selected_objects
            # for obj in objects:

                # if obj.animation_data:
                #     smart_anim_bake(obj)

                    # bpy.context.scene.frame_current = startFrame
                    # obj.keyframe_insert(data_path="location", index=-1, frame=startFrame)
                    # # bpy.ops.anim.keyframe_insert(type='Available')
                    # bpy.context.scene.frame_current = endFrame
                    # obj.keyframe_insert(data_path="location", index=-1, frame=endFrame)
                    # # bpy.ops.anim.keyframe_insert(type='Available')





            # letters = [o for o in bpy.context.scene.objects if o.type == 'FONT']
            # for text in letters:
            #     bpy.ops.object.select_all(action='DESELECT')
            #     text.select_set(state=True)
            #     bpy.context.view_layer.objects.active = text
            #     bpy.ops.object.convert(target='MESH')
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
                    load_resource(self, context, "skyball.blend", False)
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


            # armatures = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
            # for a in armatures:
            #     bpy.ops.object.select_all(action='DESELECT')
            #     bpy.context.view_layer.objects.active = a
            #     a.select_set(state=True)

            actions = bpy.data.actions
            for action in actions:
                if '3DComic_poses' in action.name:
                    try:
                        action.user_clear()
                    except:
                        pass
                    # empty_trash(self, context)


            # for linked_collection in linked_library_collections:
            #     linked_collection_name = linked_collection.name
            #     bpy.context.view_layer.layer_collection.children[linked_collection_name].exclude = False
            #     for lob in linked_collection.objects:
            #         if lob.type == 'ARMATURE':
            #             bpy.ops.object.select_all(action='DESELECT')
            #             lob.select_set(state=True)
            #             bpy.context.view_layer.objects.active = lob
            #             #get shared file name
            #             linked_library_blend_file_name = lob.data.library.name
            #             stringFragments = linked_library_blend_file_name.split('.')
            #             linked_library_filename = stringFragments[0]
                        
            #             # check if shared_asset_name.glb exists.
            #             linked_glb_filename = (file_dir + '/panels/shared/' + linked_library_filename + ".glb")
            #             if not os.path.exists(linked_glb_filename):
            #                 self.report({'ERROR'}, 'Cannot find shared asset :' + linked_glb_filename)

            #             # make shared asset local
            #             bpy.ops.object.make_local(type='ALL')

            #             # add custom property with string of shared asset
            #             lob["shared_filename"] = linked_glb_filename


            #             #delete all meshes associated with armature
            #             for child in lob.children:
            #                 bpy.ops.object.select_all(action='DESELECT')
            #                 child.select_set(state=True)
            #                 bpy.context.view_layer.objects.active = child
            #                 bpy.ops.object.delete() 

            panel_path = (os.path.join(file_dir, "panels"))
            path_to_export_file = (panel_path + "\\" + scene.name + "." + active_language_abreviated + ".glb")
            bpy.ops.export_scene.gltf(
                export_format='GLB',
                ui_tab='GENERAL', 
                export_copyright='', 
                export_image_format='AUTO', 
                export_texture_dir='', 
                export_texcoords=True, 
                export_normals=True, 
                export_draco_mesh_compression_enable=False, 
                export_draco_mesh_compression_level=6, 
                export_draco_position_quantization=14, 
                export_draco_normal_quantization=10, 
                export_draco_texcoord_quantization=12, 
                export_draco_color_quantization=10, 
                export_draco_generic_quantization=12, 
                export_tangents=False, 
                export_materials='EXPORT', 
                export_colors=True, 
                export_cameras=True, 
                export_selected=False, 
                use_selection=False, 
                export_extras=True, 
                export_yup=True, 
                export_apply=True, 
                export_animations=True, 
                export_frame_range=True, 
                export_frame_step=1, 
                export_force_sampling=False, 
                export_nla_strips=False, 
                export_def_bones=False, 
                export_current_frame=False, 
                export_skins=True, 
                export_all_influences=False, 
                export_morph=True, 
                export_morph_normal=True, 
                export_morph_tangent=False, 
                export_lights=True, 
                export_displacement=False, 
                will_save_settings=False, 
                filepath=(path_to_export_file), 
                check_existing=True, 
                filter_glob='*.glb;*.gltf')

                # export_format='GLB', 
                # ui_tab='GENERAL', 
                # export_copyright='', 
                # export_image_format='AUTO', 
                # export_texture_dir='', 
                # export_texcoords=True, 
                # export_normals=True, 
                # export_draco_mesh_compression_enable=False, 
                # export_draco_mesh_compression_level=6, 
                # export_draco_position_quantization=14, 
                # export_draco_normal_quantization=10, 
                # export_draco_texcoord_quantization=12, 
                # export_draco_generic_quantization=12, 
                # export_tangents=False, 
                # export_materials='EXPORT', 
                # export_colors=True, 
                # export_cameras=True, 
                # export_selected=False, 
                # use_selection=False, 
                # export_extras=True, 
                # export_yup=True, 
                # export_apply=True, 
                # export_animations=True, 
                # export_frame_range=True, 
                # export_frame_step=1, 
                # export_force_sampling=False, 
                # export_nla_strips=False, 
                # export_def_bones=False, 
                # export_current_frame=False, 
                # export_skins=True, 
                # export_all_influences=False, 
                # export_morph=True, 
                # export_morph_normal=False, 
                # export_morph_tangent=False, 
                # export_lights=True, 
                # export_displacement=False, 
                # will_save_settings=False, 
                # filepath=(path_to_export_file), 
                # check_existing=True, 
                # filter_glob='*.glb;*.gltf')

                # (
            # write the line for this file into the javascript file. 





            if not export_only_current:            
                # js_file.write('      "./panels/' + scene.name + '.' + active_language_abreviated + '.glb",' +'\n')  
                js_file.write('      "./panels/' + scene.name + '.${lan}.glb",' +'\n')  

            # rehide this collection so it's not in the next export.  
            # bpy.context.view_layer.layer_collection.children[export_collection_name].exclude = True

            # bpy.ops.scene.delete()

        # for obj in bpy.context.scene.objects:
        #     bpy.ops.object.select_all(action='DESELECT')
        #     obj.select_set(state=True)
        #     bpy.context.view_layer.objects.active = obj
        #     bpy.ops.object.delete() 
        # empty_trash(self, context)

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

    if not export_only_current:            
        # finish writing the javascript file
        js_file.write('      "./panels/shared/p.black.w100h25.generic.glb",' +'\n')  
        # js_file.write('      "./panels/footer.w100h50.glb",' +'\n')  
        js_file.write('];' +'\n')
        js_file.close()

    #     # create local server bat file (windows only)
    #     bat_file = open(bat_file_path, "w")
    #     stringFragments = file_dir.split(':')
    #     drive_letter = stringFragments[0] + ":"

    #     bat_file.write('@echo off' +'\n')  
    #     bat_file.write(drive_letter +'\n')  
    #     bat_file.write('cd ' + file_dir +'\n')  
    #     bat_file.write('taskkill /IM "python.exe" /F' +'\n')
    #     bat_file.write('start http://localhost:8000/?lan=' + active_language_abreviated +'^&savepoint=0\n')  
    #     bat_file.write('python -m  http.server ' +'\n')
    #     # bat_file.write('tasklist /nh /fi "imagename eq python.exe" | find /i "python.exe" > nul | (python -m  http.server)' +'\n')
    #     bat_file.write('pause' +'\n')
    #     bat_file.close()

    if export_only_current :
        js_file = open(js_file_path, "w")
        js_file.write('var files = [' +'\n')
        for panel_scene in bpy.data.scenes:
            if "p." in panel_scene.name:
                js_file.write('      "./panels/' + panel_scene.name + '.${lan}.glb",' +'\n')  
        js_file.write('      "./panels/shared/p.black.w100h25.generic.glb",' +'\n')  
        js_file.write('];' +'\n')
        js_file.close()


    self.report({'INFO'}, 'Exported Panels!')



    C.area.type=old_area_type

    ## reopen scene from before build comic
    bpy.ops.wm.open_mainfile(filepath=file_path)
    self.report({'INFO'}, 'Exported Comic!')
    # subprocess.Popen('explorer '+ file_dir)
    # subprocess.Popen(bat_file_path)
    # BR_MT_read_3d_comic.execute(self, context)
    
    return {'FINISHED'}

#------------------------------------------------------
# export tools

def reset_blender():
    return {'FINISHED'}








class NewComicSettings(bpy.types.PropertyGroup):
    title : bpy.props.StringProperty(name="Title", description="Enter Title Name", default="Inkbots S1 EP01")
    author : bpy.props.StringProperty(name="Author", description="Are you Moebius, Eisner, McFarlane, Miyazaki, Miller, Torres, Lee, Kirby?", default="Author Name")
    url : bpy.props.StringProperty(name="Author URL", description="where do you want readers to visit", default="https://3dcomic.shop/inkbots")
    start_panel_count : bpy.props.IntProperty(name="How Many Panels?",  description="Create a number of blank panels to start", min=1, max=99, default=1 )

class BR_OT_new_3d_comic(bpy.types.Operator, ImportHelper):
    """Start a new 3D Comic from scratch"""
    bl_idname = "wm.spiraloid_new_3d_comic"
    bl_label = "Create Comic Folder"
    bl_options = {'REGISTER', 'UNDO'}
    # config: bpy.props.PointerProperty(type=NewComicSettings)
    filepath : bpy.props.StringProperty(name="file path", description="3D Comic webite root folder")
    filter_glob: StringProperty( default='*.blend', options={'HIDDEN'}, )

    # directory = bpy.props.StringProperty(name="file path", description="3D Comic webite root folder")
    # comic_name = bpy.props.StringProperty(name="comic name", description="Name of 3D Comic Site", default= "s01e01")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}   

    # def draw(self, context):
    #     layout = self.layout
    #     # scene = context.scene
    #     # new_3d_panel_settings = scene.new_3d_panel_settings
    #     layout.prop(comic_name, "title", description="Name of 3D Comic Site")
    #     # layout.prop(new_3d_panel_settings, "author")
    #     # layout.prop(new_3d_panel_settings, "url")
    #     # layout.prop(new_3d_panel_settings, "start_panel_count")
    #     # layout.separator()


    def execute(self, context):
        global active_language_abreviated
        global backstage_collection_name
        root_folder, extension = os.path.splitext(self.filepath)
        comic_name = os.path.basename(self.filepath) 
        issue_name = "s01e01"
        issue_folder = root_folder + '\\' + issue_name 
        working_folder = issue_folder + '\\blender'
        shared_assets_folder = working_folder + '\\shared\\'

        filename = working_folder + '\\' + comic_name + "_v.001.blend"
        if os.path.exists(root_folder):
            bpy.context.window_manager.popup_menu(warn_folder_exists, title="Warning", icon='ERROR')
        else:
            if os.path.exists(working_folder):
                bpy.context.window_manager.popup_menu(warn_folder_exists, title="Warning", icon='ERROR')
            else:
                os.mkdir(root_folder)
                os.mkdir(issue_folder)
                os.mkdir(working_folder)
                os.mkdir(shared_assets_folder)

            # path to the folder
            file_path = bpy.data.filepath
            file_name = bpy.path.display_name_from_filepath(file_path)
            file_ext = '.blend'
            blend_file_dir = file_path.replace(file_name+file_ext, '')

            file_dir = issue_folder
            episode_dir_name = os.path.basename(file_dir)
            basefilename = os.path.splitext(file_name)[0]
            tmp_path_to_file = (os.path.join(file_dir, basefilename))
            js_file_path = (os.path.join(file_dir, "files.js"))
            bat_file_path = (os.path.join(file_dir, "Read_Local.bat"))
            drive_letter = os.path.splitext(file_name)[0]

            # currSceneIndex = getCurrentSceneIndex()
            # current_scene_name = bpy.data.scenes[currSceneIndex].name

            # active_language = bpy.context.scene.panel_settings.s3dc_language

            # if "english" in active_language:
            #     active_language_abreviated = 'en'                    
            # if "spanish" in active_language:
            #     active_language_abreviated = 'es'
            # if "japanese." in active_language:
            #     active_language_abreviated = 'ja'
            # if "korean." in active_language:
            #     active_language_abreviated = 'ko'
            # if "german." in active_language:
            #     active_language_abreviated = 'de'
            # if "french." in active_language:
            #     active_language_abreviated = 'fr'
            # if "dutch." in active_language:
            #     active_language_abreviated = 'da'

            if not active_language_abreviated:
            #     self.report({'ERROR'}, "No Active Language!")
                bpy.context.scene.panel_settings.s3dc_language = "english"

                active_language_abreviated = 'en'                    


            # # export all scenes
            # i = 0

            os.mkdir(file_dir+'\\panels\\')

            # copy template reader files
            if not os.path.exists(file_dir+'\\index.html'):
                scripts_dir = bpy.utils.user_resource('SCRIPTS', "addons")
                addon_resources_subdir = "/Spiraloid-Toolkit-for-Blender-3DComicToolkit-master/Resources/"        
                addon_dir = scripts_dir + addon_resources_subdir
                addon_reader_dir = addon_dir + "/Reader"
                copy_tree(addon_reader_dir, file_dir)        




            # scene = context.scene
            # settings = scene.new_3d_panel_settings
            # start_panel_count = settings.start_panel_count
            # start_panel_count = 1


            # title_name = settings.title
            title_name = "Cover"
            filepath = addon_dir + "comic_default.blend"
            bpy.ops.wm.read_homefile(filepath=filepath, load_ui=False)
            bpy.ops.wm.save_as_mainfile( filepath =filename)

            # load default scene
            # load_resource(self, context, "comic_default.blend", False)

            bpy.context.scene.name = title_name
            bpy.data.objects['Title'].data.body = comic_name

            for window in bpy.context.window_manager.windows:
                for v in  window.screen.areas:  # iterate through areas in current screen
                    if v.type=='VIEW_3D':
                        v.spaces[0].region_3d.view_perspective = 'CAMERA'
                        override = {
                            'area': v,
                            'region': v.regions[0],
                        }
                        if bpy.ops.view3d.view_center_camera.poll(override):
                            bpy.ops.view3d.view_center_camera(override)


            bpy.context.scene.render.filepath =  issue_folder + "\\images\\main_banner.jpg"
            bpy.context.scene.render.image_settings.color_mode = 'RGB'
            bpy.context.scene.render.image_settings.file_format = 'JPEG'
            bpy.context.scene.render.use_overwrite = True
            bpy.context.scene.render.resolution_x = 1024
            bpy.context.scene.render.resolution_y = 345
            bpy.context.scene.render.image_settings.file_format='JPEG'
            bpy.ops.render.render(use_viewport = True, write_still=True)

            # set backstage collection variable so new panel menu knows to draw
            backstage_collection_name = getCurrentBackstageCollectionName()

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


        # #create scene collection
        # shared_assets_collection_name = "Shared Assets"
        # shared_assets_collection = bpy.data.collections.new(shared_assets_collection_name)
        # bpy.context.scene.collection.children.link(shared_assets_collection)  

        # #create subcollection
        # cname = "Actors"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)
        # cname = "Props"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)
        # cname = "Places"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)
        # cname = "Places_Props"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)
        # cname = "Vehicles"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)
        # cname = "Creatures"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)
        # cname = "Vfx"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)
        # cname = "Items"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)
        # cname = "Figurines"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)
        # cname = "Materials"
        # c = bpy.data.collections.new(cname)
        # shared_assets_collection.children.link(c)


        # angle=math.radians(90.0)
        # bpy.ops.object.camera_add(enter_editmode=False, align='WORLD', location=(0, -12, 1.52), rotation=(angle, 0, 0), scale=(1, 1, 1))
        
        # firstPanelName = 'p.0001'
        # newScene = bpy.ops.scene.new(type='NEW')
        # firstPanelSceneIndex = getCurrentSceneIndex()
        # bpy.data.scenes[firstPanelSceneIndex].name = firstPanelName

        # this crashes for some unknown reasion
        # BR_OT_insert_comic_scene.execute(self, context)


        # scene = bpy.context.scene
        # for i in range(start_panel_count):
        #     # BR_OT_insert_comic_scene.execute(self,context)   # causes crash



        # BR_OT_insert_comic_scene.execute(self, context)
        # for i in range(start_panel_count):
        #     scene = context.scene
        #     settings = scene.new_3d_panel_settings
        #     title_name = settings.title
        #     start_panel_count = settings.start_panel_count
        #     panel_width = 100
        #     currSceneIndex = getCurrentSceneIndex()
        #     renameAllScenesAfter(self, context)
        #     newSceneIndex = currSceneIndex + 1
        #     newSceneIndexPadded = "%04d" % newSceneIndex
        #     newSceneName = 'p.'+ str(newSceneIndexPadded) + ".w" + str(panel_width) + "h100"
        #     newScene = bpy.ops.scene.new(type='NEW')
        #     bpy.context.scene.name = newSceneName
        #     BR_OT_panel_init.execute(self, context)
        #     BR_OT_panel_validate_naming_all.execute(self, context)
        #     for v in bpy.context.window.screen.areas:
        #         if v.type=='VIEW_3D':
        #             v.spaces[0].region_3d.view_perspective = 'CAMERA'
        #             override = {
        #                 'area': v,
        #                 'region': v.regions[0],
        #             }
        #             if bpy.ops.view3d.view_center_camera.poll(override):
        #                 bpy.ops.view3d.view_center_camera(override)
        #     bpy.ops.object.select_all(action='DESELECT')
        #     bpy.context.window.scene = bpy.data.scenes[newSceneIndex]

        # save_filepath = str(self.directory) + "." +  str(title_name) + ".blend"
        # bpy.ops.wm.save_as_mainfile(filepath=save_filepath)
        # print (self.directory)
        # bpy.ops.wm.save_as_mainfile(filepath=self.directory)

        # bpy.ops.wm.save_as_mainfile(filepath=self.filepath)

        # bpy.ops.wm.save_as_mainfile(filepath=filename)
        

        # BR_OT_new_panel_row.execute(self, context) # why does this crash......
        
        return {'FINISHED'}
        
    # def invoke(self, context, event):
    #     return context.window_manager.invoke_props_dialog(self)

class BR_OT_first_panel_scene(bpy.types.Operator):
    """make first panel scene the active scene"""
    bl_idname = "screen.spiraloid_3d_comic_first_panel"
    bl_label ="First"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.window.scene = bpy.data.scenes[0]
        return {'FINISHED'}

class BR_OT_last_panel_scene(bpy.types.Operator):
    """make last panel scene the active scene"""
    bl_idname = "screen.spiraloid_3d_comic_last_panel"
    bl_label ="Last"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        totalScenes = len(bpy.data.scenes) - 1
        bpy.context.window.scene = bpy.data.scenes[totalScenes]
        return {'FINISHED'}

class BR_OT_next_panel_scene(bpy.types.Operator):
    """make next panel scene the active scene"""
    bl_idname = "screen.spiraloid_3d_comic_next_panel"
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
    bl_idname = "screen.spiraloid_3d_comic_previous_panel"
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
        current_scene_name = bpy.data.scenes[currSceneIndex].name
        stringFragments = current_scene_name.split('.')
        x_stringFragments = stringFragments[2]
        xx_stringFragments = x_stringFragments.split('h')
        current_panel_height = xx_stringFragments[1]
        xxx_stringFragments = xx_stringFragments[0].split('w')
        current_panel_width = xxx_stringFragments[1]

        renameAllScenesAfter(self, context)

        newSceneIndex = currSceneIndex + 1
        sceneNumber = "%04d" % newSceneIndex  
        # newSceneName = 'p.'+ str(sceneNumber) + ".w100h100"
        newSceneName = 'p.'+ str(sceneNumber) + '.w' + str(current_panel_width) + 'h' + str(current_panel_height)

        newScene = bpy.ops.scene.new(type='FULL_COPY')
        bpy.context.scene.name = newSceneName

        bpy.context.scene.cursor.location[2] = 1.52

        # BR_OT_panel_init.execute(self, context)
        BR_OT_panel_validate_naming_all.execute(self, context)

        for v in bpy.context.window.screen.areas:
            if v.type=='VIEW_3D':
                v.spaces[0].region_3d.view_perspective = 'CAMERA'
                override = {
                    'area': v,
                    'region': v.regions[0],
                }
                if bpy.ops.view3d.view_center_camera.poll(override):
                    bpy.ops.view3d.view_center_camera(override)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.window.scene = bpy.data.scenes[newSceneIndex]


        return {'FINISHED'}



class BR_OT_blank_comic_scene(bpy.types.Operator):
    """ Insert a new panel scene after the currently active panel scene, copying contents"""
    bl_idname = "view3d.spiraloid_3d_comic_blank_panel"
    bl_label ="Insert Black"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        insert_comic_panel(self, context, "Static")
        return {'FINISHED'}






def insert_comic_panel(self, context, camera_strategy):
    toonfill_use_global = bpy.context.scene.panel_settings.s3dc_toonfill_use_global

    scene = context.scene
    new_panel_row_settings = scene.new_panel_row_settings
    new_panel_count = new_panel_row_settings.new_panel_count
    use_borders = new_panel_row_settings.border_strategy

    for i in range(new_panel_count):
        panel_width = int(100 / new_panel_count)
        currSceneIndex = getCurrentSceneIndex()
        renameAllScenesAfter(self, context)

        numString = getCurrentPanelNumber(False)
        newSceneIndex = currSceneIndex + 1
        newPanelIndex = numString + 1
        newPanelIndexPadded = "%04d" % newPanelIndex
        newSceneName = 'p.'+ str(newPanelIndexPadded) + ".w" + str(panel_width) + "h"  + str(panel_width)
        newScene = bpy.ops.scene.new(type='NEW')
        bpy.context.scene.name = newSceneName
        bpy.context.window.scene = bpy.data.scenes[newSceneIndex]
        # print("=======DEBUG: " + str(currSceneIndex))
        # raise KeyboardInterrupt()
        BR_OT_panel_init.execute(self, context)
        BR_OT_panel_validate_naming_all.execute(self, context)
        for v in bpy.context.window.screen.areas:
            if v.type=='VIEW_3D':
                v.spaces[0].region_3d.view_perspective = 'CAMERA'
                override = {
                    'area': v,
                    'region': v.regions[0],
                }
                if bpy.ops.view3d.view_center_camera.poll(override):
                    bpy.ops.view3d.view_center_camera(override)
        bpy.ops.object.select_all(action='DESELECT')

        backstage_collection = getCurrentBackstageCollection()
        if backstage_collection:
            global_ink_swatch_object = bpy.data.scenes[0].collection.children['Backstage.Global'].objects['Materials.Global']
            backstage_collection.objects.link(global_ink_swatch_object)


            if not toonfill_use_global:
                bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = True

        if "Static" not in camera_strategy:
            key_camera_auto(self, context, camera_strategy)
        if use_borders:
            BR_OT_add_letter_border.execute(self, context)


        # bpy.context.scene["s3dc_toonfill_use_global"] = BoolProperty(s3dc_toonfill_use_global)
        # bpy.context.scene["s3dc_dynamic_shadows"] = BoolProperty(s3dc_dynamic_shadows)
        # bpy.context.scene["s3dc_toonfill_mode_enum"] = EnumProperty(items=items)
        # bpy.context.scene["s3dc_toonfill_type"] = EnumProperty(items=items)


    # return {'FINISHED'}


class NewPanelRowSettings(bpy.types.PropertyGroup):
    new_panel_count : bpy.props.IntProperty(name="side-by-side panel count:",  description="number of side-by-side panels to insert in new row", min=1, max=4, default=1 )
    camera_strategy : bpy.props.EnumProperty(
        name="Camera Move", 
        description="Type of camera movement for new panels", 
        items={
            ("camera_slide_up", "Slide Up","SlideUp", 0),
            ("camera_slide_down","Slide Down", "SlideDown", 1),
            ("camera_truck_in", "Truck In","TruckIn", 2),
            ("camera_truck_out", "Truck Out","TruckOut", 3),
            ("camera_pan_left", "Pan Left","PanLeft", 4),
            ("camera_pan_right", "Pan Right","PanRight", 5),
            ("camera_random", "Randomize","Random", 6),
            ("world_spin_cw", "Randomize","Random", 7),
            ("world_spin_ccw", "Randomize","Random", 8),
            ("Static", "Static","Static", 9),
            },
        default="camera_random"
    )
    border_strategy : bpy.props.BoolProperty(name="Border",  description="create a border frame around the panels", default=True )

class BR_OT_new_panel_row(bpy.types.Operator, ImportHelper):
    """Insert a new empty comic panel scene or scenes side by side"""
    bl_idname = "wm.spiraloid_new_panel_row"
    bl_label = "Add Panels"
    bl_options = {'REGISTER', 'UNDO'}
    config: bpy.props.PointerProperty(type=NewPanelRowSettings)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        new_panel_row_settings = scene.new_panel_row_settings
        layout = self.layout
        layout.prop(new_panel_row_settings, "new_panel_count")
        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        layout.separator()
        col_1.separator()
        col_1.prop(new_panel_row_settings, "border_strategy")
        layout.prop(new_panel_row_settings, "camera_strategy", text="Camera Move")
        layout.separator()

    def execute(self, context):
        scene = bpy.data.scenes[0]
        if "Cover" not in scene.name:
            self.report({'ERROR'}, 'No 3D Comic folders found next to .blend file!  you need to Build 3D Comic first.')
        else:
            settings = context.scene.new_panel_row_settings
            # current_scene_name = context.scene.name
            # if "p." in bpy.context.scene.name:    
            insert_comic_panel(self, context, settings.camera_strategy)
            # else:
                # self.report({'ERROR'}, "No Active Comic Found")

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class BR_OT_insert_comic_scene(bpy.types.Operator):
    """ Insert a new panel scene after the currently active panel scene"""
    bl_idname = "view3d.spiraloid_3d_comic_create_panel"
    bl_label ="New Panel..."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        insert_comic_panel(self, context, settings.camera_strategy)

        # currSceneIndex = getCurrentSceneIndex()
        # renameAllScenesAfter(self, context)
        # # panels = []
        # # for scene in bpy.data.scenes:
        # #     if "p." in scene.name:
        # #         panels.append(scene.name)

        # # for panel in panels :
        # #     for i in range(len(bpy.data.scenes)):
        # #         if bpy.data.scenes[i].name == panel:
        # #             m = currSceneIndex - 1
        # #             if m > currSceneIndex:
        # #                 sceneNumber = "%04d" % m
        # #                 bpy.data.scenes[m].name = 'p.'+ str(sceneNumber)

        # newSceneIndex = currSceneIndex + 1
        # newSceneIndexPadded = "%04d" % newSceneIndex
        # newSceneName = 'p.'+ str(newSceneIndexPadded) + ".w100h100"
        # newScene = bpy.ops.scene.new(type='NEW')
        # bpy.context.scene.name = newSceneName
        # BR_OT_panel_init.execute(self, context)
        # BR_OT_panel_validate_naming_all.execute(self, context)

        # for v in bpy.context.window.screen.areas:
        #     if v.type=='VIEW_3D':
        #         v.spaces[0].region_3d.view_perspective = 'CAMERA'
        #         override = {
        #             'area': v,
        #             'region': v.regions[0],
        #         }
        #         if bpy.ops.view3d.view_center_camera.poll(override):
        #             bpy.ops.view3d.view_center_camera(override)




        # bpy.ops.object.select_all(action='DESELECT')





        # return {'FINISHED'}



class BR_OT_extract_comic_scene(bpy.types.Operator):
    """export current panel scene"""
    bl_idname = "view3d.spiraloid_3d_comic_extract_panel"
    bl_label ="Extract Panel Scene..."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # if bpy.data.is_dirty:
        #     # self.report({'WARNING'}, "You must save your file first!")
        #     bpy.context.window_manager.popup_menu(warn_not_saved, title="Warning", icon='ERROR')

        # else:
        currSceneIndex = getCurrentSceneIndex()
        sceneNumber = "%04d" % currSceneIndex
        current_scene = bpy.context.scene
        current_scene_name = current_scene.name
        file_path = bpy.data.filepath
        file_name = bpy.path.display_name_from_filepath(file_path)
        file_ext = '.blend'
        blend_file_dir = file_path.replace(file_name+file_ext, '')
        file_dir = os.path.dirname(os.path.dirname(file_path))
                 
        panels_dir = file_dir+"\\panels\\"
        if not os.path.exists(panels_dir):
            os.makedirs(panels_dir)

        export_file = (panels_dir + current_scene_name + ".blend") 

        for scene in bpy.data.scenes :
            scene_name = scene.name
            if scene is not current_scene :
                # bpy.ops.scene.delete({'scene': bpy.data.scenes[current_scene_name]})  
                # bpy.context.screen.scene = bpy.data.scenes[scene_name]
                bpy.context.window.scene = bpy.data.scenes[scene_name]
                bpy.ops.scene.delete()
                empty_trash(self, context)

        bpy.ops.wm.save_as_mainfile(filepath=export_file)
        ## reopen scene from before build comic
        bpy.ops.wm.open_mainfile(filepath=file_path)
        self.report({'INFO'}, 'Exported  ./panels/' + current_scene_name + '.blend!')


        return {'FINISHED'}

class BR_OT_inject_comic_scene(Operator, ImportHelper):
    """import current panel scene"""
    bl_idname = "view3d.spiraloid_3d_comic_inject_panel"
    bl_label ="Inject Panel Scene..."
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".blend"  # ExportHelper mixin class uses this
    filter_glob: StringProperty(
        default="*.blend",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )


    def execute(self, context):
        objects = bpy.context.selected_objects
        if objects is not None :
            for obj in objects:
                starting_mode = bpy.context.object.mode
                if "OBJECT" not in starting_mode:
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                    bpy.ops.object.select_all(action='DESELECT')

        filepath = self.filepath
        file_path = bpy.data.filepath

        # currSceneIndex = getCurrentSceneIndex()
        # renameAllScenesAfter(self, context)
        # newSceneIndex = currSceneIndex + 1
        # newSceneIndexPadded = "%04d" % newSceneIndex
        # imported_scene_name = 'temp.'+ str(newSceneIndexPadded) + ".w100h100"



        currSceneIndex = getCurrentSceneIndex()
        renameAllScenesAfter(self, context)
        numString = getCurrentPanelNumber(False)
        newSceneIndex = currSceneIndex + 1
        newPanelIndex = numString + 1
        newPanelIndexPadded = "%04d" % newPanelIndex
        imported_scene_name = 'temp.'+ str(newPanelIndexPadded) + ".w100h100"


        # scenes = []
        # with bpy.data.libraries.load(filepath ) as (data_from, data_to):
        #     for name in data_from.scenes:
        #         scenes.append({'name': name})
                        
        #     action = bpy.ops.wm.append
        #     action(directory=filepath + "/Scene/", files=scenes, use_recursive=True)
        #     scenes = bpy.data.scenes[-len(scenes):]

        scenes = []
        with bpy.data.libraries.load(filepath ) as (data_from, data_to):
            data_to.scenes = [name for name in data_from.scenes if name.startswith("p.")]
            for imported_scene_name in data_from.scenes:
                if "p." in imported_scene_name:
                    scenes.append({'name': imported_scene_name})

                    action = bpy.ops.wm.append
                    action(directory=filepath + "/Scene/", files=scenes, use_recursive=True)
                    # scenes = bpy.data.scenes[-len(scenes):]

                else:
                    self.report({'ERROR'}, 'No scene with "p." prefix found: ')
         
                # print("=======DEBUG: " + str(importedSceneIndex))
                # raise KeyboardInterrupt()
                imported_scene = bpy.data.scenes.get(imported_scene_name)
                imported_scene.name = imported_scene_name

        bpy.context.window.scene = bpy.data.scenes[newSceneIndex]

        # BR_OT_panel_init.execute(self, context)
        BR_OT_panel_validate_naming_all.execute(self, context)
        for v in bpy.context.window.screen.areas:
            if v.type=='VIEW_3D':
                v.spaces[0].region_3d.view_perspective = 'CAMERA'
                override = {
                    'area': v,
                    'region': v.regions[0],
                }
                if bpy.ops.view3d.view_center_camera.poll(override):
                    bpy.ops.view3d.view_center_camera(override)
        bpy.ops.object.select_all(action='DESELECT')

        return {'FINISHED'}





class BR_OT_delete_comic_scene(bpy.types.Operator):
    """ Delete currently active panel scene"""
    bl_idname = "view3d.spiraloid_3d_comic_delete_panel"
    bl_label ="Delete"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currSceneIndex = getCurrentSceneIndex()
        previousSceneIndex = currSceneIndex - 1
        bpy.ops.scene.delete()
        bpy.context.window.scene = bpy.data.scenes[previousSceneIndex]
        renameAllScenesAfter(self, context)
        BR_OT_panel_validate_naming_all.execute(self, context)



        return {'FINISHED'}

class BR_OT_reorder_scene_later(bpy.types.Operator):
    """Shift current scene later, changing the read order of panel scenes"""
    bl_idname = "screen.spiraloid_3d_comic_reorder_scene_later"
    bl_label ="Shift Scene Later"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # currSceneIndex = getCurrentSceneIndex()
        # nextSceneIndex = currSceneIndex + 1
        # current_scene_name = bpy.data.scenes[currSceneIndex].name
        # next_scene_name = bpy.data.scenes[nextSceneIndex].name
        # bpy.data.scenes[nextSceneIndex].name = next_scene_name + ".1111111111"
        # bpy.data.scenes[currSceneIndex].name = next_scene_name
        # bpy.data.scenes[nextSceneIndex].name = current_scene_name

        # validate_naming()
        # bpy.context.window.scene = bpy.data.scenes[currSceneIndex]
        # validate_naming()
        # bpy.context.window.scene = bpy.data.scenes[nextSceneIndex]
        currSceneIndex = getCurrentSceneIndex()
        nextSceneIndex = currSceneIndex + 1
        current_scene_name = bpy.data.scenes[currSceneIndex].name
        next_scene_name = bpy.data.scenes[nextSceneIndex].name
        tmp_name = "zzzz999"
        bpy.data.scenes[nextSceneIndex].name = tmp_name
        currSceneIndex = getCurrentSceneIndex()
        bpy.data.scenes[currSceneIndex].name = next_scene_name


        # bpy.data.scenes[currSceneIndex].name = previous_scene_name

        for i in range(len(bpy.data.scenes)):
            if bpy.data.scenes[i].name == tmp_name:
                bpy.data.scenes[i].name = current_scene_name
                bpy.context.window.scene = bpy.data.scenes[currSceneIndex]

        bpy.context.window.scene = bpy.data.scenes[currSceneIndex]
        validate_naming(self, context)
        bpy.context.window.scene = bpy.data.scenes[nextSceneIndex]
        validate_naming(self, context)


        return {'FINISHED'}

class BR_OT_reorder_scene_earlier(bpy.types.Operator):
    """Shift current scene Earlier, changing the read order of panel scenes"""
    bl_idname = "screen.spiraloid_3d_comic_reorder_scene_earlier"
    bl_label ="Shift Scene Earlier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currSceneIndex = getCurrentSceneIndex()
        previousSceneIndex = currSceneIndex - 1
        current_scene_name = bpy.data.scenes[currSceneIndex].name
        previous_scene_name = bpy.data.scenes[previousSceneIndex].name
        tmp_name = "zzzz"
        bpy.data.scenes[previousSceneIndex].name = tmp_name
        currSceneIndex = getCurrentSceneIndex()
        bpy.data.scenes[currSceneIndex].name = previous_scene_name
        validate_naming(self, context)


        # bpy.data.scenes[currSceneIndex].name = previous_scene_name

        for i in range(len(bpy.data.scenes)):
            if bpy.data.scenes[i].name == tmp_name:
                bpy.data.scenes[i].name = current_scene_name
                bpy.context.window.scene = bpy.data.scenes[currSceneIndex + 1]
                validate_naming(self, context)

        bpy.context.window.scene = bpy.data.scenes[currSceneIndex]

        return {'FINISHED'}


class BR_OT_add_letter_border(bpy.types.Operator):
    """Add a panel border"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_border"
    bl_label ="Add Border"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.object:
            starting_mode = bpy.context.object.mode
            if "OBJECT" not in starting_mode:
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                bpy.ops.object.select_all(action='DESELECT')

        export_collection = getCurrentExportCollection(self, context)
        active_camera = bpy.context.scene.camera
        if active_camera is not None :
            active_camera_name = active_camera.name
        else:
            self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)

        bpy.ops.object.select_all(action='DESELECT')
        # load_resource("letter_wordballoon.blend", False)
        load_resource(self, context, "letter_border.002.blend", False)
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


        letters_collection = getCurrentLettersCollection()
        if not letters_collection:
            self.report({'WARNING'}, "Export Collection " + letters_collection.name + "was not found in scene, skipping export of" + scene.name)
        else:
            for obj in objects:
                bpy.context.collection.objects.unlink(obj) 
                letters_collection.objects.link(obj)

        bpy.ops.object.select_all(action='DESELECT')
        # letter.select_set(state=True)
        # bpy.context.view_layer.objects.active = letter
        # for v in bpy.context.window.screen.areas:
        #     if v.type=='VIEW_3D':
        #         bpy.ops.view3d.snap_cursor_to_selected()


        return {'FINISHED'}



class BR_OT_add_letter_caption(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_caption"
    bl_label ="Add Caption"
    bl_options = {'REGISTER', 'UNDO'}

    # def execute(self, context):

    #     export_collection = getCurrentExportCollection(self, context)
    #     active_camera = bpy.context.scene.camera
    #     if active_camera is not None :
    #         active_camera_name = active_camera.name
    #     else:
    #         self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)

    #     bpy.ops.object.select_all(action='DESELECT')
    #     # load_resource("letter_wordballoon.blend", False)
    #     # load_resource(self, context, "letter_wordballoon.000.blend", True)
    #     load_resource(self, context, "letter_caption.000.blend", True)

    #     # load_resource("letter_caption.blend")
    #     # load_resource("letter_sfx.blend")

    #     objects = bpy.context.selected_objects
    #     if objects is not None :
    #         bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    #     letter = objects[0]
    #     letter_group = getCurrentLetterGroup()

    #     bpy.ops.object.select_all(action='DESELECT')
    #     letter.select_set(state=True)
    #     letter_group.select_set(state=True)
    #     bpy.context.view_layer.objects.active = letter_group
    #     # bpy.ops.object.parent_set()
    #     bpy.ops.object.parent_no_inverse_set()

    #     bpy.ops.object.select_all(action='DESELECT')
    #     letter.select_set(state=True)
    #     bpy.context.view_layer.objects.active = letter
    #     bpy.ops.object.origin_clear()

    #     camera_position = active_camera.matrix_world.to_translation()


    #     letters_collection = getCurrentLettersCollection()
    #     if not letters_collection:
    #         self.report({'WARNING'}, "Export Collection " + letters_collection.name + "was not found in scene, skipping export of" + scene.name)
    #     else:
    #         for obj in objects:
    #             bpy.context.collection.objects.unlink(obj) 
    #             letters_collection.objects.link(obj)

    #     bpy.ops.object.select_all(action='DESELECT')
    #     letter.select_set(state=True)
    #     bpy.context.view_layer.objects.active = letter


    #     return {'FINISHED'}

    def execute(self, context):
        add_letter(self, context, "caption", 1)
        return {'FINISHED'}



def add_letter(self, context, letter_type, letter_count):
    if bpy.context.object:
        starting_mode = bpy.context.object.mode
        if "OBJECT" not in starting_mode:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
            bpy.ops.object.select_all(action='DESELECT')

    export_collection = getCurrentExportCollection(self, context)
    backstage_collection = getCurrentBackstageCollection()

    

    active_camera = bpy.context.scene.camera
    if active_camera is not None :
        active_camera_name = active_camera.name
    else:
        self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)

    bpy.ops.object.select_all(action='DESELECT')
    # load_resource("letter_wordballoon.blend", False)

    if "wordballoon" in letter_type:
        if letter_count == 1:
            load_resource(self, context, "letter_wordballoon.000.blend", True)
        if letter_count == 2:
            load_resource(self, context, "letter_wordballoon_double.000.blend", True)
        if letter_count == 3:
            load_resource(self, context, "letter_wordballoon_triple.000.blend", True)
        if letter_count == 4:
            load_resource(self, context, "letter_wordballoon_quadruple.000.blend", True)


    if "caption" in letter_type:
        if letter_count == 1:
            load_resource(self, context, "letter_caption.000.blend", True)



    if "sfx" in letter_type:
        if letter_count == 1:
            load_resource(self, context, "letter_sfx.000.blend", True)
    #     load_resource(self, context, "letter_sfx.blend", False)


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

    if backstage_collection:
        bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = False
        backstage_objects = backstage_collection.objects
        for mobj in backstage_objects:
            if "Materials." in mobj.name:
                # bpy.context.scene.collection.objects.link(mobj)
                bpy.ops.object.select_all(action='DESELECT')
                letter.select_set(state=True)
                mobj.select_set(state=True)
                bpy.context.view_layer.objects.active = mobj
                bpy.ops.object.material_slot_copy()

                bpy.ops.object.select_all(action='DESELECT')
                letter.select_set(state=True)
                bpy.context.view_layer.objects.active = letter
                for i, mat in reversed(list(enumerate(letter.data.materials))):
                    if ("L_Wordballoon." not in mat.name) and  ("L_WordballoonOutlineDark." not in mat.name) and  ("L_WordballoonOutlineLight." not in mat.name):
                        # letter.data.materials.pop(index=i)
                        letter.active_material_index = i
                        bpy.ops.object.material_slot_remove()

                for p in letter.data.polygons:
                    if p.material_index >= len(letter.data.materials):
                        p.material_index = -1
                        


                for tobj in letter.children:
                    if tobj.type == 'FONT':
                        bpy.ops.object.select_all(action='DESELECT')
                        tobj.select_set(state=True)
                        mobj.select_set(state=True)
                        bpy.context.view_layer.objects.active = mobj
                        bpy.ops.object.material_slot_copy()

                        bpy.ops.object.select_all(action='DESELECT')
                        tobj.select_set(state=True)
                        bpy.context.view_layer.objects.active = tobj
                        for i, tmat in reversed(list(enumerate(tobj.data.materials))):
                            if ("L_WordballoonText." not in tmat.name):
                                # tobj.data.materials.pop(index=i)
                                tobj.active_material_index = i
                                bpy.ops.object.material_slot_remove()


        # bpy.context.scene.collection.objects.unlink(mobj)
        # bpy.context.scene.collection.objects.unlink(text_material_object)
        bpy.ops.object.select_all(action='DESELECT')
        letter.select_set(state=True)
        bpy.context.view_layer.objects.active = letter
        bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = True
    

    bpy.ops.object.select_all(action='DESELECT')
    letter.select_set(state=True)
    bpy.context.view_layer.objects.active = letter
    bpy.ops.object.origin_clear()

    camera_position = active_camera.matrix_world.to_translation()


    letters_collection = getCurrentLettersCollection()
    if not letters_collection:
        self.report({'WARNING'}, "Export Collection " + letters_collection.name + "was not found in scene, skipping export of" + scene.name)
    else:
        for obj in objects:
            bpy.context.collection.objects.unlink(obj) 
            letters_collection.objects.link(obj)

    bpy.ops.object.select_all(action='DESELECT')
    letter.select_set(state=True)
    bpy.context.view_layer.objects.active = letter
    for v in bpy.context.window.screen.areas:
        if v.type=='VIEW_3D':
            bpy.ops.view3d.snap_cursor_to_selected()


    return {'FINISHED'}


class BR_OT_add_letter_wordballoon(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_wordballoon"
    bl_label ="Add Wordballoon"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        add_letter(self, context, "wordballoon", 1)
        return {'FINISHED'}

class BR_OT_add_letter_wordballoon_double(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_wordballoon_double"
    bl_label ="Add Wordballoon Double"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        add_letter(self, context, "wordballoon", 2)
        return {'FINISHED'}

class BR_OT_add_letter_wordballoon_triple(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_wordballoon_triple"
    bl_label ="Add Wordballoon Triple"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        add_letter(self, context, "wordballoon", 3)
        return {'FINISHED'}

class BR_OT_add_letter_wordballoon_quadruple(bpy.types.Operator):
    """Add a new worldballoon with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_wordballoon_quadruple"
    bl_label ="Add Wordballoon Quadruple"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        add_letter(self, context, "wordballoon", 4)
        return {'FINISHED'}


# class BR_OT_language_select_english(bpy.types.Operator):
#     """Set Active lettering language to English"""
#     bl_idname = "view3d.spiraloid_3d_comic_language_select_english"
#     bl_label ="English"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#         global active_language 
#         current_scene = bpy.context.scene
#         active_language = current_scene.panel_settings.s3dc_language
#         set_active_language()
#         return {'FINISHED'}



class BR_OT_add_letter_sfx(bpy.types.Operator):
    """Add a new sfx with letters"""
    bl_idname = "view3d.spiraloid_3d_comic_add_letter_sfx"
    bl_label ="Add Sfx"
    bl_options = {'REGISTER', 'UNDO'}

    # def execute(self, context):
    #     if bpy.context.object:
    #         starting_mode = bpy.context.object.mode
    #         if "OBJECT" not in starting_mode:
    #             bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
    #             bpy.ops.object.select_all(action='DESELECT')
    #     export_collection = getCurrentExportCollection(self, context)
    #     letters_collection = getCurrentLettersCollection()
    #     objects = bpy.context.selected_objects

    #     active_camera = bpy.context.scene.camera
    #     if active_camera is not None :
    #         active_camera_name = active_camera.name
    #     else:
    #         self.report({'ERROR'}, 'No Camera found in scene: ' + bpy.context.scene.name)

    #     bpy.ops.object.select_all(action='DESELECT')
    #     # load_resource("letter_wordballoon.blend")
    #     # load_resource("letter_caption.blend")
    #     load_resource(self, context, "letter_sfx.blend", False)
    #     imported_objects = bpy.context.selected_objects

    #     if not letters_collection:
    #         self.report({'WARNING'}, "Export Collection " + letters_collection.name + "was not found in scene, skipping export of" + scene.name)
    #     else:
    #         if imported_objects:
    #             bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    #             letter = imported_objects[0]
    #             letter_group = getCurrentLetterGroup()
    #             for obj in imported_objects:
    #                 bpy.context.collection.objects.unlink(obj) 
    #                 letters_collection.objects.link(obj)

    #             bpy.ops.object.select_all(action='DESELECT')
    #             letter.select_set(state=True)
    #             letter_group.select_set(state=True)
    #             bpy.context.view_layer.objects.active = letter_group
    #             # bpy.ops.object.parent_set()
    #             bpy.ops.object.parent_no_inverse_set()

    #             bpy.ops.object.select_all(action='DESELECT')
    #             letter.select_set(state=True)
    #             bpy.context.view_layer.objects.active = letter
    #             bpy.ops.object.origin_clear()

    #             camera_position = active_camera.matrix_world.to_translation()


    #     bpy.ops.object.select_all(action='DESELECT')
    #     letter.select_set(state=True)
    #     bpy.context.view_layer.objects.active = letter
    #     for v in bpy.context.window.screen.areas:
    #         if v.type=='VIEW_3D':
    #             bpy.ops.view3d.snap_cursor_to_selected()


    #     return {'FINISHED'}

    def execute(self, context):
        add_letter(self, context, "sfx", 1)
        return {'FINISHED'}



def key_camera_auto(self, context, camera_strategy):
    active_camera = bpy.context.scene.camera
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    mid = end / 2.3
    if active_camera:
        active_camera.animation_data_clear()
        C=bpy.context
        if (C):
            old_area_type = C.area.type
            C.area.type='DOPESHEET_EDITOR'

            if camera_strategy == "camera_random":
                print("Camera needs to pan randomly!!!!!!!!!!!!!")
                bpy.context.scene.frame_current = start
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 10
                active_camera.keyframe_insert(data_path="location", index=-1, frame=start)

                bpy.context.scene.frame_current = mid
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 3
                active_camera.keyframe_insert(data_path="location", index=-1, frame=mid)

                bpy.context.scene.frame_current = end
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=end)

                bpy.ops.action.interpolation_type(type='BEZIER')
                bpy.ops.action.select_all(action='DESELECT')

            if camera_strategy == "camera_slide_up":
                bpy.context.scene.frame_current = start
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = -10
                active_camera.keyframe_insert(data_path="location", index=-1, frame=start)

                bpy.context.scene.frame_current = mid
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 0
                active_camera.keyframe_insert(data_path="location", index=-1, frame=mid)

                bpy.context.scene.frame_current = end
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=end)

                bpy.ops.action.interpolation_type(type='BEZIER')
                bpy.ops.action.select_all(action='DESELECT')

            if camera_strategy == "camera_slide_down":
                bpy.context.scene.frame_current = start
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 10
                active_camera.keyframe_insert(data_path="location", index=-1, frame=start)

                bpy.context.scene.frame_current = mid
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 3
                active_camera.keyframe_insert(data_path="location", index=-1, frame=mid)

                bpy.context.scene.frame_current = end
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=end)

                bpy.ops.action.interpolation_type(type='BEZIER')
                bpy.ops.action.select_all(action='DESELECT')

            if camera_strategy == "camera_pan_left":
                bpy.context.scene.frame_current = start
                active_camera.location[0] = 10
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=start)

                bpy.context.scene.frame_current = mid
                active_camera.location[0] = 2
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=mid)

                bpy.context.scene.frame_current = end
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=end)

                bpy.ops.action.interpolation_type(type='BEZIER')
                bpy.ops.action.select_all(action='DESELECT')

            if camera_strategy == "camera_pan_right":
                bpy.context.scene.frame_current = start
                active_camera.location[0] = -10
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=start)

                bpy.context.scene.frame_current = mid
                active_camera.location[0] = -2
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=mid)

                bpy.context.scene.frame_current = end
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=end)

                bpy.ops.action.interpolation_type(type='BEZIER')
                bpy.ops.action.select_all(action='DESELECT')


            if camera_strategy == "camera_truck_in":
                bpy.context.scene.frame_current = start
                active_camera.location[0] =  0
                active_camera.location[1] = -30
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=start)

                bpy.context.scene.frame_current = mid
                active_camera.location[0] =  0
                active_camera.location[1] = -15
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=mid)

                bpy.context.scene.frame_current = end
                active_camera.location[0] = 0.0
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=end)

                bpy.ops.action.interpolation_type(type='BEZIER')
                bpy.ops.action.select_all(action='DESELECT')


            if camera_strategy == "camera_truck_out":
                bpy.context.scene.frame_current = start
                active_camera.location[0] =  0
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=start)

                bpy.context.scene.frame_current = mid
                active_camera.location[0] =  0
                active_camera.location[1] = -17
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=mid)

                bpy.context.scene.frame_current = end
                active_camera.location[0] = 0.0
                active_camera.location[1] = -30
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=end)

                bpy.ops.action.interpolation_type(type='BEZIER')
                bpy.ops.action.select_all(action='DESELECT')


            if camera_strategy == "world_spin_cw":
                
                bpy.context.scene.frame_current = start
                active_camera.location[0] =  0
                active_camera.location[1] = -12
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=start)

                bpy.context.scene.frame_current = mid
                active_camera.location[0] =  0
                active_camera.location[1] = -17
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=mid)

                bpy.context.scene.frame_current = end
                active_camera.location[0] = 0.0
                active_camera.location[1] = -30
                active_camera.location[2] = 1.52
                active_camera.keyframe_insert(data_path="location", index=-1, frame=end)

                bpy.ops.action.interpolation_type(type='BEZIER')
                bpy.ops.action.select_all(action='DESELECT')


        C.area.type = old_area_type






class BR_OT_key_scale_hide(bpy.types.Operator):
    """Generate keyframes to scale the selected to 0.0001 and then appear on the current frame with a bounce curve"""
    bl_idname = "wm.spiraloid_3d_comic_key_scale_hide"
    bl_label ="key scale hide"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        C=bpy.context
        if (C):
            old_area_type = C.area.type
            C.area.type='DOPESHEET_EDITOR'
            bpy.ops.action.select_all(action='DESELECT')
            for ob in selected_objects:
                duration = 20
                visible_frame = bpy.context.scene.frame_current
                hide_frame = visible_frame - duration

                bpy.context.scene.frame_current = visible_frame
                ob.keyframe_insert(data_path="scale", index=-1, frame=visible_frame)

                bpy.context.scene.frame_current = hide_frame
                ob.scale[1] = 0.0001
                ob.scale[2] = 0.0001
                ob.scale[0] = 0.0001


                ob.keyframe_insert(data_path="scale", index=-1, frame=hide_frame)
                bpy.ops.action.interpolation_type(type='BOUNCE')
                bpy.ops.action.select_all(action='DESELECT')

        C.area.type = old_area_type


        return {'FINISHED'}

class BR_OT_key_camera_random(bpy.types.Operator):
    """Generate keyframes for camera randomly"""
    bl_idname = "wm.spiraloid_3d_comic_key_camera_random"
    bl_label ="random"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        key_camera_auto(self, context, "camera_random")
        return {'FINISHED'}

class BR_OT_key_camera_slide_up(bpy.types.Operator):
    """Generate keyframes for camera slide up"""
    bl_idname = "wm.spiraloid_3d_comic_key_camera_slide_up"
    bl_label ="slide up"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        key_camera_auto(self, context, "camera_slide_up")
        return {'FINISHED'}

class BR_OT_key_camera_slide_down(bpy.types.Operator):
    """Generate keyframes for camera slide down"""
    bl_idname = "wm.spiraloid_3d_comic_key_camera_slide_down"
    bl_label ="slide down"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        key_camera_auto(self, context, "camera_slide_down")
        return {'FINISHED'}


class BR_OT_key_camera_pan_left(bpy.types.Operator):
    """Generate keyframes for camera slide down"""
    bl_idname = "wm.spiraloid_3d_comic_key_camera_pan_left"
    bl_label ="slide left"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        key_camera_auto(self, context, "camera_pan_left")
        return {'FINISHED'}


class BR_OT_key_camera_pan_right(bpy.types.Operator):
    """Generate keyframes for camera pan right"""
    bl_idname = "wm.spiraloid_3d_comic_key_camera_pan_right"
    bl_label ="slide right"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        key_camera_auto(self, context, "camera_pan_left")
        return {'FINISHED'}


class BR_OT_key_camera_truck_in(bpy.types.Operator):
    """Generate keyframes for camera truck in"""
    bl_idname = "wm.spiraloid_3d_comic_key_camera_truck_in"
    bl_label ="truck in"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        key_camera_auto(self, context, "camera_truck_in")
        return {'FINISHED'}


class BR_OT_key_camera_truck_out(bpy.types.Operator):
    """Generate keyframes for camera truck in"""
    bl_idname = "wm.spiraloid_3d_comic_key_camera_truck_out"
    bl_label ="truck out"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        key_camera_auto(self, context, "camera_truck_out")
        return {'FINISHED'}


class  BR_OT_key_world_spin_cw(bpy.types.Operator):
    """Generate keyframes for camera spinning clockwise"""
    bl_idname = "wm.spiraloid_3d_comic_key_world_spin_cw"
    bl_label ="spin CW"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        key_camera_auto(self, context, "world_spin_cw")
        return {'FINISHED'}

class  BR_OT_key_world_spin_ccw(bpy.types.Operator):
    """Generate keyframes for camera spinning counter clockwise"""
    bl_idname = "wm.spiraloid_3d_comic_key_world_spin_ccw"
    bl_label ="spin CCW"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        key_camera_auto(self, context, "world_spin_ccw")
        return {'FINISHED'}





class BR_OT_panel_validate_naming(bpy.types.Operator):
    """Verify 3d panel naming is correct for export"""
    bl_idname = "view3d.spiraloid_3d_comic_panel_validate_naming"
    bl_label ="Validate Panel Naming"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        validate_naming(self, context)
        return {'FINISHED'}



class BR_OT_panel_validate_naming_all(bpy.types.Operator):
    """Verify 3d panel naming is correct for export"""
    bl_idname = "view3d.spiraloid_3d_comic_panel_validate_naming_all"
    bl_label ="Validate All Panel Naming"
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
                    bpy.context.window.scene = bpy.data.scenes[i]                
                    validate_naming(self, context)

        bpy.context.window.scene = bpy.data.scenes[currSceneIndex]

        return {'FINISHED'}




class BR_OT_panel_init(bpy.types.Operator):
    """Setup scene as a 3D comic panel"""
    bl_idname = "view3d.spiraloid_3d_comic_panel_init"
    bl_label ="Initialize Panel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.object:
            starting_mode = bpy.context.object.mode
            if "OBJECT" not in starting_mode:
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                bpy.ops.object.select_all(action='DESELECT')


        currSceneIndex = getCurrentSceneIndex()
        currScene =  bpy.data.scenes[currSceneIndex]
        currsceneName = currScene.name
        panelNumber = getCurrentPanelNumber(True)
        existing_prefix_name = "previously_existing_"
        active_camera = bpy.context.scene.camera



        current_scene_name = bpy.data.scenes[currSceneIndex].name
        stringFragments = current_scene_name.split('.')
        if len(stringFragments) >= 2:
            x_stringFragments = stringFragments[2]
            xx_stringFragments = x_stringFragments.split('h')
            current_panel_height = xx_stringFragments[1]
            xxx_stringFragments = xx_stringFragments[0].split('w')
            current_panel_width = xxx_stringFragments[1]
            panelSceneName = 'p.'+ str(panelNumber) + '.w' + str(current_panel_width) + 'h' + str(current_panel_height)
        else:
            panelSceneName = 'p.'+ str(panelNumber) + '.w100h100'

        bpy.data.scenes[currSceneIndex].name = panelSceneName

        wip_collection_name = "Wip." + panelNumber
        export_collection_name = "Export." + panelNumber
        letters_collection_name = "Letters." + panelNumber
        backstage_collection_name = "Backstage." + panelNumber

        scene_collections = bpy.data.scenes[currSceneIndex].collection.children

        # for c in scene_collections:
        #     c.name = existing_prefix_name + c.name

        objects = bpy.context.scene.objects
        pcamera = []
        pcamera_aim = []
        if active_camera:
            for obj in objects:
                if obj.type == 'CAMERA':
                    obj.name = existing_prefix_name + "Camera"
                    pcamera.append(obj)
                if "Camera_aim." in obj.name:
                    obj.name = existing_prefix_name + "Camera_aim"
                    pcamera_aim.append(obj)


        # wip_collection = bpy.data.collections.new(wip_collection_name)
        # bpy.context.scene.collection.children.link(wip_collection)


        hasExportCollection = False
        hasLettersCollection = False
        hasBackstageCollection = False

        scene_collections = bpy.data.scenes[currSceneIndex].collection.children
        for c in scene_collections:
            collectionNameStringFragments = c.name.split('.')

            if "Export" in collectionNameStringFragments[0]:
                c.name = export_collection_name
                hasExportCollection = True
                export_collection = c

            if "Letters" in collectionNameStringFragments[0]:
                c.name = letters_collection_name
                hasLettersCollection = True
                letters_collection = c

            if "Backstage" in collectionNameStringFragments[0]:
                c.name = backstage_collection_name
                hasBackstageCollection = True
                backstage_collection = c

        # # stop to see what's going on
        # raise KeyboardInterrupt()

        try:
            active_collection = bpy.context.collection
        except:
            pass 

        if hasExportCollection:
            export_collection = bpy.data.collections.get(export_collection_name)
        else:
            export_collection =  bpy.data.collections.new(export_collection_name)
            bpy.context.scene.collection.children.link(export_collection)

        # # stop to see what's going on
        # raise KeyboardInterrupt()


        if hasLettersCollection:
            letters_collection = bpy.data.collections.get(letters_collection_name)
        else:
            letters_collection =  bpy.data.collections.new(letters_collection_name)
            bpy.context.scene.collection.children.link(letters_collection)


        if hasBackstageCollection:
            backstage_collection = bpy.data.collections.get(backstage_collection_name)
        else:
            backstage_collection =  bpy.data.collections.new(backstage_collection_name)
            bpy.context.scene.collection.children.link(backstage_collection)




        # existing_export_collection = bpy.data.collections.get(export_collection_name)
        # existing_letters_collection = bpy.data.collections.get(letters_collection_name)



        # load default scene
        load_resource(self, context, "panel_default.blend", False)



        # link imported collection to scene so it shows up in outliner
        loaded_export_collection_name =  "Export.TEMPLATE"
        loaded_export_collection = bpy.data.collections.get(loaded_export_collection_name)
        loaded_letter_collection_name =  "Letters.TEMPLATE"
        loaded_letter_collection = bpy.data.collections.get(loaded_letter_collection_name)
        loaded_backstage_collection_name =  "Backstage.TEMPLATE"
        loaded_backstage_collection = bpy.data.collections.get(loaded_backstage_collection_name)

        # # stop to see what's going on
        # raise KeyboardInterrupt()

        bpy.context.scene.collection.children.link(loaded_export_collection)
        bpy.context.scene.collection.children.link(loaded_letter_collection)
        bpy.context.scene.collection.children.link(loaded_backstage_collection)






        if active_camera:
            for obj in objects:
                if obj.type == 'CAMERA':
                    if "Camera.TEMPLATE" in obj.name:
                        camera_name = 'Camera.'+ str(panelNumber)
                        obj.name = camera_name
                        bpy.context.scene.camera = bpy.data.objects[obj.name]   
                        letters_collection = getCurrentLettersCollection()
                        obj.location[0] = active_camera.location[0]
                        obj.location[1] = active_camera.location[1]
                        obj.location[2] = active_camera.location[2]
                        if letters_collection:
                            letters_objects = letters_collection.objects
                            for letter_group in letters_objects:
                                if letter_group.type == 'EMPTY':
                                    if "Letters_" in letter_group.name:
                                        scene_camera = bpy.context.scene.objects[camera_name]
                                        bpy.ops.object.select_all(action='DESELECT')
                                        letter_group.select_set(state=True)
                                        scene_camera.select_set(state=True)
                                        bpy.context.view_layer.objects.active = scene_camera
                                        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                        obj.data.lens = active_camera.data.lens
                        obj.data.clip_start = active_camera.data.clip_start
                        obj.data.clip_end = active_camera.data.clip_end
                        obj.data.dof.use_dof = active_camera.data.dof.use_dof
                        obj.data.sensor_fit = active_camera.data.sensor_fit
                        obj.data.show_background_images = active_camera.data.show_background_images
                        obj.data.show_safe_areas = active_camera.data.show_safe_areas
                        bpy.data.objects.remove(bpy.data.objects[active_camera.name], do_unlink=True)
                        # bpy.context.scene.camera = obj
               
                if "Camera_aim." in obj.name:
                    obj.name = 'Camera_aim.'+ str(panelNumber)

                # if pcamera_aim:
                    # obj = pcamera_aim[0]
                    # bpy.data.objects.remove(bpy.data.objects[obj.name], do_unlink=True)
        else:
            for obj in objects:
                if obj.type == 'CAMERA':
                    if "Camera.TEMPLATE" in obj.name:
                        obj.name = 'Camera.'+ str(panelNumber)
                        bpy.context.scene.camera = bpy.data.objects[obj.name]   
                if obj.type == 'EMPTY':                
                    if "Camera_aim.TEMPLATE" in obj.name:
                        obj.name = 'Camera_aim.'+ str(panelNumber)

        if letters_collection:
            letters_objects = letters_collection.objects
            template_letters_objects = loaded_letter_collection.objects
            for tobj in template_letters_objects:
                isMatchFound = False
                templateStringFragments = tobj.name.split('.TEMPLATE')
                new_letter_group_name = templateStringFragments[0] + "." + str(panelNumber) 
                for lobj in letters_objects:
                    if lobj.type == 'EMPTY':
                        if "Letters_" in lobj.name:
                            letterNameStringFragments = lobj.name.split('.')
                            if letterNameStringFragments[0] == templateStringFragments[0]:
                                isMatchFound = True
                if isMatchFound:
                    bpy.data.objects.remove(bpy.data.objects[tobj.name], do_unlink=True)
                else:
                    letters_collection.objects.link(tobj)
                    tobj.name = new_letter_group_name

            for obj in letters_objects:
                if obj.type == 'EMPTY':
                    if "Letters_" in obj.name:
                        letterPrefixStringFragments = lobj.name.split('.')
                        new_letter_group_name = letterPrefixStringFragments[0] + "." + str(panelNumber) 

                        # letters_collection.objects.link(obj)

                        if "TEMPLATE" in obj.name:
                            isMatchFound = False
                            languageStringFragments = obj.name.split('.TEMPLATE')
                            new_letter_group_name = languageStringFragments[0] + "." + str(panelNumber) 
                            for o in letters_objects:
                                if o.name == new_letter_group_name:
                                    bpy.data.objects.remove(bpy.data.objects[obj.name], do_unlink=True)
                                    isMatchFound = True
                            if not isMatchFound:
                                obj.name = new_letter_group_name

                        try:
                            loaded_letter_collection.objects.unlink(obj)
                            export_collection.objects.unlink(obj)
                        except:
                            pass

            scene_collections = bpy.data.scenes[currSceneIndex].collection.children
            for c in scene_collections:
                if c.name == loaded_letter_collection_name:                        
                    bpy.data.scenes[currSceneIndex].collection.children.unlink(c)
                if c.name == loaded_export_collection_name:                        
                    bpy.data.scenes[currSceneIndex].collection.children.unlink(c)


            coll = bpy.data.collections.get(loaded_letter_collection_name)
            if coll:
                obs = [o for o in coll.objects if o.users == 1]
                while obs:
                    bpy.data.objects.remove(obs.pop())
                bpy.data.collections.remove(coll)

            coll = bpy.data.collections.get(loaded_export_collection_name)
            if coll:
                obs = [o for o in coll.objects if o.users == 1]
                while obs:
                    bpy.data.objects.remove(obs.pop())
                bpy.data.collections.remove(coll)






        if backstage_collection:
            backstage_objects = backstage_collection.objects
            template_backstage_objects = loaded_backstage_collection.objects
            for tobj in template_backstage_objects:
                templateStringFragments = tobj.name.split('.TEMPLATE')
                new_backstage_object_name = templateStringFragments[0] + "." + str(panelNumber) 
                backstage_collection.objects.link(tobj)
                # export_collection.objects.unlink(tobj)
                tobj.name = new_backstage_object_name

            backstage_objects = backstage_collection.objects
            for obj in backstage_objects:
                if "Materials" in obj.name:
                    for i in range(len(obj.material_slots)):
                        mat = obj.material_slots[i].material
                        if ".TEMPLATE" in mat.name:
                            templateStringFragments = mat.name.split('.TEMPLATE')
                            new_backstage_material_name = templateStringFragments[0] + "." + str(panelNumber) 
                            mat.name = new_backstage_material_name
                    try:
                        export_collection.objects.unlink(obj)
                    except:
                        pass

            scene_collections = bpy.data.scenes[currSceneIndex].collection.children
            for c in scene_collections:
                if c.name == loaded_backstage_collection_name:                        
                    bpy.data.scenes[currSceneIndex].collection.children.unlink(c)
                if c.name == loaded_export_collection_name:                        
                    bpy.data.scenes[currSceneIndex].collection.children.unlink(c)


            coll = bpy.data.collections.get(loaded_backstage_collection_name)
            if coll:
                obs = [o for o in coll.objects if o.users == 1]
                while obs:
                    bpy.data.objects.remove(obs.pop())
                bpy.data.collections.remove(coll)

            coll = bpy.data.collections.get(loaded_export_collection_name)
            if coll:
                obs = [o for o in coll.objects if o.users == 1]
                while obs:
                    bpy.data.objects.remove(obs.pop())
                bpy.data.collections.remove(coll)

            bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = True


            # shuffled_letters_objects = letters_collection.objects
            # if shuffled_letters_objects:
            #     for obj in shuffled_letters_objects:
            #         if obj.type == 'EMPTY':
            #                 if "TEMPLATE" in obj.name:
            #                     languageStringFragments = obj.name.split('.TEMPLATE')
            #                     for ob in shuffled_letters_objects:
            #                         if "TEMPLATE" not in ob.name:
            #                             if languageStringFragments[0] in ob.name:
            #                                 bpy.data.objects.remove(bpy.data.objects[obj.name], do_unlink=True)
            #                                 letterGroupStringFragments = ob.name.split('.')
            #                                 ob.name = letterGroupStringFragments[0] + "." + str(panelNumber)



        # objects = bpy.context.scene.objects
        # for obj in objects:
        #     try:
        #         bpy.context.scene.collection.objects.unlink(obj)
        #     except:
        #         pass
            
        #     for c in bpy.data.collections:
        #         try:
        #             c.objects.unlink(obj)
        #         except:
        #             pass
        #     if "Letters_" not in obj.name:
        #         export_collection.objects.link(obj)
        #     else:
        #         letters_collection.objects.link(obj)
        # objects = export_collection.objects
        # pcamera = []
        # pcamera_aim = []
        # for obj in objects:
        #     if obj.type == 'CAMERA':
        #         pcamera.append(obj)
        #     if "Camera_aim." in obj.name:
        #         pcamera_aim.append(obj)


        # if pcamera:
        #     obj = pcamera[0]
        #     bpy.context.scene.camera = bpy.data.objects[obj.name]

        #     if active_camera:
        #         obj.name = 'Camera.'+ str(panelNumber)
        #         obj.location[0] = active_camera.location[0]
        #         obj.location[1] = active_camera.location[1]
        #         obj.location[2] = active_camera.location[2]
        #         bpy.data.objects.remove(bpy.data.objects[active_camera.name], do_unlink=True)

            
        #     if pcamera_aim:
        #         obj = pcamera_aim[0]
        #         obj.name = 'Camera_aim.'+ str(panelNumber)

        # letters_objects = letters_collection.objects
        # for obj in letters_objects:
        #     if "Letters_english." in obj.name:
        #         obj.name = 'Letters_english.'+ str(panelNumber)
        #     if "Letters_spanish." in obj.name:
        #         obj.name = 'Letters_spanish.'+ str(panelNumber)
        #     if "Letters_japanese." in obj.name:
        #         obj.name = 'Letters_japanese.'+ str(panelNumber)
        #     if "Letters_korean." in obj.name:
        #         obj.name = 'Letters_korean.'+ str(panelNumber)  
        #     if "Letters_german." in obj.name:
        #         obj.name = 'Letters_german.'+ str(panelNumber)  
        #     if "Letters_french." in obj.name:
        #         obj.name = 'Letters_french.'+ str(panelNumber)  
        #     if "Letters_dutch." in obj.name:
        #         obj.name = 'Letters_dutch.'+ str(panelNumber)  


        # # library = bpy.data.libraries['panel_default.blend']
        # # for usid in  library.users_id:
        # #     usid.user_clear()

        # # for library in bpy.data.libraries:
        # #     bpy.data.libraries.

        bpy.context.scene.render.resolution_x = 1024
        bpy.context.scene.render.resolution_y = 1024
        bpy.context.scene.frame_start = 1 
        bpy.context.scene.frame_end = 72
        bpy.context.scene.cursor.location[2] = 1.52


        #cleanup
        for c in scene_collections:
            if existing_prefix_name in c.name:
                bpy.data.scenes[currSceneIndex].collection.children.unlink(c)
                bpy.data.collections.remove(c)



        objects = bpy.context.scene.objects
        for obj in objects:
            if existing_prefix_name in obj.name:
                bpy.data.objects.remove(bpy.data.objects[obj.name], do_unlink=True)
        empty_trash(self, context)




        for itex in bpy.data.textures: 
            if "L_InkThickness.TEMPLATE" in itex.name:
                itexStringFragments = itex.name.split('.TEMPLATE')
                itex.name = itexStringFragments[0] + "." + str(panelNumber)
                print(itex.name)



        return {'FINISHED'}



# class BR_OT_panel_init(bpy.types.Operator):
#     """Setup scene as a 3D comic panel"""
#     bl_idname = "view3d.spiraloid_3d_comic_panel_init"
#     bl_label ="Initialize Panel"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#         currSceneIndex = getCurrentSceneIndex()
#         currPanelIndex = getCurrentPanelNumber(False)
#         panelNumber = "%04d" % currPanelIndex
#         # sceneNumber = "%04d" % currSceneIndex
#         current_scene_name = bpy.data.scenes[currSceneIndex].name
#         old_export_collection_name = "old_export_collection"

#         stringFragments = current_scene_name.split('.')
#         x_stringFragments = stringFragments[2]
#         xx_stringFragments = x_stringFragments.split('h')
#         current_panel_height = xx_stringFragments[1]
#         xxx_stringFragments = xx_stringFragments[0].split('w')
#         current_panel_width = xxx_stringFragments[1]
#         # print (stringFragments)
#         # print (x_stringFragments)
#         # print (xx_stringFragments)
#         # print (xxx_stringFragments)


#         bpy.ops.object.select_all(action='DESELECT')
#         active_camera = bpy.context.scene.camera

#         # panels = []
#         # for scene in bpy.data.scenes:
#         #     if "p." in scene.name:
#         #         panels.append(scene.name)

#         # for panel in panels :
#         #     for i in range(len(bpy.data.scenes)):
#         #         if bpy.data.scenes[i].name == panel:
#         #             m = currSceneIndex - 1
#         #             if m > currSceneIndex:
#         #                 sceneNumber = "%04d" % m
#         #                 bpy.data.scenes[m].name = 'p.'+ str(sceneNumber)


#         currScene =  bpy.data.scenes[currSceneIndex]
#         currsceneName = currScene.name
#         # panelSceneName = 'p.'+ str(sceneNumber) + ".w100h100"
#         panelSceneName = 'p.'+ str(panelNumber) + '.w' + str(current_panel_width) + 'h' + str(current_panel_height)

#         # if panelSceneName != currsceneName:
#         bpy.data.scenes[currSceneIndex].name = panelSceneName
#         # currsceneName = currScene.name

#         # for c in bpy.data.collections:
#         #     if c.name is export_collection_name:


#         wip_collection_name = "Wip." + panelNumber
#         export_collection_name = "Export." + panelNumber
#         letters_collection_name = "Letters." + panelNumber
#         scene_collections = bpy.data.scenes[currSceneIndex].collection.children

#         for c in scene_collections:
#             if c.name == export_collection_name:
#                 c.name = old_export_collection_name
#                 self.report({'INFO'}, 'Renaming Old Export Collection!')
#                 # print ("Removing existing export collection")
#                 # bpy.data.scenes[currSceneIndex].collection.children.unlink(c)
#                 # bpy.data.collections.remove(c)
#                 # bpy.ops.outliner.orphans_purge()


#         wip_collection = bpy.data.collections.new(wip_collection_name)
#         export_collection =  bpy.data.collections.new(export_collection_name)
#         letters_collection =  bpy.data.collections.new(letters_collection_name)
#         bpy.context.scene.collection.children.link(wip_collection)
#         bpy.context.scene.collection.children.link(export_collection)
#         bpy.context.scene.collection.children.link(letters_collection)
#         # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[wip_collection_name]

#         # load selected scene
#         load_resource(self, context, "panel_default.blend", False)

#         # link imported collection to scene so it shows up in outliner
#         loaded_export_collection_name =  "Export.TEMPLATE"
#         loaded_export_collection = bpy.data.collections.get(loaded_export_collection_name)

#         loaded_letter_collection_name =  "Letters.TEMPLATE"
#         loaded_letter_collection = bpy.data.collections.get(loaded_letter_collection_name)

#         # bpy.data.scenes[currSceneIndex].collection.children.link(export_collection_name)

#         objects = bpy.context.scene.objects
#         # objects = loaded_export_collection.all_objects
#         for obj in objects:
#             # try :
#             #     # loaded_export_collection.objects.unlink(obj)
#             #     bpy.data.collections[loaded_export_collection_name].objects.unlink(obj)
#             # except:
#             #     pass
#             try:
#                 bpy.context.scene.collection.objects.unlink(obj)
#             except:
#                 pass
            
#             for c in bpy.data.collections:
#                 try:
#                     c.objects.unlink(obj)
#                 except:
#                     pass
#             if "Letters_" not in obj.name:
#                 export_collection.objects.link(obj)
#             else:
#                 letters_collection.objects.link(obj)
#             # bpy.data.collections[export_collection_name].objects.link(obj)
#         objects = export_collection.objects
#         pcamera = []
#         pcamera_aim = []
#         for obj in objects:
#             if obj.type == 'CAMERA':
#                 pcamera.append(obj)
#             if "Camera_aim." in obj.name:
#                 pcamera_aim.append(obj)


#         if pcamera:
#             obj = pcamera[0]
#             # if "Camera." in obj.name:


#             # if active_camera:
#             #     active_camera.name = 'Camera.'+ str(sceneNumber)
#             #     bpy.data.objects[obj.name]
#             #     export_collection.objects.link(active_camera)

#             #     bpy.ops.object.select_all(action='DESELECT')
#             #     bpy.data.objects['Letters_eng.'+ str(sceneNumber)].select = True
#             #     active_camera.select = True
#             #     bpy.context.view_layer.objects.active = active_camera
#             #     bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)

#             #     bpy.data.objects.remove(bpy.data.objects[obj.name], do_unlink=True)
#             #     # bpy.ops.object.delete(use_global=False)
#             # else:
#             bpy.context.scene.camera = bpy.data.objects[obj.name]

#             if active_camera:
#                 obj.name = 'Camera.'+ str(panelNumber)
#                 obj.location[0] = active_camera.location[0]
#                 obj.location[1] = active_camera.location[1]
#                 obj.location[2] = active_camera.location[2]
#                 bpy.data.objects.remove(bpy.data.objects[active_camera.name], do_unlink=True)

            
#             if pcamera_aim:
#                 obj = pcamera_aim[0]
#                 obj.name = 'Camera_aim.'+ str(panelNumber)

#         letters_objects = letters_collection.objects
#         for obj in letters_objects:
#             if "Letters_english." in obj.name:
#                 obj.name = 'Letters_english.'+ str(panelNumber)
#             if "Letters_spanish." in obj.name:
#                 obj.name = 'Letters_spanish.'+ str(panelNumber)
#             if "Letters_japanese." in obj.name:
#                 obj.name = 'Letters_japanese.'+ str(panelNumber)
#             if "Letters_korean." in obj.name:
#                 obj.name = 'Letters_korean.'+ str(panelNumber)  
#             if "Letters_german." in obj.name:
#                 obj.name = 'Letters_german.'+ str(panelNumber)  
#             if "Letters_french." in obj.name:
#                 obj.name = 'Letters_french.'+ str(panelNumber)  
#             if "Letters_dutch." in obj.name:
#                 obj.name = 'Letters_dutch.'+ str(panelNumber)  


#         # library = bpy.data.libraries['panel_default.blend']
#         # for usid in  library.users_id:
#         #     usid.user_clear()

#         # for library in bpy.data.libraries:
#         #     bpy.data.libraries.

#         bpy.context.scene.render.resolution_x = 1024
#         bpy.context.scene.render.resolution_y = 1024
#         bpy.context.scene.frame_start = 1 
#         bpy.context.scene.frame_end = 72
#         bpy.context.scene.cursor.location[2] = 1.52


#         #cleanup
#         for c in scene_collections:
#             if c.name == old_export_collection_name:
#                 bpy.data.scenes[currSceneIndex].collection.children.unlink(c)
#                 bpy.data.collections.remove(c)
#                 bpy.ops.outliner.orphans_purge()


#         return {'FINISHED'}


class BR_OT_panel_init_workshop_lighting(bpy.types.Operator):
    """initialize with workshop lighting"""
    bl_idname = "view3d.spiraloid_3d_comic_init_workshop_lighting"
    bl_label ="Lightkit"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        currSceneIndex = getCurrentSceneIndex()
        numString = getCurrentPanelNumber(False)
        sceneNumber = "%04d" % numString

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
        keylight.data.use_contact_shadow = True
        keylight.data.shadow_buffer_bias = 0.0100001
        keylight.data.angle = 0
        keylight.data.shadow_cascade_max_distance = 10
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
        rim.data.use_contact_shadow = True
        rim.data.shadow_buffer_bias = 0.0100001
        rim.data.angle = 0
        rim.data.shadow_cascade_max_distance = 10
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
        back.data.use_contact_shadow = True
        back.data.shadow_buffer_bias = 0.0100001
        back.data.angle = 0
        back.data.shadow_cascade_max_distance = 10
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
        fill.data.use_contact_shadow = True
        fill.data.shadow_buffer_bias = 0.0100001
        fill.data.angle = 0
        fill.data.shadow_cascade_max_distance = 10
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

        #setup renderer.
        bpy.context.scene.eevee.taa_samples = 1
        bpy.context.scene.eevee.use_taa_reprojection = False
        bpy.context.scene.eevee.use_gtao = False
        bpy.context.scene.eevee.use_bloom = False
        bpy.context.scene.eevee.use_ssr = False
        bpy.context.scene.eevee.use_soft_shadows = True
        bpy.context.scene.eevee.shadow_cube_size = '64'
        bpy.context.scene.eevee.shadow_cascade_size = '4096'
        bpy.context.scene.eevee.sss_samples = 1



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







class BR_OT_panel_cycle_sky(bpy.types.Operator):
    """initialize with Ink and Shade All lighting"""
    bl_idname = "view3d.spiraloid_3d_comic_cycle_sky"
    bl_label ="Cycle Sky"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        backstage_collection = getCurrentBackstageCollection()
        objects = bpy.context.selected_objects
        currSceneIndex = getCurrentSceneIndex()
        currPanelIndex = getCurrentPanelNumber(True)

        scene = bpy.data.scenes[currSceneIndex]
        sky_name = "Sky." + str(currPanelIndex)

        if objects is not None :
            for obj in objects:
                starting_mode = bpy.context.object.mode
                if "OBJECT" not in starting_mode:
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  


        if not backstage_collection:
            self.report({'INFO'}, 'No Backstage Collection found, initializng as 3D Comic Panel!')
            BR_OT_panel_init.execute(self, context)
            backstage_collection = getCurrentBackstageCollection()

        scene = bpy.data.scenes[currSceneIndex]
        if scene.world is not None:
            current_world = scene.world
            bpy.data.worlds.remove(current_world, do_unlink=True)
            empty_trash(self, context)

        # if backstage_collection:
        #     backstage_objects = backstage_collection.objects
        #     for mobj in backstage_objects:
        #         if "Materials." in mobj.name:
        #             sky_color = mobj["Sky"]
        #             print(":::::::::::::::" + str(sky_color[0]) + ":::::::::::::::::::")
        #             if sky_color:
        #                 # col = [(1 - sky_color[i]) for i in range(4)]
        #                 # mobj["Sky"] = col
        #                 mobj["Sky"] = sky_color

                    # bpy.context.scene.frame_set(bpy.context.scene.frame_current)
                    # bpy.context.view_layer.update()
                    # context = bpy.context
                    # scene = context.scene
                    # frame_current = scene.frame_current

                    # scene.frame_set(frame_current)
                    # context.view_layer.update()

                    # for area in bpy.context.screen.areas:
                    #     if area.type == 'VIEW_3D':
                    #         area.tag_redraw()
                    # bpy.context.view_layer.update()
                    # bpy.context.scene.update()


        # if scene.world is not None:
        #     if scene.world.name != sky_name:


        
        colorSwatch = [(1.0,1.0,1.0,1.0), (0.0,0.0,0.0,1.0), (0.05,0.08,0.11,1.0) ]
        # # 13, 21, 29
        # global previous_sky_color_index
        # if (previous_sky_color_index != 1):
        #     nextColorIndex = previous_sky_color_index + 1
        # else:
        #     nextColorIndex = 0
        # previous_sky_color_index = nextColorIndex 
        # sky_color = colorSwatch[nextColorIndex]
        # if backstage_collection:
        #     backstage_objects = backstage_collection.objects
        #     for mobj in backstage_objects:
        #         if "Materials." in mobj.name:
        #             mobj["Sky"] = sky_color

        bpy.ops.object.select_all(action='DESELECT')
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

        # background_color.outputs[0].default_value = sky_color

        if backstage_collection:
            bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = False
            backstage_objects = backstage_collection.objects
            for mobj in backstage_objects:
                if "Materials." in mobj.name:
                    sky_color = mobj["Sky"]
                    if sky_color:
                        if sky_color == colorSwatch[0]:
                            mobj["Sky"] = colorSwatch[1]

                        if sky_color == colorSwatch[1]:
                            mobj["Sky"] = colorSwatch[0]                     

                        colorDriverRed = background_color.outputs[0].driver_add("default_value")[0] 
                        colorDriverGreen = background_color.outputs[0].driver_add("default_value")[1] 
                        colorDriverBlue = background_color.outputs[0].driver_add("default_value")[2] 

                        colorDriverRed.driver.type = 'SUM'
                        newVar = colorDriverRed.driver.variables.new()
                        newVar.name = "Sky"
                        newVar.type = 'SINGLE_PROP'
                        newVar.targets[0].id = mobj
                        newVar.targets[0].data_path = '["Sky"][0]' 

                        colorDriverGreen.driver.type = 'SUM'
                        newVar = colorDriverGreen.driver.variables.new()
                        newVar.name = "Sky"
                        newVar.type = 'SINGLE_PROP'
                        newVar.targets[0].id = mobj
                        newVar.targets[0].data_path = '["Sky"][1]' 

                        colorDriverBlue.driver.type = 'SUM'
                        newVar = colorDriverBlue.driver.variables.new()
                        newVar.name = "Sky"
                        newVar.type = 'SINGLE_PROP'
                        newVar.targets[0].id = mobj
                        newVar.targets[0].data_path = '["Sky"][2]' 

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

        # bpy.context.scene.eevee.use_gtao = False
        # bpy.context.scene.eevee.use_bloom = False
        # bpy.context.scene.eevee.use_ssr = False
        # bpy.context.scene.eevee.use_taa_reprojection = False
        # bpy.context.scene.eevee.taa_samples = 8
        # bpy.context.scene.eevee.shadow_cube_size = '512'
        # bpy.context.scene.eevee.shadow_cascade_size = '64'
        # bpy.context.scene.eevee.use_soft_shadows = False



        bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = True
        return {'FINISHED'}






class BR_OT_panel_clear_ink_lighting(bpy.types.Operator):
    """Clear all Ink and Toonshading"""
    bl_idname = "wm.spiraloid_3d_comic_clear_all_ink_lighting"
    bl_label ="Clear Ink Toonshade All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.object:
            starting_mode = bpy.context.object.mode
            if "OBJECT" not in starting_mode:
                if "POSE" in starting_mode:
                    selected_bones = bpy.context.selected_pose_bones
                if "EDIT" in starting_mode:
                    selected_elementes = bpy.context.selected
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)   

        lighting_collection = getCurrentLightingCollection(self, context)
        if lighting_collection:
            obs = [o for o in lighting_collection.objects if o.users == 1]
            while obs:
                bpy.data.objects.remove(obs.pop())
            bpy.data.collections.remove(lighting_collection)
            empty_trash(self, context)

        # backstage_collection = getCurrentBackstageCollection()

        export_collection = getCurrentExportCollection(self, context)
        export_objects = export_collection.all_objects

        for obj in export_objects:
            if obj is not None:
                if bpy.context.object:
                    starting_mode = bpy.context.object.mode
                    if "OBJECT" not in starting_mode:
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                        bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(state=True)
            bpy.context.view_layer.objects.active = obj

            is_insensitive = False
            if obj.type == 'MESH' or obj.type == 'CURVE' :
                try:
                    del obj["is_toon_shaded"]
                except:
                    pass 

                if obj.hide_select:
                    obj.hide_select = False
                    is_insensitive = True

                try:
                    drivers_data = obj.animation_data.drivers
                    for dr in drivers_data:  
                        obj.driver_remove(dr.data_path, -1)
                except:
                    pass

                for mod in obj.modifiers:
                    # print("-----------------------------")
                    if 'InkThickness' in mod.name:
                        bpy.ops.object.modifier_remove(modifier=mod.name)
                    if 'WhiteOutline' in mod.name:
                        bpy.ops.object.modifier_remove(modifier=mod.name)
                    if 'BlackOutline' in mod.name:
                        bpy.ops.object.modifier_remove(modifier=mod.name)


                for vgroup in obj.vertex_groups:
                    if 'Ink_Thickness' in vgroup.name:
                        obj.vertex_groups.remove(vgroup)

                if obj.active_material:
                    for i in range(len(obj.material_slots)):
                        bpy.ops.object.material_slot_remove({'object': obj})


            if is_insensitive:
                obj.hide_select = True

        return {'FINISHED'}


class BR_OT_panel_init_ink_lighting(bpy.types.Operator):
    """initialize with Ink and Shade All lighting"""
    bl_idname = "view3d.spiraloid_3d_comic_init_ink_lighting"
    bl_label ="Ink Toonshade Visible"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.object:
            starting_mode = bpy.context.object.mode
            if "OBJECT" not in starting_mode:
                if "POSE" in starting_mode:
                    selected_bones = bpy.context.selected_pose_bones
                if "EDIT" in starting_mode:
                    selected_elementes = bpy.context.selected
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)                

        currSceneIndex = getCurrentSceneIndex()
        sceneNumber = getCurrentPanelNumber(True)
        lighting_group = ""
        export_collection = getCurrentExportCollection(self, context)
        lighting_collection = getCurrentLightingCollection(self, context)
        backstage_collection = getCurrentBackstageCollection()

        if not backstage_collection:
            self.report({'INFO'}, 'No Backstage Collection found, initializng as 3D Comic Panel!')
            BR_OT_panel_init.execute(self, context)
            backstage_collection = getCurrentBackstageCollection()

        if backstage_collection:
            backstage_objects = backstage_collection.objects
            for obj in backstage_objects:
                if "Materials" in obj.name:
                    material_swatch_object = obj
        
        if material_swatch_object:

            # sky_color = (1, 1, 1, 1)
            sky_color = (0, 0, 0, 1)

            # lighting_collection = bpy.data.collections.get(lighting_collection_name)
            # if lighting_collection:
            #     bpy.data.collections.remove(lighting_collection)
            #     empty_trash(self, context)


            # existing_lighting_collection = lighting_collection
            # if existing_lighting_collection:
            #     obs = [o for o in existing_lighting_collection.objects if o.users == 1]
            #     while obs:
            #         bpy.data.objects.remove(obs.pop())
            #     bpy.data.collections.remove(existing_lighting_collection)
            #     empty_trash(self, context)
            #     self.report({'INFO'}, 'Deleted Previous Lighting!')
            # lighting_collection = getCurrentLightingCollection(self, context)

            bpy.ops.object.select_all(action='DESELECT')


            visible_objects = []
            for obj in bpy.context.view_layer.objects:
                if obj.visible_get: 
                    if obj.type == 'MESH' or obj.type == 'CURVE' :
                        material_swatch_object_name = material_swatch_object.name
                        if not "ground" in obj.name and not material_swatch_object_name in obj.name: 
                            visible_objects.append(obj)
                        else:
                            tmp_array = [obj]
                            # outline(self,context,tmp_array, "toon")
            outline(self, context, visible_objects, "toon_ink")

            active_camera = bpy.context.scene.camera
            if active_camera:
                active_camera_name = active_camera.name


            lighting_collection_name =  "Lighting." + str(sceneNumber) 
            lighting_group_name = lighting_collection_name
            keylight_name = "Key." + str(sceneNumber)
            sky_name = "Sky." + str(sceneNumber)

            # if (currSceneIndex > 0):
            #     lighting_collection_name =  "Lighting." + str(sceneNumber) 
            #     lighting_group_name = lighting_collection_name
            #     keylight_name = "Key." + str(sceneNumber)
            #     sky_name = "Sky." + str(sceneNumber)
            # else:
            #     lighting_group_name = "Lighting"
            #     lighting_collection_name =  lighting_group_name
            #     keylight_name = "Key"
            #     sky_name = "Sky"

            scene = bpy.data.scenes[currSceneIndex]
            scene_objects = scene.objects
            for obj in scene_objects:
                if lighting_collection_name in obj.name:
                    lighting_group = obj
                if keylight_name in obj.name:
                    keylight = obj

            # else:

            if not lighting_collection:
                lighting_collection = bpy.data.collections.new(lighting_collection_name)
                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.empty_add(type='SPHERE', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
                lighting_group = bpy.context.active_object
                lighting_group.name = lighting_group_name
                lighting_group.show_in_front = True
                lighting_group.empty_display_size = 0.1
                lighting_collection.objects.link(lighting_group)
                try:
                    export_collection.objects.unlink(lighting_group)
                except:
                    pass

                if export_collection:
                    export_collection.children.link(lighting_collection)
                    bpy.context.scene.collection.children.link(lighting_collection)

                    



            # rim_name = "Rim." + str(sceneNumber)
            # back_name = "Back." + str(sceneNumber)
            # fill_name = "Fill." + str(sceneNumber)
            # bouncelight_name = "Bounce." + str(sceneNumber)


            # bpy.ops.object.select_all(action='DESELECT')
            # for obj in bpy.data.scenes[currSceneIndex].objects:
            #     if lighting_group_name in obj.name: 
            #         existing_lighting_group_name = obj.name
            #         bpy.ops.object.select_all(action='DESELECT')
            #         obj.select = True
            #         for c in obj.children:
            #             c.select = True
            #         bpy.ops.object.delete(use_global=False)
            #         empty_trash(self, context)
            #         self.report({'INFO'}, 'Deleted Previous Lighting!')








            # if currSceneIndex != 0:
            #     lighting_group = bpy.context.active_object
            #     lighting_group.name = lighting_group_name
            # else:
            #     lighting_collection_name =  "Lighting.Main" 
            #     lighting_collection = bpy.data.collections.get(lighting_collection_name)
            #     if lighting_collection:
            #         bpy.data.collections.remove(lighting_collection)
            #         empty_trash(self, context)

            #     lighting_collection = bpy.data.collections.new(lighting_collection_name)
            #     bpy.context.scene.collection.children.link(lighting_collection)


            #     bpy.ops.object.select_all(action='DESELECT')
            #     bpy.ops.object.empty_add(type='SPHERE', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
            #     lighting_group = bpy.context.active_object
            #     lighting_group.name = "Lighting_group"
            #     lighting_group.show_in_front = True
            #     lighting_group.empty_display_size = 0.1

            #     if active_camera:
            #         active_camera.select_set(state=True)
            #         bpy.context.view_layer.objects.active = active_camera
            #         bpy.ops.object.parent_no_inverse_set()


            # lighting_group.show_in_front = True
            # lighting_group.empty_display_size = 0.1

            # if active_camera:
            #     active_camera.select_set(state=True)
            #     bpy.context.view_layer.objects.active = active_camera
            #     bpy.ops.object.parent_no_inverse_set()
            # lighting_collection.objects.link(lighting_group)
            # bpy.context.collection.objects.unlink(lighting_group)

                bpy.ops.object.select_all(action='DESELECT')
                lighting_group.select_set(state=True)

                for obj in bpy.data.scenes[currSceneIndex].objects:
                    if "Camera_aim." in obj.name:
                        if active_camera:
                            active_camera.select_set(state=True)
                            bpy.context.view_layer.objects.active = active_camera
                            bpy.ops.object.parent_no_inverse_set()

                        # lighting_group.select_set(state=True)
                        # bpy.context.view_layer.objects.active = lighting_group
                        # constraint = bpy.ops.object.constraint_add(type='COPY_LOCATION')
                        # bpy.context.object.constraints["Copy Location"].target = bpy.data.objects[obj.name]


                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.light_add(type='SPOT', align='WORLD', location=(5, -5, 10), scale=(1, 1, 1))
                keylight = bpy.context.active_object
                keylight.name = keylight_name
                lighting_group.select_set(state=True)
                bpy.context.view_layer.objects.active = lighting_group
                # bpy.ops.object.parent_no_inverse_set()
                # bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

                keylight.location[0] = 2.5
                keylight.location[1] = -2.5
                keylight.location[2] = 5
                keylight.rotation_euler[0] = -2.61799
                keylight.rotation_euler[1] = -2.61799
                keylight.rotation_euler[2] = -1.5708
                keylight.data.energy = 10000
                keylight.data.color = (1, 1, 1)
                keylight.data.use_contact_shadow = False
                keylight.data.shadow_buffer_clip_start = .1
                keylight.data.spot_size =  2.26893
                keylight.data.shadow_soft_size = 0
                keylight.data.shadow_buffer_bias = 0.001
                keylight.data.use_custom_distance = True
                keylight.data.cutoff_distance = 100


                bpy.context.collection.objects.unlink(keylight) 
                lighting_collection.objects.link(keylight)

                # keylight.rotation_euler[0] = -3.5
                # keylight.rotation_euler[1] = -3.5
                # keylight.rotation_euler[2] = 3.5



                # Sun settings
                # keylight.rotation_euler[0] = -3.31613
                # keylight.rotation_euler[1] = -3.83972
                # keylight.rotation_euler[2] = 4.18879
                # keylight.data.energy = 1
                # keylight.data.color = (1, 1, 1)
                # keylight.data.use_contact_shadow = False
                # keylight.data.contact_shadow_distance = 10
                # keylight.data.shadow_buffer_bias = 0.001
                # keylight.data.contact_shadow_bias = 0.001
                # keylight.data.angle = 0



                # bpy.context.collection.objects.unlink(lighting_group) 
                # lighting_collection.objects.link(lighting_group)

                # lighting_collection.objects.link(lighting_group)
                # bpy.context.collection.objects.unlink(lighting_group) 

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

                # if active_camera:
                #     active_camera.select_set(state=True)
                # else:
                #     lighting_group.rotation_euler[1] = 0
                #     lighting_group.rotation_euler[0] = 1.36136
                #     lighting_group.rotation_euler[2] = 0.331613
            
            try:
                bpy.context.scene.collection.children.unlink(lighting_collection)
            except:
                pass

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

            background_color.outputs[0].default_value = sky_color


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

            bpy.context.scene.eevee.use_gtao = False
            bpy.context.scene.eevee.use_bloom = False
            bpy.context.scene.eevee.use_ssr = False
            bpy.context.scene.eevee.use_taa_reprojection = False
            bpy.context.scene.eevee.taa_samples = 8
            # bpy.context.scene.eevee.shadow_cube_size = '512'
            bpy.context.scene.eevee.shadow_cube_size = '4096'
            bpy.context.scene.eevee.shadow_cascade_size = '64'
            bpy.context.scene.eevee.use_soft_shadows = False


            bpy.ops.object.select_all(action='DESELECT')
            keylight.select_set(state=True)
            bpy.context.view_layer.objects.active = keylight

            bpy.ops.view3d.snap_cursor_to_center()
            context.scene.tool_settings.transform_pivot_point = 'CURSOR'

            # context.scene.tool_settings.transform_pivot_point = 'CURSOR'
            # bpy.ops.view3d.snap_cursor_to_center()


        return {'FINISHED'}


# class BR_OT_add_ground(bpy.types.Operator):
#     """Add a new ground disc with falloff"""
#     bl_idname = "view3d.spiraloid_3d_comic_add_ground"
#     bl_label ="Add Ground Disc"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#         # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
#         bpy.ops.object.select_all(action='DESELECT')
#         load_resource("ground_disc.blend")
#         selected_objects = bpy.context.selected_objects
#         for ob in selected_objects:
#             ob.hide_select = True

#         return {'FINISHED'}

class BR_OT_add_outline( bpy.types.Operator):
    """create a polygon outline for selected objects."""
    bl_idname = "view3d.spiraloid_3d_comic_ink"
    bl_label = "Ink Selected"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        selected_objects = bpy.context.selected_objects
        for ob in selected_objects:
            try:
                del ob["is_toon_shaded"]
            except:
                pass 
        outline(self,context,selected_objects, "ink")
        return {'FINISHED'}


class BR_OT_add_toonshade(bpy.types.Operator):
    """create a polygon outline for selected objects."""
    bl_idname = "view3d.spiraloid_3d_comic_toonshade"
    bl_label = "Toonshade Selected"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        selected_objects = bpy.context.selected_objects
        for ob in selected_objects:
            try:
                del ob["is_toon_shaded"]
            except:
                pass 
        outline(self,context,selected_objects, "toon")
        return {'FINISHED'}


class BR_OT_add_blackout(bpy.types.Operator):
    """make object material white for selected objects."""
    bl_idname = "view3d.spiraloid_3d_comic_blackout"
    bl_label = "Blackout Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ink_swatch_object = getCurrentMaterialSwatch()
        selected_objects = bpy.context.selected_objects
        if bpy.context.mode == 'OBJECT':
        # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            for mesh_object in selected_objects:
                if mesh_object.type == 'MESH' or mesh_object.type == 'CURVE' :
                    try:
                        del mesh_object["is_toon_shaded"]
                    except:
                        pass 

                    is_insensitive = False
                    if mesh_object.hide_select:
                        mesh_object.hide_select = False
                        is_insensitive = True

                        for mod in mesh_object.modifiers:
                            if 'InkThickness' in mod.name:
                                bpy.ops.object.modifier_remove(modifier=mod.name)
                            if 'WhiteOutline' in mod.name:
                                bpy.ops.object.modifier_remove(modifier=mod.name)
                            if 'BlackOutline' in mod.name:
                                bpy.ops.object.modifier_remove(modifier=mod.name)

                        for vgroup in mesh_object.vertex_groups:
                            if 'Ink_Thickness' in vgroup.name:
                                mesh_object.vertex_groups.remove(vgroup)

                        try:
                            drivers_data = mesh_object.animation_data.drivers
                            for dr in drivers_data:  
                                mesh_object.driver_remove(dr.data_path, -1)
                        except:
                            pass

                    if mesh_object.active_material:
                        mesh_object.active_material.node_tree.nodes.clear()
                        for i in range(len(mesh_object.material_slots)):
                            bpy.ops.object.material_slot_remove({'object': mesh_object})

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

                        shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                        shader.name = "Background"
                        shader.label = "Background"
                        shader.inputs[0].default_value = (0, 0, 0, 1)
                        mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])
                        mat.use_backface_culling = True
                        mat.shadow_method = 'NONE'

                        # Assign it to object
                        if mesh_object.data.materials:
                            mesh_object.data.materials[0] = mat
                        else:
                            mesh_object.data.materials.append(mat)
                        mesh_object["is_toon_shaded"] = 1


                    if is_insensitive:
                        mesh_object.hide_select = True

        if bpy.context.mode == 'EDIT_MESH':
            for mesh_object in selected_objects:
                if mesh_object.type == 'MESH':
                    try:
                        del mesh_object["is_toon_shaded"]
                    except:
                        pass 

                    if ink_swatch_object:
                            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            ink_swatch_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = ink_swatch_object
                            bpy.ops.object.material_slot_copy()
                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = mesh_object
                            for i, mat in reversed(list(enumerate(mesh_object.data.materials))):
                                if "L_BlackShadow." not in mat.name:
                                    # letter.data.materials.pop(index=i)
                                    mesh_object.active_material_index = i
                                    bpy.ops.object.material_slot_remove()
                            mesh_object.active_material_index =  len(mesh_object.data.materials) - 1
                            mesh_object.select_set(state=True)
                            bpy.context.view_layer.objects.active = mesh_object
                            bpy.ops.object.mode_set(mode='EDIT_MESH', toggle=False)  
                            bpy.ops.object.material_slot_assign()


        return {'FINISHED'}


class BR_OT_add_whiteout(bpy.types.Operator):
    """make object material white for selected objects."""
    bl_idname = "view3d.spiraloid_3d_comic_whiteout"
    bl_label = "Whiteout Selected"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        selected_objects = bpy.context.selected_objects
        for mesh_object in selected_objects:
            if mesh_object.type == 'MESH' or mesh_object.type == 'CURVE' :
                hasVertexColor = False

                try:
                    del mesh_object["is_toon_shaded"]
                except:
                    pass 

                is_insensitive = False
                if mesh_object.hide_select:
                    mesh_object.hide_select = False
                    is_insensitive = True

                for mod in mesh_object.modifiers:
                    if 'InkThickness' in mod.name:
                        bpy.ops.object.modifier_remove(modifier=mod.name)
                    if 'WhiteOutline' in mod.name:
                        bpy.ops.object.modifier_remove(modifier=mod.name)
                    if 'BlackOutline' in mod.name:
                        bpy.ops.object.modifier_remove(modifier=mod.name)

                for vgroup in mesh_object.vertex_groups:
                    if 'Ink_Thickness' in vgroup.name:
                        mesh_object.vertex_groups.remove(vgroup)

                try:
                    drivers_data = mesh_object.animation_data.drivers
                    for dr in drivers_data:  
                        mesh_object.driver_remove(dr.data_path, -1)
                except:
                    pass

                if mesh_object.active_material:
                    mesh_object.active_material.node_tree.nodes.clear()
                    for i in range(len(mesh_object.material_slots)):
                        bpy.ops.object.material_slot_remove({'object': mesh_object})

                if mesh_object.active_material is None:
                    if mesh_object.type == 'MESH':
                        if mesh_object.data.vertex_colors:
                            hasVertexColor = True
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

                    shader = mat.node_tree.nodes.new(type='ShaderNodeBackground')
                    shader.name = "Background"
                    shader.label = "Background"
                    shader.inputs[0].default_value = (1, 1, 1, 1)
                    mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])
                    mat.use_backface_culling = True
                    mat.shadow_method = 'NONE'

                    # Assign it to object
                    if mesh_object.data.materials:
                        mesh_object.data.materials[0] = mat
                    else:
                        mesh_object.data.materials.append(mat)

                    mesh_object["is_toon_shaded"] = 1

                    if (hasVertexColor):
                        vertexColorName = mesh_object.data.vertex_colors[0].name
                        colorNode = mat.node_tree.nodes.new('ShaderNodeAttribute')
                        colorNode.attribute_name = vertexColorName
                        mat.node_tree.links.new(shader.inputs[0], colorNode.outputs[0])


                if is_insensitive:
                    mesh_object.hide_select = True




        return {'FINISHED'}



class BR_OT_add_toon_outline(bpy.types.Operator):
    """create a polygon outline for selected objects."""
    bl_idname = "view3d.spiraloid_3d_comic_ink_toonshade"
    bl_label = "Ink and Toonshade Selected"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        selected_objects = bpy.context.selected_objects
        for ob in selected_objects:
            try:
                del ob["is_toon_shaded"]
            except:
                pass 
        outline(self,context,selected_objects, "ink_toon")
        return {'FINISHED'}

class BR_OT_toonfill(bpy.types.Operator):
    """Toonfill obects in scene."""
    bl_idname = "wm.spiraloid_3d_comic_toonfill"
    bl_label = "Toonfill"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        panel_settings = bpy.context.scene.panel_settings
        toonfill_mode = panel_settings.s3dc_toonfill_mode
        toonfill_type = panel_settings.s3dc_toonfill_type
        selected_objects = bpy.context.selected_objects

        currSceneIndex = getCurrentSceneIndex()
        sceneNumber = getCurrentPanelNumber(True)
        lighting_group = ""
        export_collection = getCurrentExportCollection(self, context)
        lighting_collection = getCurrentLightingCollection(self, context)
        backstage_collection = getCurrentBackstageCollection()
        panel_material_swatch = getMaterialSwatch(False)
        ink_swatch_object = getCurrentMaterialSwatch()
        if backstage_collection:
            bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = False

        if bpy.context.mode != 'EDIT_MESH':
            if "Visible" in toonfill_mode:
                if bpy.context.object:
                    starting_mode = bpy.context.object.mode
                    if "OBJECT" not in starting_mode:
                        if "POSE" in starting_mode:
                            selected_bones = bpy.context.selected_pose_bones
                        if "EDIT" in starting_mode:
                            selected_elementes = bpy.context.selected
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)                


                if not backstage_collection:
                    self.report({'INFO'}, 'No Backstage Collection found, initializng as 3D Comic Panel!')
                    BR_OT_panel_init.execute(self, context)
                    backstage_collection = getCurrentBackstageCollection()

                # if backstage_collection:
                #     backstage_objects = backstage_collection.objects
                #     for obj in backstage_objects:
                #         if "Materials" in obj.name:
                #             material_swatch_object = obj
                
                if ink_swatch_object:
                    sky_color = (0, 0, 0, 1)
                    bpy.ops.object.select_all(action='DESELECT')
                    visible_objects = []
                    for obj in bpy.context.view_layer.objects:
                        if obj.visible_get: 
                            if obj.type == 'MESH' or obj.type == 'CURVE' :
                                ink_swatch_object_name = ink_swatch_object.name
                                if not "ground" in obj.name and not ink_swatch_object_name in obj.name: 
                                    visible_objects.append(obj)
                                else:
                                    tmp_array = [obj]
                                    # outline(self,context,tmp_array, "toon")
                    outline(self, context, visible_objects, "toon_ink")
                    active_camera = bpy.context.scene.camera
                    if active_camera:
                        active_camera_name = active_camera.name

                    lighting_collection_name =  "Lighting." + str(sceneNumber) 
                    lighting_group_name = lighting_collection_name
                    keylight_name = "Key." + str(sceneNumber)
                    sky_name = "Sky." + str(sceneNumber)

                    scene = bpy.data.scenes[currSceneIndex]
                    scene_objects = scene.objects
                    for obj in scene_objects:
                        if lighting_collection_name in obj.name:
                            lighting_group = obj
                        if keylight_name in obj.name:
                            keylight = obj

                    if not lighting_collection:
                        lighting_collection = bpy.data.collections.new(lighting_collection_name)
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.ops.object.empty_add(type='SPHERE', align='WORLD', location=(0, 0, 1.52), scale=(1, 1, 1))
                        lighting_group = bpy.context.active_object
                        lighting_group.name = lighting_group_name
                        lighting_group.show_in_front = True
                        lighting_group.empty_display_size = 0.1
                        lighting_collection.objects.link(lighting_group)
                        try:
                            export_collection.objects.unlink(lighting_group)
                        except:
                            pass

                        if export_collection:
                            export_collection.children.link(lighting_collection)
                            bpy.context.scene.collection.children.link(lighting_collection)

                        bpy.ops.object.select_all(action='DESELECT')
                        lighting_group.select_set(state=True)

                        for obj in bpy.data.scenes[currSceneIndex].objects:
                            if "Camera_aim." in obj.name:
                                if active_camera:
                                    active_camera.select_set(state=True)
                                    bpy.context.view_layer.objects.active = active_camera
                                    bpy.ops.object.parent_no_inverse_set()

                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.ops.object.light_add(type='SPOT', align='WORLD', location=(5, -5, 10), scale=(1, 1, 1))
                        keylight = bpy.context.active_object
                        keylight.name = keylight_name
                        lighting_group.select_set(state=True)
                        bpy.context.view_layer.objects.active = lighting_group
                        keylight.location[0] = 2.5
                        keylight.location[1] = -2.5
                        keylight.location[2] = 5
                        keylight.rotation_euler[0] = -2.61799
                        keylight.rotation_euler[1] = -2.61799
                        keylight.rotation_euler[2] = -1.5708
                        keylight.data.energy = 10000
                        keylight.data.color = (1, 1, 1)
                        keylight.data.use_contact_shadow = False
                        keylight.data.shadow_buffer_clip_start = .1
                        keylight.data.spot_size =  2.26893
                        keylight.data.shadow_soft_size = 0
                        keylight.data.shadow_buffer_bias = 0.001
                        keylight.data.use_custom_distance = True
                        keylight.data.cutoff_distance = 100
                        bpy.context.collection.objects.unlink(keylight) 
                        lighting_collection.objects.link(keylight)
                    try:
                        bpy.context.scene.collection.children.unlink(lighting_collection)
                    except:
                        pass


                    # create a new world
                    if scene.world is not None:
                        current_world = scene.world
                        bpy.data.worlds.remove(current_world, do_unlink=True)
                        empty_trash(self, context)

                    colorSwatch = [(1.0,1.0,1.0,1.0), (0.0,0.0,0.0,1.0), (0.05,0.08,0.11,1.0) ]
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

                    # background_color.outputs[0].default_value = sky_color

                    if backstage_collection:
                        bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = False

                    if ink_swatch_object:
                        # backstage_objects = backstage_collection.objects
                        # for mobj in backstage_objects:
                        #     if "Materials." in mobj.name:
                                sky_color = ink_swatch_object["Sky"]
                                if sky_color:
                                    if sky_color == colorSwatch[0]:
                                        ink_swatch_object["Sky"] = colorSwatch[1]

                                    if sky_color == colorSwatch[1]:
                                        ink_swatch_object["Sky"] = colorSwatch[0]                     

                                    colorDriverRed = background_color.outputs[0].driver_add("default_value")[0] 
                                    colorDriverGreen = background_color.outputs[0].driver_add("default_value")[1] 
                                    colorDriverBlue = background_color.outputs[0].driver_add("default_value")[2] 

                                    colorDriverRed.driver.type = 'SUM'
                                    newVar = colorDriverRed.driver.variables.new()
                                    newVar.name = "Sky"
                                    newVar.type = 'SINGLE_PROP'
                                    newVar.targets[0].id = ink_swatch_object
                                    newVar.targets[0].data_path = '["Sky"][0]' 

                                    colorDriverGreen.driver.type = 'SUM'
                                    newVar = colorDriverGreen.driver.variables.new()
                                    newVar.name = "Sky"
                                    newVar.type = 'SINGLE_PROP'
                                    newVar.targets[0].id = ink_swatch_object
                                    newVar.targets[0].data_path = '["Sky"][1]' 

                                    colorDriverBlue.driver.type = 'SUM'
                                    newVar = colorDriverBlue.driver.variables.new()
                                    newVar.name = "Sky"
                                    newVar.type = 'SINGLE_PROP'
                                    newVar.targets[0].id = ink_swatch_object
                                    newVar.targets[0].data_path = '["Sky"][2]' 

                    bpy.context.scene.eevee.use_gtao = False
                    bpy.context.scene.eevee.use_bloom = False
                    bpy.context.scene.eevee.use_ssr = False
                    bpy.context.scene.eevee.use_taa_reprojection = False
                    bpy.context.scene.eevee.taa_samples = 8
                    bpy.context.scene.eevee.shadow_cube_size = '4096'
                    bpy.context.scene.eevee.shadow_cascade_size = '64'
                    bpy.context.scene.eevee.use_soft_shadows = False


                    bpy.ops.object.select_all(action='DESELECT')
                    keylight.select_set(state=True)
                    bpy.context.view_layer.objects.active = keylight

                    bpy.ops.view3d.snap_cursor_to_center()
                    context.scene.tool_settings.transform_pivot_point = 'CURSOR'
            if "Selected" in toonfill_mode:
                if "ink_toon" in toonfill_type:
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    for ob in selected_objects:
                        try:
                            del ob["is_toon_shaded"]
                        except:
                            pass 
                    outline(self,context,selected_objects, "ink_toon")
                if "blackout" in toonfill_type:
                    outline(self,context,selected_objects, "blackout")

        else:
            for mesh_object in selected_objects:
                if mesh_object.type == 'MESH':
                    if ink_swatch_object:
                            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            # ink_swatch_object.select_set(state=True)
                            # bpy.context.view_layer.objects.active = ink_swatch_object
                            # bpy.ops.object.material_slot_copy()
                            # bpy.ops.object.select_all(action='DESELECT')
                            # mesh_object.select_set(state=True)
                            # bpy.context.view_layer.objects.active = mesh_object
                            # for i, mat in reversed(list(enumerate(mesh_object.data.materials))):
                            #     if "L_BlackShadow." not in mat.name and ".TEMPLATE" in mat.name  :
                            #         # letter.data.materials.pop(index=i)
                            #         mesh_object.active_material_index = i
                            #         bpy.ops.object.material_slot_remove()

                            for i, mat in reversed(list(enumerate(ink_swatch_object.data.materials))):
                                if "blackout" in toonfill_type:
                                    if "L_BlackShadow." in mat.name:
                                        fill_mat = mat
                                if "whiteout" in toonfill_type:
                                    if "L_WhiteShadow." in mat.name:
                                        fill_mat = mat
                            
                            
                            bpy.ops.object.material_slot_add()
                            new_material_slot_index =  len(mesh_object.data.materials) -1
                            if fill_mat:
                                mesh_object.data.materials[new_material_slot_index] = fill_mat

                            bpy.ops.object.select_all(action='DESELECT')
                            mesh_object.select_set(state=True)
                            mesh_object.active_material_index =  len(mesh_object.data.materials) - 1
                            bpy.context.view_layer.objects.active = mesh_object
                            bpy.ops.object.mode_set(mode='EDIT', toggle=False)  
                            bpy.ops.object.material_slot_assign()


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


        if backstage_collection:
            bpy.context.view_layer.layer_collection.children[backstage_collection.name].exclude = True
        
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

class BR_MT_export_3d_comic_all(bpy.types.Operator):
    """Print to Audience.  Export all 3D Comic panels and start a local server.  Existing panels will be overwritten"""
    bl_idname = "view3d.spiraloid_export_3d_comic_all"
    bl_label ="Build 3D Comic"
    bl_options = {'REGISTER', 'UNDO'}
    # config: bpy.props.PointerProperty(type=BuildComicSettings)

    # def draw(self, context):
        # bpy.types.Scene.bake_panel_settings = bpy.props.CollectionProperty(type=BakePanelSettings)
        # scene = bpy.data.scene[0]
        # layout = self.layout
        # scene = context.scene
        # build_panel_settings = scene.build_panel_settings

    # def execute(self, context):
    #     if bpy.data.is_dirty:
    #         # self.report({'WARNING'}, "You must save your file first!")
    #         # bpy.context.window_manager.popup_menu(warn_not_saved, title="Warning", icon='ERROR')
    #         self.report({'WARNING'}, "You must save your file first!")
    #     else:
    #         export_panel(self, context,False, True)
    #         # export_letters(self, context,False)



    def execute(self, context):
        file_path = bpy.data.filepath
        file_dir = os.path.dirname(os.path.dirname(file_path)) 
        index_file_path = (os.path.join(file_dir, "index.html"))

        if bpy.data.is_dirty:
            self.report({'WARNING'}, "You must save your file first!")
        else:
            export_panel(self, context,False, True)
            BR_MT_read_3d_comic.execute(self, context)


        return {'FINISHED'}

# class BR_MT_export_3d_comic_letters_all(bpy.types.Operator):
#     """Export all 3D Comic letters and start a local server.  Existing panels will be overwritten"""
#     bl_idname = "view3d.spiraloid_export_3d_comic_letters_all"
#     bl_label ="Export All Letters"
#     bl_options = {'REGISTER', 'UNDO'}
#     # config: bpy.props.PointerProperty(type=BuildComicSettings)

#     def execute(self, context):
#         if bpy.data.is_dirty:
#             # self.report({'WARNING'}, "You must save your file first!")
#             bpy.context.window_manager.popup_menu(warn_not_saved, title="Warning", icon='ERROR')
#         else:
#             export_letters(self, context, False)
#         return {'FINISHED'}



# class BR_MT_export_3d_comic_letters_current(bpy.types.Operator):
#     """Export current scedne 3D Comic letters and start a local server.  Existing letters will be overwritten"""
#     bl_idname = "view3d.spiraloid_export_3d_comic_letters_current"
#     bl_label ="Export Current Letters"
#     bl_options = {'REGISTER', 'UNDO'}
#     # config: bpy.props.PointerProperty(type=BuildComicSettings)

#     def execute(self, context):
#         if bpy.data.is_dirty:
#             # self.report({'WARNING'}, "You must save your file first!")
#             bpy.context.window_manager.popup_menu(warn_not_saved, title="Warning", icon='ERROR')
#         else:
#             export_letters(self, context,True)
#         return {'FINISHED'}

 
class BR_MT_quick_save_export_3d_comic_current(bpy.types.Operator):
    """Export current 3D Comic panel scene and start a local server.  Only Existing panel will be overwritten"""
    bl_idname = "wm.spiraloid_quicks_save_export_3d_comic_current"
    bl_label ="Quick Export Panel"
    bl_options = {'REGISTER', 'UNDO'}
    # config: bpy.props.PointerProperty(type=BuildComicSettings)


    def execute(self, context):
        file_path = bpy.data.filepath
        file_dir = os.path.dirname(os.path.dirname(file_path)) 
        index_file_path = (os.path.join(file_dir, "index.html"))
        if os.path.isfile(index_file_path):
            print (":::::::::::::::::::")
            export_panel(self, context,True, True)
        else:
            # looks like a doesn't exist.  check if we're in a comic dbs.
            if not os.path.exists(file_dir+'\\panels\\'):
                #we're not in a comic dbs, lets make one.
                # self.report({'WARNING'}, "No comic folders found, try making a comic first")
                self.report({'ERROR'}, 'No 3D Comic found next to .blend file!  Try Export 3D Comic first.' + bpy.context.scene.name)
            else:
                #looks like a panel exists, generate the comic folders and files
                # bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath) # why does this break the UI?
                export_panel(self, context,False, True)

        BR_MT_read_3d_comic.execute(self, context)
        return {'FINISHED'}



class BR_MT_explore_3d_comic(bpy.types.Operator):
    """Open 3D Comic Folder"""
    bl_idname = "view3d.spiraloid_explore_3d_comic"
    bl_label ="Open 3D Comic Folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        file_path = bpy.data.filepath
        comic_name = os.path.dirname(file_path) 
        issue_folder = os.path.dirname(comic_name) 
        os.startfile(issue_folder) 
        return {'FINISHED'}


class BR_MT_read_3d_comic(bpy.types.Operator):
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
    #     bake_panel_settings = scene.build_panel_settings


    def execute(self, context):
        global localHostIsRunning
        global active_language_abreviated
        global localComicServerProcess

        # path to the folder
        file_path = bpy.data.filepath
        file_name = bpy.path.display_name_from_filepath(file_path)
        file_ext = '.blend'
        blend_file_dir = file_path.replace(file_name+file_ext, '')
        file_dir = os.path.dirname(os.path.dirname(file_path)) 
        bat_file_path = (os.path.join(file_dir, "Read_Local.bat"))
        index_file_path = (os.path.join(file_dir, "index.html"))
        print (index_file_path)

        if os.path.isfile(index_file_path):
            if not os.path.isfile(bat_file_path):
                bat_file = open(bat_file_path, "w")
                stringFragments = file_dir.split(':')
                drive_letter = stringFragments[0] + ":"
                bat_file.write('@echo off' +'\n')  
                bat_file.write(drive_letter +'\n')  
                bat_file.write('cd ' + file_dir +'\n')  
                bat_file.write('taskkill /IM "python.exe" /F' +'\n')
                bat_file.write('start http://localhost:8000/?lan=' + active_language_abreviated +'&savepoint=0\n')  
                bat_file.write('python -m  http.server ' +'\n')
                bat_file.write('pause' +'\n')
                bat_file.close()

            # subprocess.Popen('explorer '+ file_dir)

            if not localComicServerProcess:
                cmd = bat_file_path
            else:
                cmd = "start http://localhost:8000/?lan=en^&savepoint=0"
            localComicServerProcess = subprocess.Popen(cmd, shell=True)

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


# class ComicSettings(bpy.types.PropertyGroup):
#     language : bpy.props.EnumProperty(
#         name="Language", 
#         description="The currently active language", 
#         items={
#             ("english", "english", "english", 0),
#             ("spanish", "spanish", "spanish", 1),
#             ("japanese", "japanese", "japanese", 2),
#             ("korean", "korean", "korean", 3),
#             ("german", "german", "german", 4),
#             ("french", "french", "french", 5),
#             ("dutch", "dutch", "dutch", 5)
#             },
#         default=0,
#         update = set_active_language,
#     )





def bake_collection_composite():
    if bake_ao_applied and bake_ao and bake_albedo:
        if os.path.exists(file_dir):
            materials_dir = file_dir+"\\Materials\\"
            if os.path.exists(materials_dir):
                assetName = target_object.name
                texName_albedo = (assetName + "_albedo")
                outBakeFileName = (texName_albedo + "_w_ao")
                outRenderFileNamePadded = materials_dir+outBakeFileName+"0001.png"
                outRenderFileName = materials_dir+outBakeFileName+".png"

                if os.path.exists(outRenderFileName):
                    os.remove(outRenderFileName)
                os.rename(outRenderFileNamePadded, outRenderFileName)

                self.report({'INFO'},"Composited texture saved to: " + outRenderFileName )

                texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                try:
                    img = bpy.data.images.load(outRenderFileName)
                    texture.image = img
                    mat.node_tree.links.new(texture.outputs[0], shader.inputs[0])
                except:
                    raise NameError("Cannot load image %s" % path)




class BakePanelSettings(bpy.types.PropertyGroup):
    target_automesh : bpy.props.BoolProperty(name="Automesh", description="Generate a new mesh to recieve textures", default=True)
    target_existing : bpy.props.BoolProperty(name="Existing", description="Use an existing UV mapped mesh to recieve textures", default=True)
    target_duplicate : bpy.props.BoolProperty(name="Duplicate", description="Duplicate objects in collection to recieve textures", default=True)

    bakeSourceCollection : bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Source",         
        description="The collection to bake"
    )


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
            ("target_automesh", "Combined Mesh","Automesh", 0),
            ("target_duplicate","Duplicate Meshes", "Duplicate", 1),
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
    bake_to_pbr : bpy.props.BoolProperty(name="Bake Texture Maps", description="Bake Collection to new mesh with a Principled BSDF shader", default=False)
    bake_albedo : bpy.props.BoolProperty(name="Bake Albedo", description="Bake Collection to mesh with Albedo Texture", default=True)
    bake_normal : bpy.props.BoolProperty(name="Bake Normal", description="Bake Collection to mesh with Normal Texture", default=True)
    bake_metallic : bpy.props.BoolProperty(name="Bake Metallic", description="Bake Collection to mesh with Metallic Texture", default=True)
    bake_roughness : bpy.props.BoolProperty(name="Bake Roughness", description="Bake Collection to mesh with Roughness Texture", default=True)
    bake_emission : bpy.props.BoolProperty(name="Bake Emission", description="Bake Collection to mesh with Emission Texture", default=True)
    bake_opacity : bpy.props.BoolProperty(name="Bake Transparency", description="Bake Collection to mesh with Opacity Texture", default=True)
    bake_ao : bpy.props.BoolProperty(name="Bake AO", description="Bake Collection to mesh with Ambient Occlusion Texture", default=False)
    bake_ao_LoFi : bpy.props.BoolProperty(name="Lowpoly", description="Use target for Ambient Occlusion, otherwise use source meshes (slower).", default=True)
    bake_ao_applied : bpy.props.BoolProperty(name="Apply", description="Composite Ambient Occlusion into Albedo Texture", default=False)
    bake_curvature : bpy.props.BoolProperty(name="Curvature", description="Bake Collection to mesh with Curvature Texture", default=False)
    bake_curvature_applied : bpy.props.BoolProperty(name="Apply", description="Bake Curvature into Albedo Texture", default=False)
    bake_cavity : bpy.props.BoolProperty(name="Cavity*", description="Bake Collection to mesh with Cavity Texture", default=False)
    bake_cavity_applied : bpy.props.BoolProperty(name="Apply", description="Bake Cavity into Albedo Texture", default=False)
    bake_w_decimate : bpy.props.BoolProperty(name="Decimate", description="Bake and Emission Textures", default=True)
    bake_w_decimate_ratio : bpy.props.FloatProperty(name="Decimate Ratio",  description="Amount to decimate target mesh", min=0, max=1, default=0.5 )
    bake_outline : bpy.props.BoolProperty(name="Outline", description="Add ink outline to bake mesh", default=False)
    bake_background : bpy.props.BoolProperty(name="Background", description="Bake all but collection to skyball", default=False)

class BR_OT_save_check(bpy.types.Operator):
    """Merge all meshes in active collection, unwrap and toggle_workmodeing and textures into a new "Export" collection"""
    bl_idname = "wm.spiraloid_save_check_bake_panel"
    bl_label = "Bake Collection..."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):  
        if bpy.data.is_dirty:
            bpy.context.window_manager.popup_menu(warn_not_saved, title="Warning", icon='ERROR')
        else:
            BR_OT_bake_collection.execute(self, context)




class BR_OT_bake_collection(bpy.types.Operator):
    """Merge all meshes in active collection, unwrap and toggle_workmodeing and textures into a new "Export" collection"""
    bl_idname = "wm.spiraloid_bake_collection"
    bl_label = "Bake Collection..."
    bl_options = {'REGISTER', 'UNDO'}
    config: bpy.props.PointerProperty(type=BakePanelSettings)


    def draw(self, context):
        global developer_mode
        # bpy.types.Scene.bake_panel_settings = bpy.props.CollectionProperty(type=BakePanelSettings)
        # scene = bpy.data.scene[0]

        # if bpy.data.is_dirty:
        #     bpy.types.Operator.report({'WARNING'}, "Unsaved changes, save?")

        layout = self.layout
        scene = context.scene
        bake_panel_settings = scene.bake_panel_settings

        strategy_row = layout.row(align=True)

        layout.prop(bake_panel_settings, "bakeSourceCollection" )

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
        layout.prop(bake_panel_settings, "bake_to_pbr")
        pbr_row = layout.row(align=True)
        if bake_panel_settings.bake_to_pbr:
            pbr_row.enabled = True
            pbr_split = layout.split(factor=0.5)
            col_1 = pbr_split.column()
            col_2 = pbr_split.column()
            col_2.prop(bake_panel_settings, "bake_albedo")
            col_2.prop(bake_panel_settings, "bake_normal")
            col_2.prop(bake_panel_settings, "bake_metallic")
            col_2.prop(bake_panel_settings, "bake_roughness")
            col_2.prop(bake_panel_settings, "bake_emission")
            col_2.prop(bake_panel_settings, "bake_opacity")
            layout.separator()
            split = layout.split(factor=0.05)
            col_1 = split.column()
            col_2 = split.column()
            col_3 = split.column()
            col_4 = split.column()
            col_2.prop(bake_panel_settings, "bake_curvature")
            if developer_mode:
                if bake_panel_settings.bake_curvature:
                    col_3.enabled = True
                    col_3.prop(bake_panel_settings, "bake_curvature_applied")

            split = layout.split(factor=0.05)
            col_1 = split.column()
            col_2 = split.column()
            col_3 = split.column()
            col_4 = split.column()
            col_2.prop(bake_panel_settings, "bake_ao")
            if developer_mode:
                if bake_panel_settings.bake_ao:
                    col_3.enabled = True
                    col_3.prop(bake_panel_settings, "bake_ao_applied")
                    col_4.prop(bake_panel_settings, "bake_ao_LoFi")

        if developer_mode:
            normal_cavity_row = layout.row(align=True)
            if bake_panel_settings.bake_normal:
                normal_cavity_row.enabled = True
                normal_cavity_row.prop(bake_panel_settings, "bake_cavity")
                normal_cavity_row.prop(bake_panel_settings, "bake_cavity_applied")
            ao_row = layout.row(align=True)
            if bake_panel_settings.bake_ao:
                ao_row.enabled = True
                ao_row.prop(bake_panel_settings, "bake_ao_applied")
            else:
                ao_row.enabled = False
            layout.separator()
            layout.prop(bake_panel_settings, "bake_outline")
            layout.separator()
            layout.prop(bake_panel_settings, "bake_background")
            layout.separator()


        layout.separator()
        layout.prop(bake_panel_settings, "bake_w_decimate")
        pbr_row = layout.row(align=True)
        if bake_panel_settings.bake_w_decimate:
            pbr_row.enabled = True
            layout.prop(bake_panel_settings, "bake_w_decimate_ratio")
        else :
            pbr_row.enabled = False







    def execute(self, context):  
        settings = context.scene.bake_panel_settings
        if bpy.context.object:
            if "OBJECT" not in bpy.context.object.mode:
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        scene_name = bpy.context.window.scene.name
        currSceneIndex = getCurrentSceneIndex()

        isComicPanel = False
        if "p." in context.scene.name:
            isComicPanel = True
            export_collection = getCurrentExportCollection(self, context)
            if (export_collection):
                export_collection_name = export_collection.name
            else:
                if settings.target_strategy != "target_existing":
                    export_collection_name = "Export"
                    e_collection = bpy.data.collections.new(export_collection_name)
                    bpy.context.scene.collection.children.link(e_collection)  
                    export_collection = bpy.data.collections.get(export_collection_name)

        # panel_number = "0000"
        # panels = []

        # for scene in bpy.data.scenes:
        #     if "p." in scene.name:
        #         panels.append(scene.name)
        # for panel in panels :
        #     for i in range(len(bpy.data.scenes)):
        #         if bpy.data.scenes[currSceneIndex].name == panel:
        #             stringFragments = panel.split('.')
        #             export_collection_name = "Export." + stringFragments[1]
        #             panel_number = stringFragments[1]




        # layer_collection = bpy.context.view_layer.layer_collection

        source_collection = settings.bakeSourceCollection
        source_collection_name = source_collection.name
        scene_collection = bpy.context.view_layer.layer_collection
        bake_collection_name =  (source_collection_name  + "_baked")
        bake_mesh_name = (source_collection_name  + "_baked")

        hasMultires = False



        # if source_collection is None :
        #     selected_objects = bpy.context.selected_objects
        #     if len(selected_objects) > 0:
        #         source_collection = selected_objects[0].users_collection[0]            
        #         source_collection_name = source_collection.name  
        #     else:
        #         # source_collection = scene_collection
        #         collections =  context.view_layer.objects.active.users_collection          
        #         if len(collections) > 2:
        #             self.report({'ERROR'}, 'You must select a collection!')
        #     return {'FINISHED'} 


        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')



        # cleanup previous bake collection 
        if bpy.data.collections.get(bake_collection_name) : 
            old_bake_collection = bpy.data.collections.get(bake_collection_name)
            if isComicPanel:
                bpy.context.view_layer.active_layer_collection = export_collection.children[bake_collection_name]
            bpy.data.collections.remove(old_bake_collection)
            empty_trash(self, context)
            self.report({'INFO'}, 'Deleted Previous Export collection!')


        # manage export collection 
        layer_collection = bpy.context.view_layer.layer_collection
        # source_collection_name = bpy.context.view_layer.active_layer_collection.collection.name
        # source_collection = bpy.data.collections.get(source_collection_name)
        scene_collection = bpy.context.view_layer.layer_collection

        if settings.target_strategy != "target_existing":
                bake_collection = bpy.data.collections.new(bake_collection_name)
                if isComicPanel:
                    export_collection.children.link(bake_collection)
                else:
                    bpy.context.scene.collection.children.link(bake_collection)

        else:
            bake_collection = settings.bakeTargetObject.users_collection[0] 
            bake_collection_name = bake_collection.name 


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
            pixelMargin = 4
        if settings.bakeSize == "size_256":
            width = 256
            height = 256
            pixelMargin = 4
        if  settings.bakeSize == "size_512":
            width = 512
            height = 512
            pixelMargin = 4
        if  settings.bakeSize == "size_1024":
            width = 1024
            height = 1024
            pixelMargin = 4
        if  settings.bakeSize == "size_2048":
            width = 2048
            height = 2048
            pixelMargin = 4
        if  settings.bakeSize == "size_4096":
            width = 4096
            height = 4096
            pixelMargin = 4
        if  settings.bakeSize == "size_8192":
            width = 8192
            height = 8192
            pixelMargin = 4


        bake_to_unlit = settings.bake_to_unlit
        bake_to_pbr = settings.bake_to_pbr
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
        tot = 1
        wm.progress_begin(0,tot)       
        progress_current = 0.0
        process_count =   bake_to_pbr + bake_to_unlit + bake_albedo + bake_normal + bake_roughness + bake_metallic + bake_emission +  bake_opacity + bake_ao + bake_outline + bake_background
        progress_step = tot/process_count
        progress_current += progress_step
        wm.progress_update(progress_current)
        # for i in range(tot):
        #     wm.progress_update(i)

        visible_objects = []
        visible_objects=[ob for ob in bpy.context.scene.objects if ob.visible_get()]


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
                if ob.visible_get() :
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
                if bpy.context.object:
                    if "OBJECT" not in bpy.context.object.mode:
                        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  
                bpy.ops.object.select_all(action='DESELECT')
                tmp_ob.select_set(state=True)
                bpy.context.view_layer.objects.active = tmp_ob
                for mod in [m for m in tmp_ob.modifiers]:
                    bpy.ops.object.modifier_apply( modifier=mod.name)            
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')
                bpy.ops.mesh.select_all(action='TOGGLE')
                bpy.ops.mesh.delete_loose()
                bpy.ops.mesh.dissolve_degenerate()
                bpy.ops.mesh.remove_doubles()
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)


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
            bpy.ops.mesh.remove_doubles()
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
                target_object = bpy.context.selected_objects[0]
                automap(bpy.context.selected_objects, ratio)
                bpy.ops.object.select_all(action='DESELECT')
                target_object.select_set(state=True)
                bpy.context.view_layer.objects.active = target_object
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
                    bpy.ops.object.modifier_add(type='REMESH')
                    bpy.context.object.modifiers["Remesh"].voxel_size = 0.007
                    bpy.context.object.modifiers["Remesh"].adaptivity = 0.015
                    bpy.context.object.modifiers["Remesh"].use_smooth_shade = True

                    bpy.ops.object.modifier_add(type='DECIMATE')
                    bpy.context.object.modifiers["Decimate"].decimate_type = 'DISSOLVE'
                    bpy.context.object.modifiers["Decimate"].angle_limit = 0.0523599
                    bpy.context.object.modifiers["Decimate"].delimit = {'UV'}
                    bpy.ops.object.modifier_apply( modifier="Decimate")

                    bpy.ops.object.modifier_add(type='TRIANGULATE')
                    bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
                    bpy.context.object.modifiers["Triangulate"].quad_method = 'FIXED'
                    bpy.ops.object.modifier_apply( modifier="Triangulate")

                    bpy.ops.object.modifier_add(type='DECIMATE')
                    print (ratio)
                    bpy.context.object.modifiers["Decimate"].ratio = ratio
                    bpy.ops.object.modifier_apply( modifier="Decimate")

                    for mod in [m for m in bm.modifiers]:
                        bpy.ops.object.modifier_apply( modifier=mod.name)  

                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')
                    bpy.ops.mesh.select_all(action='TOGGLE')
                    bpy.ops.mesh.delete_loose()
                    bpy.ops.mesh.dissolve_degenerate()
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

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

                if isComicPanel:
                    bpy.context.view_layer.layer_collection.children[export_collection_name].exclude = False
                bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = False
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[source_collection_name]

            progress_current += progress_step
            wm.progress_update(progress_current)

        if bake_to_pbr:
            if bake_albedo or bake_normal or bake_roughness or bake_metallic or bake_emission or bake_opacity or bake_ao or bake_curvature:
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
                        #         bpy.ops.object.modifier_apply( modifier="Decimate")

                        #         bpy.ops.object.modifier_add(type='TRIANGULATE')
                        #         bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
                        #         bpy.context.object.modifiers["Triangulate"].quad_method = 'FIXED'
                        #         bpy.ops.object.modifier_apply( modifier="Triangulate")

                        #         bpy.ops.object.modifier_add(type='DECIMATE')
                        #         bpy.context.object.modifiers["Decimate"].ratio = ratio
                        #         bpy.ops.object.modifier_apply( modifier="Decimate")

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

                        blend_filename = os.path.basename(bpy.data.filepath)
                        stringFragments = blend_filename.split('_v')
                        if stringFragments[0]:
                            assetName = stringFragments[0] + "_" + target_object.name
                        else:
                            assetName = target_object.name
                        matName = (assetName + "Mat")
                        mat = bpy.data.materials.new(name=matName)
                        
                        mat.use_nodes = True
                        texName_albedo = (assetName + "_albedo")
                        texName_roughness = (assetName + "_roughness")
                        texName_metal = (assetName + "_metallic")
                        texName_emission = (assetName + "_emission")
                        texName_opacity = (assetName + "_opacity")
                        texName_normal = (assetName + "_normal") 
                        texName_ao = (assetName + "_ao") 
                        texName_curvature = (assetName + "_curvature")
                        # texName_orm = (assetName + "_orm")

                        mat.node_tree.nodes.clear()
                        # bpy.ops.object.shade_smooth()
                        mat_output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                        shader = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
                        shader.inputs[0].default_value = (1, 1, 1, 1)
                        mat.node_tree.links.new(shader.outputs[0], mat_output.inputs[0])

                        albedo_texture = ""
                        ao_texture = ""
                        curvature_texture = ""

                        if bake_albedo:
                            albedo_texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            albedo_texture.image = bpy.data.images.new(texName_albedo,  width=width, height=height)
                            mat.node_tree.links.new(albedo_texture.outputs[0], shader.inputs[0])


                        if bake_ao:
                            ao_texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            ao_texture.image = bpy.data.images.new(texName_ao,  width=width, height=height)
                            mat.node_tree.links.new(ao_texture.outputs[0], shader.inputs[0])

                            if bake_albedo and not bake_curvature and not bake_ao_applied:
                                albedo_mixer = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
                                mat.node_tree.links.new(albedo_mixer.outputs[0], shader.inputs[0])
                                mat.node_tree.links.new(albedo_texture.outputs[0], albedo_mixer.inputs[1])
                                mat.node_tree.links.new(ao_texture.outputs[0], albedo_mixer.inputs[2])
                                albedo_mixer.blend_type = 'OVERLAY'
                                albedo_mixer.inputs[0].default_value = 0.5

                        if bake_roughness:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_roughness,  width=width, height=height)
                            mat.node_tree.links.new(texture.outputs[0], shader.inputs[7])

                        if bake_metallic:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_metal,  width=width, height=height)
                            mat.node_tree.links.new(texture.outputs[0], shader.inputs[4])

                        if bake_curvature:
                            curvature_texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            curvature_texture.image = bpy.data.images.new(texName_curvature,  width=width, height=height)
                            mat.node_tree.links.new(curvature_texture.outputs[0], shader.inputs[0])

                            if bake_albedo and not bake_ao and not bake_curvature_applied:
                                albedo_mixer = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
                                mat.node_tree.links.new(albedo_mixer.outputs[0], shader.inputs[0])
                                mat.node_tree.links.new(albedo_texture.outputs[0], albedo_mixer.inputs[1])
                                mat.node_tree.links.new(curvature_texture.outputs[0], albedo_mixer.inputs[2])
                                albedo_mixer.blend_type = 'OVERLAY'
                                albedo_mixer.inputs[0].default_value = 0.5

                        if bake_curvature and not bake_ao_applied and not bake_curvature_applied:
                                albedo_mixer = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
                                if bake_albedo:
                                    albedo_color_input = albedo_texture
                                    mat.node_tree.links.new(albedo_color_input.outputs[0], albedo_mixer.inputs[1])
                                else:
                                    existing_albedo_color = shader.inputs[0].default_value
                                    albedo_mixer.inputs[1].default_value = existing_albedo_color

                                curvature_ao_mixer = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
                                mat.node_tree.links.new(curvature_ao_mixer.outputs[0], shader.inputs[0])
                                mat.node_tree.links.new(ao_texture.outputs[0], curvature_ao_mixer.inputs[1])
                                mat.node_tree.links.new(curvature_texture.outputs[0], curvature_ao_mixer.inputs[2])
                                curvature_ao_mixer.blend_type = 'MULTIPLY'
                                curvature_ao_mixer.inputs[0].default_value = 0.5
                                mat.node_tree.links.new(albedo_mixer.outputs[0], shader.inputs[0])

                                mat.node_tree.links.new(curvature_ao_mixer.outputs[0], albedo_mixer.inputs[2])
                                albedo_mixer.blend_type = 'OVERLAY'
                                albedo_mixer.inputs[0].default_value = 0.5


                        if bake_emission:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_emission,  width=width, height=height)
                            mat.node_tree.links.new(texture.outputs[0], shader.inputs[17])

                        if bake_opacity:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_opacity,  width=width, height=height)
                            mat.node_tree.links.new(texture.outputs[0], shader.inputs[19])
                            mat.blend_method = 'BLEND'


                        if bake_normal:
                            texture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                            texture.image = bpy.data.images.new(texName_normal, width=width, height=height)
                            texture.image.colorspace_settings.name = 'Non-Color'
                            bump = mat.node_tree.nodes.new(type='ShaderNodeNormalMap')
                            mat.node_tree.links.new(texture.outputs[0], bump.inputs[1])
                            mat.node_tree.links.new(bump.outputs[0], shader.inputs[20])
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

                        tmp_flat_shader = ""
                        mat_output = ""
                        existing_mat_output_connection = ""
                        geometry_node = ""
                        curvature_colorramp = ""
                        ao_node = ""
                        
                        # for n in imgnodes:
                        #     if n.image.name == texName_ao:
                        #         n.select = True
                        #         matnodes.active = n
                        #         bpy.context.scene.cycles.bake_type = 'AO'
                        #         bpy.context.scene.render.image_settings.file_format = 'PNG'
                        #         bpy.context.scene.render.image_settings.color_depth = '8'
                        #         bpy.context.scene.render.image_settings.color_mode = 'BW'
                        #         if bake_ao_LoFi :
                        #             bpy.context.scene.render.bake.use_selected_to_active = False
                        #             bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = True
                        #         else :
                        #             bpy.context.scene.render.bake.use_selected_to_active = True
                        #             bpy.context.scene.render.bake.use_cage = True
                        #             ray_length = target_object.dimensions[1] * bake_distance
                        #             bpy.context.scene.render.bake.cage_extrusion = ray_length
                        #         bpy.context.scene.cycles.samples = 128
                        #         bpy.context.scene.render.bake.margin = pixelMargin
                        #         if os.path.exists(file_dir):
                        #             if os.path.exists(materials_dir):
                        #                 outBakeFileName = n.image.name+".png"
                        #                 outRenderFileName = materials_dir+outBakeFileName
                        #                 n.image.file_format = 'PNG'
                        #                 n.image.filepath = outRenderFileName
                        #                 bpy.ops.object.bake(type='AO', filepath=outRenderFileName, save_mode='EXTERNAL')
                        #                 n.image.save()
                        #                 self.report({'INFO'},"Ambient Oclusion texture saved to: " + outRenderFileName )
                        #         else:
                        #             bpy.ops.object.bake(type='AO')
                        #             n.image.pack()
                        #         bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = False
                        #         progress_current += progress_step
                        #         wm.progress_update(int(progress_current))


                        for n in imgnodes:
                            if n.image.name == texName_ao:
                                n.select = True
                                matnodes.active = n
                                existing_albedo_color = (0, 0, 0, 1)
                                existing_metal_color = (0, 0, 0, 1)

                                bpy.context.scene.cycles.bake_type = 'EMIT'  #('COMBINED', 'AO', 'SHADOW', 'NORMAL', 'UV', 'ROUGHNESS', 'EMIT', 'ENVIRONMENT', 'DIFFUSE', 'GLOSSY', 'TRANSMISSION')
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'BW'
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_direct = False
                                bpy.context.scene.render.bake.use_selected_to_active = True
                                bpy.context.scene.render.bake.use_cage = True
                                ray_length = target_object.dimensions[1] * bake_distance
                                bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 8
                                bpy.context.scene.render.bake.margin = pixelMargin

                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            mat_output = src_mat.node_tree.nodes.get('Material Output')
                                            existing_mat_output_connection = mat_output.inputs[0].links[0].from_node
                                            tmp_flat_shader = src_mat.node_tree.nodes.new(type='ShaderNodeBackground')
                                            ao_node = src_mat.node_tree.nodes.new(type='ShaderNodeAmbientOcclusion')
                                            ao_node.inputs[1].default_value = 60
                                            ao_node.samples = 64

                                            src_mat.node_tree.links.new(tmp_flat_shader.outputs[0], mat_output.inputs[0])
                                            src_mat.node_tree.links.new(ao_node.outputs[0], tmp_flat_shader.inputs[0])

                                    tmp_src.select_set(state=True)

                                temp_stored_selection = bpy.context.selected_objects

                                bpy.ops.object.select_all(action='DESELECT')
                                bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(50, 50, 25))
                                ao_cube = bpy.context.selected_objects[0]
                                ao_cube_mat = bpy.data.materials.new(name="aoMatName")
                                ao_cube_mat.use_nodes = True
                                ao_cube.data.materials.append(ao_cube_mat)
                                ao_mat_output = ao_cube_mat.node_tree.nodes.get('Material Output')

                                ao_nodes = ao_cube_mat.node_tree.nodes
                                for node in ao_nodes:
                                    if node.type != 'OUTPUT_MATERIAL': # skip the material output node as we'll need it later
                                        ao_nodes.remove(node) 

                                tmp_black_shader = ao_cube_mat.node_tree.nodes.new(type='ShaderNodeBackground')
                                tmp_black_shader.inputs[0].default_value = (0, 0, 0, 1)
                                ao_cube_mat.node_tree.links.new(tmp_black_shader.outputs[0], ao_mat_output.inputs[0])


                                # delete top and bottom face
                                bm = bmesh.new()
                                bm.from_mesh( ao_cube.data )
                                bm.faces.ensure_lookup_table()
                                faces = [f for f in bm.faces if GoingUp( f.normal )]
                                bmesh.ops.delete( bm, geom = faces, context = 'FACES_ONLY' )
                                faces = [f for f in bm.faces if GoingDown( f.normal )]
                                bm.to_mesh( ao_cube.data )

                                # warp cube to tune ground and toplight
                                # m_taper = bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
                                m_taper = ao_cube.modifiers.new(name="SIMPLE_DEFORM", type='SIMPLE_DEFORM')
                                m_taper.deform_method = 'TAPER'
                                m_taper.deform_axis = 'Z'
                                m_taper.factor = -1.7
                                # m_stretcher = bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
                                m_stretcher = ao_cube.modifiers.new(name="SIMPLE_DEFORM", type='SIMPLE_DEFORM')
                                m_stretcher.deform_method = 'STRETCH'
                                m_stretcher.deform_axis = 'Z'
                                m_stretcher.factor = -0.55

                                # raise KeyboardInterrupt()


                                for mod in [m for m in ao_cube.modifiers]:
                                    bpy.ops.object.modifier_apply( modifier=mod.name)   


                                bpy.ops.object.select_all(action='DESELECT')
                                for o in temp_stored_selection:
                                    o.select_set(state=True)
                                target_object.select_set(state=True)
                                bpy.context.view_layer.objects.active = target_object

                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='EMIT', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked ao texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='EMIT')
                                    n.image.pack()

                                # raise KeyboardInterrupt()



                                # cleanup
                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            src_mat.node_tree.links.new(existing_mat_output_connection.outputs[0], mat_output.inputs[0])
                                            src_mat.node_tree.nodes.remove(tmp_flat_shader)
                                            src_mat.node_tree.nodes.remove(ao_node)
                                bpy.ops.object.select_all(action='DESELECT')
                                ao_cube.select_set(state=True)
                                bpy.context.view_layer.objects.active = ao_cube
                                bpy.ops.object.delete(use_global=False)
                                if isComicPanel:
                                    bpy.context.view_layer.layer_collection.children[export_collection_name].exclude = False


                                # reselect objects
                                target_object.select_set(state=True)
                                bpy.ops.object.select_all(action='DESELECT')
                                for o in temp_stored_selection:
                                    o.select_set(state=True)
                                target_object.select_set(state=True)
                                bpy.context.view_layer.objects.active = target_object
                                            

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
                                    treeF(albedo_image_node.outputs['Image'], mix_node.inputs[2])


                                    # bpy.context.scene.node_tree.links.new(mix_node.outputs[0], viewer_node.inputs[0])

                                    # baked_ao_image = bpy.data.images.new(texName_albedo + "_w_ao",  width=width, height=height)


                                    output_node.base_path =  materials_dir
                                    output_node.file_slots[0].path = outBakeFileName
                                    output_node.format.file_format = 'PNG'
                                    output_node.format.color_mode = 'RGB'

                                    tree.links.new(mix_node.outputs[0], output_node.inputs[0])
                                    tree.links.new(mix_node.outputs[0], comp_node.inputs[0])

                                    bpy.context.scene.render.use_file_extension = True
                                    bpy.context.scene.render.use_compositing = True
                                    
                                    bpy.ops.render.render(animation=False, write_still=True)

                                    # bpy.app.handlers.render_complete(bake_collection_composite)

                                    outRenderFileNamePadded = materials_dir+outBakeFileName+"0001.png"
                                    outRenderFileName = materials_dir+outBakeFileName+".png"
                                    if os.path.exists(outRenderFileName):
                                        os.remove(outRenderFileName)
                                    os.rename(outRenderFileNamePadded, outRenderFileName)

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
                                existing_albedo_color = (0, 0, 0, 1)

                                bpy.context.scene.cycles.bake_type = 'COMBINED'  #('COMBINED', 'AO', 'SHADOW', 'NORMAL', 'UV', 'ROUGHNESS', 'EMIT', 'ENVIRONMENT', 'DIFFUSE', 'GLOSSY', 'TRANSMISSION')
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
                                bpy.context.scene.cycles.samples = 1
                                bpy.context.scene.render.bake.margin = pixelMargin

                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            mat_output = src_mat.node_tree.nodes.get('Material Output')
                                            existing_mat_output_connection = mat_output.inputs[0].links[0].from_node
                                            shandernode = src_mat.node_tree.nodes.get("Principled BSDF")
                                            if shandernode:
                                                tmp_flat_shader = src_mat.node_tree.nodes.new(type='ShaderNodeBackground')
                                                src_mat.node_tree.links.new(tmp_flat_shader.outputs[0], mat_output.inputs[0])
                                                if not shandernode.inputs[0].links:
                                                    existing_metal_color = shandernode.inputs[0].default_value
                                                    tmp_flat_shader.inputs[0].default_value = existing_metal_color
                                                else:
                                                    existing_metal_color_input = shandernode.inputs[0].links[0].from_node
                                                    src_mat.node_tree.links.new(existing_metal_color_input.outputs[0], tmp_flat_shader.inputs[0])
                                    tmp_src.select_set(state=True)

                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='COMBINED', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked albedo texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='COMBINED')
                                    n.image.pack()

                                # cleanup
                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            src_mat.node_tree.links.new(existing_mat_output_connection.outputs[0], mat_output.inputs[0])
                                            src_mat.node_tree.nodes.remove(tmp_flat_shader)




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

                                for tmp_src in source_meshes:
                                    tmp_src.select_set(state=True)

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
                                    bpy.ops.object.modifier_apply( modifier=mod.name)     
                                # for mod in [m for m in target_object.modifiers]:

                                progress_current += progress_step
                                wm.progress_update(int(progress_current))

                        for n in imgnodes:
                            if n.image.name == texName_metal:
                                n.select = True
                                matnodes.active = n
                                existing_albedo_color = (0, 0, 0, 1)
                                existing_metal_color = (0, 0, 0, 1)

                                bpy.context.scene.cycles.bake_type = 'COMBINED'  #('COMBINED', 'AO', 'SHADOW', 'NORMAL', 'UV', 'ROUGHNESS', 'EMIT', 'ENVIRONMENT', 'DIFFUSE', 'GLOSSY', 'TRANSMISSION')
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'BW'
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_direct = False
                                # bpy.context.scene.render.bake.use_pass_color = True
                                bpy.context.scene.render.bake.use_selected_to_active = True
                                bpy.context.scene.render.bake.use_cage = True
                                ray_length = target_object.dimensions[1] * bake_distance
                                bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 1
                                bpy.context.scene.render.bake.margin = pixelMargin

                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            mat_output = src_mat.node_tree.nodes.get('Material Output')
                                            existing_mat_output_connection = mat_output.inputs[0].links[0].from_node
                                            shandernode = src_mat.node_tree.nodes.get("Principled BSDF")
                                            if shandernode:
                                                tmp_flat_shader = src_mat.node_tree.nodes.new(type='ShaderNodeBackground')
                                                src_mat.node_tree.links.new(tmp_flat_shader.outputs[0], mat_output.inputs[0])

                                                if not shandernode.inputs[4].links:
                                                    existing_metal_color = shandernode.inputs[4].default_value
                                                    tmp_flat_shader.inputs[0].default_value = (existing_metal_color, existing_metal_color, existing_metal_color, 1)
                                                else:
                                                    existing_metal_color_input = shandernode.inputs[4].links[0].from_node
                                                    src_mat.node_tree.links.new(existing_metal_color_input.outputs[0], tmp_flat_shader.inputs[0])
                                    tmp_src.select_set(state=True)

                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='COMBINED', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked metal texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='COMBINED')
                                    n.image.pack()

                                # raise KeyboardInterrupt()

                                # cleanup
                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            src_mat.node_tree.links.new(existing_mat_output_connection.outputs[0], mat_output.inputs[0])
                                            src_mat.node_tree.nodes.remove(tmp_flat_shader)

                        for n in imgnodes:
                            if n.image.name == texName_curvature:
                                n.select = True
                                matnodes.active = n
                                existing_albedo_color = (0, 0, 0, 1)
                                existing_metal_color = (0, 0, 0, 1)

                                bpy.context.scene.cycles.bake_type = 'EMIT'  #('COMBINED', 'AO', 'SHADOW', 'NORMAL', 'UV', 'ROUGHNESS', 'EMIT', 'ENVIRONMENT', 'DIFFUSE', 'GLOSSY', 'TRANSMISSION')
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'BW'
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_direct = False
                                # bpy.context.scene.render.bake.use_pass_color = True
                                bpy.context.scene.render.bake.use_selected_to_active = True
                                bpy.context.scene.render.bake.use_cage = True
                                ray_length = target_object.dimensions[1] * bake_distance
                                bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 1
                                bpy.context.scene.render.bake.margin = pixelMargin

                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            mat_output = src_mat.node_tree.nodes.get('Material Output')
                                            existing_mat_output_connection = mat_output.inputs[0].links[0].from_node

                                            tmp_flat_shader = src_mat.node_tree.nodes.new(type='ShaderNodeBackground')
                                            geometry_node = src_mat.node_tree.nodes.new(type='ShaderNodeNewGeometry')
                                            curvature_colorramp = src_mat.node_tree.nodes.new(type='ShaderNodeValToRGB')
                                            src_mat.node_tree.links.new(tmp_flat_shader.outputs[0], mat_output.inputs[0])
                                            curvature_colorramp.color_ramp.elements[1].position = 0.6
                                            curvature_colorramp.color_ramp.elements[0].position = 0.45
                                            curvature_colorramp.color_ramp.interpolation = 'EASE'


                                            src_mat.node_tree.links.new(geometry_node.outputs[7], curvature_colorramp.inputs[0])
                                            src_mat.node_tree.links.new(curvature_colorramp.outputs[0], tmp_flat_shader.inputs[0])

                                    tmp_src.select_set(state=True)


                                # raise KeyboardInterrupt()

                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='EMIT', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked curvature texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='EMIT')
                                    n.image.pack()

                                # cleanup
                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            src_mat.node_tree.links.new(existing_mat_output_connection.outputs[0], mat_output.inputs[0])
                                            src_mat.node_tree.nodes.remove(tmp_flat_shader)
                                            src_mat.node_tree.nodes.remove(geometry_node)
                                            src_mat.node_tree.nodes.remove(curvature_colorramp)



                        for n in imgnodes:
                            if n.image.name == texName_roughness:
                                n.select = True
                                matnodes.active = n
                                existing_albedo_color = (0, 0, 0, 1)
                                existing_roughness_color = (0, 0, 0, 1)

                                bpy.context.scene.cycles.bake_type = 'COMBINED'  #('COMBINED', 'AO', 'SHADOW', 'NORMAL', 'UV', 'ROUGHNESS', 'EMIT', 'ENVIRONMENT', 'DIFFUSE', 'GLOSSY', 'TRANSMISSION')
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'BW'
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_direct = False
                                # bpy.context.scene.render.bake.use_pass_color = True
                                bpy.context.scene.render.bake.use_selected_to_active = True
                                bpy.context.scene.render.bake.use_cage = True
                                ray_length = target_object.dimensions[1] * bake_distance
                                bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 1
                                bpy.context.scene.render.bake.margin = pixelMargin

                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            mat_output = src_mat.node_tree.nodes.get('Material Output')
                                            existing_mat_output_connection = mat_output.inputs[0].links[0].from_node
                                            shandernode = src_mat.node_tree.nodes.get("Principled BSDF")
                                            if shandernode:
                                                tmp_flat_shader = src_mat.node_tree.nodes.new(type='ShaderNodeBackground')
                                                src_mat.node_tree.links.new(tmp_flat_shader.outputs[0], mat_output.inputs[0])

                                                if not shandernode.inputs[7].links:
                                                    existing_roughness_color = shandernode.inputs[7].default_value
                                                    tmp_flat_shader.inputs[0].default_value = (existing_roughness_color, existing_roughness_color, existing_roughness_color, 1)
                                                else:
                                                    existing_roughness_color = shandernode.inputs[7].links[0].from_node
                                                    src_mat.node_tree.links.new(existing_roughness_color.outputs[0], tmp_flat_shader.inputs[0])
                                    tmp_src.select_set(state=True)

                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='COMBINED', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked roughness texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='COMBINED')
                                    n.image.pack()

                                # raise KeyboardInterrupt()


                                # cleanup
                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            src_mat.node_tree.links.new(existing_mat_output_connection.outputs[0], mat_output.inputs[0])
                                            src_mat.node_tree.nodes.remove(tmp_flat_shader)


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



                        for n in imgnodes:
                            if n.image.name == texName_opacity:
                                n.select = True
                                matnodes.active = n
                                existing_albedo_color = (0, 0, 0, 1)
                                existing_opacity_color = (0, 0, 0, 1)

                                bpy.context.scene.cycles.bake_type = 'COMBINED'  #('COMBINED', 'AO', 'SHADOW', 'NORMAL', 'UV', 'ROUGHNESS', 'EMIT', 'ENVIRONMENT', 'DIFFUSE', 'GLOSSY', 'TRANSMISSION')
                                bpy.context.scene.render.image_settings.file_format = 'PNG'
                                bpy.context.scene.render.image_settings.color_depth = '8'
                                bpy.context.scene.render.image_settings.color_mode = 'BW'
                                bpy.context.scene.render.bake.use_pass_indirect = False
                                bpy.context.scene.render.bake.use_pass_direct = False
                                # bpy.context.scene.render.bake.use_pass_color = True
                                bpy.context.scene.render.bake.use_selected_to_active = True
                                bpy.context.scene.render.bake.use_cage = True
                                ray_length = target_object.dimensions[1] * bake_distance
                                bpy.context.scene.render.bake.cage_extrusion = ray_length
                                bpy.context.scene.cycles.samples = 1
                                bpy.context.scene.render.bake.margin = pixelMargin

                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            mat_output = src_mat.node_tree.nodes.get('Material Output')
                                            existing_mat_output_connection = mat_output.inputs[0].links[0].from_node
                                            shandernode = src_mat.node_tree.nodes.get("Principled BSDF")
                                            if shandernode:
                                                tmp_flat_shader = src_mat.node_tree.nodes.new(type='ShaderNodeBackground')
                                                src_mat.node_tree.links.new(tmp_flat_shader.outputs[0], mat_output.inputs[0])

                                                if not shandernode.inputs[19].links:
                                                    existing_opacity_color = shandernode.inputs[19].default_value
                                                    tmp_flat_shader.inputs[0].default_value = (existing_opacity_color, existing_opacity_color, existing_opacity_color, 1)
                                                else:
                                                    existing_opacity_color = shandernode.inputs[19].links[0].from_node
                                                    src_mat.node_tree.links.new(existing_opacity_color.outputs[0], tmp_flat_shader.inputs[0])
                                    tmp_src.select_set(state=True)

                                if os.path.exists(file_dir):
                                    if os.path.exists(materials_dir):
                                        outBakeFileName = n.image.name+".png"
                                        outRenderFileName = materials_dir+outBakeFileName
                                        n.image.file_format = 'PNG'
                                        n.image.filepath = outRenderFileName
                                        bpy.ops.object.bake(type='COMBINED', filepath=outRenderFileName, save_mode='EXTERNAL')
                                        n.image.save()
                                        self.report({'INFO'},"Baked opacity texture saved to: " + outRenderFileName )
                                else:
                                    bpy.ops.object.bake(type='COMBINED')
                                    n.image.pack()

                                # raise KeyboardInterrupt()


                                # cleanup
                                for tmp_src in source_meshes:
                                    if tmp_src.data.materials:
                                        for src_mat in tmp_src.data.materials:
                                            src_mat.node_tree.links.new(existing_mat_output_connection.outputs[0], mat_output.inputs[0])
                                            src_mat.node_tree.nodes.remove(tmp_flat_shader)





        bpy.context.view_layer.layer_collection.children[source_collection_name].exclude = True

        if settings.target_strategy != "target_existing" and isComicPanel:
            bpy.context.view_layer.layer_collection.children[export_collection_name].children[bake_collection_name].exclude = False
        
        # export_collection.children[bake_collection_name].exclude = False
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'


        if bake_outline :
            outline(self,context,bake_meshes, "ink_toon")
            progress_current += progress_step
            wm.progress_update(int(progress_current))



        if bake_background :
            active_camera = bpy.context.scene.camera
            skyball_cam = bpy.context.scene.camera
            skyball_cam_object = bpy.context.selected_objects[0]
            bpy.context.scene.render.engine = 'CYCLES'



            if active_camera is not None :
                camera_collection = active_camera.users_collection[0]
                if isComicPanel:
                    if camera_collection is not export_collection:
                        export_collection.objects.link(active_camera)
                bpy.ops.object.select_all(action='DESELECT')
                active_camera.select_set(state=True)
                bpy.context.view_layer.objects.active = active_camera
            else :
                skyball_cam = bpy.data.cameras.new("MirrorBallCamera")
                skyball_cam_object = bpy.data.objects.new("MirrorBallCamera",skyball_cam)
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

            if isComicPanel:
                bpy.context.view_layer.layer_collection.children[export_collection_name].children[bake_collection_name].exclude = False


            #reset active camera
            bpy.context.scene.camera = active_camera
            bpy.ops.object.select_all(action='DESELECT')
            skyball_cam_object.select_set(state=True)
            bpy.context.view_layer.objects.active = skyball_cam_object
            bpy.ops.object.delete(use_global=False)

            bpy.ops.object.select_all(action='DESELECT')
            load_resource(self, context, "skyball.blend", False)
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

                    bake_collection.objects.link(ob)
                    bpy.context.scene.collection.objects.unlink(ob)



                    

            bpy.ops.object.select_all(action='DESELECT')
            load_resource(self, context, "skyball_warp.blend", False)
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
                    bake_collection.objects.link(ob)
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




class BR_OT_pose_cycle_next(bpy.types.Operator):
    """make first panel scene the active scene"""
    bl_idname = "wm.spiraloid_pose_cycle_next"
    bl_label ="Pose Cycle Next"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        is_armature_selected = False
        objects = bpy.context.selected_objects
        for obj in objects:
            if obj.type == 'ARMATURE':
                is_armature_selected = True
            else:
                for mod in obj.modifiers:
                    if 'Skeleton' in mod.name:
                        is_armature_selected = True
        if is_armature_selected:
            cycle_pose(self, objects, "next")
        return {'FINISHED'}


class BR_OT_pose_cycle_previous(bpy.types.Operator):
    """make first panel scene the active scene"""
    bl_idname = "wm.spiraloid_pose_cycle_previous"
    bl_label ="Pose Cycle Previous"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        is_armature_selected = False
        objects = bpy.context.selected_objects
        for obj in objects:
            if obj.type == 'ARMATURE':
                is_armature_selected = True
            else:
                for mod in obj.modifiers:
                    if 'Skeleton' in mod.name:
                        is_armature_selected = True
        if is_armature_selected:
            cycle_pose(self, objects, "previous")
        return {'FINISHED'}


class BR_OT_add_pose(bpy.types.Operator):
    """Add new pose"""
    bl_idname = "wm.spiraloid_pose_add"
    bl_label ="Add Pose"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        add_full_pose(self)
        return {'FINISHED'}

class BR_OT_subcollection_cycler(bpy.types.Operator):
    """add property to active object to cycle the child objects of the active collection"""
    bl_idname = "wm.spiraloid_subcollection_cycler"
    bl_label ="subcollection cycler"
    bl_options = {'REGISTER', 'UNDO'}



    def execute(self, context):
        backstage_collection = getCurrentBackstageCollection()
        try:
            active_collection = bpy.context.collection
            active_collection_name = active_collection.name
            active_collection_parent_collection = get_parent_collection(active_collection)
            active_collection_parent_collection_name = active_collection_parent_collection.name  
        except:
            pass 

        try:
            control_object = bpy.context.selected_objects[0]
        except:
            if active_collection:
              
                control_object_name = active_collection_name + "_Cycler"
                control_object = bpy.data.objects.new(control_object_name, None)
                control_object["is_cycler"] = 1

                if 'Master Collection' in active_collection_parent_collection_name:
                    scene = bpy.context.scene
                    scene.collection.objects.link(control_object)
                else:
                    bpy.data.collections[active_collection_parent_collection_name].objects.link(control_object)

        active_collection_children = active_collection.children
        if len(active_collection_children) == 0:
            collection_objects = active_collection.all_objects
            for obj in collection_objects:
                new_subcollection_name = obj.name 
                new_subcollection =  bpy.data.collections.new(new_subcollection_name)
                active_collection.children.link(new_subcollection)
                bpy.data.collections[new_subcollection_name].objects.link(obj)
                try:
                    bpy.data.collections[active_collection_name].objects.unlink(obj)
                except:
                    pass
                # bpy.context.scene.collection.children.unlink(new_subcollection)

            try:
                bpy.data.collections[active_collection_name].objects.link(control_object)
            except:
                pass




        if control_object and active_collection:
            active_collection_name = active_collection.name 
            control_property = "[\"" + active_collection_name + "\"]"
            control_property_name =  active_collection.name
            active_collection_children = active_collection.children
            collection_count = len(active_collection.children)
            print(collection_count)
            try:
                del control_object[control_property_name]
            except:
                pass 
            control_object[control_property_name] = 1 

            if '_RNA_UI' not in control_object.keys():
                control_object['_RNA_UI'] = {}
                

            control_object['_RNA_UI'][control_property_name]  = { "default": 1,
                                                                    "soft_min": 1,
                                                                    "soft_max": collection_count,
                                                                    "is_overridable_library":0,
                                                                }
                
            count = 1 
            collection_instances = []
            control_object_collection = control_object.users_collection[0]
            
            for col in active_collection_children:
                col_name = col.name + "_inst"
                bpy.ops.object.collection_instance_add(collection=col.name, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
                i_col = bpy.context.selected_objects[0]
                i_col.name = col_name
                collection_instances.append(i_col)
                
                #need to figure out how to exclude nested collections.


                
            count = 1   
            for icol in collection_instances:
                if 'Master Collection' in active_collection_parent_collection_name:
                    scene = bpy.context.scene
                    scene.collection.objects.link(icol)
                else:
                    bpy.data.collections[active_collection_parent_collection_name].objects.link(icol)


                bpy.ops.object.select_all(action='DESELECT')
                icol.select_set(state=True)
                control_object.select_set(state=True)
                bpy.context.view_layer.objects.active = control_object
                bpy.ops.object.parent_set()


                visibilityDriver = icol.driver_add('hide_viewport')
                visibilityDriver.driver.type = 'SCRIPTED'
                newVar = visibilityDriver.driver.variables.new()
                newVar.name = "var"
                newVar.type = 'SINGLE_PROP'
                newVar.targets[0].id = control_object
                newVar.targets[0].data_path = control_property
                visibilityDriver.driver.expression =  ("var != " + str(count))

                # the switcher int can be driven by camera to switcher distance using this logic for LOD
                # 1 if (var <= lod_1_dist) else 2 if (var >= lod_1_dist) else (lod_1_dist - var)

                count += 1


            try:
                bpy.data.collections[active_collection_name].objects.unlink(control_object)                
                active_collection_parent_collection.children.unlink(active_collection)
                if backstage_collection:
                    backstage_collection.children.link(active_collection)



            except:
                pass

        else:
             self.report({'WARNING'}, "You must have an active collection!")
        return {'FINISHED'}


class BR_OT_subcollection_cycler_exportable(bpy.types.Operator):
    """add property to active object to cycle the child objects of the active collection"""
    bl_idname = "wm.spiraloid_subcollection_cycler_exportable"
    bl_label ="subcollection cycler exportable"
    bl_options = {'REGISTER', 'UNDO'}



    def execute(self, context):
        try:
            control_object = bpy.context.selected_objects[0]
        except:
            pass 

        try:
            active_collection = bpy.context.collection
        except:
            pass 

        if control_object and active_collection:
            active_collection_name = active_collection.name 
            control_property = "[\"" + active_collection_name + "\"]"
            control_property_name =  active_collection.name
            active_collection_children = active_collection.children
            collection_count = len(active_collection.children)
            print(collection_count)
            try:
                del control_object[control_property_name]
            except:
                pass 
            control_object[control_property_name] = 1 

            if '_RNA_UI' not in control_object.keys():
                control_object['_RNA_UI'] = {}
                

            control_object['_RNA_UI'][control_property_name]  = { "default": 1,
                                                                    "soft_min": 1,
                                                                    "soft_max": collection_count,
                                                                    "is_overridable_library":0,
                                                                }
                
            count = 1   
            for icol in active_collection_children:
                cobjs = icol.objects
                for obj in cobjs:
                    try:
                        obj.driver_remove('location', 2)
                    except:
                        pass
                    visibilityDriver = obj.driver_add('location', 2)
                    visibilityDriver.driver.type = 'SCRIPTED'
                    newVar = visibilityDriver.driver.variables.new()
                    newVar.name = "var"
                    newVar.type = 'SINGLE_PROP'
                    newVar.targets[0].id = control_object
                    newVar.targets[0].data_path = control_property
                    visibilityDriver.driver.expression = "(var != " + str(count) + ") * (-1000000) "
                count += 1
        else:
             self.report({'WARNING'}, "You must have an active control object and an active collection!")
        return {'FINISHED'}



class BR_OT_overwrite_pose(bpy.types.Operator):
    """Overwrite last cycled pose"""
    bl_idname = "wm.spiraloid_pose_overwrite"
    bl_label ="Overwrite Pose"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        overwrite_full_pose(self)
        return {'FINISHED'}

class BR_OT_remove_pose(bpy.types.Operator):
    """Add new pose"""
    bl_idname = "wm.spiraloid_pose_remove"
    bl_label ="Remove Pose"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        remove_full_pose(self)
        return {'FINISHED'}

class BR_OT_toggle_child_lock(bpy.types.Operator):
    """Toggle if child bones inherit rotation or not"""
    bl_idname = "wm.spiraloid_toggle_child_lock"
    bl_label ="Toggle Child Lock"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global isChildLock
        # if not isChildLock:
        #     self.report({'INFO'}, 'Bone Rotations Locked!')
        # else:
        #     self.report({'INFO'}, 'Bone Rotations Unlocked!')
        obj = bpy.context.object
        selected_bones = bpy.context.selected_pose_bones
        isSymmetryActive = bpy.context.selected_objects[0].pose.use_mirror_x
        # if obj is not None :
        #     if obj.type == 'ARMATURE':
        #         bpy.ops.pose.select_all(action='DESELECT')
        #         for s_bone in selected_bones:
        #             for poseBone in obj.pose.bones:
        #                 if poseBone.parent:
        #                     if s_bone.name in poseBone.parent.name :
        #                         poseBone.bone.select = True
        #                         matrix_final = obj.matrix_world @ poseBone.matrix
        #                         if not isChildLock:
        #                             bpy.ops.wm.context_collection_boolean_set(data_path_iter="selected_pose_bones", data_path_item="bone.use_inherit_rotation", type='DISABLE')
        #                             poseBone.matrix_world = matrix_final
        #                         else:
        #                             bpy.ops.wm.context_collection_boolean_set(data_path_iter="selected_pose_bones", data_path_item="bone.use_inherit_rotation", type='ENABLE')
        #                             poseBone.matrix_world = matrix_final

        if obj is not None :
            if obj.type == 'ARMATURE':
                if selected_bones is None:
                    for poseBone in obj.pose.bones:
                        bpy.ops.pose.select_all(action='DESELECT')
                        poseBone.bone.select = True
                        
                        matrix_final = obj.matrix_world @ poseBone.matrix
                        if not isChildLock:
                            self.report({'INFO'}, 'Bone Rotations Locked!')
                            bpy.ops.wm.context_collection_boolean_set(data_path_iter="selected_pose_bones", data_path_item="bone.use_inherit_rotation", type='DISABLE')
                            poseBone.matrix = matrix_final
                        else:
                            self.report({'INFO'}, 'Bone Rotations Unlocked!')
                            bpy.ops.wm.context_collection_boolean_set(data_path_iter="selected_pose_bones", data_path_item="bone.use_inherit_rotation", type='ENABLE')
                            poseBone.matrix = matrix_final
                else:
                    child_bones = []
                    for SelectedPoseBone in selected_bones:
                        for poseBone in obj.pose.bones:
                            if poseBone.parent ==  SelectedPoseBone:
                                child_bones.append(poseBone)
                    for c in child_bones:
                        bpy.ops.pose.select_all(action='DESELECT')
                        c.bone.select = True
                        # matrix_final = obj.matrix_world @ c.matrix
                        world_final = obj.convert_space(pose_bone=c, 
                                            matrix=c.matrix, 
                                            from_space='POSE', 
                                            to_space='WORLD')
                        if not isChildLock:
                            self.report({'INFO'}, 'Bone Rotations Locked!')
                            bpy.ops.wm.context_collection_boolean_set(data_path_iter="selected_pose_bones", data_path_item="bone.use_inherit_rotation", type='DISABLE')
                            local_matrix = obj.convert_space(pose_bone=c, 
                                            matrix=world_final, 
                                            from_space='WORLD', 
                                            to_space='POSE')
                            c.matrix = local_matrix
                        else:
                            self.report({'INFO'}, 'Bone Rotations Unlocked!')
                            bpy.ops.wm.context_collection_boolean_set(data_path_iter="selected_pose_bones", data_path_item="bone.use_inherit_rotation", type='ENABLE')
                            # c.matrix = matrix_final
                            local_matrix = obj.convert_space(pose_bone=c, 
                                            matrix=world_final, 
                                            from_space='WORLD', 
                                            to_space='POSE')
                            c.matrix = local_matrix

                if selected_bones is not None:
                    bpy.ops.pose.select_all(action='DESELECT')
                    for b in selected_bones:
                        b.bone.select = True


            isChildLock = not isChildLock

        return {'FINISHED'}





class OBJECT_OT_add_inkbot(Operator, AddObjectHelper):
    """Create a new InkBot Object"""
    bl_idname = "mesh.spiraloid_add_inkbot"
    bl_label = "Inkbot"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        load_resource(self, context, "inkbot_mesh.blend", False)
        return {'FINISHED'}



class OBJECT_OT_3d_comic_add_dog(Operator, AddObjectHelper):
    """Create Random Object"""
    bl_idname = "mesh.add_random_dog"
    bl_label = "Dog"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        load_resource(self, context, "robopup.000.blend", True)

        # aim at viewport camera.
        objects = bpy.context.selected_objects
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        for v in bpy.context.window.screen.areas:
            if v.type=='VIEW_3D':
                M = v.spaces[0].region_3d.view_matrix
                view_position = camera_position(M)
        target = bpy.data.objects.new("Empty", None)
        bpy.context.scene.collection.objects.link(target)
        target.location = view_position
        bpy.ops.object.select_all(action='DESELECT')
        objects[0].select_set(state=True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.constraint_add(type='TRACK_TO')
        c = bpy.context.object.constraints["Track To"]
        c.target = bpy.data.objects[target.name]
        c.track_axis = 'TRACK_NEGATIVE_Y'
        c.up_axis = 'UP_Z'
        bpy.ops.object.visual_transform_apply()
        objects[0].constraints.remove(c)
        bpy.context.object.rotation_euler[0] = 0
        bpy.context.object.rotation_euler[1] = 0
        bpy.ops.object.select_all(action='DESELECT')
        target.select_set(state=True)
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.delete() 
        bpy.ops.object.select_all(action='DESELECT')
        objects[0].select_set(state=True)
        bpy.context.view_layer.objects.active = objects[0]

        return {'FINISHED'}





class OBJECT_OT_add_inkbot_puppet(Operator, AddObjectHelper):
    """Create a new InkBot Object"""
    bl_idname = "mesh.spiraloid_add_inkbot_puppet"
    bl_label = "Inkbot Puppet"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        load_resource(self, context, "inkbot_puppet.blend", False)
        return {'FINISHED'}

def camera_position(matrix):
    t= (matrix[0][3],matrix[1][3],matrix[2][3])
    r=((matrix[0][0],matrix[0][1],matrix[0][2]),
        (matrix[1][0],matrix[1][1],matrix[1][2]),
        (matrix[2][0],matrix[2][1],matrix[2][2]))

    rp=((-r[0][0],-r[1][0],-r[2][0]),
        (-r[0][1],-r[1][1],-r[2][1]),
        (-r[0][2],-r[1][2],-r[2][2]))

    output=(rp[0][0]*t[0]+rp[0][1]*t[1]+rp[0][2]*t[2],
            rp[1][0]*t[0]+rp[1][1]*t[1]+rp[1][2]*t[2],
            rp[2][0]*t[0]+rp[2][1]*t[1]+rp[2][2]*t[2])
    return output

class OBJECT_OT_add_inkbot_shuffle(Operator, AddObjectHelper):
    """Create a new InkBot Object"""
    bl_idname = "mesh.spiraloid_add_inkbot_shuffle"
    bl_label = "Inkbot"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        load_resource(self, context, "inkbot.000.blend", True)

        # aim at viewport camera.
        objects = bpy.context.selected_objects
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        for v in bpy.context.window.screen.areas:
            if v.type=='VIEW_3D':
                M = v.spaces[0].region_3d.view_matrix
                view_position = camera_position(M)
        target = bpy.data.objects.new("Empty", None)
        bpy.context.scene.collection.objects.link(target)
        target.location = view_position
        bpy.ops.object.select_all(action='DESELECT')
        objects[0].select_set(state=True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.constraint_add(type='TRACK_TO')
        c = bpy.context.object.constraints["Track To"]
        c.target = bpy.data.objects[target.name]
        c.track_axis = 'TRACK_NEGATIVE_Y'
        c.up_axis = 'UP_Z'
        bpy.ops.object.visual_transform_apply()
        objects[0].constraints.remove(c)
        bpy.context.object.rotation_euler[0] = 0
        bpy.context.object.rotation_euler[1] = 0
        bpy.ops.object.select_all(action='DESELECT')
        target.select_set(state=True)
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.delete() 
        bpy.ops.object.select_all(action='DESELECT')
        objects[0].select_set(state=True)
        bpy.context.view_layer.objects.active = objects[0]

        return {'FINISHED'}


class OBJECT_OT_add_omnibot_shared(Operator, AddObjectHelper):
    """Create a new InkBot Object"""
    bl_idname = "mesh.spiraloid_add_omnibot_shared"
    bl_label = "Omnibot"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        load_shared_resource(self, context, "omnibot.blend", False)

        # # aim at viewport camera.
        # objects = bpy.context.selected_objects
        # bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        # for v in bpy.context.window.screen.areas:
        #     if v.type=='VIEW_3D':
        #         M = v.spaces[0].region_3d.view_matrix
        #         view_position = camera_position(M)
        # target = bpy.data.objects.new("Empty", None)
        # bpy.context.scene.collection.objects.link(target)
        # target.location = view_position
        # bpy.ops.object.select_all(action='DESELECT')
        # objects[0].select_set(state=True)
        # bpy.context.view_layer.objects.active = objects[0]
        # bpy.ops.object.constraint_add(type='TRACK_TO')
        # c = bpy.context.object.constraints["Track To"]
        # c.target = bpy.data.objects[target.name]
        # c.track_axis = 'TRACK_NEGATIVE_Y'
        # c.up_axis = 'UP_Z'
        # bpy.ops.object.visual_transform_apply()
        # objects[0].constraints.remove(c)
        # bpy.context.object.rotation_euler[0] = 0
        # bpy.context.object.rotation_euler[1] = 0
        # bpy.ops.object.select_all(action='DESELECT')
        # target.select_set(state=True)
        # bpy.context.view_layer.objects.active = target
        # bpy.ops.object.delete() 
        # bpy.ops.object.select_all(action='DESELECT')
        # objects[0].select_set(state=True)
        # bpy.context.view_layer.objects.active = objects[0]

        return {'FINISHED'}



class OBJECT_OT_add_bonus(Operator, AddObjectHelper):
    """Add Bonus for Panel"""
    bl_idname = "mesh.spiraloid_add_bonus"
    bl_label = "Bonus"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        numString = getCurrentPanelNumber(False)
        paddedNumString = "%04d" % numString
        bonus_name = "Bonus_" + paddedNumString
        load_resource(self, context, "panel_bonus.blend", False)


        # aim at viewport camera.
        objects = bpy.context.selected_objects
        bonusObject = objects[0]
        bonusObject.name = bonus_name
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        active_camera = bpy.context.scene.camera
        bpy.ops.object.select_all(action='DESELECT')
        bonusObject.select_set(state=True)
        bpy.context.view_layer.objects.active = bonusObject
        bpy.ops.object.constraint_add(type='TRACK_TO')
        c = bpy.context.object.constraints["Track To"]
        c.target = bpy.data.objects[active_camera.name]
        c.track_axis = 'TRACK_NEGATIVE_Y'
        c.up_axis = 'UP_Z'
        bpy.ops.object.select_all(action='DESELECT')
        bonusObject.select_set(state=True)
        bpy.context.view_layer.objects.active = bonusObject

        return {'FINISHED'}

class OBJECT_OT_add_bonus_shared(Operator, AddObjectHelper):
    """Add Bonus for Panel"""
    bl_idname = "mesh.spiraloid_add_bonus_shared"
    bl_label = "Bonus"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        numString = getCurrentPanelNumber(False)
        paddedNumString = "%04d" % numString
        bonus_name = "Bonus_" + paddedNumString
        load_shared_resource(self, context, "panel_bonus.blend", False)


        # aim at viewport camera.
        objects = bpy.context.selected_objects
        bonusObject = objects[0]
        bonusObject.name = bonus_name
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        active_camera = bpy.context.scene.camera
        bpy.ops.object.select_all(action='DESELECT')
        bonusObject.select_set(state=True)
        bpy.context.view_layer.objects.active = bonusObject
        bpy.ops.object.constraint_add(type='TRACK_TO')
        c = bpy.context.object.constraints["Track To"]
        c.target = bpy.data.objects[active_camera.name]
        c.track_axis = 'TRACK_NEGATIVE_Y'
        c.up_axis = 'UP_Z'
        bpy.ops.object.select_all(action='DESELECT')
        bonusObject.select_set(state=True)
        bpy.context.view_layer.objects.active = bonusObject

        return {'FINISHED'}

class OBJECT_OT_add_inksplat(Operator, AddObjectHelper):
    """Create a new inksplat Object"""
    bl_idname = "mesh.spiraloid_add_inksplat"
    bl_label = "Inksplat"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        load_resource(self, context, "inksplat.blend", False)
        return {'FINISHED'}

class OBJECT_OT_add_ground(Operator, AddObjectHelper):
    """Create a new exterior street Object"""
    bl_idname = "mesh.spiraloid_add_ground"
    bl_label = "Ground"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        # export_collection = getCurrentExportCollection(self, context)
        # bpy.context.view_layer.active_layer_collection = export_collection

        # objects = bpy.context.selected_objects
        # if objects:
        #     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # load_resource(self, context, "ground_disc.blend", False)

        # imported_objects = bpy.context.selected_objects
        # if not export_collection:
        #     self.report({'WARNING'}, "Export Collection " + export_collection.name + "was not found in scene, skipping export of" + scene.name)
        # else:
        #     for obj in imported_objects:
        #         bpy.context.collection.objects.unlink(obj) 
        #         export_collection.objects.link(obj)

        load_resource(self, context, "ground_disc.blend", False)
        return {'FINISHED'}




class OBJECT_OT_add_speedlines(Operator, AddObjectHelper):
    """Create a new exterior street Object"""
    bl_idname = "mesh.spiraloid_add_speedlines"
    bl_label = "Speedlines"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        load_resource(self, context, "speedlines.blend", False)
        return {'FINISHED'}

class OBJECT_OT_add_speedlines_radial(Operator, AddObjectHelper):
    """Create a new exterior street Object"""
    bl_idname = "mesh.spiraloid_add_speedlines_radial"
    bl_label = "Speedlines Radial"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        load_resource(self, context, "speedlines_radial.blend", False)
        return {'FINISHED'}

class OBJECT_OT_add_speedlines_ground(Operator, AddObjectHelper):
    """Create a new exterior street Object"""
    bl_idname = "mesh.spiraloid_add_speedlines_ground"
    bl_label = "Speedlines Ground"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        load_resource(self, context, "speedlines_ground.blend", False)
        return {'FINISHED'}


class OBJECT_OT_add_ground_rocks(Operator, AddObjectHelper):
    """Drop rocks on the active object"""
    bl_idname = "mesh.spiraloid_add_ground_rocks"
    bl_label = "Drop Rocks"
    bl_options = {'REGISTER', 'UNDO'}


    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 1


    def execute(self, context):
        active_ground = bpy.context.view_layer.objects.active
        if active_ground:
            load_resource(self, context, "ground_rocks.blend", False)
            active_ground.select_set(state=True)
            bpy.context.view_layer.objects.active = active_ground
            drop_objects(self, context,  False, True)
            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
            bpy.ops.object.join()
            bpy.context.selected_objects[0].name = "Dropped_Rocks"

        return {'FINISHED'}
       
class OBJECT_OT_add_sprite_card(Operator, AddObjectHelper):
    """Create a new animated Sprite Card Object"""
    bl_idname = "mesh.spiraloid_add_sprite_card"
    bl_label = "Sprite Card"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        load_resource(self, context, "sprite_card.blend", False)
        return {'FINISHED'}




class BR_OT_spiraloid_automap(bpy.types.Operator):
    """Automatically UV unwrap selected objects"""
    bl_idname = "wm.spiraloid_automap"
    bl_label = "Automap"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(cls, context):
    #     return True #context.space_data.type == 'VIEW_3D'

    def execute(self, context):
        automap(bpy.context.selected_objects, 1)
        return {'FINISHED'}





class BR_OT_spiraloid_toggle_workmode(bpy.types.Operator):
    """Toggle Workmode"""
    bl_idname = "wm.spiraloid_toggle_workmode"
    bl_label = "Toggle Workmode"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True #context.space_data.type == 'VIEW_3D'

    def execute(self, context):
        toggle_workmode(self, context, False)
        return {'FINISHED'}


class BR_OT_spiraloid_toggle_developer_mode(bpy.types.Operator):
    """Toggle developer mode"""
    bl_idname = "wm.spiraloid_toggle_developer_mode"
    bl_label = "Toggle Developer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global developer_mode
        developer_mode = not developer_mode
        return {'FINISHED'}




#------------------------------------------------------

def populate_coll(scene):
    bpy.app.handlers.scene_update_pre.remove(populate_coll)
    scene.coll.clear()
    for identifier, name, description in enum_items:
        scene.coll.add().name = name

def menu_draw_bake(self, context):
    self.layout.operator("wm.spiraloid_save_check_bake_panel", 
        text="Bake Panel...")
    bpy.ops.object.dialog_operator('INVOKE_DEFAULT')

def menu_draw_view(self, context):
    layout = self.layout
    layout.separator()
    self.layout.operator(BR_OT_spiraloid_toggle_workmode.bl_idname)

class BR_MT_3d_comic_menu(bpy.types.Menu):
    bl_idname = "BR_MT_3d_comic_menu"
    bl_label = "3D Comics"

    def draw(self, context):
        global developer_mode
        layout = self.layout
        layout.operator("wm.spiraloid_new_3d_comic", icon="NODE_COMPOSITING", text="New 3D Comic...")
        layout.separator()
        layout.menu(BR_MT_3d_comic_submenu_panels.bl_idname, icon="VIEW_ORTHO")
        layout.menu(BR_MT_3d_comic_submenu_letters.bl_idname, icon="INFO")
        layout.menu(BR_MT_3d_comic_submenu_assets.bl_idname, icon="FILE_3D")
        layout.menu(BR_MT_3d_comic_submenu_disk_assets.bl_idname, icon='FILE_3D')
        if developer_mode:
            layout.menu(BR_MT_3d_comic_submenu_assets_shared.bl_idname, icon="LINKED")
        layout.menu(BR_MT_3d_comic_submenu_lighting.bl_idname, icon="COLORSET_13_VEC")
        layout.separator()
        layout.menu(BR_MT_3d_comic_submenu_utilities.bl_idname, icon="PREFERENCES")
        layout.separator()
        layout.operator("view3d.spiraloid_export_3d_comic_all", icon="NODE_COMPOSITING")
        if developer_mode:
            layout.operator("wm.spiraloid_quicks_save_export_3d_comic_current", icon="FILE_BLANK")
        layout.operator("wm.spiraloid_quicks_save_export_3d_comic_current", icon="SOLO_ON")
        layout.separator()
        layout.operator("view3d.spiraloid_read_3d_comic", icon="HIDE_OFF")

try:
    ink_swatch_object = getCurrentMaterialSwatch()
except:
    pass


class PanelSettings(PropertyGroup):
    s3dc_toonfill_use_global :  bpy.props.BoolProperty(
                    name='s3dc_toonfill_use_global',
                    default=True,
                    description='Use global materials for toonshading')

    s3dc_toonfill_use_global_ink :  bpy.props.BoolProperty(
                    name='s3dc_toonfill_use_global_ink',
                    default=False,
                    description='Use global ink texture for ink wobble')

    s3dc_dynamic_shadows :  bpy.props.BoolProperty(
                    name='s3dc_dynamic_shadows',
                    default=False,
                    description='Use per frame shadowmaps in browser (warning perf cost)') 

    s3dc_apply_armatures :  bpy.props.BoolProperty(
                    name='s3dc_apply_armatures',
                    default=True,
                    description='Apply Armatures and Shape Keys to all meshes') 


    s3dc_toonfill_mode : bpy.props.EnumProperty(
                    name='s3dc_toonfill_mode',
                    description='How to apply toonfill.',
                    items={
                        ("Visible", "Visible", "Visible", 0),
                        ("Selected", "Selected", "Selected", 1)},
                    default='Visible')

    s3dc_toonfill_type : bpy.props.EnumProperty(
                    name='s3dc_toonfill_type',
                    description='type of toonfill.',
                    items={
                        ("ink_toon", "ink_toon", "ink_toon", 0),
                        ("toon", "toon", "toon", 1),
                        ("ink", "ink", "ink", 2),
                        ("whiteout", "whiteout", "whiteout", 3),
                        ("blackout", "blackout", "blackout", 4)},
                    default='ink_toon')

    s3dc_language : bpy.props.EnumProperty(
                    name="Language", 
                    description="The currently active language", 
                    items={
                        ("english", "english", "english", 0),
                        ("spanish", "spanish", "spanish", 1),
                        ("japanese", "japanese", "japanese", 2),
                        ("korean", "korean", "korean", 3),
                        ("german", "german", "german", 4),
                        ("french", "french", "french", 5),
                        ("dutch", "dutch", "dutch", 5)
                        },
                    default=0,
                    update = set_active_language)

    s3dc_camera_strategy : bpy.props.EnumProperty(
        name="Camera Move", 
        description="Type of camera movement for new panels", 
        items={
            ("camera_random", "Random","Random", 0),
            ("camera_slide_up", "Slide Up","SlideUp", 1),
            ("camera_slide_down","Slide Down", "SlideDown", 2),
            ("camera_truck_in", "Truck In","TruckIn", 3),
            ("camera_truck_out", "Truck Out","TruckOut", 4),
            ("camera_pan_left", "Pan Left","PanLeft", 5),
            ("camera_pan_right", "Pan Right","PanRight", 6),
            ("turntable_cw", "Turntable CW","RandomCw", 7),
            ("turntable_ccw", "Turntable CCW","RandomCCW", 8),
            ("Static", "Static","Static", 9),
            },
        default=0)

    s3dc_wordballoon_anim_strategy : bpy.props.EnumProperty(
        name="Wordballoon Anim Strategy", 
        description="Type of movement for new Letters", 
        items={
            ("random", "Random","Random", 0),
            ("slide_up", "Slide Up","SlideUp", 1),
            ("slide_down","Slide Down", "SlideDown", 2),
            ("truck_in", "Truck In","TruckIn", 3),
            ("truck_out", "Truck Out","TruckOut", 4),
            ("pan_left", "Pan Left","PanLeft", 5),
            ("pan_right", "Pan Right","PanRight", 6),
            ("Static", "Static","Static", 7),
            },
        default=0)

    s3dc_wordballoon_count :  bpy.props.IntProperty(
                    name='s3dc_wordballoon_count',
                    default=1,
                    description='Number of Wordballoons to add')

class BR_MT_3d_comic_panels(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "3D Comic: Scenes"
    bl_idname = "SCENE_PT_3d_comic_panelss"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "3D Comics"

    @classmethod 
    def poll(self, context):
        backstage_collection = getCurrentBackstageCollection()
        return backstage_collection

    def draw(self, context):
        global ink_swatch_object
        layout = self.layout
        scene = context.scene
        ink_swatch_object = getCurrentMaterialSwatch()
        panel_settings = scene.panel_settings

        if ink_swatch_object:
            layout.label(text="Transport:")
            layout.separator()
            row = layout.row()
            row.operator("screen.spiraloid_3d_comic_first_panel", icon="TRIA_UP")
            row.operator("screen.spiraloid_3d_comic_previous_panel", icon="TRIA_LEFT", text="")
            row.operator("screen.spiraloid_3d_comic_next_panel", icon="TRIA_RIGHT", text="")
            row.operator("screen.spiraloid_3d_comic_last_panel", icon="TRIA_DOWN")
            layout.separator()

            row = layout.row()
            row.operator("screen.spiraloid_3d_comic_reorder_scene_earlier", icon="REW", text="Shift Earlier")
            row.operator("screen.spiraloid_3d_comic_reorder_scene_later", icon="FF", text="Shift Later")

            layout.separator()


            layout.operator("wm.spiraloid_new_panel_row", text="New...", icon="FILE_BLANK")
            layout.operator("view3d.spiraloid_3d_comic_clone_panel", text="Duplicate", icon="DUPLICATE")
            layout.operator("view3d.spiraloid_3d_comic_blank_panel", text="Insert Black", icon="COLORSET_16_VEC")
            layout.separator()
            layout.operator("view3d.spiraloid_3d_comic_delete_panel", text="Delete Current", icon="TRASH")


            layout.separator()

        else:
            self.layout.label(text= 'Comic Panel Not Found')



class BR_MT_3d_comic_panel_color(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "3D Comic: Colors"
    bl_idname = "SCENE_PT_3d_comic_panel_color"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "3D Comics"
    # bl_space_type = 'PROPERTIES'
    # bl_context = "scene"
    # config: bpy.props.PointerProperty(type=PanelSettings)

    @classmethod 
    def poll(self, context):
        backstage_collection = getCurrentBackstageCollection()
        return backstage_collection


    def draw(self, context):
        global ink_swatch_object
        layout = self.layout
        scene = context.scene
        ink_swatch_object = getCurrentMaterialSwatch()
        panel_material_swatch = getMaterialSwatch(False)

        panel_settings = scene.panel_settings
        backstage_collection_name = getCurrentBackstageCollectionName()
        if "Backstage.Global" not in backstage_collection_name:
            if ink_swatch_object:
                
                layout.prop(panel_settings, "s3dc_toonfill_use_global", text="Use Global Panel Colors")

                # Create a simple row.
                layout.label(text="Sky:")
                row = layout.row()
                row.prop(ink_swatch_object, '["Sky"]', text="")



                # Create an row where the buttons are aligned to each other.
                # Create two columns, by using a split layout.
                split = layout.split()
                # First column
                col = split.column()
                col.prop(ink_swatch_object, '["ToonWhite"]', text="Toonshade Lit")

                # Second column, aligned
                col = split.column(align=True)
                col.prop(ink_swatch_object, '["ToonBlack"]', text="Toonshade Shadow")


                split = layout.split()
                col = split.column()
                col.prop(ink_swatch_object, '["OutlineNoShadowDark"]', text="Ink Inner")
                col = split.column(align=True)
                col.prop(ink_swatch_object, '["OutlineNoShadowLight"]', text="Ink Outer")

                layout.separator()
                layout.prop(panel_settings, "s3dc_toonfill_use_global_ink", text="Use Global Ink Thickness")
                layout.prop(panel_material_swatch, '["OutlineThickness"]', text="Ink Thickness")
                layout.prop(panel_material_swatch, '["OutlineWobble"]', text="Ink Wobble")
                layout.prop(panel_material_swatch, '["OutlineSmooth"]', text="Ink Smoothness")
                layout.separator()
                        
                layout.label(text="Actions:")
                layout.use_property_split = True
                layout.prop(panel_settings, "s3dc_toonfill_mode", text="Toon Fill Mode")
                layout.prop(panel_settings, "s3dc_toonfill_type", text="Toon Fill Type")

                layout.operator("wm.spiraloid_3d_comic_toonfill", text="Toon Fill")
                layout.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="Clear")
                layout.separator()

            else:
                self.layout.label(text= 'Comic Panel Not Found')

class BR_MT_3d_comic_panel_letters(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "3D Comic: Letters"
    bl_idname = "SCENE_PT_3d_comic_letters"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "3D Comics"

    @classmethod 
    def poll(self, context):
        backstage_collection = getCurrentBackstageCollection()
        return backstage_collection


    def draw(self, context):
        backstage_collection_name = getCurrentBackstageCollectionName()
        if "Backstage.Global" not in backstage_collection_name:
            global ink_swatch_object
            layout = self.layout
            scene = context.scene
            ink_swatch_object = getCurrentMaterialSwatch()
            panel_settings = scene.panel_settings

            if ink_swatch_object:
                layout = self.layout
                layout.use_property_split = True
                layout.prop(panel_settings, "s3dc_language", text="Language")
                layout.separator()

                layout.operator("view3d.spiraloid_3d_comic_add_letter_wordballoon", icon="INFO")
                layout.operator("view3d.spiraloid_3d_comic_add_letter_caption", icon="INFO")
                layout.operator("view3d.spiraloid_3d_comic_add_letter_sfx", icon="INFO")
                layout.operator("view3d.spiraloid_3d_comic_add_letter_border", icon="SNAP_FACE")
                layout.separator()

                if developer_mode:
                    layout.use_property_split = True
                    layout.prop(panel_settings, "s3dc_wordballoon_count", text="Balloon Count")
                    layout.prop(panel_settings, "s3dc_wordballoon_anim_strategy", text="Animation")
                    layout.separator()

            else:
                self.layout.label(text= 'Comic Letters Not Found')




class BR_MT_3d_comic_panel_contents(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "3D Comic: Contents"
    bl_idname = "SCENE_PT_3d_comic_panel_contents"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "3D Comics"


    # @classmethod 
    # def poll(self, context):
    #     backstage_collection_name = getCurrentBackstageCollectionName()
    #     return backstage_collection_name


    @classmethod 
    def poll(self, context):
        return developer_mode

    def draw(self, context):
        backstage_collection_name = getCurrentBackstageCollectionName()
        if "Backstage.Global" not in backstage_collection_name:
            global ink_swatch_object
            layout = self.layout
            scene = context.scene
            ink_swatch_object = getCurrentMaterialSwatch()
            panel_settings = scene.panel_settings
            if ink_swatch_object:
                layout.label(text="Shuffle:")
                row = layout.row()
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="<")
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="All")
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text=">")
                row = layout.row()
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="<")
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="Background")
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text=">")
                row = layout.row()
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="<")
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="Actors")
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text=">")
                row = layout.row()
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="<")
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="Letters")
                row.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text=">")


            else:
                self.layout.label(text= 'Comic Panel Not Found')




class BR_MT_3d_comic_panel_build(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "3D Comic: Build"
    bl_idname = "SCENE_PT_3d_comic_panel_build"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "3D Comics"
    # bl_space_type = 'PROPERTIES'
    # bl_context = "scene"
    # config: bpy.props.PointerProperty(type=PanelSettings)



    def draw(self, context):
        global ink_swatch_object
        layout = self.layout
        scene = context.scene
        ink_swatch_object = getCurrentMaterialSwatch()
        panel_settings = scene.panel_settings


        if ink_swatch_object:
            if developer_mode:
                layout.prop(panel_settings, "s3dc_dynamic_shadows", text="Dynamic Shadows")
                layout.prop(panel_settings, "s3dc_apply_armatures", text="Apply Armatutures")

            # Big render button
            row = layout.row()
            row.scale_y = 2.0
            row.operator("view3d.spiraloid_export_3d_comic_all")
            row.operator("wm.spiraloid_quicks_save_export_3d_comic_current")
            layout.operator("view3d.spiraloid_explore_3d_comic", text="Open 3D Comic Folder", icon="FILE_FOLDER")
            layout.operator("view3d.spiraloid_read_3d_comic", icon="HIDE_OFF")

        else:
            self.layout.label(text= 'No Backstage material object found !')

            # Big render button
            row = layout.row()
            row.scale_y = 1.0
            if developer_mode:
                row.operator("view3d.spiraloid_3d_comic_panel_init", text="Initialize as Template Panel?")
            row = layout.row()
            row.scale_y = 1.0
            row.operator("wm.spiraloid_new_3d_comic", text="Initialize as new 3D Comic?")



class BR_MT_3d_comic_submenu_panels(bpy.types.Menu):
    bl_idname = 'BR_MT_3d_comic_submenu_panels'
    bl_label = 'Panels'

    def draw(self, context):
        layout = self.layout

        # layout.operator("view3d.spiraloid_3d_comic_create_panel")
        # layout.operator("view3d.spiraloid_new_panel_row")
        layout.operator("wm.spiraloid_new_panel_row", icon="FILE_IMAGE", text="Insert...")
        layout.operator("view3d.spiraloid_3d_comic_blank_panel")
        layout.operator("view3d.spiraloid_3d_comic_clone_panel", text="Clone Current")
        layout.operator("view3d.spiraloid_3d_comic_delete_panel", text="Delete Current")
        layout.separator()
        layout.operator("screen.spiraloid_3d_comic_first_panel", icon="TRIA_UP")
        layout.operator("screen.spiraloid_3d_comic_next_panel", icon="TRIA_RIGHT")
        layout.operator("screen.spiraloid_3d_comic_previous_panel", icon="TRIA_LEFT")
        layout.operator("screen.spiraloid_3d_comic_last_panel", icon="TRIA_DOWN")
        layout.separator()
        layout.operator("screen.spiraloid_3d_comic_reorder_scene_earlier", icon="REW")
        layout.operator("screen.spiraloid_3d_comic_reorder_scene_later", icon="FF")
        if developer_mode:
            layout.separator()
            layout.operator("view3d.spiraloid_3d_comic_inject_panel", icon="IMPORT")
            layout.operator("view3d.spiraloid_3d_comic_extract_panel", icon="EXPORT")

class BR_MT_3d_comic_submenu_letters(bpy.types.Menu):
    bl_idname = 'BR_MT_3d_comic_submenu_letters'
    bl_label = 'Letters'
    

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        panel_settings = scene.panel_settings

        layout.operator("view3d.spiraloid_3d_comic_add_letter_wordballoon", icon="INFO")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_wordballoon_double", icon="INFO")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_wordballoon_triple", icon="INFO")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_wordballoon_quadruple", icon="INFO")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_caption", icon="INFO")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_sfx", icon="INFO")
        layout.operator("view3d.spiraloid_3d_comic_add_letter_border", icon="SNAP_FACE")

        layout.separator()
        layout.prop(panel_settings, "s3dc_language", text="Active Language")






# def add_items_from_collection_callback(self, context):
#     global working_folder
#     scene = context.scene
#     path =  working_folder + "\\shared\\"
#     shared_disk_assets = []
#     if path.is_file():
#         with bpy.data.libraries.load(str(path)) as (data_from, data_to):
#             object_names = [ob for ob in data_from.objects]
#         for object_name in object_names:
#             shared_disk_assets.append((object_name, object_name, ""))
#     else:
#         shared_disk_assets.append(("MISSING","Library is Missing",""))
#     return shared_disk_assets

# class MyEnumItems(bpy.types.PropertyGroup):
#     shared_disk_assets : bpy.props.EnumProperty(
#         name="shared_disk_assets",
#         description="disk_assets",
#         # items argument required to initialize, just filled with empty values
#         items = add_items_from_collection_callback,
#     )

class BR_MT_3d_comic_submenu_disk_assets(bpy.types.Menu):
    bl_idname = 'BR_MT_3d_comic_submenu_disk_assets'
    bl_label = 'Disk Assets'

    def draw(self, context):
        layout = self.layout
        chosen_disk_asset = bpy.context.scene.shared_disk_assets
        layout.operator(OBJECT_OT_3d_comic_add_dog.bl_idname, icon='HEART')
        layout.prop(chosen_disk_asset, "0")
        layout.operator(OBJECT_OT_3d_comic_add_dog.bl_idname, icon='HEART')


# class MY_OT_add_disk_item(bpy.types.Operator):
#     ''' add item to bpy.context.scene.shared_disk_assets '''
#     bl_label = "Workshop Empty"
#     bl_idname = "wm.add_item"

#     def execute(self, context):
#         current_scene = bpy.context.scene
#         disk_asset_file = current_scene["SharedDiskAsset"]["shared_disk_assets"]
#         print("----------------------" + disk_asset_file + "------------------------------------")
#         return {'FINISHED'}

# preview_collections = {}

# def enum_previews_from_directory_items(self, context):

#     category = context.scene.my_tool.cat
    
#     #Extensions
#     extensions = ('.jpeg', '.jpg', '.png')

#     # Icons Directory    
#     # directory = bpy.utils.user_resource('SCRIPTS', "addons\\Icons\\")
#     global working_folder
#     directory =  working_folder + "\\shared\\"

#     enum_items = []

#     if context is None:
#         return enum_items

#     pcoll = preview_collections["main"]

#     if directory == pcoll.my_previews_dir:
#         return pcoll.my_previews

#     if directory and os.path.exists(directory):
#         # Scan the directory for png files
#         image_paths = []
#         for fn in os.listdir(directory):
#             if fn.lower().endswith(extensions):
#                 image_paths.append(fn)

#         for i, name in enumerate(image_paths):
#             # generates a thumbnail preview for a file.
#             filepath = os.path.join(directory, name)
#             icon = pcoll.get(name)
#             if filepath in pcoll:
#                 enum_items.append((name, name, "", pcoll[filepath].icon_id, i))
#             else:
#                 thumb = pcoll.load(filepath, filepath, 'IMAGE')
#                 enum_items.append((name, name, "", thumb.icon_id, i))

#     pcoll.my_previews = enum_items
#     pcoll.my_previews_dir = directory
#     return pcoll.my_previews


def update_selected(self, context):
    # get_shared_disk_assets(self, context)
    print("loading item : ", context.scene.shared_disk_assets)
    return None

def get_shared_disk_assets(self, context):
    global working_folder
    scene = context.scene
    path =  working_folder + "\\shared\\"
    disk_assets = []
    if context is None:
        return disk_assets
    if path and os.path.exists(path):
        print(path + "--------------------------")
        for fn in os.listdir(path):
            if fn.lower().endswith(".blend"):
                disk_assets.append(fn)
    return disk_assets



class SharedDiskAsset(bpy.types.PropertyGroup):
    # disk_assets = [
    #     ("shared_disk_assets", "shared_disk_assets", '', 0),
    # ]
    bpy.types.Scene.shared_disk_assets = bpy.props.EnumProperty(
        name = "shared_disk_assets",
        items = get_shared_disk_assets,
        description="Files in Shared Folder",
        default=0,
        update= update_selected,
    )

class BR_MT_3d_comic_submenu_disk_assets(bpy.types.Menu):
    bl_idname = 'BR_MT_3d_comic_submenu_disk_assets'
    bl_label = 'Disk Assets'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        shared_disk_assets = scene.shared_disk_assets
        layout.operator(OBJECT_OT_3d_comic_add_dog.bl_idname, icon='HEART')
        layout.prop(shared_disk_assets, "disk_asset", text="Shared Asset")



class BR_MT_3d_comic_submenu_assets(bpy.types.Menu):
    bl_idname = 'BR_MT_3d_comic_submenu_assets'
    bl_label = 'Assets'

    def draw(self, context):
        layout = self.layout
        layout.operator(OBJECT_OT_3d_comic_add_dog.bl_idname, icon='HEART')
        layout.separator()
        layout.operator(OBJECT_OT_add_bonus.bl_idname, icon='KEYTYPE_BREAKDOWN_VEC')
        layout.separator()
        layout.operator(OBJECT_OT_add_inkbot_shuffle.bl_idname, icon='FILE_3D')
        # layout.operator(OBJECT_OT_add_inkbot.bl_idname, icon='FILE_3D')
        # layout.operator(OBJECT_OT_add_inkbot_puppet.bl_idname, icon='FILE_3D')
        layout.operator(OBJECT_OT_add_ground.bl_idname, icon='FILE_3D')
        layout.operator(OBJECT_OT_add_speedlines.bl_idname, icon='FILE_3D')
        layout.operator(OBJECT_OT_add_speedlines_radial.bl_idname, icon='FILE_3D')
        layout.operator(OBJECT_OT_add_speedlines_ground.bl_idname, icon='FILE_3D')
        layout.operator(OBJECT_OT_add_inksplat.bl_idname, icon='FILE_3D')
        layout.separator()
        layout.operator(OBJECT_OT_add_ground_rocks.bl_idname, icon='OUTLINER_DATA_POINTCLOUD')
        layout.operator(OBJECT_OT_add_sprite_card.bl_idname, icon='OUTLINER_DATA_POINTCLOUD')
        layout.operator("view3d.spiraloid_3d_comic_workshop")


class BR_MT_3d_comic_submenu_assets_shared(bpy.types.Menu):
    bl_idname = 'BR_MT_3d_comic_submenu_assets_shared'
    bl_label = 'Assets Shared'

    def draw(self, context):
        global developer_mode
        layout = self.layout
        layout.operator(OBJECT_OT_add_bonus_shared.bl_idname, icon='KEYTYPE_BREAKDOWN_VEC')
        layout.separator()
        layout.operator(OBJECT_OT_add_omnibot_shared.bl_idname, icon='FILE_3D')
        layout.operator(OBJECT_OT_add_ground.bl_idname, icon='FILE_3D')
        if developer_mode:
            layout.operator("view3d.spiraloid_3d_comic_workshop")



class BR_MT_3d_comic_submenu_key_camera(bpy.types.Menu):
    bl_idname = 'BR_MT_3d_comic_submenu_key_camera'
    bl_label = 'Key Camera'

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.spiraloid_3d_comic_key_camera_random", icon="CON_CAMERASOLVER")
        layout.operator("wm.spiraloid_3d_comic_key_camera_slide_up", icon="CON_CAMERASOLVER")
        layout.operator("wm.spiraloid_3d_comic_key_camera_slide_down", icon="CON_CAMERASOLVER")
        layout.operator("wm.spiraloid_3d_comic_key_camera_pan_left", icon="CON_CAMERASOLVER")
        layout.operator("wm.spiraloid_3d_comic_key_camera_pan_right", icon="CON_CAMERASOLVER")
        layout.operator("wm.spiraloid_3d_comic_key_camera_truck_in", icon="CON_CAMERASOLVER")
        layout.operator("wm.spiraloid_3d_comic_key_camera_truck_out", icon="CON_CAMERASOLVER")
        layout.operator("wm.spiraloid_3d_comic_key_world_spin_CW", icon="CON_CAMERASOLVER")
        layout.operator("wm.spiraloid_3d_comic_key_world_spin_CCW", icon="CON_CAMERASOLVER")



class BR_MT_3d_comic_submenu_utilities(bpy.types.Menu):
    bl_idname = 'BR_MT_3d_comic_submenu_utilities'
    bl_label = 'Utilities'

    def draw(self, context):
        global developer_mode

        layout = self.layout
        layout.operator("wm.spiraloid_toggle_workmode", icon="SEQ_PREVIEW")
        layout.separator()
        layout.operator(BR_OT_bake_collection.bl_idname, icon="TEXTURE_DATA")
        layout.operator("wm.spiraloid_automap", icon="UV_VERTEXSEL")
        layout.separator()
        layout.operator("wm.spiraloid_subcollection_cycler", icon="MATCLOTH")
        if developer_mode:
            layout.operator("wm.spiraloid_subcollection_cycler_exportable", icon="MATCLOTH")
        if operator_exists("BakeMeshFlipbook"):
            layout.operator("view3d.bake_mesh_flipbook", icon="MATCLOTH")
        if developer_mode:
            if operator_exists("KeyCollectionTreadmill"):
                layout.operator("wm.spiraloid_key_collection_readmill", icon="MATCLOTH")
        layout.separator()
        layout.operator("wm.spiraloid_pose_cycle_next", icon="ARMATURE_DATA")
        layout.operator("wm.spiraloid_pose_cycle_previous", icon="ARMATURE_DATA")

        if developer_mode:
            layout.separator()
            layout.operator("wm.spiraloid_pose_add", icon="ARMATURE_DATA")
            layout.operator("wm.spiraloid_pose_overwrite", icon="ARMATURE_DATA")
            layout.operator("wm.spiraloid_pose_remove", icon="ARMATURE_DATA")
            layout.operator("wm.spiraloid_toggle_child_lock", icon="RESTRICT_INSTANCED_OFF")
        layout.separator()
        layout.operator("wm.spiraloid_3d_comic_key_scale_hide", icon="HIDE_ON")
        layout.menu(BR_MT_3d_comic_submenu_key_camera.bl_idname, icon="CON_CAMERASOLVER")
        layout.separator()
        if developer_mode:
            layout.operator("view3d.spiraloid_3d_comic_preview", icon= "FILE_MOVIE")
            layout.separator()
            layout.operator("view3d.spiraloid_3d_comic_panel_init")
            layout.operator("view3d.spiraloid_3d_comic_panel_validate_naming")
            layout.operator("view3d.spiraloid_3d_comic_panel_validate_naming_all")
        layout.operator("wm.spiraloid_toggle_developer_mode")
        


        # layout.operator("view3d.spiraloid_export_3d_comic_letters_current", icon="RENDER_RESULT")
        # layout.operator("view3d.spiraloid_export_3d_comic_letters_all", icon="RENDER_RESULT")


class BR_MT_3d_comic_submenu_lighting(bpy.types.Menu):
    bl_idname = 'BR_MT_3d_comic_submenu_lighting'
    bl_label = 'Color'

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.spiraloid_3d_comic_init_ink_lighting", text="Ink Toonshade Visible", icon="MATSHADERBALL")
        layout.separator()
        layout.operator("view3d.spiraloid_3d_comic_ink_toonshade", text="Ink Toonshade Selected", icon="NODE_MATERIAL")
        layout.operator("view3d.spiraloid_3d_comic_toonshade", text="Toonshade Selected", icon="SHADING_SOLID")
        layout.operator("view3d.spiraloid_3d_comic_ink", text="Ink Selected", icon="MESH_CIRCLE")
        layout.separator()
        layout.operator("view3d.spiraloid_3d_comic_whiteout", text="Whiteout Selected", icon="SNAP_FACE")
        layout.operator("view3d.spiraloid_3d_comic_blackout", text="Blackout Selected", icon="COLORSET_20_VEC")
        layout.separator()
        if developer_mode:
            layout.operator("view3d.spiraloid_3d_comic_init_workshop_lighting", text="Studio Lights", icon="BRUSH_TEXFILL")
        layout.separator()
        layout.operator("view3d.spiraloid_3d_comic_cycle_sky", text="Cycle Sky", icon="FILE_IMAGE")
        layout.separator()
        layout.operator("wm.spiraloid_3d_comic_clear_all_ink_lighting", text="Clear Ink Toonshade all", icon="MATSHADERBALL")

        # layout.operator("view3d.spiraloid_3d_comic_init_vehicle_lighting")
        # layout.operator("view3d.spiraloid_3d_comic_init_magic_hour_lighting")



def add_object_button(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(OBJECT_OT_add_inkbot.bl_idname, icon='GHOST_DISABLED')
    layout.operator(OBJECT_OT_add_ground.bl_idname, icon='AXIS_TOP')
    layout.operator(OBJECT_OT_add_speedlines.bl_idname, icon='AXIS_TOP')
    layout.operator(OBJECT_OT_add_speedlines_radial.bl_idname, icon='AXIS_TOP')
    layout.operator(OBJECT_OT_add_speedlines_ground.bl_idname, icon='AXIS_TOP')
    layout.separator()
    layout.operator(OBJECT_OT_add_ground_rocks.bl_idname, icon='AXIS_TOP')


def add_3dcomic_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu(BR_MT_3d_comic_menu.bl_idname, text="3D Comic", icon='GHOST_ENABLED')
    layout.separator()

def draw_item(self, context):
    layout = self.layout
    layout.menu(BR_MT_3d_comic_menu.bl_idname)



#------------------------------------------------------

classes = (
    BakePanelSettings,
    NewComicSettings,
    NewPanelRowSettings,
    SharedDiskAsset,
    PanelSettings,
    BR_OT_spiraloid_toggle_developer_mode,
    BR_OT_add_pose,
    OBJECT_OT_3d_comic_add_dog,
    BR_OT_subcollection_cycler,
    BR_OT_subcollection_cycler_exportable,
    BR_OT_overwrite_pose,
    BR_OT_remove_pose,
    BR_OT_toggle_child_lock,
    BR_OT_panel_init,
    BR_OT_panel_validate_naming,
    BR_OT_panel_validate_naming_all,
    BR_MT_3d_comic_menu,
    BR_MT_3d_comic_submenu_panels,
    BR_MT_3d_comic_submenu_letters,
    BR_OT_spiraloid_3d_comic_workshop,
    BR_OT_key_scale_hide,
    BR_OT_key_camera_random,
    BR_OT_key_camera_slide_up,
    BR_OT_key_camera_slide_down,
    BR_OT_key_camera_pan_left,
    BR_OT_key_camera_pan_right,
    BR_OT_key_camera_truck_in,
    BR_OT_key_camera_truck_out,
    BR_OT_key_world_spin_cw,
    BR_OT_key_world_spin_ccw,
    BR_OT_add_outline,
    BR_OT_add_toonshade,
    BR_OT_add_whiteout,
    BR_OT_add_blackout,
    BR_OT_add_toon_outline,
    BR_OT_toonfill,
    BR_OT_save_check,
    BR_OT_bake_collection,
    BR_OT_new_3d_comic,
    BR_OT_next_panel_scene,
    BR_OT_previous_panel_scene,
    BR_OT_first_panel_scene,
    BR_OT_last_panel_scene,
    BR_OT_panel_init_workshop_lighting,
    BR_OT_panel_init_ink_lighting,
    BR_OT_panel_clear_ink_lighting,
    BR_OT_panel_cycle_sky,
    BR_MT_3d_comic_submenu_lighting,
    BR_MT_3d_comic_submenu_utilities,
    BR_OT_reorder_scene_later,
    BR_OT_reorder_scene_earlier,
    BR_OT_new_panel_row,
    BR_OT_insert_comic_scene,
    BR_OT_clone_comic_scene,
    BR_OT_blank_comic_scene,
    BR_OT_add_letter_border,
    BR_OT_add_letter_caption,
    BR_OT_add_letter_wordballoon,
    BR_OT_add_letter_wordballoon_double,
    BR_OT_add_letter_wordballoon_triple,
    BR_OT_add_letter_wordballoon_quadruple,
    BR_OT_add_letter_sfx,
    # BR_OT_add_ground,
    BR_MT_3d_comic_submenu_assets,
    BR_MT_3d_comic_submenu_assets_shared,
    BR_OT_regenerate_3d_comic_preview,
    BR_OT_delete_comic_scene,
    BR_MT_export_3d_comic_all,
    BR_MT_quick_save_export_3d_comic_current,
    # BR_MT_export_3d_comic_letters_all,
    # BR_MT_export_3d_comic_letters_current,
    BR_MT_read_3d_comic,
    BR_OT_inject_comic_scene,
    BR_OT_extract_comic_scene,
    OBJECT_OT_add_inksplat,
    OBJECT_OT_add_ground,
    OBJECT_OT_add_speedlines,
    OBJECT_OT_add_speedlines_radial,
    OBJECT_OT_add_speedlines_ground,
    OBJECT_OT_add_ground_rocks,
    OBJECT_OT_add_sprite_card,
    # OBJECT_OT_add_inkbot,  
    # OBJECT_OT_add_inkbot_puppet,
    OBJECT_OT_add_inkbot_shuffle,
    OBJECT_OT_add_bonus_shared,
    OBJECT_OT_add_bonus,
    OBJECT_OT_add_omnibot_shared,
    BR_OT_pose_cycle_next,
    BR_OT_pose_cycle_previous,
    BR_OT_spiraloid_toggle_workmode,
    BR_OT_spiraloid_automap,
    OBJECT_OT_drop_to_ground,
    BR_MT_3d_comic_submenu_key_camera,
    BR_MT_3d_comic_submenu_disk_assets,
    BR_MT_explore_3d_comic,
    BR_MT_3d_comic_panels,
    BR_MT_3d_comic_panel_color,
    BR_MT_3d_comic_panel_letters,
    BR_MT_3d_comic_panel_contents,
    BR_MT_3d_comic_panel_build,
)



def register():
    # bpy.app.handlers.depsgraph_update_post.append(scene_update_handler)

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


    bpy.types.Scene.bake_panel_settings = bpy.props.PointerProperty(type=BakePanelSettings)
    bpy.types.Scene.new_3d_panel_settings = bpy.props.CollectionProperty(type=NewComicSettings)
    # bpy.types.Scene.panel_settings = bpy.props.PointerProperty(type=ComicSettings)
    bpy.types.Scene.new_panel_row_settings = bpy.props.PointerProperty(type=NewPanelRowSettings)
    bpy.types.Scene.shared_disk_assets = bpy.props.PointerProperty(type=SharedDiskAsset)
    bpy.types.Scene.panel_settings = bpy.props.PointerProperty(type=PanelSettings)




    bpy.types.TOPBAR_MT_editor_menus.append(draw_item)
    bpy.types.VIEW3D_MT_add.prepend(add_3dcomic_menu)
    bpy.types.VIEW3D_MT_view.append(menu_draw_view)  





def unregister():
    # bpy.app.handlers.depsgraph_update_post.remove(scene_update_handler)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    bpy.types.TOPBAR_MT_editor_menus.remove(draw_item)
    bpy.types.VIEW3D_MT_add.remove(add_3dcomic_menu)
    bpy.types.VIEW3D_MT_view.remove(menu_draw_view)  

    del bpy.types.Scene.bake_panel_settings
    del bpy.types.Scene.new_3d_panel_settings
    # del bpy.types.Scene.panel_settings
    del bpy.types.Scene.new_panel_row_settings
    del bpy.types.Scene.shared_disk_assets
    del bpy.types.Scene.panel_settings

    if __name__ != "__main__":
        bpy.types.TOPBAR_MT_editor_menus.remove(menu_draw_bake)


if __name__ == "__main__":
    register()


# def register():
#     bpy.utils.register_class(BR_OT_panel_init)
#     bpy.utils.register_class(BR_MT_3d_comic_menu)
#     bpy.utils.register_class(BR_MT_3d_comic_submenu_panels)
#     bpy.utils.register_class(BR_MT_3d_comic_submenu_letters)
#     bpy.utils.register_class(BR_OT_spiraloid_3d_comic_workshop)
#     bpy.utils.register_class(BR_OT_add_outline)

#     bpy.utils.register_class(BR_OT_bake_collection)
#     bpy.utils.register_class(BR_OT_new_3d_comic) 

#     bpy.utils.register_class(BR_OT_next_panel_scene)      
#     bpy.utils.register_class(BR_OT_previous_panel_scene)
#     bpy.utils.register_class(BR_OT_first_panel_scene)
#     bpy.utils.register_class(BR_OT_last_panel_scene)

#     bpy.utils.register_class(BR_OT_panel_init_workshop_lighting)
#     bpy.utils.register_class(BR_OT_panel_init_ink_lighting)
#     bpy.utils.register_class(BR_MT_3d_comic_submenu_lighting)
#     bpy.utils.register_class(BR_MT_3d_comic_submenu_utilities)

#     bpy.utils.register_class(BR_OT_reorder_scene_later)   
#     bpy.utils.register_class(BR_OT_reorder_scene_earlier)   
#     bpy.utils.register_class(BR_OT_insert_comic_scene)       
#     bpy.utils.register_class(BR_OT_clone_comic_scene)       
#     bpy.utils.register_class(BR_OT_add_letter_caption) 
#     bpy.utils.register_class(BR_OT_add_letter_wordballoon) 
#     bpy.utils.register_class(BR_OT_add_letter_sfx) 

#     bpy.utils.register_class(BR_OT_add_ground) 
#     bpy.utils.register_class(BR_MT_3d_comic_submenu_assets) 


#     bpy.utils.register_class(BR_OT_regenerate_3d_comic_preview) 
#     bpy.utils.register_class(BR_OT_delete_comic_scene)      
#     bpy.utils.register_class(BR_OT_export_3d_comic_all) 
#     bpy.utils.register_class(BR_OT_read_3d_comic) 

#     bpy.utils.register_class(BakePanelSettings)
    

#     bpy.utils.register_class(ComicPreferences)

#     bpy.types.Scene.bake_panel_settings = bpy.props.PointerProperty(type=BakePanelSettings)
#     bpy.types.TOPBAR_MT_editor_menus.append(draw_item)

# def unregister():
#     bpy.utils.unregister_class(BR_OT_panel_init)
#     bpy.utils.unregister_class(BR_MT_3d_comic_menu)
#     bpy.utils.unregister_class(BR_MT_3d_comic_submenu_panels)
#     bpy.utils.unregister_class(BR_MT_3d_comic_submenu_letters)
#     bpy.utils.unregister_class(BR_OT_spiraloid_3d_comic_workshop) 
#     bpy.utils.unregister_class(BR_OT_add_outline) 
#     bpy.utils.unregister_class(BR_OT_bake_collection) 
#     bpy.utils.unregister_class(BR_OT_new_3d_comic)
#     bpy.utils.unregister_class(BR_OT_next_panel_scene)      
#     bpy.utils.unregister_class(BR_OT_previous_panel_scene)  
#     bpy.utils.unregister_class(BR_OT_first_panel_scene)
#     bpy.utils.unregister_class(BR_OT_last_panel_scene)
#     bpy.utils.unregister_class(BR_OT_panel_init_workshop_lighting)
#     bpy.utils.unregister_class(BR_OT_panel_init_ink_lighting)
#     bpy.utils.unregister_class(BR_MT_3d_comic_submenu_lighting)
#     bpy.utils.unregister_class(BR_MT_3d_comic_submenu_utilities)
#     bpy.utils.unregister_class(BR_OT_reorder_scene_later)   
#     bpy.utils.unregister_class(BR_OT_reorder_scene_earlier)   
#     bpy.utils.unregister_class(BR_OT_insert_comic_scene)      
#     bpy.utils.unregister_class(BR_OT_clone_comic_scene)      
#     bpy.utils.unregister_class(BR_OT_add_letter_caption) 
#     bpy.utils.unregister_class(BR_OT_add_letter_wordballoon) 
#     bpy.utils.unregister_class(BR_OT_add_letter_sfx) 
#     bpy.utils.unregister_class(BR_OT_add_ground) 
#     bpy.utils.unregister_class(BR_MT_3d_comic_submenu_assets) 
#     bpy.utils.unregister_class(BR_OT_regenerate_3d_comic_preview) 
#     bpy.utils.unregister_class(BR_OT_delete_comic_scene)      
#     bpy.utils.unregister_class(BR_OT_export_3d_comic_all) 
#     bpy.utils.unregister_class(BR_OT_read_3d_comic) 
#     bpy.utils.unregister_class(BakePanelSettings)
#     bpy.utils.unregister_class(ComicPreferences)
    
#     bpy.types.TOPBAR_MT_editor_menus.remove(draw_item)

#     if __name__ != "__main__":
#         bpy.types.TOPBAR_MT_editor_menus.remove(menu_draw_bake)
# #    bpy.types.SEQUENCER_MT_add.remove(add_object_button)


    # The menu can also be called from scripts
#bpy.ops.wm.call_menu(name=BR_MT_3d_comic_menu.bl_idname)

#debug console
#__import__('code').interact(local=dict(globals(), **locals()))
# pauses wherever this line is:
# code.interact