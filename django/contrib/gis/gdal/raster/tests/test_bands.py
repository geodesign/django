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

@skipUnless(HAS_GDAL, "GDAL is required")
class RasterBandDataTest(unittest.TestCase):

    def setUp(self):
        "Setup parent gdal layers"
        self.d = DataSource({
            'sizex': 11, 'sizey': 12, 'bands': 3, 'datatype': 1})

    def test_sizex(self):
        "Testing size property of raster bands."
        for band in self.d:
            self.assertEqual(11, band.sizex)
            self.assertEqual(12, band.sizey)
