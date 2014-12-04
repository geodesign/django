from django.db import models
from django.contrib.gis.gdal.raster.rasters import GDALRaster
from django.contrib.gis.db.models.proxy import GeometryProxy


class RasterField(models.Field):
    """
    Raster field for GeoDjango
    """

    description = "Raster Field"
    geom_type = 'RASTER'

    def db_type(self, connection):
        return 'raster'

    def from_db_value(self, value, connection):
        if value and not isinstance(value, GDALRaster):
            value = GDALRaster(value)
        return value

    def get_prep_value(self, value):
        value = super(RasterField, self).get_prep_value(value)

        if value is None:
            return value
        elif isinstance(value, GDALRaster):
            return value.wkb
        elif isinstance(value, str):
            return value
        else:
            raise ValueError('Could not create raster from lookup value.')

    def to_python(self, value):
        if value is None:
            return value
        elif isinstance(value, GDALRaster):
            return value
        else:
            return GDALRaster(value)

    def contribute_to_class(self, cls, name, **kwargs):
        super(RasterField, self).contribute_to_class(cls, name, **kwargs)

        # Setup for lazy-instantiated Raster object.
        setattr(cls, self.attname, GeometryProxy(GDALRaster, self))
