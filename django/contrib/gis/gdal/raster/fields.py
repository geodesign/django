from django.db import models

from django.contrib.gis.gdal.raster.rasters import GDALRaster

class RasterField(models.Field):
    """
    Raster field for GeoDjango
    """

    description = "Raster Field"
     
    __metaclass__ = models.SubfieldBase

    def db_type(self, connection):
        return 'raster'

    def from_db_value(self, value, connection):
        # Convert PostGIS Raster string to OGR Rasters
        if value:
            value = GDALRaster(value)

        return value

    def get_prep_value(self, value):
        value = super(RasterField, self).get_prep_value(value)

        if value is None:
            return value
        elif isinstance(value, GDALRaster):
            return value.to_postgis_raster()
        elif isinstance(value, str):
            return value
        else:
            raise ValueError('Could not create raster from lookup value.')

    def to_python(self, value):
        if value is None:
            return value

        if isinstance(value, GDALRaster):
            return value

        return GDALRaster(value)
