import math
from enum import IntEnum
from pprint import pformat
from typing import List

try:
    from .ByteIO import ByteIO
except:
    from ByteIO import ByteIO

####### DEFINES #######

HEADER_LUMPS = 64
SURF_LIGHT = 0x1  # value will hold the light strength
SURF_SKY2D = 0x2  # don't draw, indicates we should skylight + draw 2d sky but not draw the 3D skybox
SURF_SKY = 0x4  # don't draw, but add to skybox
SURF_WARP = 0x8  # turbulent water warp
SURF_TRANS = 0x10  # texture is translucent
SURF_NOPORTAL = 0x20  # the surface can not have a portal placed on it
SURF_TRIGGER = 0x40  # FIXME: This is an xbox hack to work around elimination of trigger surfaces, which breaks occluders
SURF_NODRAW = 0x80  # don't bother referencing the texture
SURF_HINT = 0x100  # make a primary bsp splitter
SURF_SKIP = 0x200  # completely ignore, allowing non-closed brushes
SURF_NOLIGHT = 0x400  # Don't calculate light
SURF_BUMPLIGHT = 0x800  # calculate three lightmaps for the surface for bumpmapping
SURF_NOSHADOWS = 0x1000  # Don't receive shadows
SURF_NODECALS = 0x2000  # Don't receive decals
SURF_NOCHOP = 0x4000  # Don't subdivide patches on this surface
SURF_HITBOX = 0x8000  # surface is part of a hitbox


class SettingContainer:
    settings = {}

    @classmethod
    def update_settings(cls, **kwargs):
        cls.settings.update(kwargs)


class LUMP_ENUM(IntEnum):
    LUMP_ENTITIES = 0
    LUMP_PLANES = 1
    LUMP_TEXDATA = 2
    LUMP_VERTEXES = 3
    LUMP_VISIBILITY = 4
    LUMP_NODES = 5
    LUMP_TEXINFO = 6
    LUMP_FACES = 7
    LUMP_LIGHTING = 8
    LUMP_OCCLUSION = 9
    LUMP_LEAFS = 10
    LUMP_FACEIDS = 11
    LUMP_EDGES = 12
    LUMP_SURFEDGES = 13
    LUMP_MODELS = 14
    LUMP_WORLDLIGHTS = 15
    LUMP_LEAFFACES = 16
    LUMP_LEAFBRUSHES = 17
    LUMP_BRUSHES = 18
    LUMP_BRUSHSIDES = 19
    LUMP_AREAS = 20
    LUMP_AREAPORTALS = 21
    LUMP_PROPCOLLISION = 22
    LUMP_PROPHULLS = 23
    LUMP_PROPHULLVERTS = 24
    LUMP_PROPTRIS = 25
    LUMP_DISPINFO = 26
    LUMP_ORIGINALFACES = 27
    LUMP_PHYSDISP = 28
    LUMP_PHYSCOLLIDE = 29
    LUMP_VERTNORMALS = 30
    LUMP_VERTNORMALINDICES = 31
    LUMP_DISP_LIGHTMAP_ALPHAS = 32
    LUMP_DISP_VERTS = 33
    LUMP_DISP_LIGHTMAP_SAMPLE_POSITIONS = 34
    LUMP_GAME_LUMP = 35
    LUMP_LEAFWATERDATA = 36
    LUMP_TEXDATA_STRING_DATA = 44
    LUMP_TEXDATA_STRING_TABLE = 43
    LUMP_UNKNOWN = -1
    # @classmethod
    # def _missing_(cls,*args):
    #     return cls.LUMP_UNKNOWN


class emittype_t(IntEnum):
    emit_surface = 0  # 90 degree spotlight
    emit_point = 1  # simple point light source
    emit_spotlight = 2  # spotlight with penumbra
    emit_skylight = 3  # directional light with no falloff (surface must trace to SKY texture)
    emit_quakelight = 4  # linear falloff, non-lambertian
    emit_skyambient = 5  # spherical light source with no falloff (surface must trace to SKY texture)


class Header(SettingContainer):

    def __init__(self):
        self.ident = ''
        self.version = 0
        self.lumps = []  # type: List[Lump]
        self.mapRevision = 0

    def __repr__(self):
        return "<BSP header ident:{} version:{} map revision:{}>".format(self.ident, self.version, self.mapRevision)

    def read(self, reader: ByteIO):
        self.ident = reader.read_fourcc()
        self.version = reader.read_int32()
        self.update_settings(BSP_VERSION=self.version)
        self.lumps = [Lump(i).read(reader) for i in range(64)]
        self.mapRevision = reader.read_int32()
        return self


