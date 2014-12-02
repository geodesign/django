"""
Utilities for pixel data type conversions between Python, GDAL and PostGIS
"""

import struct, binascii
from ctypes import c_byte, c_uint16, c_int16, c_uint32, c_int32, c_float,\
    c_double
from math import copysign
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.gdal.raster.driver import Driver
from django.contrib.gis.gdal.raster.prototypes import ds as capi
# TODO: Organize the utils better, maybe split into constants and functions

"""
Structure of a PostGIS Raster Header

http://postgis.net/docs/RT_ST_MakeEmptyRaster.html
http://postgis.net/docs/doxygen/2.2/d8/d5e/structrt__raster__serialized__t.html
"""

HEADER_NAMES = [
    'endianness',
    'version',
    'nr_of_bands',
    'scalex',
    'scaley',
    'originx',
    'originy',
    'skewx',
    'skewy',
    'srid',
    'sizex',
    'sizey'
]

HEADER_STRUCTURE = 'B H H d d d d d d i H H'

"""
GDAL

Pixel data types

http://www.gdal.org/gdal_8h.html#a22e22ce0a55036a96f652765793fb7a4

GDT_Unknown  - Unknown or unspecified type 
GDT_Byte     - Eight bit unsigned integer
GDT_UInt16   - Sixteen bit unsigned integer
GDT_Int16    - Sixteen bit signed integer
GDT_UInt32   - Thirty two bit unsigned integer
GDT_Int32    - Thirty two bit signed integer
GDT_Float32  - Thirty two bit floating point
GDT_Float64  - Sixty four bit floating point
GDT_CInt16   - Complex Int16
GDT_CInt32   - Complex Int32
GDT_CFloat32 - Complex Float32
GDT_CFloat64 - Complex Float64
"""

GDAL_PIXEL_TYPES = {
    0:  'GDT_Unknown',
    1:  'GDT_Byte',
    2:  'GDT_UInt16',
    3:  'GDT_Int16',
    4:  'GDT_UInt32',
    5:  'GDT_Int32',
    6:  'GDT_Float32',
    7:  'GDT_Float64',
    8:  'GDT_CInt16',
    9:  'GDT_CInt32',
    10: 'GDT_CFloat32',
    11: 'GDT_CFloat64'
}

GDAL_PIXEL_TYPES_INV = {v: k for k, v in GDAL_PIXEL_TYPES.items()}

GDAL_PIXEL_TYPES_UNISGNED = [1, 2, 4]

GDAL_TO_CTYPES = {
    0: None,
    1: c_byte,
    2: c_uint16,
    3: c_int16,
    4: c_uint32,
    5: c_int32,
    6: c_float,
    7: c_double,
    8: None,
    9: None,
    10: None,
    11: None
}

GDAL_RESAMPLE_ALGORITHMS = {
    0: 'NearestNeighbour',
    1: 'Bilinear',
    2: 'Cubic',
    3: 'CubicSpline',
    4: 'Lanczos', 
    5: 'Average',
    6: 'Mode'
}

GDAL_RESAMPLE_ALGORITHMS_INV = {v: k for k, v in GDAL_RESAMPLE_ALGORITHMS.items()}

"""
POSTGIS

Band Pixel Type definitions at line 186 of file librtcore.h
http://postgis.net/docs/doxygen/2.2/d8/d4f/librtcore_8h_source.html#l00186

Band header structure definition at line 2279 of file librtcore.h
http://postgis.net/docs/doxygen/2.2/d8/d4f/librtcore_8h_source.html#l02279

enum {
    PT_1BB=0,     /* 1-bit boolean            */
    PT_2BUI=1,    /* 2-bit unsigned integer   */
    PT_4BUI=2,    /* 4-bit unsigned integer   */
    PT_8BSI=3,    /* 8-bit signed integer     */
    PT_8BUI=4,    /* 8-bit unsigned integer   */
    PT_16BSI=5,   /* 16-bit signed integer    */
    PT_16BUI=6,   /* 16-bit unsigned integer  */
    PT_32BSI=7,   /* 32-bit signed integer    */
    PT_32BUI=8,   /* 32-bit unsigned integer  */
    PT_32BF=10,   /* 32-bit float             */
    PT_64BF=11,   /* 64-bit float             */
    PT_END=13
} rt_pixtype;

"""

