import os
import unittest
from unittest import skipUnless

from django.contrib.gis.gdal import HAS_GDAL
from django.contrib.gis.geometry.test_data import get_ds_file, TestDS, TEST_DATA

if HAS_GDAL:
    from django.contrib.gis.gdal import OGRException
    from django.contrib.gis.gdal.srs import SpatialReference
    from django.contrib.gis.gdal.raster.datasource import DataSource
    from django.contrib.gis.gdal.raster.bands import Band

valid_data_types = [
    'GDT_Byte', 'GDT_UInt16', 'GDT_Int16', 'GDT_UInt32',
    'GDT_Int32', 'GDT_Float32', 'GDT_Float64', 'GDT_CInt16', 'GDT_CInt32',
    'GDT_CFloat32', 'GDT_CFloat64'
]

invalid_data_types = ['abc']

@skipUnless(HAS_GDAL, "GDAL is required")
class RasterDataSourceTest(unittest.TestCase):

    def setUp(self):
        self.ds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    'data/raster.tif')
        self.ds = DataSource(self.ds_path)

    def test_valid_datatypes(self):
        "Testing creation of GDAL Data Source in memory."
        for d in valid_data_types:
            ds = DataSource({
                'sizex': 10, 'sizey': 10, 'bands': 1, 'datatype': d})
            self.assertEqual('', ds.name)

    def test_invalid_datatypes(self):
        "Testing invalid GDAL Data Source Drivers."
        self.assertRaises(KeyError, DataSource, {
                'sizex': 10, 'sizey': 10, 'bands': 1, 'datatype': 'abc'})

    def test_ds_name(self):
        "Testing creation of a GDAL Data Source from a Tif file."
        self.assertEqual(self.ds_path, self.ds.name)

    def test_ds_size(self):
        "Testing xsize and ysize properties for a GDAL Data Source"
        self.assertEqual(163, self.ds.sizex)
        self.assertEqual(174, self.ds.sizey)

    def test_ds_band_count(self):
        "Testing band count property for a GDAL Data Source"
        ds = DataSource({'sizex': 11, 'sizey': 12, 'bands': 23, 'datatype': 1})
        self.assertEqual(23, ds.band_count)
        self.assertEqual(1, self.ds.band_count)
        self.assertEqual(1, len(self.ds))

    def test_ds_band_accessor(self):
        "Testing access of raster bands"
        x = self.ds[0]
        self.assertTrue(isinstance(x, Band))

    def test_get_geotransform(self):
        "Tests that geotransform returns the right parameters"
        self.assertAlmostEqual(
            [511700.4680706557, 100.0, 0.0, 435103.3771231986, 0.0, -100.0],
            self.ds.geotransform
        )

    def test_set_geotransform(self):
        "Test setting geotransfrom and corresponding error msg"
        ds = DataSource({'sizex': 1, 'sizey': 2, 'bands': 1, 'datatype': 1})

        # Test setting the geotransform        
        ds.geotransform = range(6)
        self.assertEqual(range(6), ds.geotransform)

        # Make sure lenght of array is 6
        with self.assertRaises(ValueError):
            ds.geotransform = range(5)

        # Confirm all values are numbers
        with self.assertRaises(ValueError):
            ds.geotransform = [1,2,3,4,5,'6']

    def test_srs(self):
        "Test spatial reference setting "
        print self.ds.srs

    def test_ds_projection_reference(self):
        "Testing spatial reference related methods"
        # Test for tif file
        ref = 'PROJCS["Albers_Conical_Equal_Area_Florida_Geographic_Data_Library",GEOGCS["GCS_North_American_1983_HARN",DATUM["NAD83_High_Accuracy_Reference_Network",SPHEROID["GRS 1980",6378137,298.2572221010002,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","6152"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",24],PARAMETER["standard_parallel_2",31.5],PARAMETER["latitude_of_center",24],PARAMETER["longitude_of_center",-84],PARAMETER["false_easting",400000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'
        self.assertEqual(ref, self.ds.srs.wkt)

        # Test for in-memory creation and setting through srid
        ds = DataSource({'sizex': 1, 'sizey': 2, 'bands': 1, 'datatype': 1})
        ds.srid = 4326
        srs = SpatialReference(4326)
        self.assertEqual(srs.wkt, ds.srs.wkt)
