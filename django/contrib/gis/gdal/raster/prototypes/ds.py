"""
 This module houses the ctypes function prototypes for GDAL DataSource
 related data structures.
"""
from ctypes import c_char_p, c_double, c_int, c_long, c_void_p, POINTER
from django.contrib.gis.gdal.libgdal import lgdal
from django.contrib.gis.gdal.prototypes.generation import (const_string_output,
    double_output, geom_output, int_output, srs_output, void_output, voidptr_output)

c_int_p = POINTER(c_int)  # shortcut type

# For more detail about c function names etc, see
# http://gdal.org/gdal_8h.html

### Driver Routines ###
register_all = void_output(lgdal.GDALAllRegister, [])
get_driver = voidptr_output(lgdal.GDALGetDriver, [c_int])
get_driver_by_name = voidptr_output(lgdal.GDALGetDriverByName, [c_char_p])
get_driver_count = int_output(lgdal.GDALGetDriverCount, [])
get_driver_description = const_string_output(lgdal.GDALGetDescription, [])

### DataSource ###
create_ds = voidptr_output(lgdal.GDALCreate, [c_void_p, c_char_p, c_int, c_int, c_int, c_int])
open_ds = voidptr_output(lgdal.GDALOpen, [c_char_p, c_int])
close_ds = void_output(lgdal.GDALClose, [c_void_p])
add_band_ds = void_output(lgdal.GDALAddBand, [c_void_p, c_int])
get_ds_description = const_string_output(lgdal.GDALGetDescription, [])
get_ds_driver = voidptr_output(lgdal.GDALGetDatasetDriver, [c_void_p])
get_ds_xsize = int_output(lgdal.GDALGetRasterXSize, [c_void_p])
get_ds_ysize = int_output(lgdal.GDALGetRasterYSize, [c_void_p])
get_ds_raster_count = int_output(lgdal.GDALGetRasterCount, [c_void_p])
get_ds_raster_band = voidptr_output(lgdal.GDALGetRasterBand, [c_void_p, c_int])
get_ds_projection_ref = const_string_output(lgdal.GDALGetProjectionRef, [c_void_p])
set_ds_projection = void_output(lgdal.GDALSetProjection, [c_char_p])
# get_ds_geotransform = voidptr_output(lgdal.GDALGetGeoTransform, [c_void_p, c_void_p])
# set_ds_geotransform = voidptr_output(lgdal.GDALSetGeoTransform, [c_void_p])
set_ds_projection = void_output(lgdal.GDALSetProjection, [c_char_p])

### Raster Band Routines ###
get_band_xsize = int_output(lgdal.GDALGetRasterBandXSize, [c_void_p])
get_band_ysize = int_output(lgdal.GDALGetRasterBandYSize, [c_void_p])
get_band_index = int_output(lgdal.GDALGetBandNumber, [c_void_p])
get_band_description = const_string_output(lgdal.GDALGetDescription, [c_void_p])
get_band_ds = voidptr_output(lgdal.GDALGetBandDataset, [c_void_p])
#get_band_datatype = voidptr_output(lgdal.GDALGetRasterDataType, [])
get_band_nodata_value = double_output(lgdal.GDALGetRasterNoDataValue, [c_void_p, c_int])
#set_band_nodata_value = void_output(lgdal.GDALSetRasterNoDataValue, [c_double])
get_band_minimum = double_output(lgdal.GDALGetRasterMinimum, [c_void_p, c_int])
get_band_maximum = double_output(lgdal.GDALGetRasterMaximum, [c_void_p, c_int])
get_band_offset = double_output(lgdal.GDALGetRasterOffset, [c_void_p, c_int])
get_band_scale = double_output(lgdal.GDALGetRasterScale, [c_void_p, c_int])
get_band_unit_type = const_string_output(lgdal.GDALGetRasterUnitType, [c_void_p, c_int])