POSTGIS_PIXEL_TYPES = {
    0:  '1BB',
    1:  '2BUI',
    2:  '4BUI',
    3:  '8BSI',
    4:  '8BUI',
    5:  '16BSI',
    6:  '16BUI',
    7:  '32BSI',
    8:  '32BUI',
    10: '32BF',
    11: '64BF',
    13: 'END'
}

POSTGIS_PIXEL_TYPES_INV = {v: k for k, v in POSTGIS_PIXEL_TYPES.items()}

GDAL_TO_POSTGIS = {
    'GDT_Unknown':  None,
    'GDT_Byte':     '8BUI',
    'GDT_UInt16':   '16BUI',
    'GDT_Int16':    '16BSI',
    'GDT_UInt32':   '32BUI',
    'GDT_Int32':    '32BSI',
    'GDT_Float32':  '32BF',
    'GDT_Float64':  '64BF',
    'GDT_CInt16':   None,
    'GDT_CInt32':   None,
    'GDT_CFloat32': None,
    'GDT_CFloat64': None
}

POSTGIS_TO_GDAL = {
    '1BB':   'GDT_Byte',
    '2BUI':  'GDT_Byte',
    '4BUI':  'GDT_Byte',
    '8BSI':  'GDT_Int16',
    '8BUI':  'GDT_Byte',
    '16BSI': 'GDT_Int16',
    '16BUI': 'GDT_UInt16',
    '32BSI': 'GDT_Int32',
    '32BUI': 'GDT_UInt32',
    '32BF':  'GDT_Float32',
    '64BF':  'GDT_Float64'
}

"""
PYTHON

Python Struct Types

https://docs.python.org/2/library/struct.html#format-characters

Format, C Type          Python Type Standard Size
b - signed char         integer     1
B - unsigned char       integer     1
? - _Bool               bool        1
h - short               integer     2
H - unsigned short      integer     2
i - int                 integer     4
I - unsigned int        integer     4
l - long                integer     4
L - unsigned long       integer     4
q - long long           integer     8
Q - unsigned long long  integer     8
f - float               float       4
d - double              float       8
"""

STRUCT_SIZE = {
    'b': 1,
    'B': 1,
    '?': 1,
    'h': 2,
    'H': 2,
    'i': 4,
    'I': 4,
    'l': 4,
    'L': 4,
    'f': 4,
    'd': 8
}

GDAL_TO_STRUCT = {
    'GDT_Unknown':  None,
    'GDT_Byte':     'B',
    'GDT_UInt16':   'H',
    'GDT_Int16':    'h',
    'GDT_UInt32':   'L',
    'GDT_Int32':    'l',
    'GDT_Float32':  'f',
    'GDT_Float64':  'd',
    'GDT_CInt16':   None,
    'GDT_CInt32':   None,
    'GDT_CFloat32': None,
    'GDT_CFloat64': None
}

POSTGIS_TO_STRUCT = {
    '1BB':   '?',
    '2BUI':  'B',
    '4BUI':  'B',
    '8BSI':  'b',
    '8BUI':  'B',
    '16BSI': 'h',
    '16BUI': 'H',
    '32BSI': 'l',
    '32BUI': 'L',
    '32BF':  'f',
    '64BF':  'd'
}

# Data conversion methods
def convert_pixeltype(data, source, target):
    """
    Utility to convert pixel types between GDAL, PostGIS and Python Struct
    """
    if source == 'gdal':
        data = GDAL_PIXEL_TYPES[data]
        if target == 'postgis':
            return POSTGIS_PIXEL_TYPES_INV[GDAL_TO_POSTGIS[data]]
        elif target == 'struct':
            return GDAL_TO_STRUCT[data]

    elif source == 'postgis':
        data = POSTGIS_PIXEL_TYPES[data]
        if target == 'gdal':
            return GDAL_PIXEL_TYPES_INV[POSTGIS_TO_GDAL[data]]
        elif target == 'struct':
            return POSTGIS_TO_STRUCT[data]

def pack(structure, data):
    """Packs data into binary data in little endian format"""
    return binascii.hexlify(struct.pack('<' + structure, *data)).upper()

def unpack(structure, data):
    """Unpacks hexlified binary data in little endian format."""
    return struct.unpack('<' + structure, binascii.unhexlify(data))

def chunk(data, index):
    """Splits string data into two halfs at the input index"""
    return data[:index], data[index:]

