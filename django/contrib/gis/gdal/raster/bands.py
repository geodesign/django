from ctypes import c_byte, byref
from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.raster.prototypes import ds as capi
from django.contrib.gis.gdal.raster import utils

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
    def nr_of_pixels(self):
        return self.sizex*self.sizey

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

    #### IO Section ####
    def block(self, offsetx=0, offsety=0, sizex=0, sizey=0, data=None,
              as_buffer=False):
        """
        Gets or sets data for a raster band. The offset indicates a distance in
        pixel values from the upper left corner from which to handle the block
        of the specified size. If data is provided, it will be used to write in
        that block, if no input data is provided, the data for the block is
        returned.
        """
        # Set default size if not provided
        if not sizex:
            sizex = self.sizex - offsetx
        if not sizey:
            sizey = self.sizey - offsety

        if sizex <= 0 or sizey <= 0:
            raise ValueError('Offset too big for this raster.')

        if sizex > self.sizex or sizey > self.sizey:
            raise ValueError('Size is larger than raster.')
        
        # Create c array of required size
        if not data:
            data_array = (utils.GDAL_TO_CTYPES[self.datatype]*self.nr_of_pixels)()
            # Acces data to read
            GF_Read = 0
        else:
            data_array = (utils.GDAL_TO_CTYPES[self.datatype]*self.nr_of_pixels)(*data)
            # Acces data to write
            GF_Read = 1

        # Access data
        capi.band_io(self._ptr, GF_Read, offsetx, offsety, sizex, sizey,
                     byref(data_array), sizex, sizey, self.datatype, 0, 0)

        # Return data as list or buffer
        if not data:
            if as_buffer:
                return buffer(data_array)
            else:
                return list(data_array)

    def _get_data(self):
        return self.block()

    def _set_data(self, data):
        self.block(data=data)
        pass

    data = property(_get_data, _set_data)
