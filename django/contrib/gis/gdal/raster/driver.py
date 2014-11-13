# prerequisites imports
from ctypes import c_void_p
from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.error import OGRException
from django.contrib.gis.gdal.raster.prototypes import ds as capi
from django.utils import six
from django.utils.encoding import force_bytes

class Driver(GDALBase):

    # Case-insensitive aliases for some GDAL Raster Drivers.
    # For a complete list of original driver names see
    # http://www.gdal.org/formats_list.html
    _alias = {'memory': 'MEM',
              'tiff': 'GTiff',
              'tif': 'GTiff',
              'jpeg': 'JPEG',
              'jpg': 'JPEG',
              }

    def __init__(self, dr_input):
        "Initializes an GDAL Raster driver on either a string or integer input."

        if isinstance(dr_input, six.string_types):
            # If a string name of the driver was passed in
            self._register()

            # Checking the alias dictionary (case-insensitive) to see if an alias
            #  exists for the given driver.
            if dr_input.lower() in self._alias:
                name = self._alias[dr_input.lower()]
            else:
                name = dr_input

            # Attempting to get the OGR driver by the string name.
            dr = capi.get_driver_by_name(force_bytes(name))
        elif isinstance(dr_input, int):
            self._register()
            dr = capi.get_driver(dr_input)
        elif isinstance(dr_input, c_void_p):
            dr = dr_input
        else:
            raise OGRException('Unrecognized input type for OGR Driver: %s' % str(type(dr_input)))

        # Making sure we get a valid pointer to the OGR Driver
        if not dr:
            raise OGRException('Could not initialize OGR Driver on input: %s' % str(dr_input))
        self.ptr = dr

    def __str__(self):
        "Returns the string name of the OGR Driver."
        return capi.get_driver_description(self.ptr)

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
