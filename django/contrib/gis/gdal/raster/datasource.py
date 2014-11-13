# ctypes prerequisites.
from ctypes import byref

# The GDAL C library, OGR exceptions, and the Layer object.
from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.raster.driver import Driver
from django.contrib.gis.gdal.error import OGRException, OGRIndexError
from django.contrib.gis.gdal.layer import Layer

# Getting the ctypes prototypes for the DataSource.
from django.contrib.gis.gdal.raster.prototypes import ds as capi
from django.contrib.gis.gdal.raster.constants import GDAL_PIXEL_TYPES

from django.utils.encoding import force_bytes, force_text
from django.utils import six
from django.utils.six.moves import xrange


class DataSource(GDALBase):
    "Wraps an GDAL Data Source object."

    #### Python 'magic' routines ####
    def __init__(self, ds_input=None, ds_driver=False, write=False, encoding='utf-8'):
        # The write flag.
        if write:
            self._write = 1
        else:
            self._write = 0
        # See also http://trac.osgeo.org/gdal/wiki/rfc23_ogr_unicode
        self.encoding = encoding

        # Registering all the drivers, this needs to be done
        #  _before_ we try to open up a data source.
        if not capi.get_driver_count():
            capi.register_all()

        if isinstance(ds_input, dict):
            # If data type is provided as string, map to integer
            if isinstance(ds_input['datatype'], str):
                ds_input['datatype'] = GDAL_PIXEL_TYPES[ds_input['datatype']]

            # Create empty in-memory raster if input data is tuple
            ds_driver = Driver('MEM')
            ds = capi.create_ds(
                ds_driver.ptr, force_bytes(''),
                ds_input['sizex'], ds_input['sizey'],
                ds_input['bands'], ds_input['datatype'], None
            )
        elif isinstance(ds_input, six.string_types):
            # The data source driver is a void pointer.
            # ds_driver = Driver.ptr_type()
            # ds_driver = Driver('tif')
            try:
                # GDALOpen will auto-detect the data source type.
                ds = capi.open_ds(ds_input, self._write)
            except OGRException:
                # Making the error message more clear rather than something
                # like "Invalid pointer returned from OGROpen".
                raise OGRException('Could not open the datasource at "%s"' % ds_input)
        elif isinstance(ds_input, self.ptr_type) and isinstance(ds_driver, Driver.ptr_type):
            ds = ds_input
        else:
            raise OGRException('Invalid data source input type: %s' % type(ds_input))


        if ds:
            if not isinstance(ds_driver, Driver):
                ds_driver = capi.get_ds_driver(ds)
                ds_driver = Driver(ds_driver)
            self.ptr = ds
            self.driver = ds_driver
        else:
            # Raise an exception if the returned pointer is NULL
            raise OGRException('Invalid data source file "%s"' % ds_input)

    def __del__(self):
        "Destroys this DataStructure object."
        if self._ptr and capi:
            capi.close_ds(self._ptr)

    def __iter__(self):
        "Allows for iteration over the layers in a data source."
        for i in xrange(self.band_count):
            yield self[i]

    def __getitem__(self, index):
        "Allows use of the index [] operator to get a layer at the index."
        if isinstance(index, int):
            if index < 0 or index >= self.band_count:
                raise OGRIndexError('index out of range')
            b = capi.get_ds_raster_band(self._ptr, index)
        else:
            raise TypeError('Invalid index type: %s' % type(index))
        # return Layer(l, self)
        return b

    def __len__(self):
        "Returns the number of layers within the data source."
        return self.band_count

    def __str__(self):
        "Returns OGR GetName and Driver for the Data Source."
        return '%s' % (self.name)

    @property
    def band_count(self):
        "Returns the number of layers in the data source."
        return capi.get_ds_raster_count(self._ptr)

    @property
    def name(self):
        "Returns the name of the data source."
        name = capi.get_ds_description(self._ptr)
        return force_text(name, self.encoding, strings_only=True)
