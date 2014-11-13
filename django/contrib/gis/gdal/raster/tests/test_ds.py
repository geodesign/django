import os
import unittest
from unittest import skipUnless

from django.contrib.gis.gdal import HAS_GDAL
from django.contrib.gis.geometry.test_data import get_ds_file, TestDS, TEST_DATA

if HAS_GDAL:
    from django.contrib.gis.gdal import OGRException
    from django.contrib.gis.gdal.raster.datasource import DataSource

valid_data_types = [
    'GDT_Byte', 'GDT_UInt16', 'GDT_Int16', 'GDT_UInt32',
    'GDT_Int32', 'GDT_Float32', 'GDT_Float64', 'GDT_CInt16', 'GDT_CInt32',
    'GDT_CFloat32', 'GDT_CFloat64'
]

invalid_data_types = ['abc']

@skipUnless(HAS_GDAL, "GDAL is required")
class RasterDataSourceTest(unittest.TestCase):

    def test01_valid_datatypes(self):
        "Testing creation of GDAL Data Source in memory."
        for d in valid_data_types:
            ds=DataSource({
                'sizex': 10, 'sizey': 10, 'bands': 1, 'datatype': d})
            self.assertEqual('', ds.name)

    def test02_invalid_datatypes(self):
        "Testing invalid GDAL Data Source Drivers."
        self.assertRaises(KeyError, DataSource, {
                'sizex': 10, 'sizey': 10, 'bands': 1, 'datatype': 'abc'})

    def test03_tif_ds(self):
        "Testing creation of a GDAL Data Source from a Tif file."
        ds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/raster.tif')
        ds=DataSource(ds_path)
        self.assertEqual(ds_path, ds.name)