class Lump(SettingContainer):
    def __init__(self, nid):
        self.offset = 0
        self.length = 0
        self.version = 0
        self.fourCC = []  # type: List[str]*4
        try:
            self.id = LUMP_ENUM(nid)
        except:
            self.id = nid

    def __repr__(self):
        return "<BSP {} lump offset:{} length:{} version:{} >".format(self.id.name, self.offset, self.length,
                                                                      self.version)

    def read(self, reader: ByteIO):
        self.offset = reader.read_int32()
        self.length = reader.read_int32()
        self.version = reader.read_int32()
        self.fourCC = reader.read_fourcc()
        return self


class Dummy(SettingContainer):
    size = 4
    bsp = None

    def read(self, reader: ByteIO):
        raise NotImplementedError()

    def __repr__(self):
        template = "<{} {}>"
        member_template = "{}:{}"
        members = []
        for key, item in self.__dict__.items():
            members.append(member_template.format(key, item))
        return template.format(type(self).__name__, " ".join(members))


class SourceVector(Dummy):
    def __init__(self, init_vec=None):
        if init_vec:
            self.x, self.y, self.z = init_vec
        else:
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0

    def read(self, reader: ByteIO):
        self.x, self.y, self.z = reader.read_fmt('fff')

        return self

    def __add__(self, other):
        return SourceVector([self.x + other.x, self.y + other.y, self.z + other.z])

    def __sub__(self, other):
        return SourceVector([self.x - other.x, self.y - other.y, self.z - other.z])

    def to_rotation(self):
        x = 90 * self.x
        y = 90 * self.y
        z = 90 * self.z

        return SourceVector((x, y, z))

    @property
    def as_list(self):
        return [self.x, self.y, self.z]

    @property
    def as_string_smd(self):
        return "{:.6f} {:.6f} {:.6f}".format(self.x, self.y, self.z)

    def as_rounded(self, n):
        return "{} {} {}".format(round(self.x, n), round(self.y, n), round(self.z, n))

    @property
    def as_string(self):
        return " X:{} Y:{} Z:{}".format(self.x, self.y, self.z)

    def __str__(self):
        return "<Vector 3D X:{} Y:{} Z:{}".format(round(self.x, 3), round(self.y, 3), round(self.z, 3))

    def __repr__(self):
        return "<Vector 3D X:{} Y:{} Z:{}".format(round(self.x, 3), round(self.y, 3), round(self.z, 3))


class Plane(Dummy):
    size = 20

    def __init__(self):
        self.normal = SourceVector()
        self.dist = 0.0
        self.type = 0

    def read(self, reader: ByteIO):
        self.normal.read(reader)
        self.dist = reader.read_float()
        self.type = reader.read_int32()

    def __repr__(self):
        return "<Plane normal:{} dist:{} type:{}>".format(self.normal.as_string, self.dist, self.type)


class Edge(Dummy):
    size = 4

    def __init__(self):
        self.v = []

    def read(self, reader: ByteIO):
        self.v = [reader.read_uint16(), reader.read_uint16()]


class VertexNormal(Dummy):
    size = 2

    def __init__(self):
        self.v = 0

    def read(self, reader: ByteIO):
        self.v = reader.read_uint16()

    def __repr__(self):
        return '<Normal index:{}>'.format(self.v)


class SurfEdge(Dummy):
    size = 4

    def __init__(self):
        self.surf_edge = 0

    def read(self, reader: ByteIO):
        self.surf_edge = reader.read_int32()


class Face(Dummy):
    size = 56

    def __init__(self):
        self.plane_num = 0
        self.side = 0
        self.on_node = 0
        self.firstedge = 0
        self.numedges = 0
        self.texinfo = 0
        self.dispinfo = 0
        self.surface_fog_volume_id = 0
        self.styles = []
        self.light_offset = 0
        self.area = 0.0
        self.lightmap_texture_mins_in_luxels = []
        self.lightmap_texture_size_in_luxels = []
        self.orig_face = 0
        self.num_prims = 0
        self.first_prim_id = 0
        self.smoothing_groups = 0

    def read(self, reader: ByteIO):
        self.plane_num = reader.read_uint16()
        self.side = reader.read_uint8()
        self.on_node = reader.read_uint8()
        self.firstedge = reader.read_int32()
        self.numedges = reader.read_int16()
        self.texinfo = reader.read_int16()
        self.dispinfo = reader.read_int16()
        self.surface_fog_volume_id = reader.read_int16()
        self.styles = [reader.read_int8() for _ in range(4)]
        self.light_offset = reader.read_int32()
        self.area = reader.read_float()
        self.lightmap_texture_mins_in_luxels = [reader.read_int32() for _ in range(2)]
        self.lightmap_texture_size_in_luxels = [reader.read_int32() for _ in range(2)]
        self.orig_face = reader.read_int32()
        self.num_prims = reader.read_uint16()
        self.first_prim_id = reader.read_uint16()
        self.smoothing_groups = reader.read_uint32()


