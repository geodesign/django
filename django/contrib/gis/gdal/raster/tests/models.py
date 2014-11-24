from django.contrib.gis.db import models
from django.contrib.gis.gdal.raster.fields import RasterField

class RasterModel(models.Model):
    rast = RasterField()

    class Meta:
        app_label = 'gis'

    def __str__(self):
        return str(self.id)
