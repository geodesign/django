import unittest
from unittest import skipUnless

from django.contrib.gis.gdal import HAS_GDAL

if HAS_GDAL:
    from django.contrib.gis.gdal.raster.tests.data.pgraster import pgrasters
    from .models import RasterModel

from django.contrib.gis.db import models
from django.contrib.gis.gdal.raster.fields import RasterField

@skipUnless(HAS_GDAL, "GDAL is required")
class RasterFieldTest(unittest.TestCase):

    def test_model_creation(self):
        "Testing creation of GDAL Data Source in memory."
        expected_data = {
            'r1bb': 1, 'r2bui': 2, 'r4bui': 4, 'r8bui': 8,  'r16bsi': -16,
            'r16bui': 16, 'r32bsi': -32, 'r32bui': 32, 'r32bf':  32.3223,
            'r64bf': 64.6446}

        for key, rast in pgrasters.items():
            x = RasterModel.objects.create(rast=rast)

            # Test raster properties
            self.assertEqual((10, 10), (x.rast.sizex, x.rast.sizey))
            self.assertEqual([0.0, 1.0, 0.0, 0.0, 0.0, -1.0], x.rast.geotransform)
            if key != 'nono':
                self.assertAlmostEqual(expected_data[key] - 1, x.rast[0].nodata_value)
            else:
                self.assertAlmostEqual(None , x.rast[0].nodata_value)
