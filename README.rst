

commit f269c1d6f6dcc22c0a781f3223c6da0a4483b06e Date: Fri Mar 13 18:49:02 2015 +0000

    Added write support for GDALRaster

        Instantiation of GDALRaster instances from dict or json data.
        Retrieve and write pixel values in GDALBand objects.
        Support for the GDALFlushCache in gdal C prototypes
        Added private flush method to GDALRaster to make sure all data is written to files when file-based rasters are changed.
        Replaced ptr with _ptr for internal ptr variable

    Refs #23804. Thanks Claude Paroz and Tim Graham for the reviews.

commit 0d9b018e07c384314e142372153eb670c2e129f3 Date: Fri Mar 20 17:12:44 2015 +0000

    Fixed gis test failures when numpy isn't installed.

    Thanks to Bas Peschier for pointing this out. Refs #23804.

commit 32ed4c202f9f8ecd0bf305db06d363cd7a9927eb Date: Mon Feb 9 10:14:48 2015 +0000

    Moved numpy import helper to shortcuts

    Numpy will be used in both the geos and gdal modules, so the import should sit in the parent module gis.

commit 26996e2d55719deb0a0b85c642c88658c929106c Date:   Tue Mar 17 11:16:50 2015 -0400

    Fixed #24499 -- Dropped support for PostGIS 1.5.

commit b769bbd4f6a3cd1bcd9ebf3559ec6ea0f9b50565 Date: Fri Jun 19 16:46:03 2015 +0100

    Fixed #23804 -- Added RasterField for PostGIS.

    Thanks to Tim Graham and Claude Paroz for the reviews and patches.

commit 3ef03d09b36b628f5c33e9ea94a20125c76206a0 Date: Fri Jun 19 13:56:50 2015 +0100

    Warp and transform methods for GDALRasters

    Thanks to Tim Graham for the review
