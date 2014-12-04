from PIL import Image
import binascii
import numpy as np
from ctypes import byref, POINTER, c_int

from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.gdal.prototypes import raster as capi
from django.contrib.gis.gdal.raster import const

class GDALBand(GDALBase):
    """
    Wraps the GDAL Raster Object, needs to be instantiated from a
    GDALRaster object.
    """
    def __init__(self, band_ptr):
        if not band_ptr:
            raise GDALException('Cannot create Band, invalid pointer given.')
        self.ptr = band_ptr

    @property
    def sizex(self):
        "Returns the number of pixels of the band in x direction."
        return capi.get_band_xsize(self.ptr)

    @property
    def sizey(self):
        "Returns the number of pixels of the band in y direction."
        return capi.get_band_ysize(self.ptr)

    @property
    def nr_of_pixels(self):
        "Returns the total number of pixels of the band."
        return self.sizex*self.sizey

    @property
    def index(self):
        "Returns the index position of this band within the owning raster."
        return capi.get_band_index(self.ptr)

    @property
    def description(self):
        "Returns the description string of the band."
        return capi.get_band_description(self.ptr)

    @property
    def dataset(self):
        "Returns a pointer to the owning dataset."
        return capi.get_band_ds(self.ptr)

    @property
    def datatype(self):
        "Returns the GDAL Pixel Datatype for this band."
        return capi.get_band_datatype(self.ptr)

    def _get_nodata_value(self):
        "Returns the nodata value for this band."
        nodata_exists = c_int()
        value = capi.get_band_nodata_value(self.ptr, nodata_exists)
        return value if nodata_exists else None

    def _set_nodata_value(self, nodata):
        "Sets the nodata value for this band."
        if not isinstance(nodata, (int, float)):
            raise ValueError('Nodata value needs to numeric.')
        capi.set_band_nodata_value(self.ptr, nodata)

    nodata_value = property(_get_nodata_value, _set_nodata_value)

    @property
    def max(self):
        "Returns the maximum pixel value for this band."
        return capi.get_band_maximum(self.ptr)

    @property
    def min(self):
        "Returns the minimum pixel value for this band."
        return capi.get_band_minimum(self.ptr)

    @property
    def hex(self):
        return binascii.hexlify(self.block(as_buffer=True)).upper()

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

        # Get ctypes type array generator function
        ctypes_array = const.GDAL_TO_CTYPES[self.datatype] * self.nr_of_pixels

        # Create c array of required size
        if data is None:
            # Acces band in read mode
            access_flag = 0

            # Instantiate empty array to load data into
            data_array = ctypes_array()
        else:
            # Acces band in write mode
            access_flag = 1

            # Instantiate ctypes array holding data from a buffer,
            # list, tuple or array
            if isinstance(data, (str, buffer)):
                data_array = ctypes_array.from_buffer_copy(data)
            else:
                data_array = ctypes_array(*data)

        # Access data
        capi.band_io(self.ptr, access_flag, offsetx, offsety, sizex, sizey,
                     byref(data_array), sizex, sizey, self.datatype, 0, 0)

        # Return data as list or buffer
        if data is None:
            if as_buffer:
                return buffer(data_array)
            else:
                return list(data_array)

    def _get_data(self):
        "Gets complete raster data as list."
        return self.block()

    def _set_data(self, data):
        "Sets complete raster data."
        self.block(data=data)

    data = property(_get_data, _set_data)

    def img(self, colormap):
        "Creates an python image from pixel values"
        # Get data as array
        dat = self.block(as_buffer=True)
        dat = np.frombuffer(dat, dtype='byte')

        # A dictionary will be interpreted as discrete category colormap
        if isinstance(colormap, dict):
            # Create zeros array
            rgba = np.zeros((self.nr_of_pixels, 4))

            # Override matched categories with colors
            for key, color in colormap.items():
                rgba[dat == key] = color

            # Reshape array
            rgba = rgba.reshape(self.sizey, self.sizex, 4)

            # Create image from array
            return Image.fromarray(np.uint8(rgba))
        else:
            # TODO: Continuous scale handling
            dat = [(255, 255, 255, 255)]*self.nr_of_pixels
            img = Image.new('RGBA', (self.sizey, self.sizex))
            img.putdata(dat)
            return img
