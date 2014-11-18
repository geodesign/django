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
        for key, rast in pgrasters.items():
            x = RasterModel(rast=rast)
            self.assertEqual((10, 10), (x.rast.sizex, x.rast.sizey))
            self.assertEqual([0.0, 1.0, 0.0, 0.0, 0.0, -1.0], x.rast.geotransform)