def ptr_from_dict(header, driver='MEM'):
    """
    Returns pointer to a raster created from input header and the
    specified driver.
    The reqiored keys are sizex, sizey, nr_of_bands and datatype.
    Where the datatype is a gdal pixeltype as string or integer.
    """

    # If data type is provided as string, map to integer
    pixeltype = header['datatype']
    if isinstance(pixeltype, str):
        pixeltype = GDAL_PIXEL_TYPES_INV[pixeltype]

    # Create driver (use in-memory by default)
    driver = Driver(header.get('driver', 'MEM'))

    # Create raster from driver with input characteristics
    return capi.create_ds(driver.ptr, force_bytes(header.get('name', '')),
                          header['sizex'], header['sizey'],
                          header['nr_of_bands'], pixeltype, None)

def parse_wkb(data):
    """
    Parses a PostGIS WKB Raster String. Returns the raster header data as
    a dict and the bands as a list.
    """
    # Split raster header from data
    header, data = chunk(data, 122)

    # Process header
    header = unpack(HEADER_STRUCTURE, header)
    header = dict(zip(HEADER_NAMES, header))

    nr_of_pixels = header['sizex'] * header['sizey']

    # Process bands
    bands = []

    # Parse band data
    while data:
        # Get pixel type for this band
        pixeltype, data = chunk(data, 2)
        pixeltype = unpack('B', pixeltype)[0]

        # Substract nodata byte from band nodata value if exists
        has_nodata = pixeltype >= 64
        if has_nodata:
            pixeltype -= 64

        # String with hex type name for unpacking
        pack_type = convert_pixeltype(pixeltype, 'postgis', 'struct')

        # Length in bytes of the hex type
        pixeltype_len = STRUCT_SIZE[pack_type]

        # Get band nodata value if exists
        if has_nodata:
            nodata, data = chunk(data, 2 * pixeltype_len)
            nodata = unpack(pack_type, nodata)[0]
        else:
            nodata = None

        # PostGIS datatypes mapped to Gdalconstants data types
        pixtype_gdal = convert_pixeltype(pixeltype, 'postgis', 'gdal')

        # Chunk and unpack band data
        band, data = chunk(data, 2 * pixeltype_len * nr_of_pixels)
        bands.append({'type': pixtype_gdal, 'nodata': nodata,
                      'data': binascii.unhexlify(band)})

    # Check that all bands have the same pixeltype
    if len(set([x['type'] for x in bands])) != 1:
        raise ValidationError("Band pixeltypes are not all equal.")
    else:
        header['datatype'] = bands[0]['type']

    return header, bands

def transform_coords(originx, originy, srid_src, srid_dest):
    "Transforms input coordinates from source srid to destination srid"
    # Create ogr point geometry from input
    point = 'POINT ({0} {1})'.format(repr(originx),
                                     repr(originy))
    point = OGRGeometry(point, srid_src)

    # Transform point into new projection
    point.transform(srid_dest)

    # Return coordinates
    return point.x, point.y

def calculate_scale(rast, srid_dest, squared_pixel=True):
    """
    Returns the scale of the raster in a given coordinate system. The scale is
    calculated over the size of the raster, assuming the pixel size is kept the
    same. The squared_pixel flag indicates if the absolute value of the xscale
    and the yscale should be the same, i.e. to have squared pixels in the new
    projection.
    """
    # Calculate origin point in new coordinates
    point_a = 'POINT ({0} {1})'.format(repr(rast.originx),
                                       repr(rast.originy))
    point_a = OGRGeometry(point_a, rast.srid)
    point_a.transform(srid_dest)

    # Calculate lower right corner point in new coordinates
    point_b = 'POINT ({0} {1})'.format(repr(rast.originx + rast.scalex*rast.sizex),
                                       repr(rast.originy + rast.scaley*rast.sizey))
    point_b = OGRGeometry(point_b, rast.srid)
    point_b.transform(srid_dest)

    # Calculate scales
    scalex = abs(point_a.x - point_b.x)/rast.sizex
    scaley = abs(point_a.y - point_b.y)/rast.sizey

    # If squared pixel is requested, make scales equal, keeping the larger
    # values to assure that the new raster overlays the old one if the 
    # number of pixels is kept the same.
    if squared_pixel:
        if abs(scalex) > abs(scaley):
            scaley = scalex
        else:
            scalex = scaley

    # Assure scale signs are the same
    scaley = copysign(scalex, rast.scalex)
    scaley = copysign(scaley, rast.scaley)

    return scalex, scaley