class Brush(Dummy):
    size = 12

    def __init__(self):
        self.first_side = 0
        self.num_sides = 0
        self.contents = 0

    def read(self, reader: ByteIO):
        self.first_side = reader.read_int32()
        self.num_sides = reader.read_int32()
        self.contents = reader.read_int32()


class BrushSide(Dummy):
    size = 8

    def __init__(self):
        self.plane_num = 0
        self.texinfo = 0
        self.dispinfo = 0
        self.bevel = 0

    def read(self, reader: ByteIO):
        self.plane_num = reader.read_int16()
        self.texinfo = reader.read_int16()
        self.dispinfo = reader.read_int16()
        self.bevel = reader.read_int16()


class Model(Dummy):
    size = 48

    def __init__(self):
        self.mins = SourceVector()
        self.maxs = SourceVector()
        self.origin = SourceVector()
        self.head_node = 0
        self.first_face = 0
        self.num_faces = 0

    def read(self, reader: ByteIO):
        self.mins.read(reader)
        self.maxs.read(reader)
        self.origin.read(reader)
        self.head_node = reader.read_int32()
        self.first_face = reader.read_int32()
        self.num_faces = reader.read_int32()


class TextureVector(Dummy):
    size = 16

    def __init__(self):
        self.xyz = SourceVector()
        self.offset = 0

    def read(self, reader: ByteIO):
        self.xyz.read(reader)
        self.offset = reader.read_float()
        return self


class TextureInfo(Dummy):
    size = 72

    def __init__(self):
        self.texture_vectors = []  # type: List[TextureVector]
        self.lightmap_vectors = []  # type: List[TextureVector]
        self.flags = 0
        self.texdata = 0

    def read(self, reader: ByteIO):
        self.texture_vectors = [TextureVector().read(reader), TextureVector().read(reader)]
        self.lightmap_vectors = [TextureVector().read(reader), TextureVector().read(reader)]
        self.flags = reader.read_int32()
        self.texdata = reader.read_int32()


class TextureData(Dummy):
    size = 32

    def __init__(self):
        self.reflectivity = SourceVector()
        self.name_id = 0
        self.width = 0
        self.height = 0
        self.view_width = 0
        self.view_height = 0

    def read(self, reader: ByteIO):
        self.reflectivity.read(reader)
        self.name_id = reader.read_int32()
        self.width = reader.read_int32()
        self.height = reader.read_int32()
        self.view_width = reader.read_int32()
        self.view_height = reader.read_int32()


class TexdataStringData(Dummy):
    size = 4

    def __init__(self):
        self.texdata_string_data = 0

    def read(self, reader: ByteIO):
        self.texdata_string_data = reader.read_int32()


# struct dnode_t
# {
# 	int			planenum;
# 	int			children[2];	// negative numbers are -(leafs+1), not nodes
# 	short		mins[3];		// for frustom culling
# 	short		maxs[3];
# 	unsigned short	firstface;
# 	unsigned short	numfaces;	// counting both sides
# 	short			area;		// If all leaves below this node are in the same area, then
# 								// this is the area index. If not, this is -1.
# };
class Node(Dummy):
    size = 32

    def __init__(self):
        self.plane_count = 0
        self.childrens = []  # type: List[Node]
        self.mins = []  # type: List[int]
        self.maxs = []  # type: List[int]
        self.first_face = 0
        self.face_count = 0
        self.area = 0

    def read(self, reader: ByteIO):
        self.plane_count = reader.read_int32()  # 4
        self.childrens = [reader.read_int32(), reader.read_int32()]  # 8 12
        self.mins = [reader.read_int16() for _ in range(3)]  # 6
        self.maxs = [reader.read_int16() for _ in range(3)]  # 6
        self.first_face = reader.read_uint16()  # 2
        self.face_count = reader.read_uint16()  # 2
        self.area = reader.read_int16()  # 2


