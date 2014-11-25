"""
 This module houses the ctypes function prototypes for GDAL Warper functions.
 http://www.gdal.org/warptut.html
 http://www.gdal.org/gdalwarper_8h.html
http://www.gdal.org/gdal__alg_8h_source.html
http://www.gdal.org/gdalwarper_8h_source.html
 http://tentacles666.wordpress.com/2012/01/21/python-ctypes-dereferencing-a-pointer-to-a-c/
"""
from ctypes import c_char_p, c_double, c_int, c_void_p, c_bool, c_float,\
    POINTER, Structure
from django.contrib.gis.gdal.libgdal import lgdal
from django.contrib.gis.gdal.prototypes.generation import const_string_output,\
    double_output, int_output, void_output, voidptr_output


class GDALWarpOptions(Structure):
    _fields_ = [
        ('warp_options', POINTER(c_char_p)),
        ('dfWarpMemoryLimit', c_double),
        ('eResampleAlg', c_int),
        ('GDALDataType', c_int),
        ('hSrcDS', c_void_p),
        ('hDstDS', c_void_p),
        ('nBandCount', c_int),
        ('panSrcBands', POINTER(c_int)),
        ('panDstBands', POINTER(c_int)),
        ('nSrcAlphaBand', c_int),
        ('nDstAlphaBand', c_int),
        ('padfSrcNoDataReal', POINTER(c_double)),
        ('padfSrcNoDataImag', POINTER(c_double)),
        ('padfDstNoDataReal', POINTER(c_double)),
        ('padfDstNoDataImag', POINTER(c_double)),
        ('pfnProgress', c_void_p),
        ('pProgressArg', c_void_p),
        ('pfnTransformer', c_void_p),
        ('pTransformerArg', c_void_p),
        ('papfnSrcPerBandValidityMaskFunc', c_void_p),
        ('papSrcPerBandValidityMaskFuncArg', c_void_p),
        ('pfnSrcValidityMaskFunc', c_void_p),
        ('pSrcValidityMaskFuncArg', c_void_p),
        ('pfnSrcDensityMaskFunc', c_void_p),
        ('pSrcDensityMaskFuncArg', c_void_p),
        ('pfnDstDensityMaskFunc', c_void_p),
        ('pDstDensityMaskFuncArg', c_void_p),
        ('pfnDstValidityMaskFunc', c_void_p),
        ('pDstValidityMaskFuncArg', c_void_p),
        ('pfnPreWarpChunkProcessor', c_void_p),
        ('pPreWarpProcessorArg', c_void_p),
        ('pfnPostWarpChunkProcessor', c_void_p),
        ('pPostWarpProcessorArg', c_void_p),
        ('hCutline', c_void_p),
        ('dfCutlineBlendDist', c_double)]


create_warp_options = lgdal.GDALCreateWarpOptions
create_warp_options.argtypes = []
create_warp_options.restype = POINTER(GDALWarpOptions)
destroy_warp_options = voidptr_output(lgdal.GDALDestroyWarpOptions, [c_void_p])

create_img_transformer = voidptr_output(lgdal.GDALCreateGenImgProjTransformer, [c_void_p, c_char_p, c_void_p, c_char_p, c_int, c_double, c_int])
destroy_img_transformer = void_output(lgdal.GDALDestroyGenImgProjTransformer, [c_void_p])

warp_operation_init = voidptr_output(lgdal.GDALCreateWarpOperation, [c_void_p])
warp_operation_destroy = void_output(lgdal.GDALDestroyWarpOperation, [c_void_p])
warp_image = voidptr_output(lgdal.GDALChunkAndWarpImage, [c_void_p, c_int, c_int, c_int, c_int])


# bla = voidptr_output(lgdal.GDALAutoCreateWarpedVRT, [c_void_p, c_char_p, c_char_p, c_int, c_double, c_void_p])

bla = void_output(lgdal.GDALReprojectImage, [c_void_p, c_char_p, c_void_p, c_char_p, 
                                                c_int, c_double, c_double,
                                                c_void_p, c_void_p, c_void_p])
"""


    GDALAllRegister();

    hSrcDS = GDALOpen( "in.tif", GA_ReadOnly );
    hDstDS = GDALOpen( "out.tif", GA_Update );

    // Setup warp options. 
    
    GDALWarpOptions *psWarpOptions = GDALCreateWarpOptions();

    psWarpOptions->hSrcDS = hSrcDS;
    psWarpOptions->hDstDS = hDstDS;

    psWarpOptions->nBandCount = 1;
    psWarpOptions->panSrcBands = 
        (int *) CPLMalloc(sizeof(int) * psWarpOptions->nBandCount );
    psWarpOptions->panSrcBands[0] = 1;
    psWarpOptions->panDstBands = 
        (int *) CPLMalloc(sizeof(int) * psWarpOptions->nBandCount );
    psWarpOptions->panDstBands[0] = 1;

    psWarpOptions->pfnProgress = GDALTermProgress;   

    // Establish reprojection transformer. 

    psWarpOptions->pTransformerArg = 
        GDALCreateGenImgProjTransformer( hSrcDS, 
                                         GDALGetProjectionRef(hSrcDS), 
                                         hDstDS,
                                         GDALGetProjectionRef(hDstDS), 
                                         FALSE, 0.0, 1 );
    psWarpOptions->pfnTransformer = GDALGenImgProjTransform;

    // Initialize and execute the warp operation. 

    GDALWarpOperation oOperation;

    oOperation.Initialize( psWarpOptions );
    oOperation.ChunkAndWarpImage( 0, 0, 
                                  GDALGetRasterXSize( hDstDS ), 
                                  GDALGetRasterYSize( hDstDS ) );

    GDALDestroyGenImgProjTransformer( psWarpOptions->pTransformerArg );
    GDALDestroyWarpOptions( psWarpOptions );

    GDALClose( hDstDS );
    GDALClose( hSrcDS );




    typedef enum { GRA_NearestNeighbour=0,                         GRA_Bilinear=1,  GRA_Cubic=2,     GRA_CubicSpline=3, GRA_Lanczos=4, GRA_Average=5,  GRA_Mode=6
    } GDALResampleAlg;



    """