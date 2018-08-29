import os.path
import sys
from pathlib import Path
from pprint import pprint
from typing import Type
import re

try:
    from BSP_DATA import *
    from ByteIO import ByteIO
except ImportError:
    from .BSP_DATA import *
    from .ByteIO import ByteIO

fix_re = re.compile(r"_[\d]+_[\d]+_[\d]+")

class BSP:

    def __init__(self, filepath):
        print("Reading {}".format(Path(filepath).filename))
        self.reader = ByteIO(path=filepath)
        self.filename = os.path.basename(filepath)[:-4]
        self.header = Header()
        self.header.read(self.reader)
        print(self.header)
        self.vertexes = [] #type: List[SourceVector]
        self.normals = [] #type: List[SourceVector]
        self.normal_indices = [] #type: List[VertexNormal]
        self.planes = [] #type: List[Plane]
        self.edges = [] #type: List[Edge]
        self.surf_edges = [] #type: List[SurfEdge]
        self.faces = [] #type: List[Face]
        self.models = [] #type: List[Model]
        self.orig_faces = [] #type: List[Face]
        self.brushes = [] #type: List[Brush]
        self.brush_sides = [] #type: List[BrushSide]
        self.world_lights = [] #type: List[WorldLight]
        self.tex_infos = [] #type: List[TextureInfo]
        self.tex_datas = [] #type: List[TextureData]
        self.nodes = [] #type: List[Node]
        self.tex_string_datas = [] #type: List[TexdataStringData]
        self.tex_strings = [] #type: List[str]
        self.static_prop_lump = StaticPropLump()

        self.static_props = []
        # self.key_values = ""
        self.game_header = GameLumpHeader()

    def read_all(self):
        ### PLANES ###
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_PLANES],Plane,self.planes)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_EDGES],Edge,self.edges)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_SURFEDGES],SurfEdge,self.surf_edges)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_VERTEXES],SourceVector,self.vertexes)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_VERTNORMALS],SourceVector,self.normals)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_VERTNORMALINDICES],VertexNormal,self.normal_indices)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_FACES],Face,self.faces)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_MODELS],Model,self.models)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_ORIGINALFACES],Face,self.orig_faces)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_BRUSHES],Brush,self.brushes)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_BRUSHSIDES],BrushSide,self.brush_sides)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_TEXDATA],TextureData,self.tex_datas)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_TEXINFO],TextureInfo,self.tex_infos)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_WORLDLIGHTS],WorldLight,self.world_lights)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_TEXDATA_STRING_DATA],TexdataStringData,self.tex_string_datas)
        self.read_array(self.header.lumps[LUMP_ENUM.LUMP_NODES],Node,self.nodes)
        self.read_string_array(self.header.lumps[LUMP_ENUM.LUMP_TEXDATA_STRING_TABLE],self.tex_strings)
        # self.read_key_values(self.header.lumps[LUMP_ENUM.LUMP_ENTITIES])

        self.reader.seek(self.header.lumps[LUMP_ENUM.LUMP_GAME_LUMP].offset)
        self.game_header.read(self.reader)
        self.read_game_lumps()

    def read_game_lumps(self):
        for glump in self.game_header.game_lumps:
            if glump.id == 'prps':
                self.reader.seek(glump.offset)
                self.static_prop_lump.read(self.reader,glump.version,glump.size)

    def read_array(self,lump:Lump,array_item:Type[Dummy],array:list):
        self.reader.seek(lump.offset)
        # print(lump.length/array_item.size,lump)
        array_item.bsp = self.header

        count = lump.length//int(array_item().size)
        if lump.length%int(array_item().size):
            print('ERROR on ',lump.id.name,lump.length/int(array_item().size))
            raise NotImplementedError('Unknown structure, size of structure does not match')
        if __name__ == '__main__':
            if hasattr(lump.id,'name'):
                print("Reading",count,"{}".format(lump.id.name[5:]))
            else:
                print("Reading", count, "{} lump".format(lump.id))
        for _ in range(count):
            item = array_item()
            item.read(self.reader)
            array.append(item)

    def read_string_array(self,lump:Lump,array:list):
        self.reader.seek(lump.offset)
        buffer = self.reader.read_bytes(lump.length)
        array.extend(buffer.split(b'\x00'))
        array_ = list(map(lambda a:a.decode("utf"),array))
        array.clear()
        for string in array_:
            if fix_re.search(string):
                string = fix_re.sub("",string)
            array.append(string)


    def test(self):
        print(self.header)
        for s in self.static_prop_lump.props:
            print(s)
        # for obj in self.nodes:
        #     pprint(obj)
        # print('Vertexes')
        # for v in self.vertexes:
        #     print(v)
        # print('Normals')
        # for vn in self.normals:
        #     print(vn)
        # print('Normal indices')
        # for vni in self.normal_indices:
        #     print(vni)
    # def read_key_values(self,lump:Lump):
    #     self.reader.seek(lump.offset)
    #     buffer = self.reader.read_ascii_string(lump.length)
    #     self.key_values = KeyValueFile(string_buffer=buffer.split("\n"))
    #     print(self.key_values)



if __name__ == '__main__':
    with open('log.log', "w") as f:
        with f as sys.stdout:
            map_path = r'G:\SteamLibrary\SteamApps\common\SourceFilmmaker\game\usermod\maps\me3_apartments_sfm_v2.bsp'
            # map_path = r'G:\SteamLibrary\SteamApps\common\SourceFilmmaker\game\workshop\maps\koth_suijin.bsp'
            # map_path = r'test_data\sfm_campsite_night.bsp'
            a = BSP(map_path)
            # print(a.header)
            # for lump in a.header.lumps:
            #     print(lump)
            a.read_all()
            a.test()
            # print(a.game_header)
            # print(a.static_prop_lump.prop_num)
            # for prop in a.static_prop_lump.props:
            #     print(a.static_prop_lump.static_prop_dict.name[prop.prop_type],prop)