class EmitType(IntEnum):
    emit_surface = 0  # 90 degree spotlight
    emit_point = 1  # simple point light source
    emit_spotlight = 2  # spotlight with penumbra
    emit_skylight = 3  # directional light with no falloff (surface must trace to SKY texture)
    emit_quakelight = 4  # linear falloff, non-lambertian
    emit_skyambient = 5  # spherical light source with no falloff (surface must trace to SKY texture)


class color32(Dummy):
    size = 12

    def __init__(self):
        self.r, self.g, self.b, self.a = 1, 1, 1, 1

    @staticmethod
    def from_array(rgba):
        color = color32()
        if len(rgba) >= 4:
            color.r, color.g, color.b, color.a = rgba
        color.r, color.g, color.b = rgba
        return color

    def read(self, reader: ByteIO):
        self.r, self.g, self.b = reader.read_fmt('fff')
        return self

    def magnitude(self):
        magn = math.sqrt(self.r ** 2 + self.g ** 2 + self.b ** 2)
        return magn

    def normalize(self):
        magn = self.magnitude()
        if magn == 0:
            return self
        self.r = self.r / magn
        self.g = self.g / magn
        self.b = self.b / magn
        return self

    @property
    def as_normalized(self):
        magn = self.magnitude()
        if magn == 0:
            return self
        r = self.r / magn
        g = self.g / magn
        b = self.b / magn
        return "<Color R:{} G:{} B:{}>".format(r, g, b)

    @property
    def to_array_rgba(self):
        return self.r, self.g, self.b, self.a

    @property
    def to_array_rgb(self):
        return self.r, self.g, self.b


class WorldLight(Dummy):
    # size = 88

    def __init__(self):
        self.origin = SourceVector()
        self.intensity = color32()
        self.normal = SourceVector()
        self.shadow_cast_offset = SourceVector()
        self.cluster = 0
        self.type = []
        self.style = 0
        self.stopdot = 0.0
        self.stopdot2 = 0.0
        self.exponent = 0.0
        self.radius = 0.0
        self.constant_attn = 0.0
        self.linear_attn = 0.0
        self.quadratic_attn = 0.0
        self.flags = 0
        self.texinfo = 0
        self.owner = 0

    #
    # def __repr__(self):
    #     return "<World light origin:{} intensity:{} normal:{} radius:{}>".format(self.origin.as_string,self.intensity.as_normalized,self.normal.to_rotation().as_string,self.radius)

    @property
    def size(self):
        if self.bsp.version > 20:
            return 100
        else:
            return 88

    def read(self, reader: ByteIO):
        self.origin.read(reader)
        self.intensity.read(reader)
        self.normal.read(reader)
        if self.bsp.version > 20:
            self.shadow_cast_offset.read(reader)
        self.cluster = reader.read_int32()
        self.type = EmitType(reader.read_int32())
        self.style = reader.read_int32()
        self.stopdot = reader.read_float()
        self.stopdot2 = reader.read_float()
        self.exponent = reader.read_float()
        self.radius = reader.read_float()
        self.constant_attn = reader.read_float()
        self.linear_attn = reader.read_float()
        self.quadratic_attn = reader.read_float()
        self.flags = reader.read_int32()
        self.texinfo = reader.read_int32()
        self.owner = reader.read_int32()
        return self


