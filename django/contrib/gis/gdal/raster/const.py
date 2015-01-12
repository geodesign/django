"""
Constants for raster handling: WKB Header structure and Pixel types.
"""
from ctypes import c_byte, c_uint16, c_int16, c_uint32, c_int32, c_float,\
    c_double

"""
PostGIS Raster Header Structure
http://postgis.net/docs/doxygen/2.2/d8/d5e/structrt__raster__serialized__t.html
"""
HEADER_NAMES = [
    'endianness', 'version', 'nr_of_bands', 'scalex', 'scaley', 'originx',
    'originy', 'skewx', 'skewy', 'srid', 'sizex', 'sizey'
]

HEADER_STRUCTURE = 'B H H d d d d d d i H H'

"""
GDAL Pixel data types
http://www.gdal.org/gdal_8h.html#a22e22ce0a55036a96f652765793fb7a4
"""
GDAL_PIXEL_TYPES = {
    0:  'GDT_Unknown',  # Unknown or unspecified type 
    1:  'GDT_Byte',     # Eight bit unsigned integer
    2:  'GDT_UInt16',   # Sixteen bit unsigned integer
    3:  'GDT_Int16',    # Sixteen bit signed integer
    4:  'GDT_UInt32',   # Thirty two bit unsigned integer
    5:  'GDT_Int32',    # Thirty two bit signed integer
    6:  'GDT_Float32',  # Thirty two bit floating point
    7:  'GDT_Float64',  # Sixty four bit floating point
    8:  'GDT_CInt16',   # Complex Int16
    9:  'GDT_CInt32',   # Complex Int32
    10: 'GDT_CFloat32', # Complex Float32
    11: 'GDT_CFloat64'  # Complex Float64
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
POSTGIS Band Pixel Type 
Definitions at line 186 of file librtcore.h
http://postgis.net/docs/doxygen/2.2/d8/d4f/librtcore_8h_source.html#l00186
"""
POSTGIS_PIXEL_TYPES = {
    0:  '1BB',   # 1-bit boolean
    1:  '2BUI',  # 2-bit unsigned integer
    2:  '4BUI',  # 4-bit unsigned integer
    3:  '8BSI',  # 8-bit signed integer
    4:  '8BUI',  # 8-bit unsigned integer
    5:  '16BSI', # 16-bit signed integer
    6:  '16BUI', # 16-bit unsigned integer
    7:  '32BSI', # 32-bit signed integer
    8:  '32BUI', # 32-bit unsigned integer
    10: '32BF',  # 32-bit float
    11: '64BF',  # 64-bit float
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
Python Struct Types
https://docs.python.org/2/library/struct.html#format-characters
"""
STRUCT_SIZE = {
    'b': 1, # Signed char
    'B': 1, # Unsigned char
    '?': 1, # _Bool
    'h': 2, # Short
    'H': 2, # Unisgned short
    'i': 4, # Interger
    'I': 4, # Unsigned Integer
    'l': 4, # Long
    'L': 4, # Unsigned Long
    'f': 4, # Float
    'd': 8  # Double
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
