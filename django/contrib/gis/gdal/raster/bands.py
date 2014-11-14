from ctypes import c_void_p
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

    @property
    def index(self):
        return capi.get_band_index(self._ptr)

    @property
    def name(self):
        return capi.get_band_description(self._ptr)

    @property
    def dataset(self):
        return capi.get_band_ds(self._ptr)

    @property
    def datatype(self):
        return capi.get_band_datatype(self._ptr)

    def _get_nodata_value(self):
        return capi.get_band_nodata_value(self._ptr)

    def _set_nodata_value(self, nodata):
        nodata = float(nodata)
        capi.set_band_nodata_value(self._ptr, nodata)

    nodata_value = property(_get_nodata_value, _set_nodata_value)

    @property
    def max(self):
        return capi.get_band_maximum(self._ptr)

    @property
    def min(self):
        return capi.get_band_minimum(self._ptr)

    @property
    def scale(self):
        return capi.get_band_scale(self._ptr)

    @property
    def unit(self):
        return capi.get_band_unit_type(self._ptr)

    @property
    def offset(self):
        return capi.get_band_offset(self._ptr)

    #### IO Methods ####
    def _get_all_data(self):
        GF_Read = 0

        # bla = POINTER(buffertype*buffersize)
        # lgdal.GDALRasterIO.argtypes = [c_void_p, c_int, c_int, c_int, c_int, c_int,
        #                  bla, c_int, c_int, c_int, c_int, c_int]
        # lgdal.GDALRasterIO.argtypes = argtypes
        # func.restype = None
        # return func
        # band_io = band_io_output(lgdal.GDALRasterIO, buffertype, buffersize)
        dataptr = c_void_p()
        capi.band_io(self._ptr, GF_Read, 0, 0, self.sizex, self.sizey,
                     dataptr, self.sizex, self.sizey, self.datatype, 0, 0)
        return dataptr

    def _set_all_data(self):
        pass

    data = property(_get_all_data, _set_all_data)