class DispInfo(Dummy):
    size = 176

    def __init__(self):
        self.start_position = SourceVector()
        self.disp_vert_start = 0
        self.disp_tri_start = 0
        self.power = 0
        self.min_tess = 0
        self.smoothing_angle = .0
        self.contents = 0
        self.map_face = 0
        self.lightmap_alpha_start = 0
        self.lightmap_sample_position_start = 0
        self.displace_neighbors = []  # type: List[DispNeighbor]
        self.displace_corner_neighbors = []  # type: List[DisplaceCornerNeighbors]
        self.allowed_verts = []  # type: List[int]

    def read(self, reader: ByteIO):
        self.start_position.read(reader)
        self.disp_vert_start = reader.read_uint32()
        self.disp_tri_start = reader.read_uint32()
        self.power = reader.read_uint32()
        self.min_tess = reader.read_uint32()
        self.smoothing_angle = reader.read_float()
        self.contents = reader.read_uint32()
        self.map_face = reader.read_uint16()
        self.lightmap_alpha_start = reader.read_uint32()
        self.lightmap_sample_position_start = reader.read_uint32()
        for _ in range(4):
            disp_neighbor = DispNeighbor()
            disp_neighbor.read(reader)
            self.displace_neighbors.append(disp_neighbor)
        for _ in range(4):
            displace_corner_neighbors = DisplaceCornerNeighbors()
            displace_corner_neighbors.read(reader)
            self.displace_corner_neighbors.append(displace_corner_neighbors)
        reader.skip(6)
        self.allowed_verts = [reader.read_uint32() for _ in range(10)]



    def __str__(self):
        return pformat(self.__dict__, width=250, depth=8)

    def __repr__(self):
        return pformat(self.__dict__, width=250, depth=8)

    @property
    def get_power_size(self):
        return 1 << self.power

    @property
    def vertex_count(self):
        return (self.get_power_size + 1) * (self.get_power_size + 1)

    @property
    def triangle_tag_count(self):
        return 2 * self.power * self.power


class DispVert(Dummy):
    size = 20

    # {
    # public:
    # 	DECLARE_BYTESWAP_DATADESC();
    # 	Vector		m_vVector;		// Vector field defining displacement volume.
    # 	float		m_flDist;		// Displacement distances.
    # 	float		m_flAlpha;		// "per vertex" alpha values.
    # };
    def __init__(self):
        self.vector = SourceVector()
        self.dist = 0.0
        self.alpha = 0.0

    def read(self, reader: ByteIO):
        self.vector.read(reader)
        self.dist = reader.read_float()
        self.alpha = reader.read_float()

    def __str__(self):
        return pformat(self.__dict__, width=250, depth=8)

    def __repr__(self):
        return pformat(self.__dict__, width=250, depth=8)


class DispSubNeighbor(Dummy):
    size = 5

    # struct CDispSubNeighbor
    # {
    # public:
    # 	DECLARE_BYTESWAP_DATADESC();
    # 	unsigned short		GetNeighborIndex() const		{ return m_iNeighbor; }
    # 	NeighborSpan		GetSpan() const					{ return (NeighborSpan)m_Span; }
    # 	NeighborSpan		GetNeighborSpan() const			{ return (NeighborSpan)m_NeighborSpan; }
    # 	NeighborOrientation	GetNeighborOrientation() const	{ return (NeighborOrientation)m_NeighborOrientation; }
    #
    # 	bool				IsValid() const				{ return m_iNeighbor != 0xFFFF; }
    # 	void				SetInvalid()				{ m_iNeighbor = 0xFFFF; }
    #
    #
    # public:
    # 	unsigned short		m_iNeighbor;		// This indexes into ddispinfos.
    # 											// 0xFFFF if there is no neighbor here.
    #
    # 	unsigned char		m_NeighborOrientation;		// (CCW) rotation of the neighbor wrt this displacement.
    #
    # 	// These use the NeighborSpan type.
    # 	unsigned char		m_Span;						// Where the neighbor fits onto this side of our displacement.
    # 	unsigned char		m_NeighborSpan;				// Where we fit onto our neighbor.
    # };
    def __init__(self):
        self.neighbor = 0
        self.neighbor_orientation = 0
        self.span = 0
        self.neighbor_span = 0

    def read(self, reader: ByteIO):
        self.neighbor = reader.read_uint16()
        self.neighbor_orientation = reader.read_uint8()
        self.span = reader.read_uint8()
        reader.skip(1)
        self.neighbor_span = reader.read_uint8()

    def __str__(self):
        return pformat(self.__dict__, width=250, depth=8)

    def __repr__(self):
        return pformat(self.__dict__, width=250, depth=8)


class DispNeighbor(Dummy):
    def __init__(self):
        self.sub_neighbors = []  # type: List[DispSubNeighbor]

    def read(self,reader:ByteIO):
        for _ in range(2):
            sub_neighbor = DispSubNeighbor()
            sub_neighbor.read(reader)
            self.sub_neighbors.append(sub_neighbor)

    def __str__(self):
        return pformat(self.__dict__, width=250, depth=8)

    def __repr__(self):
        return pformat(self.__dict__, width=250, depth=8)


class DisplaceCornerNeighbors(Dummy):
    def __init__(self):
        self.neighbor_indices = [None] * 4  # type: List[int]
        self.neighbor_count = 0

    def read(self, reader: ByteIO):
        self.neighbor_indices = reader.read_fmt('H'*4)
        self.neighbor_count = reader.read_uint8()

    def __str__(self):
        return pformat(self.__dict__, width=250, depth=8)

    def __repr__(self):
        return pformat(self.__dict__, width=250, depth=8)


