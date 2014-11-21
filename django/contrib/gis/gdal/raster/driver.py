from ctypes import c_void_p
from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.gdal.raster.prototypes import ds as capi
from django.utils import six
from django.utils.encoding import force_bytes

class Driver(GDALBase):
    "Wraps the GDAL Driver Object."

    # Case-insensitive aliases for some GDAL Raster Drivers.
    # For a complete list of original driver names see
    # http://www.gdal.org/formats_list.html
    _alias = {'memory': 'MEM',
              'tiff': 'GTiff',
              'tif': 'GTiff',
              'jpeg': 'JPEG',
              'jpg': 'JPEG'}

    def __init__(self, dr_input):
        "Initializes an GDAL Raster driver on either a string or integer input."

        if isinstance(dr_input, six.string_types):
            # If a string name of the driver was passed in
            self._register()

            # Checking the alias dictionary (case-insensitive) to see if an
            # alias exists for the given driver.
            if dr_input.lower() in self._alias:
                name = self._alias[dr_input.lower()]
            else:
                name = dr_input

            # Attempting to get the GDAL driver by the string name.
            driver = capi.get_driver_by_name(force_bytes(name))
        elif isinstance(dr_input, int):
            self._register()
            driver = capi.get_driver(dr_input)
        elif isinstance(dr_input, c_void_p):
            driver = dr_input
        else:
            raise GDALException('Unrecognized input type for GDAL Driver: '\
                                '{0}'.format(type(dr_input)))

        # Making sure we get a valid pointer to the GDAL Driver
        if not driver:
            raise GDALException('Could not initialize GDAL Driver '\
                                'on input: {0}'.format(dr_input))
        self.ptr = driver

    def __str__(self):
        "Returns the description of the GDAL Driver."
        return self.name

    def _register(self):
        "Attempts to register all the data source drivers."
        # Only register all if the driver count is 0 (or else all drivers
        # will be registered over and over again)
        if not self.driver_count:
            capi.register_all()

    # Driver properties
    @property
    def driver_count(self):
        "Returns the number of GDAL data source drivers registered."
        return capi.get_driver_count()

    @property
    def name(self):
        "Returns description string for this driver."
        return capi.get_driver_description(self.ptr)
