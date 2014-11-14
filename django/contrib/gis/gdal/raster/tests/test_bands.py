import os
import unittest
from unittest import skipUnless

from django.contrib.gis.gdal import HAS_GDAL
from django.contrib.gis.geometry.test_data import get_ds_file, TestDS, TEST_DATA

if HAS_GDAL:
    from django.contrib.gis.gdal import OGRException
    from django.contrib.gis.gdal.raster.datasource import DataSource
    from django.contrib.gis.gdal.raster.bands import Band

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
class RasterBandDataTest(unittest.TestCase):

    def setUp(self):
        "Setup parent gdal layers"
        self.d = DataSource({
            'sizex': 11, 'sizey': 12, 'bands': 3, 'datatype': 1})
        ds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/raster.tif')
        self.ds = DataSource(ds_path)

    def test_sizex(self):
        "Testing size property of raster bands."
        for band in self.d:
            self.assertEqual(11, band.sizex)
            self.assertEqual(12, band.sizey)

    def test_nodata_value(self):
        "Set setting and getting nodata value for band"
        bnd = self.d[0]
        bnd.nodata_value = 1.23
        self.assertEqual(1.23, bnd.nodata_value)

    def test_data_io(self):
        band = self.ds[0]
        self.assertEqual(set([0, 1, 2, 3, 4, 8, 9]), set(band.data))

        band.data = [1 for x in range(band.nr_of_pixels)]
        self.assertEqual(set([1]), set(band.data))
