bl_info = {
    "name": "Source Engine map import + textures (.bsp)",
    "author": "RED_EYE",
    "version": (0, 5),
    "blender": (2, 78, 0),
    'warning': 'DO NOT ENABLE "IMPORT STATICPROPS"',
    "location": "File > Import-Export > SourceEngine BSP (.bsp) ",
    "description": "Addon allows to import Source Engine maps",
    #"wiki_url": "http://www.barneyparker.com/blender-json-import-export-plugin",
    #"tracker_url": "http://www.barneyparker.com/blender-json-import-export-plugin",
    "category": "Import-Export"}
from . import BSP,BSP_DATA,BSP_IO
if "bpy" in locals():
    import importlib
    if "BSP_import" in locals():
        importlib.reload(BSP)
        importlib.reload(BSP_DATA)
        importlib.reload(BSP_IO)
else:
    import bpy

from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper


class BSPImport(bpy.types.Operator):
    """Load Source Engine MDL models"""
    bl_idname = "import_mesh.bsp"
    bl_label = "Import Bsp"
    bl_options = {'UNDO'}

    filepath = StringProperty(
            subtype='FILE_PATH',
            )
    # Import_staticProps = BoolProperty(name="Import StaticProps?",
    #                                default=False, subtype='UNSIGNED')
    # WorkDir = StringProperty(name="path to folder with gameinfo.txt", maxlen=1024, default="", subtype='FILE_PATH')
    filter_glob = StringProperty(default="*.bsp", options={'HIDDEN'})

    def execute(self, context):

        BSP_IO.BSPIO(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_import(self, context):
    self.layout.operator(BSPImport.bl_idname, text="BSP mesh (.BSP)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_import)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_import)


if __name__ == "__main__":
    register()
