import os
import unittest
from unittest import skipUnless

from django.contrib.gis.gdal import HAS_GDAL
from django.contrib.gis.geometry.test_data import get_ds_file, TestDS, TEST_DATA

if HAS_GDAL:
    from django.contrib.gis.gdal.srs import SpatialReference
    from django.contrib.gis.gdal.raster.rasters import GDALRaster
    from django.contrib.gis.gdal.raster.bands import GDALBand
    from django.contrib.gis.gdal.raster.tests.data.pgraster import pgrasters

valid_data_types = [
    'GDT_Byte', 'GDT_UInt16', 'GDT_Int16', 'GDT_UInt32',
    'GDT_Int32', 'GDT_Float32', 'GDT_Float64', 'GDT_CInt16', 'GDT_CInt32',
    'GDT_CFloat32', 'GDT_CFloat64'
]

invalid_data_types = ['abc']

@skipUnless(HAS_GDAL, "GDAL is required")
class RasterGDALRasterTest(unittest.TestCase):

    def setUp(self):
        self.ds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    'data/raster.tif')
        self.ds = GDALRaster(self.ds_path)
        self.ds.srid = 3086

        # create warped version
        self.warped = self.ds.warp({'srid': 3857, 'driver': 'MEM',
                                    'name': 'warpedfortesting'})

    def test_valid_datatypes(self):
        "Testing creation of GDAL Data Source in memory."
        for d in valid_data_types:
            ds = GDALRaster({
                'sizex': 10, 'sizey': 10, 'nr_of_bands': 1, 'datatype': d})
            self.assertEqual('', ds.name)

    def test_invalid_datatypes(self):
        "Testing invalid GDAL Data Source Drivers."
        self.assertRaises(KeyError, GDALRaster, {
                'sizex': 10, 'sizey': 10, 'nr_of_bands': 1, 'datatype': 'abc'})

    def test_driver_getter(self):
        "Tests if driver is returned"
        self.assertEqual(self.ds.driver.name, 'GTiff')

    def test_ds_name(self):
        "Testing creation of a GDAL Data Source from a Tif file."
        self.assertEqual(self.ds_path, self.ds.name)

    def test_ds_size(self):
        "Testing xsize and ysize properties for a GDAL Data Source"
        self.assertEqual(163, self.ds.sizex)
        self.assertEqual(174, self.ds.sizey)

    def test_ds_band_count(self):
        "Testing band count property for a GDAL Data Source"
        ds = GDALRaster({'sizex': 11, 'sizey': 12, 'nr_of_bands': 23, 'datatype': 1})
        self.assertEqual(23, ds.band_count)
        self.assertEqual(1, self.ds.band_count)
        self.assertEqual(1, len(self.ds))

    def test_ds_band_accessor(self):
        "Testing access of raster bands"
        x = self.ds[0]
        self.assertTrue(isinstance(x, GDALBand))

    def test_get_geotransform(self):
        "Tests that geotransform returns the right parameters"
        self.assertAlmostEqual(
            [511700.4680706557, 100.0, 0.0, 435103.3771231986, 0.0, -100.0],
            self.ds.geotransform)

    def test_set_geotransform(self):
        "Test setting geotransfrom and corresponding error msg"
        ds = GDALRaster({'sizex': 1, 'sizey': 2, 'nr_of_bands': 1, 'datatype': 1})

        # Test setting the geotransform        
        ds.geotransform = range(6)
        self.assertEqual(range(6), ds.geotransform)

        # Make sure lenght of array is 6
        with self.assertRaises(ValueError):
            ds.geotransform = range(5)

        # Confirm all values are numbers
        with self.assertRaises(ValueError):
            ds.geotransform = [1,2,3,4,5,'6']

    def test_ds_projection_and_srs(self):
        "Testing spatial reference and srs related methods"
        # Test for tif file
        ref = 'PROJCS["NAD83 / Florida GDL Albers",GEOGCS["NAD83",DATUM["North_American_Datum_1983",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6269"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4269"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",24],PARAMETER["standard_parallel_2",31.5],PARAMETER["latitude_of_center",24],PARAMETER["longitude_of_center",-84],PARAMETER["false_easting",400000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","3086"]]'
        self.assertEqual(ref, self.ds.srs.wkt)

        # Test for in-memory creation and setting through srid
        ds = GDALRaster({'sizex': 1, 'sizey': 2, 'nr_of_bands': 1, 'datatype': 1})
        ds.srid = 4326
        srs = SpatialReference(4326)
        self.assertEqual(srs.wkt, ds.srs.wkt)

    def test_pgraster_unpacking(self):
        "Tests unpacking all postgis raster data types"
        # Expected values for data types
        expected = {2: 16, 3: -16, 4: 32, 5: -32, 6: 32.3223, 7: 64.6446}

        # Loop through all test raster strings
        for key, rast in pgrasters.items():
            ds = GDALRaster(rast)
            result = list(set(ds[0].data))[0]
            dt = ds[0].datatype
            if dt == 1:
                self.assertTrue(result in [1,2,4,8])
            else:
                self.assertTrue(round(result - expected[dt], 5) == 0)

    def test_pgraster_packing(self):
        "Tests packing postgis raster data"
        result = self.ds.wkb
        ds = GDALRaster(str(result))
        self.assertEqual(set(self.ds[0].data), set(ds[0].data))

    def test_get_spelled_out_geotransform(self):
        "Tests if correct values are returned from explicit gt values"
        ds = GDALRaster({'sizex': 1, 'sizey': 2, 'nr_of_bands': 1, 'datatype': 1})

        self.assertEqual(None, ds.originx)
        self.assertEqual(None, ds.scalex)
        self.assertEqual(None, ds.skewx)
        self.assertEqual(None, ds.originy)
        self.assertEqual(None, ds.skewy)
        self.assertEqual(None, ds.scaley)

        ds.geotransform = [1, 2, 3, 4, 5, 6]

        self.assertEqual(1, ds.originx)
        self.assertEqual(2, ds.scalex)
        self.assertEqual(3, ds.skewx)
        self.assertEqual(4, ds.originy)
        self.assertEqual(5, ds.skewy)
        self.assertEqual(6, ds.scaley)

    def test_set_spelled_out_geotransform(self):
        "Tests if correct values are returned from explicit gt values"
        ds = GDALRaster({'sizex': 1, 'sizey': 2, 'nr_of_bands': 1, 'datatype': 1})

        self.assertRaises(ValueError, ds.originx, 1)
        self.assertRaises(ValueError, ds.originy, 1)
        self.assertRaises(ValueError, ds.scalex, 1)
        self.assertRaises(ValueError, ds.scaley, 1)
        self.assertRaises(ValueError, ds.skewx, 1)
        self.assertRaises(ValueError, ds.skewy, 1)

        ds.geotransform = [1, 2, 3, 4, 5, 6]

        ds.originx = 6
        ds.scalex = 5
        ds.skewx = 4
        ds.originy = 3
        ds.skewy = 2
        ds.scaley = 1

        self.assertEqual(6, ds.originx)
        self.assertEqual(5, ds.scalex)
        self.assertEqual(4, ds.skewx)
        self.assertEqual(3, ds.originy)
        self.assertEqual(2, ds.skewy)
        self.assertEqual(1, ds.scaley)

    def test_copy_ptr(self):
        "Tests making a deep copy of the underling gdal dataset."
        ds = GDALRaster({'sizex': 1, 'sizey': 2, 'nr_of_bands': 1, 'datatype': 1})
        ds.srid = 3086

        ds_copy = GDALRaster(ds.copy_ptr('x'))
        self.assertEqual(ds_copy.sizex, ds.sizex)
        self.assertEqual(ds_copy.sizey, ds.sizey)
        self.assertEqual(ds_copy.band_count, ds.band_count)
        self.assertEqual(ds_copy.srid, ds.srid)

    def test_extent(self):
        "Tests extent property of raster."
        ds = GDALRaster({'sizex': 2, 'sizey': 2, 
                         'nr_of_bands': 1, 'datatype': 1})
        ds.geotransform = [1] * 6
        ds.scalex = 1
        ds.scaley = -1
        self.assertEqual((1, -1, 3, 1), ds.extent)

    def test_warp(self):
        "Tests warping the dataset."
        # Assert basic properties are correct
        self.assertEqual(self.warped.sizex, self.ds.sizex)
        self.assertEqual(self.warped.sizey, self.ds.sizey)
        self.assertEqual(3857, self.warped.srid)

    def test_max_zoom_level(self):
        "Tests the maximum zoom level calculation for this raster."
        zoom = self.warped.get_max_zoom_level()
        self.assertEqual(11, zoom)

    def test_tile_index_range(self):
        "Test the computation of the xyz tile range for a given zoom level."
        indexrange = self.warped.get_tile_index_range(11)
        self.assertEqual([552, 858, 553, 859], indexrange)

    def test_tile_bounds(self):
        "Tests the calculation of the tile bounds for a xyz tile."
        bounds = self.warped.get_tile_bounds(552, 858, 11)
        self.assertEqual((-9236039.001754418, 3228700.074765846,
                          -9216471.122513412, 3248267.9540068507), bounds)

    def test_tile_scale(self):
        "Test the computation of the pixelsize scale (in m) of a xyz tile."
        scale = self.warped.get_tile_scale(11)
        self.assertEqual(76.43702828517625, scale)

    def test_tile_creation(self):
        "Tests the extraction of a xyz tile from a given dataset."
        tile = self.warped.get_tile(552, 858, 11)
        self.assertEqual(3857, tile.srid)
        self.assertEqual(76.43702828517625, tile.scalex)
        self.assertEqual(-9236039.001754418, tile.originx)
        self.assertEqual('warpedfortesting-552-858-11.MEM', tile.name)

    def test_zoomdown(self):
        "Tests the setting for the maximum xzy tile zoom level."
        self.assertEqual(11, self.warped.get_max_zoom_level())
        self.warped.zoomdown = False
        self.assertEqual(10, self.warped.get_max_zoom_level())
