from django.shortcuts import render
from django.contrib import messages
from .forms import ContatoForms
from django.http import JsonResponse

from pysheds.grid import Grid
import fiona
from osgeo import osr, ogr
from shapely.geometry import mapping, Point
import numpy as np
import time
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.colors as colors

from django.views.decorators.csrf import csrf_protect

@csrf_protect

def get(request):


    mini_bacia = request.GET.get("mini_bacia")
    #print(mini_bacia)
    # Open a digital elevation model
    in_point = mini_bacia.split(",")
    print(type(in_point))

    sys.setrecursionlimit(2500000)
    #
    PATH_DEFAULT_DEM = r"C:\Users\Matheus\Desktop\Delimita_bacias\delimita_bacias\core\static\MDE\sa_dem_15s\DEM_450.tif"

    PATH_ROOT = r"C:\Users\Matheus\Desktop\Delimita_bacias\delimita_bacias\core\static\MDE"

    PATH_RASTER = PATH_DEFAULT_DEM
    ACCUMULATED_TRESHOLD = 200 / (450 * 450 / 1e6)
    snap = in_point[1], in_point[0]
    POUR_POINT = tuple(map(float, snap))
    grid = Grid.from_raster(PATH_RASTER, data_name='dem')

    print("\nProcessando, aguarde!\n")
    dg = 6.5
    xmin, xmax, ymin, ymax = float(in_point[1]) - dg, float(in_point[1]) + dg, float(in_point[0]) - dg, float(in_point[0]) + dg,
    # Define a janela no DEM
    new_bbox = (xmin, ymin, xmax, ymax)
    # Aplica a janela
    grid.set_bbox(new_bbox)
    # clear vars

    # Salvo no HD um novo raster recortado
    # =============================================================================
    raster_name = 'raster_auxiliar' # nome do raster recordato
    r_path = PATH_ROOT + '\\' + raster_name + r'.tif'
    grid.to_raster('dem', r_path, apply_mask=False)
    # =============================================================================
    # Limpo da memoria o anterior
    del grid
    grid = Grid.from_raster(r_path, data_name='dem')

    grid.fill_pits(data='dem', out_name='filled_dem')

    grid.fill_depressions(data='filled_dem', out_name='flooded_dem')

    grid.resolve_flats(data='flooded_dem', out_name='inflated_dem')

    # 'd8'    N    NE    E    SE    S    SW    W    NW
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)

    # Compute flow direction based on corrected DEM
    grid.flowdir(data='inflated_dem',
                 out_name='dir',
                 dirmap=dirmap)
    print("\nCorrigiu depressões!\n")

    # Compute flow accumulation based on computed flow direction
    grid.accumulation(data='dir', out_name='acc', pad_inplace=False)

    pour_point = POUR_POINT

    #ACCUMULATED_TRESHOLD = np.max(grid.acc) - 1000

    snapped_point, dist = grid.snap_to_mask(grid.acc > ACCUMULATED_TRESHOLD,
                                            pour_point,
                                            return_dist=True)

    fig, ax = plt.subplots(figsize=(10, 10))

    plt.imshow(grid.dem,
               cmap="terrain", zorder=1, extent=grid.acc.extent)
    plt.scatter(pour_point[0], pour_point[1], s=300, marker='o',
                color='r', zorder=2, label="Pour Point")
    plt.scatter(snapped_point[0], snapped_point[1], s=500, marker='x',
                color='k', zorder=2, label="Snapped Point")
    plt.legend(markerscale=.5)
    plt.savefig(os.path.join(PATH_ROOT, r"FIGURES\1.pour_x_snapped.png"),
                dpi=300, bbox_inches='tight')
    plt.close(fig)

    grid.catchment(data=grid.view('dir'),
                   x=snapped_point[0],
                   y=snapped_point[1],
                   out_name='catch',
                   recursionlimit=2500,
                   xytype='label')

    nz_y, nz_x = np.nonzero(grid.catch)
    xmin, xmax = np.min(nz_x), np.max(nz_x)
    ymin, ymax = np.min(nz_y), np.max(nz_y)

    grid.clip_to('catch')
    catch = grid.view('catch',
                      nodata=np.nan)

    fig, ax = plt.subplots(figsize=(8, 8))
    # fig.patch.set_alpha(0)

    # plt.grid('on', zorder=0)
    plt.imshow(np.where(grid.catch[ymin:ymax, xmin:xmax], grid.dem[ymin:ymax, xmin:xmax], np.nan),
               extent=grid.acc.extent,
               zorder=1,
               cmap='terrain')
    cbar = plt.colorbar(orientation="vertical", pad=.05, fraction=.025)
    cbar.set_label('Elevation (m)', fontsize=20, labelpad=+20)
    # plt.grid('on', zorder=0)
    # im = ax.imshow(catch,
    #               # extent=grid.extent,
    #                zorder=1,
    #                cmap='terrain')
    plt.axis("off")
    # p = plt.colorbar()
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    # plt.title('Delineated Catchment')
    plt.savefig(os.path.join(PATH_ROOT, fr"FIGURES\2.catchment_elevation.png"),
                dpi=300, bbox_inches='tight')
    # plt.show()

    grid.accumulation(data='catch',
                      dirmap=dirmap,
                      out_name='acc',
                      xytype='label',
                      pad_inplace=True)

    shapes = grid.polygonize()
    schema = {
        'geometry': 'Polygon',
        'properties': {}  # 'LABEL': 'float:16'
    }
    PATH_OUT_CATCHMENT = os.path.join(PATH_ROOT, fr'FIGURES\catchment.geojson')
    with fiona.open(PATH_OUT_CATCHMENT, 'w',
                    driver='GeoJSON',
                    crs=grid.crs.srs,
                    schema=schema) as c:
        i = 0
        for shape, value in shapes:
            rec = {}
            rec['geometry'] = shape
            rec['properties'] = {}  # 'LABEL' : str(value)
            rec['id'] = str(i)
            c.write(rec)

    fig, ax = plt.subplots(figsize=(10, 10))

    print("\nDelimitou a bacia!\n")

    # plt.grid('off', zorder=0)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    # plt.title('River network (>%d accumulation)' % (DRAINAGE_TRESHOLD))
    plt.xlim(grid.bbox[0] - .05, grid.bbox[2] + .05)
    plt.ylim(grid.bbox[1] - .05, grid.bbox[3] + .05)
    plt.scatter(snapped_point[0], snapped_point[1], s=150, marker='o', color='k')
    ax.set_aspect('equal')

    shapes = grid.polygonize()
    for shape in shapes:
        coords = np.asarray(shape[0]['coordinates'][0])
        plt.plot(coords[:, 0], coords[:, 1], color='k')

    plt.imshow(np.where(grid.catch[ymin:ymax, xmin:xmax], grid.dem[ymin:ymax, xmin:xmax], np.nan),
               extent=grid.acc.extent,
               zorder=1,
               cmap='terrain')

    for n, drainage_ts in enumerate(
            [grid.acc.max() / 1000, grid.acc.max() / 100, grid.acc.max() / 10, grid.acc.max() - 100]):

        branches = grid.extract_river_network('catch', 'acc',
                                              threshold=drainage_ts,
                                              dirmap=dirmap)

        if not branches["features"]:  # No drainage with specified accumulation
            break

        for branch in branches['features']:
            line = np.asarray(branch['geometry']['coordinates'])
            plt.plot(line[:, 0], line[:, 1], 'b', linewidth=0.25 + n * 0.5)

        # TODO: WRAP A FUNCTION!
        schema = {
            'geometry': 'LineString',
            'properties': {}
        }
        PATH_OUT_DRAINAGE = os.path.join(PATH_ROOT, fr'FIGURES\drainage_{n}.geojson')
        with fiona.open(PATH_OUT_DRAINAGE, 'w',
                        driver='GeoJSON',
                        crs=grid.crs.srs,
                        schema=schema) as c:
            i = 0
            for branch in branches['features']:
                rec = {}
                rec['geometry'] = branch['geometry']
                rec['properties'] = {}
                rec['id'] = str(i)
                c.write(rec)
                i += 1

    plt.savefig(os.path.join(PATH_ROOT, r"FIGURES\Figura 1.png"),
                dpi=300, bbox_inches='tight')

    print("\nprocessamento finalizado! Verifique os arquivos de saída.\n")

    #
    target_EPSG = 32722  # UTM 22S

    driver = ogr.GetDriverByName("GeoJSON")
    dataSource = driver.Open(PATH_OUT_CATCHMENT, 1)
    layer = dataSource.GetLayer()

    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)  # WGS 84

    target = osr.SpatialReference()
    target.ImportFromEPSG(target_EPSG)

    area = 0
    for feature in layer:
        geom = feature.GetGeometryRef()
        #     spatialRef = geom.GetSpatialReference()
        transform = osr.CoordinateTransformation(source, target)  # spatialRef, target
        geom.Transform(transform)
        area += geom.GetArea()  # Sum areas of all polygons

    print("%.3f km²" % (area / 1000000))
    #
    context = {
        "mini": mini_bacia
    }
    return JsonResponse(list(context), safe=False)







def index(request):
    return render(request, 'index.html')

def mapa(request):
    return render(request, 'mapa.html')

def grafico(request):
    return render(request, 'grafico.html')

def teste(request):
    return render(request, 'teste.html')


def contato(request):
    form = ContatoForms(request.POST or None)

    if str(request.method) == 'POST':
        if form.is_valid():
            form.send_mail()

            messages.success(request, "E-mail enviado com Sucesso!")
            form = ContatoForms()

        else:
            messages.error(request, "Erro ao enviar E-mail""")
    context = {
        'form': form
    }
    return render(request, 'contato.html', context)

