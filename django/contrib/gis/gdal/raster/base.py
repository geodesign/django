from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.prototypes import raster as capi


class GDALRasterBase(GDALBase):
    """
    Base class with attributes that exist both in GDALRaster and GDALBand
    objects.
    """
    @property
    def metadata(self):
        """
        Returns the metadata for this GDAL Major Object.
        """
        # Create initial metadata domain list containing the default domain.
        # The default is returned if domain name is None.
        domain_list = ['DEFAULT']

        # Get additional metadata domains from the raster.
        meta_list = capi.get_ds_metadata_domain_list(self.ptr)
        if meta_list:
            # The number of domains is unknown, so we need to retrieve data
            # until there are no more values in the ctypes array.
            counter = 0
            domain = meta_list.contents[counter]
            while domain:
                domain_list.append(domain)
                counter += 1
                domain = meta_list.contents[counter]

        # Retrieve metadata values for each domain.
        result = {}
        for domain in domain_list:
            # Get metadata for this domain.
            data = capi.get_ds_metadata(
                self.ptr,
                None if domain == 'DEFAULT' else domain
            )
            if not data:
                continue

            # The number of metadata items is unknown, so we need to retrieve
            # data until there are no more values in the ctypes array.
            domain_meta = {}
            counter = 0
            item = data.contents[counter]
            while item:
                key, val = item.split('=')
                domain_meta[key] = val
                counter += 1
                item = data.contents[counter]

            # The default domain values are returned if domain is None.
            result[domain if domain else 'DEFAULT'] = domain_meta

        return result
