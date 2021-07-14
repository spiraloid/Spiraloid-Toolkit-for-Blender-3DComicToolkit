bl_info = {
        'name': 'KeyCollectionTreadmill',
        'author': 'bay raitt',
        'version': (0, 1),
        'blender': (2, 92, 0),
        'category': 'Animation',
        'location': '3D Comic > Utilities > Key Collection Treadmill',
        'wiki_url': ''}


import bpy


class KeyCollectionTreadmillSettings(bpy.types.PropertyGroup):
    source_treadmill_collection : bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Source",         
        description="The collection to use as a treadmill"
    )

    speed_strategy : bpy.props.EnumProperty(
        name="Target", 
        description="Type of object to recieve baked textures", 
        items={
            ("speed_slow", "Speed Slow","slow", 0),
            ("speed_medium","Speed Medium", "medium", 1),
            ("speed_fast", "Speed Fast","fast", 2),
            },
        default="speed_medium"
    )

class BR_OT_key_collection_treadmill(bpy.types.Operator):
    """key selected collection as a stationary treadmill with two reinstances"""
    bl_idname = "wm.spiraloid_3d_comic_key_collection_readmill"
    bl_label = "key collection treadmill..."
    bl_options = {'REGISTER', 'UNDO'}
    # config: bpy.props.PointerProperty(type=KeyCollectionTreadmillSettings)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        key_collection_treadmill_settings = scene.key_collection_treadmill_settings
        strategy_row = layout.row(align=True)
        layout.prop(key_collection_treadmill_settings, "source_treadmill_collection" )
        layout.prop(key_collection_treadmill_settings, "speed_strategy")

 
    def execute(self, context):          
        settings = context.scene.key_collection_treadmill_settings
        source_collection = settings.source_treadmill_collection
        source_collection_name = source_collection.name
        scene_collection = bpy.context.view_layer.layer_collection
        treadmill_collection_name =  (source_collection_name  + "_treadmill")


        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        # cleanup previous bake collection 
        if bpy.data.collections.get(treadmill_collection_name) : 
            old_bake_collection = bpy.data.collections.get(treadmill_collection_name)
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[treadmill_collection_name]
            bpy.data.collections.remove(old_bake_collection)
            empty_trash(self, context)
            self.report({'INFO'}, 'Deleted Previous Treadmill collection!')

        treadmill_collection = bpy.data.collections.new(treadmill_collection_name)

        return {'FINISHED'}
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def menu_draw(self, context):
    self.layout.operator(BR_OT_bake_mesh_flipbook.bl_idname)



def register():
    bpy.utils.register_class(BR_OT_key_collection_treadmill)
    bpy.utils.register_class(KeyCollectionTreadmillSettings)
    bpy.types.Scene.key_collection_treadmill_settings = bpy.props.PointerProperty(type=KeyCollectionTreadmillSettings)
    bpy.types.VIEW3D_MT_object_animation.append(menu_draw)  

def unregister():
    bpy.utils.unregister_class(BR_OT_key_collection_treadmill)
    bpy.utils.unregister_class(KeyCollectionTreadmillSettings)
    del bpy.types.Scene.key_collection_treadmill_settings
    bpy.types.VIEW3D_MT_object_animation.remove(menu_draw)  

    if __name__ != "__main__":
        bpy.types.VIEW3D_MT_view.remove(menu_draw)

if __name__ == "__main__":
    register()


