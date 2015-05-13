import json

from django.contrib.gis.shortcuts import numpy
from django.test import TransactionTestCase, skipUnlessDBFeature

from ..data.rasters.textrasters import JSON_RASTER
from .models import RasterModel


@skipUnlessDBFeature('supports_raster')
class RasterFieldTest(TransactionTestCase):
    available_apps = ['gis_tests.rasterapp']

    def test_field_null_value(self):
        "Testing creating model where the RasterField has value null."
        # Create model instance with Null value
        rastermodel = RasterModel.objects.create(rast=None)
        rastermodel = RasterModel.objects.get(id=rastermodel.id)
        self.assertIsNone(rastermodel.rast)

    def test_model_creation(self):
        "Testing RasterField through a test model."
        # Create model instance from JSON raster
        rastermodel = RasterModel.objects.create(rast=JSON_RASTER)
        rastermodel = RasterModel.objects.get(id=rastermodel.id)

        # Test raster metadata properties
        self.assertEqual((5, 5), (rastermodel.rast.width, rastermodel.rast.height))
        self.assertEqual([0.0, -1.0, 0.0, 0.0, 0.0, 1.0],
                         rastermodel.rast.geotransform)

        self.assertEqual(None, rastermodel.rast.bands[0].nodata_value)

        # Compare srs
        self.assertEqual(rastermodel.rast.srs.srid, 4326)

        # Compare pixel values
        band = rastermodel.rast.bands[0].data()

        # If numpy, convert result to list
        if numpy:
            band = band.flatten().tolist()

        # Loop through rows in band data and assert single
        # value is as expected.
        self.assertEqual(
            [
                0.0, 1.0, 2.0, 3.0, 4.0,
                5.0, 6.0, 7.0, 8.0, 9.0,
                10.0, 11.0, 12.0, 13.0, 14.0,
                15.0, 16.0, 17.0, 18.0, 19.0,
                20.0, 21.0, 22.0, 23.0, 24.0
            ],
            band
        )

    def test_implicit_raster_transformation(self):
        """
        Testing automatic transformation of rasters with srid
        different from the field srid.
        """
        # Parse json raster
        rast = json.loads(JSON_RASTER)

        # Update srid to another value
        rast['srid'] = 3086

        # Save model and get it from db
        rastermodel = RasterModel.objects.create(rast=rast)
        rastermodel = RasterModel.objects.get(id=rastermodel.id)

        # Confirm raster has been transformed to default srid
        self.assertEqual(rastermodel.rast.srs.srid, 4326)

        # Confirm geotransform is in lat/lon
        self.assertEqual(
            rastermodel.rast.geotransform,
            [-87.9298551266551, 9.459646421449934e-06, 0.0,
             23.94249275457565, 0.0, -9.459646421449934e-06]
        )
