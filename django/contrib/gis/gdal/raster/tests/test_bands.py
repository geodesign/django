import os
import unittest
from unittest import skipUnless

from django.contrib.gis.gdal import HAS_GDAL
from django.contrib.gis.geometry.test_data import get_ds_file, TestDS, TEST_DATA

if HAS_GDAL:
    from django.contrib.gis.gdal.raster.rasters import GDALRaster

valid_data_types = [
    'GDT_Byte', 'GDT_UInt16', 'GDT_Int16', 'GDT_UInt32',
    'GDT_Int32', 'GDT_Float32', 'GDT_Float64', 'GDT_CInt16', 'GDT_CInt32',
    'GDT_CFloat32', 'GDT_CFloat64'
]

invalid_data_types = ['abc']

from ctypes import c_char_p, c_double, c_int, c_long, c_void_p, POINTER, byref
from django.contrib.gis.gdal.libgdal import lgdal
from django.contrib.gis.gdal.prototypes.generation import (const_string_output,
    double_output, geom_output, int_output, srs_output, void_output, voidptr_output)

c_int_p = POINTER(c_int)  # shortcut type
c_double_p6 = POINTER(c_double*6)

@skipUnless(HAS_GDAL, "GDAL is required")
class RasterGDALBandDataTest(unittest.TestCase):

    def test_sizex(self):
        "Testing size property of raster bands."
        ds = GDALRaster({
            'sizex': 11, 'sizey': 12, 'nr_of_bands': 3, 'datatype': 1})
        for band in ds:
            self.assertEqual(11, band.sizex)
            self.assertEqual(12, band.sizey)

    def test_nodata_value(self):
        "Set setting and getting nodata value for band"
        ds = GDALRaster({
            'sizex': 11, 'sizey': 12, 'nr_of_bands': 1, 'datatype': 1})
        bnd = ds[0]
        self.assertEqual(None, bnd.nodata_value)
        bnd.nodata_value = 1.23
        self.assertEqual(1.23, bnd.nodata_value)

    def test_data_io(self):
        "Tests getting and setting complete raster data"
        ds = GDALRaster({
            'sizex': 4, 'sizey': 4, 'nr_of_bands': 1, 'datatype': 1})

        band = ds[0]
        band.data = [1,2,3,4] * (band.nr_of_pixels / 4)
        self.assertEqual(set([1, 2, 3, 4]), set(band.data))

        band.data = [1] * band.nr_of_pixels
        self.assertEqual(set([1]), set(band.data))
        self.assertEqual(set([1]), set(ds[0].data))

    def test_block_io(self):
        "Tests writing of specific raster blocks"
        ds = GDALRaster({
            'sizex': 4, 'sizey': 4, 'nr_of_bands': 1, 'datatype': 1})
        bd = ds[0]
        bd.data = [1] * 16
        bd.block(2, 2, 2, 2, [2]*4)
        self.assertEqual(bd.data, [1] * 8 + [1,1,2,2]*2)

    def test_image_plotting(self):
        ds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/raster.tif')
        ds = GDALRaster(ds_path)
        bnd = ds[0]
        img = bnd.img({1: (255,0,0,255), 2:(0,255,0,255), 3:(0,0,255,255), 4:(250,100,0,255)})
        self.assertEqual((163, 174), img.size)
        #img.save('bla.png')
