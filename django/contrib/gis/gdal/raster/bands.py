from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.raster.prototypes import ds as capi

class Band(GDALBase):
    """
    Wraps the GDAL Raster Object, needs to be instantiated from a
    DataSource object.
    """
    def __init__(self, band_ptr, ds):
        if not band_ptr:
            raise OGRException('Cannot create Layer, invalid pointer given')
        self.ptr = band_ptr
        self._ds = ds

    @property
    def sizex(self):
        return capi.get_band_xsize(self._ptr)

    @property
    def sizey(self):
        return capi.get_band_ysize(self._ptr)

# get_band_index = int_output(lgdal.GDALGetBandNumber, [])
# get_band_description = const_string_output(lgdal.GDALGetDescription, [])
# get_band_ds = voidptr_output(lgdal.GDALGetBandDataset, [])
# get_band_nodata_value = double_output(lgdal.GDALGetRasterNoDataValue, [c_int])
# get_band_minimum = double_output(lgdal.GDALGetRasterMinimum, [c_int])
# get_band_maximum = double_output(lgdal.GDALGetRasterMaximum, [c_int])
# get_band_offset = double_output(lgdal.GDALGetRasterOffset, [c_int])
# get_band_scale = double_output(lgdal.GDALGetRasterScale, [c_int])
# get_band_unit_type = const_string_output(lgdal.GDALGetRasterUnitType, [c_int])
