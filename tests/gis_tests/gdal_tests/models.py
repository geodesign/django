from django.contrib.gis.db import models


class RasterModel(models.Model):

    rast = models.RasterField(null=True, srid=4326)

    def __str__(self):
        return str(self.id)
