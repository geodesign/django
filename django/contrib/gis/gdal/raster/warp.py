from ctypes import c_char_p, c_double, c_int, c_void_p, POINTER

from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.raster.prototypes import warp as capi
from django.contrib.gis.gdal.raster.rasters import GDALRaster


class GDALWarp(GDALBase):

    def __init__(self, source, destination):
        
        # self.options = capi.create_warp_options()
        # self.options.contents.hSrcDS = source.ptr
        # self.options.contents.hDstDS = destination.ptr

        # self.options.contents.nBandCount = source.band_count
        # bandarray_src = (c_int*source.band_count)(*[i+1 for i in range(source.band_count)])
        # bandarray_dst = (c_int*source.band_count)(*[i+1 for i in range(source.band_count)])
        # self.options.contents.panSrcBands = bandarray_src
        # self.options.contents.panDstBands = bandarray_dst
        capi.bla(source.ptr, source.srs.wkt, destination.ptr, destination.srs.wkt, 0, 0.0, 0.0, c_void_p(), c_void_p(), c_void_p())

        # self.options.contents.pTransformerArg = capi.create_img_transformer(source.ptr, source.srs.wkt, destination.ptr, destination.srs.wkt, 0, 0.0, 1)

        # self.operation = capi.warp_operation_init(self.options)
        # capi.warp_image(0, 0, dest.sizex, dest.sizey)

        # capi.destroy_img_transformer(self.transformer)
        # capi.destroy_warp_options(self.options)

        # orig = OGRGeometry('POINT ({0} {1})'.format(repr(source.originx), repr(source.originy)), source.srid)
        # trans = OGRGeometry('POINT (992385.4472045 481455.4944650)', 2774)

        # # Using an srid, a SpatialReference object, and a CoordTransform object
        # # or transformations.
        # t1, t2, t3 = orig.clone(), orig.clone(), orig.clone()
        # t1.transform(trans.srid)
        # t2.transform(SpatialReference('EPSG:2774'))
        # ct = CoordTransform(SpatialReference('WGS84'), SpatialReference(2774))
        # t3.transform(ct)

        # # Testing use of the `clone` keyword.
        # k1 = orig.clone()
        # k2 = k1.transform(trans.srid, clone=True)
        # self.assertEqual(k1, orig)
        # self.assertNotEqual(k1, k2)

        # prec = 3
        # for p in (t1, t2, t3, k2):
        #     self.assertAlmostEqual(trans.x, p.x, prec)
        #     self.assertAlmostEqual(trans.y, p.y, prec)