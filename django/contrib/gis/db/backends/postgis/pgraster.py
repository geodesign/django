import binascii
import struct

from django.forms import ValidationError

from .const import (
    GDAL_TO_POSTGIS, GDAL_TO_STRUCT, POSTGIS_HEADER_STRUCTURE, POSTGIS_TO_GDAL,
    STRUCT_SIZE,
)


def pack(structure, data):
    """
    Packs data into hex string with little endian format.
    """
    return binascii.hexlify(struct.pack('<' + structure, *data)).upper()


def unpack(structure, data):
    """
    Unpacks little endian hexlified binary string into python list.
    """
    return struct.unpack('<' + structure, binascii.unhexlify(data))


def chunk(data, index):
    """
    Splits a string into two parts at the input index.
    """
    return data[:index], data[index:]


def band_to_hex(band):
    """
    Returns a GDALBand's pixel values as PGRaster Band hex string.
    """
    return binascii.hexlify(band.data(as_memoryview=True)).upper()


def from_pgraster(data):
    """
    Converts a PostGIS HEX String into a python dictionary.
    """
    # Abort if input data is null
    if data is None:
        return

    # Split raster header from data
    header, data = chunk(data, 122)
    header = unpack(POSTGIS_HEADER_STRUCTURE, header)

    # Parse band data
    bands = []
    pixeltypes = []
    while data:
        # Get pixel type for this band
        pixeltype, data = chunk(data, 2)
        pixeltype = unpack('B', pixeltype)[0]

        # Subtract nodata byte from band nodata value if exists
        has_nodata = pixeltype >= 64
        if has_nodata:
            pixeltype -= 64

        # Convert datatype from PostGIS to GDAL & get pack type and size
        pixeltype = POSTGIS_TO_GDAL[pixeltype]
        pack_type = GDAL_TO_STRUCT[pixeltype]
        pack_size = 2 * STRUCT_SIZE[pack_type]

        # Parse band nodata value, even if it is ignored by the nodata flag
        nodata, data = chunk(data, pack_size)
        nodata = unpack(pack_type, nodata)[0]

        # Chunk and unpack band data (pack size times nr of pixels)
        band, data = chunk(data, pack_size * header[10] * header[11])
        band_result = {'data': binascii.unhexlify(band)}

        if has_nodata:
            band_result['nodata_value'] = nodata

        bands.append(band_result)
        pixeltypes.append(pixeltype)

    # Check that all bands have the same pixeltype, this is required by GDAL
    if len(set(pixeltypes)) != 1:
        raise ValidationError("Band pixeltypes are not all equal.")

    # Process raster header
    return {
        'srid': int(header[8]),
        'width': header[10], 'height': header[11],
        'datatype': pixeltypes[0],
        'origin': (header[5], header[6]),
        'scale': (header[3], header[4]),
        'skew': (header[7], header[8]),
        'bands': bands
    }


def to_pgraster(rast):
    """
    Converts a GDALRaster into PostGIS Raster format.
    """
    # Abort if raster is null
    if rast is None:
        return

    # Prepare the raster header data as tuple. The first two numbers are
    # the endianness and the PostGIS Raster Version, both are fixed by
    # PostGIS at the moment.
    rasterheader = (1, 0, len(rast.bands), rast.scale.x, rast.scale.y,
                    rast.origin.x, rast.origin.y, rast.skew.x, rast.skew.y,
                    rast.srs.srid, rast.width, rast.height)

    # Hexlify raster header
    result = pack(POSTGIS_HEADER_STRUCTURE, rasterheader)

    for band in rast.bands:
        # The PostGIS WKB band header has two elements, a 8BUI byte and the
        # nodata value.
        #
        # The 8BUI stores both the PostGIS pixel data type and a nodata flag.
        # It is composed as the datatype integer plus 64 as a flag for existing
        # nodata values. As a formula one could write:
        # 8BUI_VALUE = PG_PIXEL_TYPE (0-11) + FLAG (0 or 64)
        #
        # For example, if the byte value is 71, then the datatype is
        # 71-64 = 7 (32BSI) and the nodata value is True.
        structure = 'B' + GDAL_TO_STRUCT[band.datatype()]

        # Get band pixel type in PostGIS notation
        pixeltype = GDAL_TO_POSTGIS[band.datatype()]

        # Set the nodata flag
        if band.nodata_value is not None:
            pixeltype += 64

        # Pack band header
        bandheader = pack(structure, (pixeltype, band.nodata_value or 0))

        # Add packed header and band data to result string
        result += bandheader + band_to_hex(band)

    # Cast raster to string before passing it to the DB
    result = result.decode()

    return result
