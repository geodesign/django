"""
Utilities for pixel data type conversions between Python, GDAL and PostGIS
"""

import struct, binascii
from math import copysign
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.gdal.driver import Driver
from django.contrib.gis.gdal.prototypes import raster as capi
from django.contrib.gis.gdal.raster import const


def convert_pixeltype(data, source, target):
    """
    Utility to convert pixel types between GDAL, PostGIS and Python Struct
    """
    if source == 'gdal':
        data = const.GDAL_PIXEL_TYPES[data]
        if target == 'postgis':
            return const.POSTGIS_PIXEL_TYPES_INV[const.GDAL_TO_POSTGIS[data]]
        elif target == 'struct':
            return const.GDAL_TO_STRUCT[data]

    elif source == 'postgis':
        data = const.POSTGIS_PIXEL_TYPES[data]
        if target == 'gdal':
            return const.GDAL_PIXEL_TYPES_INV[const.POSTGIS_TO_GDAL[data]]
        elif target == 'struct':
            return const.POSTGIS_TO_STRUCT[data]

def pack(structure, data):
    """Packs data into binary data in little endian format"""
    return binascii.hexlify(struct.pack('<' + structure, *data)).upper()

def unpack(structure, data):
    """Unpacks hexlified binary data in little endian format."""
    return struct.unpack('<' + structure, binascii.unhexlify(data))

def chunk(data, index):
    """Splits a string data into two parts at the input index"""
    return data[:index], data[index:]

def ptr_from_dict(header):
    """
    Returns pointer to a raster created from input header and the
    specified driver.
    The reqiored keys are sizex, sizey, nr_of_bands and datatype.
    Where the datatype is a gdal pixeltype as string or integer.
    """

    # If data type is provided as string, map to integer
    pixeltype = header['datatype']
    if isinstance(pixeltype, str):
        pixeltype = const.GDAL_PIXEL_TYPES_INV[pixeltype]

    # Create driver (use in-memory by default)
    driver = Driver(header.get('driver', 'MEM'))

    # Create raster from driver with input characteristics
    return capi.create_ds(driver.ptr, force_bytes(header.get('name', '')),
                          header['sizex'], header['sizey'],
                          header['nr_of_bands'], pixeltype, None)

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
