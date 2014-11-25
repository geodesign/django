import os, unittest
from unittest import skipUnless

from django.contrib.gis.gdal import HAS_GDAL

if HAS_GDAL:
    from django.contrib.gis.gdal.error import OGRException
    from django.contrib.gis.gdal.raster.rasters import GDALRaster
    from django.contrib.gis.gdal.raster.warp import GDALWarp
    from django.contrib.gis.gdal import (OGRGeometry, OGRGeomType,
        OGRException, OGRIndexError, SpatialReference, CoordTransform,
        GDAL_VERSION)

@skipUnless(HAS_GDAL, "GDAL is required")
class WarpTest(unittest.TestCase):

    def setUp(self):
        self.ds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    'data/raster.tif')                                                    
        self.ds = GDALRaster(self.ds_path)
        self.ds.srid = 3086

    def test_warp(self):
        "Testing warp."
        dst = GDALRaster(self.ds.copy_ptr(), write=True)
        dst = GDALRaster({'sizex': 255, 'sizey': 255, 'nr_of_bands': 1, 'datatype': 1, 'driver': 'tif', 'name': self.ds.name + '_copy.tif'})
        dst.srid = 3857

        gt = self.ds.geotransform
        print gt


        # pt = 'POINT ({0} {1})'.format(repr(self.ds.originx), repr(self.ds.originy))
        pt = 'POINT (511700.4680706557 435103.3771231986)'
        orig = OGRGeometry(pt, self.ds.srid)
        orig.transform(dst.srid)
        gt[0] = orig.x
        gt[3] = orig.y
        gt = [-9224247.324296974, 100.0, 0.0, 3238525.0136368074, 0.0, -100.0]
        dst.geotransform = gt
        GDALWarp(self.ds, dst)
        
