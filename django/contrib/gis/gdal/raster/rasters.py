import os, binascii
from ctypes import byref, c_double

from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
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

def mem_ptr_from_dict(header):
    """
    Returns pointer to in-memory raster created from input header.
    The reqiored keys are sizex, sizey, nr_of_bands and datatype.
    Where the datatype is a gdal pixeltype as string or integer.
    """

    # If data type is provided as string, map to integer
    pixeltype = header['datatype']
    if isinstance(pixeltype, str):
        pixeltype = utils.GDAL_PIXEL_TYPES_INV[pixeltype]

    # Create in-memory driver
    driver = Driver('MEM')

    # Create raster from driver with input characteristics
    return capi.create_ds(driver.ptr, force_bytes(''),
                         header['sizex'], header['sizey'],
                         header['nr_of_bands'], pixeltype, None)


class GDALRaster(GDALBase):
    "Wraps a GDAL Data Source object."

    #### Python 'magic' routines ####
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
        elif isinstance(ds_input, six.string_types) and hex_regex.match(ds_input):
            try:
                # Parse data
                header, bands = self._parse_postgis_raster(ds_input)

                # Instantiate in-memory driver
                self.ptr = mem_ptr_from_dict(header)

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
                    if bands[i]['nodata']:
                        bnd.nodata = bands[i]['nodata']
            except:
                raise GDALException('Could not parse postgis raster.')

        # If input is dict, create empty in-memory raster.
        elif isinstance(ds_input, dict):
            self.ptr = mem_ptr_from_dict(ds_input)
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

    ### Band access section
    _bands = []

    def __iter__(self):
        "Allows for iteration over the layers in a data source."
        for i in xrange(self.band_count):
            yield self[i]

    def __getitem__(self, index):
        """
        Allows use of the index [] operator to get a band at the index.
        Cache bands whenever possible.
        """
        # Prepare band array if its empty
        if not len(self._bands):
            self._bands = [None] * self.band_count

        if isinstance(index, int):
            if index < 0 or index >= len(self._bands):
                raise OGRIndexError('index out of range')

            # Check for cache first
            if self._bands[index] == None:
                # Raster band index starts at 1
                band_index = index + 1
                band = capi.get_ds_raster_band(self.ptr, band_index)
                self._bands[index] = GDALBand(band, self)
        else:
            raise TypeError('Invalid index type: %s' % type(index))

        return self._bands[index]

    def __len__(self):
        "Returns the number of layers within the data source."
        return self.band_count

    def __str__(self):
        "Returns Description of the Data Source."
        return self.name

    def __repr__(self):
        "Short-hand representation because WKB may be very large."
        return '<Raster object at %s>' % hex(addressof(self.ptr))

    _driver = None

    @property
    def driver(self):
        "Returns the driver of this data source."
        if not self._driver:
            ds_driver = capi.get_ds_driver(self.ptr)
            self._driver = Driver(ds_driver)
        return self._driver

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
        return self.sizex*self.sizey

    @property
    def band_count(self):
        "Returns the number of layers in the data source."
        return capi.get_ds_raster_count(self.ptr)

    def _get_geotransform(self):
        "Returns the geotransform of the data source."
        gtf = (c_double*6)()
        capi.get_ds_geotransform(self.ptr, byref(gtf))
        return list(gtf)

    def _set_geotransform(self, gtf):
        "Sets the geotransform for the data source"
        if len(gtf) != 6 or\
           any([not isinstance(x, (int, float)) for x in gtf]):
            raise ValueError(
                'GeoTransform must be a list or tuple of 6 numeric values')

        # Prepare ctypes double array for writing
        gtf = (c_double*6)(gtf[0], gtf[1],
                           gtf[2], gtf[3],
                           gtf[4], gtf[5])

        # Write geotransform
        capi.set_ds_geotransform(self.ptr, byref(gtf))

    geotransform = property(_get_geotransform, _set_geotransform)

    #### SpatialReference-related Properties ####
    # The projection reference property
    # This property is what defines the raster projection and is used by gdal
    # The projection ref it is kept private and should be accessed and altered
    # throug setting the srs property either from an srid or an srs object.
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

    ### PostGIS IO
    def _parse_postgis_raster(self, data):
        """
        Parses a PostGIS Raster String. Returns the raster header data as
        a dict and the bands as a list.
        """
        # Split raster header from data
        header, data = utils.chunk(data, 122)

        # Process header
        header = utils.unpack(utils.HEADER_STRUCTURE, header)
        header = dict(zip(utils.HEADER_NAMES, header))

        nr_of_pixels = header['sizex'] * header['sizey']

        # Process bands
        bands = []

        # Parse band data
        while data:
            # Get pixel type for this band
            pixeltype, data = utils.chunk(data, 2)
            pixeltype = utils.unpack('B', pixeltype)[0]

            # Substract nodata byte from band nodata value if exists
            has_nodata = pixeltype >= 64
            if has_nodata:
                pixeltype -= 64

            # String with hex type name for unpacking
            pack_type = utils.convert_pixeltype(pixeltype, 'postgis', 'struct')

            # Length in bytes of the hex type
            pixeltype_len = utils.STRUCT_SIZE[pack_type]

            # Get band nodata value if exists
            if has_nodata:
                nodata, data = utils.chunk(data, 2 * pixeltype_len)
                nodata = utils.unpack(pack_type, nodata)[0]
            else:
                nodata = None

            # PostGIS datatypes mapped to Gdalconstants data types
            pixtype_gdal = utils.convert_pixeltype(pixeltype, 'postgis', 'gdal')

            # Chunk and unpack band data
            band, data = utils.chunk(data, 2 * pixeltype_len * nr_of_pixels)
            bands.append({'type': pixtype_gdal, 'nodata': nodata,
                          'data': binascii.unhexlify(band)})

        # Check that all bands have the same pixeltype
        if len(set([x['type'] for x in bands])) != 1:
            raise ValidationError("Band pixeltypes of  are not all equal.")
        else:
            header['datatype'] = bands[0]['type']

        return header, bands


    def to_postgis_raster(self):
        """Retruns the raster as postgis raster string"""

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
            # Set base structure for raster header - pixeltype
            structure = utils.GDAL_PIXEL_TYPES[band.datatype]
            structure = utils.GDAL_TO_STRUCT[structure]
            if not structure:
                raise ValueError('GDAL Pixel type not supported by postgis.')

            # Get band header data
            nodata = band.nodata_value
            pixeltype = utils.convert_pixeltype(band.datatype,
                                                'gdal', 'postgis')

            if nodata < 0 and pixeltype in utils.GDAL_PIXEL_TYPES_UNISGNED:
                nodata = abs(nodata)

            if nodata is not None:
                # Setup packing structure for header with nodata
                structure += utils.convert_pixeltype(pixeltype,
                                                     'postgis', 'struct')

                # Add flag to point to existing nodata type
                pixeltype += 64

            # Pack header
            bandheader = utils.pack(structure, (pixeltype, nodata))

            # Add band to result string
            result += bandheader + band.hex

        # Return PostGIS Raster String
        return result
