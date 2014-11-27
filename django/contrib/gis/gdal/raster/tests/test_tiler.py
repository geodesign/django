import os
import unittest
from unittest import skipUnless

from django.contrib.gis.gdal import HAS_GDAL
from django.contrib.gis.geometry.test_data import get_ds_file, TestDS, TEST_DATA

if HAS_GDAL:
    from django.contrib.gis.gdal.raster.rasters import GDALRaster
    from django.contrib.gis.gdal.raster.tiles import Tiler


@skipUnless(HAS_GDAL, "GDAL is required")
class TilerTest(unittest.TestCase):

    def setUp(self):
        self.ds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    'data/raster.tif')
        self.ds = GDALRaster(self.ds_path)
        self.ds.srid = 3086

        self.warped = self.ds.warp(srid=3857, driver='MEM',name='warpedfortesting')

        self.tiler = Tiler(self.warped)

    def test_max_zoom_level(self):
        "Tests the maximum zoom level calculation for this raster."
        zoom = self.tiler.get_max_zoom_level()
        self.assertEqual(11, zoom)

    def test_tile_index_range(self):
        "Test the computation of the xyz tile range for a given zoom level."
        indexrange = self.tiler.get_tile_index_range(11)
        self.assertEqual([552, 858, 553, 859], indexrange)

    def test_tile_bounds(self):
        "Tests the calculation of the tile bounds for a xyz tile."
        bounds = self.tiler.get_tile_bounds(552, 858, 11)
        self.assertEqual((-9236039.001754418, 3228700.074765846,
                          -9216471.122513412, 3248267.9540068507), bounds)

    def test_tile_scale(self):
        "Test the computation of the pixelsize scale (in m) of a xyz tile."
        scale = self.tiler.get_tile_scale(11)
        self.assertEqual(76.43702828517625, scale)

    def test_tile_creation(self):
        "Tests the extraction of a xyz tile from a given dataset."
        tile = self.tiler.get_tile(552, 858, 11)
        self.assertEqual(3857, tile.srid)
        self.assertEqual(76.43702828517625, tile.scalex)
        self.assertEqual(-9236039.001754418, tile.originx)
        self.assertEqual('warpedfortesting-552-858-11.mem', tile.name)

    def test_zoomdown(self):
        "Tests the setting for the maximum xzy tile zoom level."
        self.assertEqual(11, self.tiler.get_max_zoom_level())
        self.tiler.zoomdown = False
        self.assertEqual(10, self.tiler.get_max_zoom_level())

    def test_tile_iterator(self):
        "Tests iterator over all tiles for this dataset."
        for x, y, z, tile in self.tiler.tiles():
            print x,y,z,tile
