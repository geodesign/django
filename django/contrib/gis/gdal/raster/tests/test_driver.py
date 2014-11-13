import unittest
from unittest import skipUnless

from django.contrib.gis.gdal import HAS_GDAL

if HAS_GDAL:
    from django.contrib.gis.gdal import OGRException
    from django.contrib.gis.gdal.raster.driver import Driver


valid_drivers = [
    'GTiff', 'NITF', 'RPFTOC', 'ECRGTOC', 'HFA', 'SAR_CEOS', 'CEOS',
    'JAXAPALSAR', 'GFF', 'ELAS', 'AIG', 'AAIGrid', 'GRASSASCIIGrid', 'SDTS',
    'OGDI', 'DTED', 'PNG', 'JPEG', 'MEM', 'JDEM', 'GIF', 'BIGGIF', 'ESAT',
    'BSB', 'XPM', 'BMP', 'DIMAP', 'AirSAR', 'RS2', 'PCIDSK', 'PCRaster',
    'ILWIS', 'SGI', 'SRTMHGT', 'Leveller', 'Terragen', 'GMT', 'netCDF',
    'HDF4', 'HDF4Image', 'ISIS3', 'ISIS2', 'PDS', 'TIL', 'ERS', 'L1B', 'FIT',
    'GRIB', 'JPEG2000', 'RMF', 'WCS', 'WMS', 'MSGN', 'RST', 'INGR', 'GSAG',
    'GSBG', 'GS7BG', 'COSAR', 'TSX', 'COASP', 'R', 'MAP', 'PNM', 'DOQ1',
    'DOQ2', 'ENVI', 'EHdr', 'GenBin', 'PAux', 'MFF', 'MFF2', 'FujiBAS', 'GSC',
    'FAST', 'BT', 'LAN', 'CPG', 'IDA', 'NDF', 'EIR', 'DIPEx', 'LCP', 'GTX',
    'LOSLAS', 'NTv2', 'CTable2', 'ACE2', 'SNODAS', 'KRO', 'ARG', 'RIK',
    'USGSDEM', 'GXF', 'DODS', 'HTTP', 'BAG', 'HDF5', 'HDF5Image', 'NWT_GRD',
    'NWT_GRC', 'ADRG', 'SRP', 'BLX', 'Rasterlite', 'EPSILON', 'PostGISRaster',
    'SAGA', 'KMLSUPEROVERLAY', 'XYZ', 'HF2', 'PDF', 'OZI', 'CTG', 'E00GRID',
    'WEBP', 'ZMap', 'NGSGEOID', 'MBTiles', 'IRIS'
]

invalid_drivers = ('Foo baz', 'clucka', 'ESRI rast')

aliases = {
    'MeMory': 'MEM',
    'tiFf': 'GTiff',
    'tIf': 'GTiff',
    'jPEg': 'JPEG',
    'jpG': 'JPEG',
}

@skipUnless(HAS_GDAL, "GDAL is required")
class RasterDriverTest(unittest.TestCase):

    def test01_valid_driver(self):
        "Testing valid GDAL Data Source Drivers."
        for d in valid_drivers:
            dr = Driver(d)
            self.assertEqual(d, str(dr))

    def test02_invalid_driver(self):
        "Testing invalid GDAL Data Source Drivers."
        for i in invalid_drivers:
            self.assertRaises(OGRException, Driver, i)

    def test03_aliases(self):
        "Testing driver aliases."
        for alias, full_name in aliases.items():
            dr = Driver(alias)
            self.assertEqual(full_name, str(dr))
