import os
import random
import traceback

# sys.path.append(r"E:\PYTHON_STUFF\SourceBSP")
try:
    import BSP_DATA
    from BSP import BSP
    from BSP_DATA import *
    # from ValveFileSystem import valve

    try:
        import bpy
    except ImportError:
        pass
    import mathutils
    from mathutils import Vector, Matrix, Euler
except ImportError:
    import bpy
    from . import BSP_DATA
    from .BSP import BSP
    from .BSP_DATA import *
    import mathutils
    from mathutils import Vector, Matrix, Euler
    # from .ValveFileSystem import valve


from pathlib import Path


class BSPIO:

    def __init__(self, filepath, game_root_folder=None):
        if game_root_folder:
            os.environ['VProject'] = game_root_folder
        else:
            game_path = Path(filepath)
            if game_path.parent.name == 'maps':
                os.environ['VProject'] = str(game_path.parent.parent)

        self.name = Path(filepath).name
        self.bsp = BSP(filepath)
        self.bsp.read_all()
        self.verts = [(vert.x, vert.y, vert.z) for vert in self.bsp.vertexes]
        # self.objects = {} # type:Dict[List]
        # self.normals = [(normal.x, normal.y, normal.z) for normal in
        #               [self.normals[normal_ind] for normal_ind in self.BSP.BSP.LUMPS[31].indexes]]
        self.object_index = 0
        self.prepare_models()
        self.add_lights()
        self.place_static_props()

    def prepare_models(self):
        for i, model in enumerate(self.bsp.models):
            self.prepare_model(model)

    def prepare_model(self, model: Model):
        # print("Building",model)
        self.objects = {}
        for face in self.bsp.faces[model.first_face:model.first_face + model.num_faces]:
            tex_info = self.bsp.tex_infos[face.texinfo]
            if (tex_info.flags & BSP_DATA.SURF_TRIGGER):
                face_type = 'TRIGGER'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_NODRAW) > 0:
                face_type = 'NODRAW'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_SKIP) > 0:
                face_type = 'SKIP'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_SKY2D) > 0:
                face_type = 'SKY2D'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_SKY) > 0:
                face_type = 'SKY'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_HITBOX) > 0:
                face_type = 'HITBOX'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_NOCHOP) > 0:
                face_type = 'NOCHOP'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_NODECALS) > 0:
                face_type = 'NODECALS'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_NOLIGHT) > 0:
                face_type = 'NOLIGHT'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_SKIP) > 0:
                face_type = 'SKIP'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_HINT) > 0:
                face_type = 'HINT'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif (tex_info.flags & BSP_DATA.SURF_TRANS) > 0:
                face_type = 'TRANS'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)

            elif face.dispinfo != -1:
                # displacement_faces.append(face)
                face_type = 'DISP'

                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)
            else:
                face_type = 'MESH'
                if face_type not in self.objects:
                    self.objects[face_type] = [face]
                else:
                    self.objects[face_type].append(face)
        for object_type, faces in self.objects.items():
            self.build_object(faces, object_type, model)

    def get_material(self, mat_name, model_ob):
        if '/' in mat_name:
            mat_name = mat_name.split('/')[-1]

        if mat_name:
            mat_name = mat_name
        else:
            mat_name = "Material"
        mat_ind = 0
        md = model_ob.data
        mat = None
        for candidate in bpy.data.materials:  # Do we have this material already?
            if candidate.name == mat_name:
                mat = candidate
        if mat:
            if md.materials.get(mat.name):  # Look for it on this mesh
                for i in range(len(md.materials)):
                    if md.materials[i].name == mat.name:
                        mat_ind = i
                        break
            else:  # material exists, but not on this mesh
                md.materials.append(mat)
                mat_ind = len(md.materials) - 1
        else:  # material does not exist
            # print("- New material: {}".format(mat_name))
            mat = bpy.data.materials.new(mat_name)
            md.materials.append(mat)
            # Give it a random colour
            randCol = []
            for i in range(3):
                randCol.append(random.uniform(.4, 1))
            mat.diffuse_color = randCol

            mat_ind = len(md.materials) - 1

        return mat, mat_ind

    def build_object(self, faces, object_type, model):
        mat_ind = []
        uvs = []
        mats = []
        mesh_faces = []
        for face in faces:
            # print(face)

            face_indexes = []
            first_edge = face.firstedge
            num_edges = face.numedges
            tex_info = self.bsp.tex_infos[face.texinfo]
            texdata = self.bsp.tex_datas[tex_info.texdata]
            mat_name = self.bsp.tex_strings[texdata.name_id]
            mat_ind.append((tex_info.texdata, mat_name))
            edge_indexs = [self.bsp.surf_edges[first_edge + ind].surf_edge for ind in range(num_edges)]
            for edge_index in edge_indexs:
                edges = self.bsp.edges[abs(edge_index)].v
                if edge_index < 0:
                    if edges[1] not in face_indexes:
                        face_indexes.append(edges[1])
                    if edges[0] not in face_indexes:
                        face_indexes.append(edges[0])
                else:
                    if edges[0] not in face_indexes:
                        face_indexes.append(edges[0])
                    if edges[1] not in face_indexes:
                        face_indexes.append(edges[1])
                for v in edges:
                    x, y, z = self.verts[v]
                    tv = tex_info.texture_vectors
                    u = tv[0].xyz.x * x + tv[0].xyz.y * y + tv[0].xyz.z * z + tv[0].offset
                    v = tv[1].xyz.x * x + tv[1].xyz.y * y + tv[1].xyz.z * z + tv[1].offset
                    uvs.append((u, v))
                mesh_faces.append(face_indexes)

        name = '{}_{}_{}'.format(self.name, object_type, self.object_index)
        self.object_index += 1
        try:
            model_mesh = bpy.data.objects.new(name, bpy.data.meshes.new(name))
            model_mesh.location = (model.origin.x, model.origin.y, model.origin.z)
            # model_mesh.parent = self.armature_object
            bpy.context.scene.objects.link(model_mesh)
            md = model_mesh.data
            md.from_pydata(self.verts, [], mesh_faces[::-1])
            md.update()
            md.uv_textures.new()
            uv_data = md.uv_layers[0].data
            # print(len(uvs),len(uv_data))
            for i in range(len(uv_data)):
                if md.loops[i].vertex_index > len(uvs):
                    continue
                uv_data[i].uv = uvs[md.loops[i].vertex_index]
            for _, mat_name in mat_ind:

                if mat_name.startswith('maps/'):
                    mat_name = mat_name.split('/')[-1]

                mat, mat_ind_ = self.get_material(mat_name, model_mesh)
                mats.append(mat_ind_)
            for poly, mat_index in zip(model_mesh.data.polygons, mats):
                poly.material_index = mat_index
            bpy.ops.object.select_all(action="DESELECT")
            model_mesh.select = True
            bpy.context.scene.objects.active = model_mesh
            vertex_normals = []
            vn_idns_len = len(self.bsp.normal_indices)
            for poly in mesh_faces:
                for v_id in poly:
                    vn_ind = self.bsp.normal_indices[v_id].v
                    n = self.bsp.normals[vn_ind]

                    normal = [1 - n.x, 1 - n.y, 1 - n.z]
                    vertex_normals.append(normal)
            # md.create_normals_split()
            md.use_auto_smooth = True
            # md.normals_split_custom_set(vertex_normals)
            # md.normals_split_custom_set_from_vertices(vertex_normals[:len(self.verts)])

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.delete_loose()
            bpy.ops.object.mode_set(mode='OBJECT')

            if object_type == 'TRIGGER':
                model_mesh.layers[1] = True
                for i in range(20):
                    model_mesh.layers[i] = (i == 1)
            if object_type == 'MESH':
                model_mesh.layers[0] = True
                for i in range(20):
                    model_mesh.layers[i] = (i == 0)
            if object_type in ['SKY', 'SKY2D']:
                model_mesh.layers[4] = True
                for i in range(20):
                    model_mesh.layers[i] = (i == 4)

        except Exception as Ex:
            traceback.print_exc()
            print('Failed to build mesh')

    def add_lights(self):
        for light in self.bsp.world_lights:
            lamp_type = 'POINT'
            if EmitType(light.type) == EmitType.emit_point:
                lamp_type = 'POINT'
            elif emittype_t(light.type) == EmitType.emit_spotlight:
                lamp_type = 'SPOT'
            bpy.ops.object.lamp_add(type=lamp_type, radius=1.0, view_align=False,
                                    location=(light.origin.x, light.origin.y, light.origin.z),
                                    rotation=(360 * light.normal.x, 360 * light.normal.y, 360 * light.normal.z), )
            lamp = bpy.context.object
            # lamp.layers = layers
            lamp_data = lamp.data
            light = light.intensity
            lamp_nodes = lamp_data.node_tree.nodes['Emission']
            lamp_nodes.inputs['Strength'].default_value = light.magnitude() * 10
            lamp_nodes.inputs['Color'].default_value = light.normalize().to_array_rgba

    def place_static_props(self):
        for static_prop in self.bsp.static_prop_lump.props:
            empty = bpy.data.objects.new("empty", None)
            bpy.context.scene.objects.link(empty)
            pos = Vector(static_prop.origin.as_list)
            rot = Euler(static_prop.angles.as_list)
            empty.matrix_basis.identity()
            empty.location = pos
            empty.rotation_euler = rot


if __name__ == '__main__':
    # map = BSPIO(r'G:\SteamLibrary\SteamApps\common\SourceFilmmaker\game\usermod\maps\me3_apartments_sfm_v2.bsp',r'G:\SteamLibrary\SteamApps\common\Left 4 Dead 2\left4dead2')
    map = BSPIO(r'G:\SteamLibrary\SteamApps\common\SourceFilmmaker\game\usermod\maps\me3_apartments_sfm_v2.bsp')
