import Image, binascii
import numpy as np
from ctypes import c_byte, byref

from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.gdal.raster.prototypes import ds as capi
from django.contrib.gis.gdal.raster import utils

class GDALBand(GDALBase):
    """
    Wraps the GDAL Raster Object, needs to be instantiated from a
    GDALRaster object.
    """
    def __init__(self, band_ptr, ds):
        if not band_ptr:
            raise GDALException('Cannot create Layer, invalid pointer given')
        self.ptr = band_ptr
        self._ds = ds

    @property
    def sizex(self):
        return capi.get_band_xsize(self.ptr)

    @property
    def sizey(self):
        return capi.get_band_ysize(self.ptr)

    @property
    def nr_of_pixels(self):
        return self.sizex*self.sizey

    @property
    def index(self):
        return capi.get_band_index(self.ptr)

    @property
    def name(self):
        return capi.get_band_description(self.ptr)

    @property
    def dataset(self):
        return capi.get_band_ds(self.ptr)

    @property
    def datatype(self):
        return capi.get_band_datatype(self.ptr)

    def _get_nodata_value(self):
        return capi.get_band_nodata_value(self._ptr)

    def _set_nodata_value(self, nodata):
        nodata = float(nodata)
        capi.set_band_nodata_value(self.ptr, nodata)

    nodata_value = property(_get_nodata_value, _set_nodata_value)

    @property
    def max(self):
        return capi.get_band_maximum(self.ptr)

    @property
    def min(self):
        return capi.get_band_minimum(self.ptr)

    @property
    def scale(self):
        return capi.get_band_scale(self.ptr)

    @property
    def unit(self):
        return capi.get_band_unit_type(self.ptr)

    @property
    def offset(self):
        return capi.get_band_offset(self.ptr)

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
        if data is None:
            # Acces data to read
            GF_Read = 0
            data_array = (utils.GDAL_TO_CTYPES[self.datatype]*self.nr_of_pixels)()
        else:
            # Acces data to write
            GF_Read = 1
            if isinstance(data, buffer):
                data_array = (utils.GDAL_TO_CTYPES[self.datatype]*self.nr_of_pixels).from_buffer_copy(data)
            else:
                data_array = (utils.GDAL_TO_CTYPES[self.datatype]*self.nr_of_pixels)(*data)

        # Access data
        capi.band_io(self.ptr, GF_Read, offsetx, offsety, sizex, sizey,
                     byref(data_array), sizex, sizey, self.datatype, 0, 0)

        # Return data as list or buffer
        if data is None:
            if as_buffer:
                return buffer(data_array)
            else:
                return list(data_array)

    def _get_data(self):
        return self.block()

    def _set_data(self, data):
        self.block(data=data)

    data = property(_get_data, _set_data)

    @property
    def hex(self):
        return binascii.hexlify(self.block(as_buffer=True))

    def img(self, colormap):
        "Creates an python image from pixel values"
        # Get data as array
        dat = self.block(as_buffer=True)
        dat = np.frombuffer(dat, dtype='byte')

        # A dictionary will be interpreted as discrete category colormap
        if isinstance(colormap, dict):
            # Create zeros array
            rgba = np.zeros((self.sizex * self.sizey, 4))

            # Override matched categories with colors
            for k,v in colormap.items():
                rgba[dat==k] = v

            # Reshape array
            rgba = rgba.reshape(self.sizey, self.sizex, 4)

            # Create image from array
            return Image.fromarray(np.uint8(rgba))
        else:
            # TODO: Continuous scale handling
            dat = [(255,255,255,255)]*self.nr_of_pixels
            img = Image.new('RGBA', (self.sizey, self.sizex))
            img.putdata(dat)
            return img