class GameLumpHeader(Dummy):
    def __init__(self):
        self.lump_count = 0
        self.game_lumps = []  # type: List[GameLump]

    def read(self, reader: ByteIO):
        self.lump_count = reader.read_int32()
        self.game_lumps = [GameLump().read(reader) for _ in range(self.lump_count)]
        return self


class GameLump(Dummy):

    def __init__(self):
        self.id = ""
        self.flags = 0
        self.version = 0
        self.offset = 0
        self.size = 0

    def read(self, reader: ByteIO):
        self.id = reader.read_ascii_string(4)
        self.flags = reader.read_uint16()
        self.version = reader.read_uint16()
        self.offset = reader.read_int32()
        self.size = reader.read_int32()
        return self


class StaticPropLump(Dummy):
    def __init__(self):
        self.static_prop_dict = StaticPropDict()
        self.static_prop_leaf = StaticPropLeaf()
        self.prop_num = 0
        self.props = []  # type: List[StaticProp]

    def read(self, reader: ByteIO, version=0, size=0):
        start = reader.tell()
        self.static_prop_dict.read(reader)
        self.static_prop_leaf.read(reader)
        self.prop_num = reader.read_int32()
        if self.prop_num > 0:
            print("Reading {} static props".format(self.prop_num))
            prop_size = (size - (reader.tell() - start)) // self.prop_num
            # print('sizeof(StaticProp) = {}'.format(prop_size))
            self.props = [StaticProp().read(reader, version, prop_size) for _ in range(self.prop_num)]
            # print(reader.tell())


class StaticPropDict(Dummy):
    def __init__(self):
        self.dict_entries = 0
        self.name = []  # type: List[str]

    def read(self, reader: ByteIO):
        self.dict_entries = reader.read_int32()
        self.name = [reader.read_ascii_string(128) for _ in range(self.dict_entries)]


class StaticPropLeaf(Dummy):
    def __init__(self):
        self.leaf_entries = 0
        self.leaf = []  # type: List[int]

    def read(self, reader: ByteIO):
        self.leaf_entries = reader.read_int32()
        self.name = [reader.read_uint16() for _ in range(self.leaf_entries)]


class StaticProp(Dummy):
    def __init__(self):
        self.origin = SourceVector()
        self.angles = SourceVector()
        self.prop_type = 0
        self.first_leaf = 0
        self.leaf_count = 0
        self.solid = 0
        self.flags = 0
        self.skin = 0
        self.fade_min_dist = 0
        self.fade_max_dist = 0
        self.lighting_origin = SourceVector()
        self.forced_fade_scale = 0
        self.min_dx_level = 0
        self.max_dx_level = 0
        self.min_cpu_level = 0
        self.max_cpu_level = 0
        self.min_gpu_level = 0
        self.max_gpu_level = 0
        self.diffuse_modulation = color32()
        self.unknown = 0
        self.disable_x360 = 0

    def read(self, reader: ByteIO, version=0, size=0):
        s = reader.tell()
        self.origin.read(reader)
        self.angles.read(reader)
        self.prop_type = reader.read_uint16()
        self.first_leaf = reader.read_uint16()
        self.leaf_count = reader.read_uint16()
        self.solid = reader.read_uint8()
        self.flags = reader.read_uint8()
        self.skin = reader.read_int32()
        self.fade_min_dist = reader.read_float()
        self.fade_max_dist = reader.read_float()
        self.lighting_origin.read(reader)
        if version >= 5:
            self.forced_fade_scale = reader.read_float()
        if version == 6 or version == 7:
            self.min_dx_level = reader.read_uint16()
            self.max_dx_level = reader.read_uint16()
        if version >= 8:
            self.min_cpu_level = reader.read_uint8()
            self.max_cpu_level = reader.read_uint8()
            self.min_gpu_level = reader.read_uint8()
            self.max_gpu_level = reader.read_uint8()
        if version >= 7 and size > 72:
            self.diffuse_modulation.read(reader)
        if version >= 10:
            self.unknown = reader.read_float()
        if version >= 9:
            self.disable_x360 = reader.read_uint8()
        # print('sizeof = {}'.format(reader.tell()-s))
        reader.seek(s + size)
        return self
