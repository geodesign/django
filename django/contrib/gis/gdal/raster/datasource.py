# ctypes prerequisites.
from ctypes import byref, c_double

# The GDAL C library, OGR exceptions, and the Layer object.
from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.raster.driver import Driver
from django.contrib.gis.gdal.raster.bands import Band
from django.contrib.gis.gdal.error import OGRException, OGRIndexError
from django.contrib.gis.gdal.srs import SpatialReference, CoordTransform

# Getting the ctypes prototypes for the DataSource.
from django.contrib.gis.gdal.raster.prototypes import ds as capi
from django.contrib.gis.gdal.raster import utils

from django.utils.encoding import force_bytes, force_text
from django.utils import six
from django.utils.six.moves import xrange


class DataSource(GDALBase):
    "Wraps an GDAL Raster object."

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
                ds_input['datatype'] = utils.GDAL_PIXEL_TYPES_INV[ds_input['datatype']]

            # Create empty in-memory raster if input data is tuple
            ds_driver = Driver('MEM')
            ds = capi.create_ds(
                ds_driver.ptr, force_bytes(''),
                ds_input['sizex'], ds_input['sizey'],
                ds_input['bands'], ds_input['datatype'], None
            )
        elif isinstance(ds_input, six.string_types):
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
            # Raster band index starts at 1
            index += 1
            b = capi.get_ds_raster_band(self._ptr, index)
        else:
            raise TypeError('Invalid index type: %s' % type(index))
        return Band(b, self)

    def __len__(self):
        "Returns the number of layers within the data source."
        return self.band_count

    def __str__(self):
        "Returns OGR GetName and Driver for the Data Source."
        return '%s' % (self.name)

    @property
    def name(self):
        "Returns the name of the data source."
        name = capi.get_ds_description(self._ptr)
        return force_text(name, self.encoding, strings_only=True)

    @property
    def sizex(self):
        return capi.get_ds_xsize(self._ptr)

    @property
    def sizey(self):
        return capi.get_ds_ysize(self._ptr)

    @property
    def nr_of_pixels(self):
        return self.sizex*self.sizey

    @property
    def band_count(self):
        "Returns the number of layers in the data source."
        return capi.get_ds_raster_count(self._ptr)



    def _get_geotransform(self):
        "Returns the geotransform of the data source"
        gt = (c_double*6)()
        capi.get_ds_geotransform(self._ptr, byref(gt))
        return list(gt)

    def _set_geotransform(self, gt):
        "Sets the geotransform for the data source"
        if len(gt) != 6 or any([not isinstance(x, (int,float)) for x in gt]):
            raise ValueError(
                'GeoTransform must be a list or tuple of 6 numeric values')
        gt = (c_double*6)(*gt)
        capi.set_ds_geotransform(self._ptr, byref(gt))

    geotransform = property(_get_geotransform, _set_geotransform)

    #### SpatialReference-related Properties ####

    # The projection reference property
    # This property is what defines the raster projection, but it is kept
    # private and should normally be set through the srs property,
    # either from an srid or an srs object itself.
    def _get_projection_ref(self):
        return capi.get_ds_projection_ref(self._ptr)

    def _set_projection_ref(self, prj):
        capi.set_ds_projection_ref(self._ptr, prj)

    _projection_ref = property(_get_projection_ref, _set_projection_ref)

    _srs = None

    # The SRS property
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
            raise TypeError('Cannot assign spatial reference with object of type: %s' % type(srs))

        self._projection_ref = self._srs.wkt

    srs = property(_get_srs, _set_srs)

    # The SRID property
    def _get_srid(self):
        srs = self.srs
        if srs:
            return srs.srid
        return None

    def _set_srid(self, srid):
        if isinstance(srid, six.integer_types):
            self.srs = srid
        else:
            raise TypeError('SRID must be set with an integer.')

    srid = property(_get_srid, _set_srid)


    #### PostGIS IO Routines ####
    def _to_postgis_raster(self):
        """Retruns the raster as postgis raster string"""

        # Get GDAL geotransform for header data
        gt = self.geotransform

        # Get other required header data
        num_bands = self.band_count
        pixelcount = self.nr_of_pixels

        # Setup raster header as array, first two numbers are 
        # endianness and version, which are fixed by postgis.
        rasterheader = (1, 0, num_bands, gt[1], gt[5], gt[0], gt[3], 
                        gt[2], gt[4], self.srid, self.sizex, self.sizey)

        # Pack header into binary data
        result = utils.pack(utils.HEADER_STRUCTURE, rasterheader)

        # Pack band data, add to result
        for band in self:
        # for i in range(num_bands):
            # Get band
            # band = self.ptr.GetRasterBand(i + 1)

            # Set base structure for raster header - pixeltype
            structure = 'B'

            # Get band header data
            nodata = band.nodata_value
            pixeltype = utils.convert_pixeltype(band.datatype, 'gdal', 'postgis')

            if nodata < 0 and pixeltype in utils.GDAL_PIXEL_TYPES_UNISGNED:
                nodata = abs(nodata)

            if nodata is not None:
                # Setup packing structure for header with nodata
                structure += utils.convert_pixeltype(pixeltype, 'postgis', 'struct')

                # Add flag to point to existing nodata type
                pixeltype += 64

            # Pack header
            bandheader = utils.pack(structure, (pixeltype, nodata))

            # Read raster as binary and hexlify
            data = band.ReadRaster()
            data = binascii.hexlify(data).upper()

            # Add band to result string
            result += bandheader + data

        # Return PostGIS Raster String
        return result