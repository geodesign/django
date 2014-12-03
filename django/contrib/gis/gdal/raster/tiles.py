"""
This module hosts the Tiler class.

Tiler can be used to create Tile Map Service (TMS) tiles from a GDALRaster.

The xyz tiles can be used in views that act as TMS endpoints and serve raster
data in a scaleable and flexible way to endusers.

An input raster is automatically reprojected into the web-mercator projection
(epsg 3857) and split into tiles that are aligned with the XYZ tile definitions
of the TMS standard.

For example, with a model TileModel that has three integer fields x, y and z
and a raster field rast, the following would create a set of TMS tiles from
a given GDALRaster:

    rast = GDALRaster('/path/to/raster.tif')
    tiler = Tiler(rast)
    for x, y, z, tile in tiler.tiles():
        TileModel.create(x=x, y=y, z=z, rast=tile)
"""
from math import pi

from django.contrib.gis.gdal.raster.rasters import GDALRaster

class Tiler(object):
    "TMS Tiling engine for GDALRasters."

    def __init__(self, rast, **kwargs):
        if not isinstance(rast, GDALRaster):
            raise ValueError('Input must be a GDALRaster.')

        # Set defining constants
        self._tile_srid = kwargs.get('srid', 3857) 
        self._tile_size = kwargs.get('tilesize', 256)
        self._world_size = kwargs.get('worldsize', 2 * pi * 6378137)
        self._tile_shift = kwargs.get('tileshift', self._world_size / 2.0)
        self._zoomdown = kwargs.get('zoomdown', True)

        # Reproject the raster if necessary
        if not rast.srid == self._tile_srid:
            rast = rast.warp(srid=self._tile_srid)

        # Store the raster
        self.rast = rast

    def _set_zoomdown(self, value):
        """
        Sets the zoomdown value. This controls if the next-above or next-below
        tile layer should be used as the highest zoom level. Also consult the
        `get_max_zoom_level` method.
        """
        self._zoomdown = value

    def _get_zoomdown(self):
        "Returns the zoomdown parameter value."
        return self._zoomdown

    zoomdown = property(_get_zoomdown, _set_zoomdown)

    def get_max_zoom_level(self):
        """
        Returns the maximum zoomlevel for this raster's scale.

        By default, the maximum zoom level is the next underlying zoomlevel
        when compared to the raster layer's actual scale.

        The behaviour is controlled by the zoomdown property. If the zoomdown
        property is set to True (which is the default), and the original raster
        scale lies between zoom levels 2 and 3, the max zoom level is 3, if
        zoomdown is set to False, it is 2.
        """
        # Calculate all pixelsizes for the TMS zoom levels
        tms_pixelsizes = [self._world_size / (2.0**i * self._tile_size) for\
                          i in range(1, 19)]

        # If the pixelsize is smaller than all tms sizes, default to max level
        zoomlevel = 18

        # Find next-upper zoomlevel for the raster pixel scale
        for i in range(18):
            if self.rast.scalex - tms_pixelsizes[i] >= 0:
                zoomlevel = i
                break

        # If nextdown flag is true, adjust level to text-down
        if self._zoomdown:
            zoomlevel += 1

        return zoomlevel

    def get_tile_index_range(self, zoom):
        """
        Calculates index range for a given bounding box and zoomlevel.
        It returns maximum and minimum x and y tile indices that overlap
        with the input bbox at zoomlevel z.
        """
        # Calculate tile size for given zoom level
        tilesize = self._world_size / 2**zoom

        # Get extent for raster to compute tile ranges
        bbox = self.rast.extent

        # Calculate overlaying tile indices
        return [
            int((bbox[0] + self._tile_shift)/tilesize),
            int((self._tile_shift - bbox[3])/tilesize),
            int((bbox[2] + self._tile_shift)/tilesize),
            int((self._tile_shift - bbox[1])/tilesize)]

    def get_tile_bounds(self, x, y, z):
        "Calculates bounding box of a x-y-z tile."

        # Calculate size of tiles in meters
        tilesize = self._world_size / 2**z

        # Calculate corner values of bbox
        xmin = x * tilesize - self._tile_shift
        xmax = (x+1) * tilesize - self._tile_shift
        ymin = self._tile_shift - (y+1) * tilesize
        ymax = self._tile_shift - y * tilesize

        # Return bounding box
        return (xmin, ymin, xmax, ymax)

    def get_tile_scale(self, zoom):
        "Calculates pixel size scale for given zoom level."
        return self._world_size / 2.0**zoom / self._tile_size

    def get_tile(self, x, y, z):
        "Extracts a tile from this raster and returns it as a GDALRaster."
        # Calculate scale and bounds for this tile
        scale = self.get_tile_scale(z)
        bounds = self.get_tile_bounds(x, y, z)

        # Prepare name for tile creation
        name = self.rast.name + '-{0}-{1}-{2}.{3}'\
                                .format(x, y, z, self.rast.driver.name.lower())

        # Warp this dataset into a xyz tile using the calculated parameters
        return self.rast.warp(name=name,
                              scalex=scale, scaley=-scale,
                              originx=bounds[0], originy=bounds[3],
                              sizex=self._tile_size, sizey=self._tile_size,
                              driver='MEM')

    def tiles(self):
        """
        Returns an iterator over all tiles for the raterlayer.

        Use as follows:

        ds = GDALRaster('/path/to/file/rast.tif')
        tiler = Tiler(ds)
        for x, y, z, tile in tiler.tiles():
            print x, y, z, tile
        """
        max_zoom = self.get_max_zoom_level()
        for z in range(max_zoom + 1):
            indices = self.get_tile_index_range(z)
            for x in range(indices[0], indices[2] + 1):
                for y in range(indices[1], indices[3] + 1):
                    yield x, y, z, self.get_tile(x, y, z)
