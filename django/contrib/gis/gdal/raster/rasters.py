import os
from math import pi
from ctypes import byref, addressof, POINTER, c_double, c_void_p, c_char_p

from django.utils import six
from django.contrib.gis.geometry.regex import hex_regex
from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.raster.driver import Driver
from django.contrib.gis.gdal.raster.bands import GDALBand
from django.contrib.gis.gdal.error import GDALException, SRSException,\
    OGRIndexError
from django.contrib.gis.gdal.srs import SpatialReference
from django.contrib.gis.gdal.raster.prototypes import ds as capi
from django.contrib.gis.gdal.raster import utils


class GDALRaster(GDALBase):
    "Wraps a GDAL Data Source object."

    #### Python magic routines ####

    def __init__(self, ds_input, write=False):
        # The write flag.
        if write:
            self._write = 1
        else:
            self._write = 0

        # Registering all the drivers
        if not capi.get_driver_count():
            capi.register_all()

        # If input is a valid file path, try setting file as source.
        if isinstance(ds_input, six.string_types) and os.path.exists(ds_input):
            try:
                # GDALOpen will auto-detect the data source type.
                self.ptr = capi.open_ds(ds_input, self._write)
            except GDALException:
                raise GDALException('Could not open the datasource at '\
                                    '"{0}".'.format(ds_input))

        # If string is not a file, try to interpret it as postgis raster
        elif isinstance(ds_input, six.string_types) and\
             hex_regex.match(ds_input):

            try:
                # Parse data
                header, bands = utils.parse_wkb(ds_input)

                # Instantiate in-memory raster
                self.ptr = utils.ptr_from_dict(header)

                # Set projection
                self.srid = header['srid']

                # Set GeoTransform
                self.geotransform = [
                    header['originx'], header['scalex'], header['skewx'],
                    header['originy'], header['skewy'], header['scaley']]

                # Write bands
                for i in range(header['nr_of_bands']):
                    # Get band
                    bnd = self[i]

                    # Write data to band
                    bnd.data = bands[i]['data']

                    # Set band nodata value if available
                    if bands[i]['nodata'] is not None:
                        bnd.nodata_value = bands[i]['nodata']
            except:
                raise #GDALException('Could not parse postgis raster.')

        # If input is dict, create empty in-memory raster.
        elif isinstance(ds_input, dict):
            self.ptr = utils.ptr_from_dict(ds_input)
        # If input is a pointer, use it directly
        elif isinstance(ds_input, self.ptr_type):
            self.ptr = ds_input
        else:
            raise GDALException('Invalid data source input type: "{0}".'\
                                .format(type(ds_input)))

    def __del__(self):
        "Destroys this DataStructure object."
        if self._ptr:
            capi.close_ds(self._ptr)

    def __str__(self):
        "Returns Description of the Data Source."
        return self.name

    def __repr__(self):
        "Short-hand representation because WKB may be very large."
        return '<Raster object at %s>' % hex(addressof(self.ptr))

    def __len__(self):
        "Returns the number of bands within the raster."
        return self.band_count

    # For accessing the raster bands
    _bands = []

    def __getitem__(self, index):
        """
        Allows use of the index [] operator to get a band at the index.
        This caches initiated bands in _bands array.
        """
        # Instantiate band cache array
        if not len(self._bands):
            self._bands = [None] * len(self)

        if isinstance(index, int):
            if index < 0 or index >= len(self._bands):
                raise OGRIndexError('Index out of range.')

            # Create GDALBand if not cached
            if not self._bands[index]:
                # GDAL Raster band counts start at 1
                band_index = index + 1
                band_ptr = capi.get_ds_raster_band(self.ptr, band_index)
                self._bands[index] = GDALBand(band_ptr)
        else:
            raise TypeError('Invalid index type: %s' % type(index))

        # Return band
        return self._bands[index]

    def __iter__(self):
        "Allows for iteration over the bands in a data source."
        for i in xrange(self.band_count):
            yield self[i]

    #### Raster Driver ####

    _driver = None

    @property
    def driver(self):
        "Returns the driver of this data source."
        if not self._driver:
            ds_driver = capi.get_ds_driver(self.ptr)
            self._driver = Driver(ds_driver)
        return self._driver

    def copy_ptr(self, destination=None):
        "Retruns a deep-copy of this raster's gdal dataset pointer."
        # Auto-generate a copy name if not provided
        if not destination:
            destination = self.name + '_copy.' + self.driver.name.lower()

        # Copy datasource
        return capi.copy_ds(self.driver.ptr, destination, self.ptr, False,
                            POINTER(c_char_p)(), c_void_p(), c_void_p())

    #### Basic Raster Properties ####

    @property
    def name(self):
        "Returns the name of the data source."
        return capi.get_ds_description(self.ptr)

    @property
    def sizex(self):
        "Returns number of pixels of the raster in x direction."
        return capi.get_ds_xsize(self.ptr)

    @property
    def sizey(self):
        "Returns number of pixels of the raster in y direction."
        return capi.get_ds_ysize(self.ptr)

    @property
    def nr_of_pixels(self):
        "Returns total number of pixels of the raster."
        return self.sizex * self.sizey

    @property
    def band_count(self):
        "Returns the number of bands in the raster."
        return capi.get_ds_raster_count(self.ptr)

    _geotransform = None

    # Geotransform property (location and scale of raster)
    def _get_geotransform(self):
        "Returns the geotransform of the data source."

        if not self._geotransform:
            # Create empty ctypes double array for data
            gtf = (c_double*6)()

            # Write data to array
            try:
                capi.get_ds_geotransform(self.ptr, byref(gtf))
            except:
                return None

            # Convert data to list
            self._geotransform = list(gtf)
        
        return self._geotransform

    def _set_geotransform(self, gtf):
        "Sets the geotransform for the data source."
        # Check input
        if len(gtf) != 6 or\
           any([not isinstance(x, (int, float)) for x in gtf]):
            raise ValueError(
                'GeoTransform must be a list or tuple of 6 numeric values.')
        # Reset cache
        self._geotransform = None

        # Prepare ctypes double array with input data for writing
        gtf = (c_double*6)(gtf[0], gtf[1],
                           gtf[2], gtf[3],
                           gtf[4], gtf[5])

        # Write geotransform
        capi.set_ds_geotransform(self.ptr, byref(gtf))

    geotransform = property(_get_geotransform, _set_geotransform)

    def _get_originx(self):
        "Returns x coordinate of origin (upper-left corner)."
        if not self.geotransform:
            return None
        return self.geotransform[0]

    def _set_originx(self, data):
        "Sets x coordinate of origin (upper-left corner)."
        if not self.geotransform:
            raise ValueError('Set entire geotransform before '\
                             'setting individual elements.')
        gtf = self.geotransform
        gtf[0] = data
        self.geotransform = gtf

    originx = property(_get_originx, _set_originx)
        
    def _get_originy(self):
        "Returns y coordinate of origin (upper-left corner)."
        if not self.geotransform:
            return None
        return self.geotransform[3]

    def _set_originy(self, data):
        "Sets y coordinate of origin (upper-left corner)."
        if not self.geotransform:
            raise ValueError('Set entire geotransform before '\
                             'setting individual elements.')
        gtf = self.geotransform
        gtf[3] = data
        self.geotransform = gtf

    originy = property(_get_originy, _set_originy)

    def _get_scalex(self):
        "Returns the scale of pixels in x direction."
        if not self.geotransform:
            return None
        return self.geotransform[1]

    def _set_scalex(self, data):
        "Sets the scale of pixels in x direction."
        if not self.geotransform:
            raise ValueError('Set entire geotransform before '\
                             'setting individual elements.')
        gtf = self.geotransform
        gtf[1] = data
        self.geotransform = gtf

    scalex = property(_get_scalex, _set_scalex)

    def _get_scaley(self):
        "Returns the scale of pixels in y direction."
        if not self.geotransform:
            return None
        return self.geotransform[5]

    def _set_scaley(self, data):
        "Sets the scale of pixels in y direction."
        if not self.geotransform:
            raise ValueError('Set entire geotransform before '\
                             'setting individual elements.')
        gtf = self.geotransform
        gtf[5] = data
        self.geotransform = gtf

    scaley = property(_get_scaley, _set_scaley)

    def _get_skewx(self):
        "Returns skew of pixels in x direction."
        if not self.geotransform:
            return None
        return self.geotransform[2]

    def _set_skewx(self, data):
        "Sets skew of pixels in x direction."
        if not self.geotransform:
            raise ValueError('Set entire geotransform before '\
                             'setting individual elements.')
        gtf = self.geotransform
        gtf[2] = data
        self.geotransform = gtf

    skewx = property(_get_skewx, _set_skewx)

    def _get_skewy(self):
        "Returns skew of pixels in y direction."
        if not self.geotransform:
            return None
        return self.geotransform[4]

    def _set_skewy(self, data):
        "Sets skew of pixels in y direction."
        if not self.geotransform:
            raise ValueError('Set entire geotransform before '\
                             'setting individual elements.')
        gtf = self.geotransform
        gtf[4] = data
        self.geotransform = gtf

    skewy = property(_get_skewy, _set_skewy)

    @property
    def extent(self):
        "Returns extent as tuple (xmin, ymin, xmax, ymax)"
        # Cacluate boundary values based on scale and size
        xval = self.originx + self.scalex * self.sizex
        yval = self.originy + self.scaley * self.sizey

        # Calculate min and max values
        xmin = min(xval, self.originx)
        xmax = max(xval, self.originx)
        ymin = min(yval, self.originy)
        ymax = max(yval, self.originy)

        # Return extent
        return xmin, ymin, xmax, ymax

    #### SpatialReference-related Properties ####

    # The projection reference property
    # This property is what defines the raster projection and is used by gdal.
    # However, the projection ref it is kept private and should only be accessed
    # or altered through the srid or the srs property.
    def _get_projection_ref(self):
        "Returns projectction reference string as WKT."
        return capi.get_ds_projection_ref(self.ptr)

    def _set_projection_ref(self, prj):
        "Sets projection reference string from WKT."
        capi.set_ds_projection_ref(self.ptr, prj)

    _projection_ref = property(_get_projection_ref, _set_projection_ref)

    # The SRS property
    _srs = None

    def _get_srs(self):
        "Returns a Spatial Reference object for this Raster."
        if not self._srs:
            try:
                self._srs = SpatialReference(self._projection_ref)
            except SRSException:
                raise
        return self._srs

    def _set_srs(self, srs):
        "Sets the Spatial Reference object for this Raster."

        if isinstance(srs, SpatialReference):
            self._srs = srs
        elif isinstance(srs, six.integer_types + six.string_types):
            self._srs = SpatialReference(srs)
        else:
            raise TypeError('Cannot assign spatial reference with '\
                            'object of type: {0}'.format(type(srs)))

        self._projection_ref = self._srs.wkt

    srs = property(_get_srs, _set_srs)

    # The SRID property
    def _get_srid(self):
        "Gets the SRID from the srs object"
        srs = self.srs
        if srs:
            return srs.srid
        return None

    def _set_srid(self, srid):
        "Sets the SRID for the raster"
        if isinstance(srid, six.integer_types):
            self.srs = srid
        else:
            raise TypeError('SRID must be set with an integer.')

    srid = property(_get_srid, _set_srid)

    #### Warping - reprojection & resampling ####

    def warp(self, **kwargs):
        """
        Returns a warped GDALRaster with the given input characteristics.

        The input parameters that can be used are all geotransform factors and
        the srid. For instance, ds.warp({'srid': 4326}) returns the raster in
        the coordinate system WGS84.

        By default, the warp functions keeps all parameters equal to the
        original ones. This includes the driver, a copy of the raster is
        created with the original name plus _copy. + DriverName. Alternatively,
        specify what driver to use.

        Note that the new dataset is not closed, so not all data is written to
        disk at the end of the warp routine. The data is only written to disk
        completely upon releasing of the object. This usually happens when the
        object is overwritten or the function/script ends. To force all data
        to be written to disk, close dataset by setting it to None.

        dst = src.warp(srid=4326)
        dst = None
        """
        # Prepare driver and raster name
        drivername = kwargs.get('driver', self.driver.name)
        rastername = kwargs.get('name', self.name + '_copy.' + drivername)

        # Setup destination raster with input or default parameters
        dst = GDALRaster({'driver': kwargs.get('driver', drivername),
                          'sizex': kwargs.get('sizex', self.sizex), 
                          'sizey': kwargs.get('sizey', self.sizey),
                          'nr_of_bands': self.band_count, 
                          'datatype': self[0].datatype,
                          'name': rastername})
        
        dst.srid = kwargs.get('srid', self.srid)

        # Set geotransform from original raster and change it subsequently
        dst.geotransform = self.geotransform

        # Transform origin coordinates and update destination geotransfrom
        originx = kwargs.get('originx', None)
        originy = kwargs.get('originy', None)
        if None in (originx, originy):
            newx, newy = utils.transform_coords(self.originx, self.originy,
                                                self.srid, dst.srid)
            if originx is None:
                originx = newx
            if originy is None:
                originy = newy

        dst.originx = originx
        dst.originy = originy

        # Calculate new scales and update destination geotransform
        scalex = kwargs.get('scalex', None)
        scaley = kwargs.get('scaley', None)
        if None in (scalex, scaley):
            # Calculate scale of raster in new coordinate system
            newx, newy = utils.calculate_scale(self, dst.srid)
            if scalex is None:
                scalex = newx
            if scaley is None:
                scaley = newy

        dst.scalex = scalex
        dst.scaley = scaley

        # Select resampling algorithm
        algo = kwargs.get('algorithm', 0)
        if isinstance(algo, str):
            algo = utils.GDAL_RESAMPLE_ALGORITHMS_INV[algo]

        # Reproject image
        capi.reproject_image(self.ptr, self.srs.wkt, dst.ptr,
                             dst.srs.wkt, algo, 0.0, 0.0, c_void_p(),
                             c_void_p(), c_void_p())

        return dst

    #### Raster IO Section ####

    # PostGIS WKB property
    @property
    def wkb(self):
        "Retruns the raster as PostGIS WKB."
        # Get GDAL geotransform for header data
        gtf = self.geotransform

        # Get other required header data
        num_bands = self.band_count

        # Createthe raster header as array. The first two numbers are
        # endianness and pgraster-version, which are fixed by postgis.
        rasterheader = (1, 0, num_bands, gtf[1], gtf[5], gtf[0], gtf[3], 
                        gtf[2], gtf[4], self.srid, self.sizex, self.sizey)

        # Pack header into binary data
        result = utils.pack(utils.HEADER_STRUCTURE, rasterheader)

        # Pack band data, add to result
        for band in self:
            # Set byte struct for converting datatype and nodata flag.
            # In postgis, the datatype and the nodata flag are combined
            # in a 8BUI. The integer is composed as the datatype integer
            # plus 64 (one bit) as a flag for existing nodata values.
            #
            # I.e. if the byte value is 71, the datatype is 71-64 = 7 (32BSI)
            # and a nodata value exists.
            structure = 'B'

            # Get band pixel type structure string
            pixeltype = utils.convert_pixeltype(band.datatype,
                                                'gdal', 'postgis')

            # Get nodata value, if exists add to header
            nodata = band.nodata_value
            if nodata is not None:
                # Sanity check on nodata value
                if nodata < 0 and pixeltype in utils.GDAL_PIXEL_TYPES_UNISGNED:
                    print 'WARNING: Negative nodata value for unsigned type.'
                    nodata = abs(nodata)

                # Add nodata packing structure
                structure += utils.convert_pixeltype(pixeltype,
                                                     'postgis', 'struct')

                # Add nodata flag to pixeltype byte
                pixeltype += 64

                # Set header tuple with nodata value
                bandheader = (pixeltype, nodata)
            else:
                # Set header tuple without nodata value
                bandheader = (pixeltype, )

            # Pack band header
            bandheader = utils.pack(structure, bandheader)

            # Add band to result string
            result += bandheader + band.hex

        # Return PostGIS Raster String
        return result
