from unittest import skipUnless, TestCase
from django.contrib.gis.gdal import HAS_GDAL
from django.contrib.gis.db import models

if HAS_GDAL:
    from django.contrib.gis.gdal.tests.data.pgraster import pgrasters

    class RasterModel(models.Model):
        rast = models.RasterField()
        class Meta:
            app_label = 'gis'
        def __str__(self):
            return str(self.id)


@skipUnless(HAS_GDAL, "GDAL is required")
class RasterFieldTest(TestCase):

    def test_model_creation(self):
        "Testing RasterField through a test model."
        expected_data = {
            'r1bb': 1, 'r2bui': 2, 'r4bui': 4, 'r8bui': 8, 'r16bsi': -16,
            'r16bui': 16, 'r32bsi': -32, 'r32bui': 32, 'r32bf':  32.3223,
            'r64bf': 64.6446}

        for key, rast in pgrasters.items():
            x = RasterModel.objects.create(rast=rast)

            # Test raster properties
            self.assertEqual((10, 10), (x.rast.sizex, x.rast.sizey))
            self.assertEqual([0.0, 1.0, 0.0, 0.0, 0.0, -1.0],
                             x.rast.geotransform)
            if key != 'nono':
                self.assertAlmostEqual(expected_data[key] - 1,
                                       x.rast[0].nodata_value)
            else:
                self.assertAlmostEqual(None, x.rast[0].nodata_value)
