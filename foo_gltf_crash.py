import bpy

file_path = bpy.data.filepath
file_name = bpy.path.display_name_from_filepath(file_path)
file_ext = '.blend'
file_dir = file_path.replace(file_name+file_ext, '')

bpy.context.window.scene = bpy.data.scenes[0]
path_to_export_file = (file_dir + bpy.data.scenes[0].name +".glb")
bpy.ops.export_scene.gltf(
    export_nla_strips=False,  
    export_apply=True,     
    export_format='GLB', 
    ui_tab='GENERAL', 
    export_copyright="", 
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
    use_selection=True, 
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

print(path_to_export_file)
                    

bpy.context.window.scene = bpy.data.scenes[1]
path_to_export_file = (file_dir + bpy.data.scenes[1].name +".glb")

bpy.ops.export_scene.gltf(
    export_nla_strips=False,  
    export_apply=True,     
    export_format='GLB', 
    ui_tab='GENERAL', 
    export_copyright="", 
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
    use_selection=True, 
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
print(path_to_export_file)
