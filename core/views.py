from django.shortcuts import render
from django.contrib import messages
from .forms import ContatoForms
from django.http import JsonResponse

import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from pysheds.grid import Grid
import mplleaflet
from django.views.decorators.csrf import csrf_protect

@csrf_protect

def get(request):


    mini_bacia = request.GET.get("mini_bacia")
    print(mini_bacia)
    # Open a digital elevation model
    in_point = mini_bacia.split(",")
    folder_master = r'C:\Users\matheus.sampaio.RHAMA0\Desktop\Nova pasta (2)'
    # Carrega o raster HydroSHEDS (DEM 15 arc-seconds)
    r_path = r'{}\\Default_DEM.tif'.format(
        folder_master)  # Mosaico 15as (450m)#Define a function to plot the digital elevation model

    grid = Grid.from_raster(r_path, data_name='dem')

    # clear vars
    # tempo
    t2 = time.time()
    print("Tempo total: {:2f} minutos".format(1 / 60 * (t2 - t1)))

    # Cria uma janela em torno do ponto; dg é o tamanho da janela em  graus decimais
    dg = 6.5
    xmin, xmax, ymin, ymax = in_point[0] - dg, in_point[0] + dg, in_point[1] - dg, in_point[1] + dg,
    # Define a janela no DEM
    new_bbox = (xmin, ymin, xmax, ymax)
    # Aplica a janela
    grid.set_bbox(new_bbox)
    # clear vars

    # Salvo no HD um novo raster recortado
    # =============================================================================
    raster_name = 'raster_auxiliar' # nome do raster recordato
    r_path = raster_dir + '\\' + raster_name + r'.tif'
    grid.to_raster('dem', r_path, apply_mask=False)
    # =============================================================================
    # Limpo da memoria o anterior
    del grid

    # Lê novamente o raster recortado
    grid = Grid.from_raster(r_path, data_name='dem')
    # clear vars
    # tempo
    t2 = time.time()
    print("Tempo total: {:2f} minutos".format(1 / 60 * (t2 - t1)))

    def plotFigure(data, label, cmap='Blues'):
        plt.figure(figsize=(12, 10))
        plt.imshow(data, extent=grid.extent)
        plt.colorbar(label=label)
        plt.grid()

    # Minnor slicing on borders to enhance colobars
    elevDem = grid.dem[:-1, :-1]
    plotFigure(elevDem, 'Elevation (m)')
    # Detect depressions

    # Detect depressions
    depressions = grid.detect_depressions('dem')

    # Plot depressions
    plt.imshow(depressions)
    # Fill depressions
    grid.fill_depressions(data='dem', out_name='flooded_dem')
    # Test result
    depressions = grid.detect_depressions('flooded_dem')
    plt.imshow(depressions)
    # Detect flats
    flats = grid.detect_flats('flooded_dem')

    # Plot flats
    plt.imshow(flats)
    grid.resolve_flats(data='flooded_dem', out_name='inflated_dem')
    plt.imshow(grid.inflated_dem[:-1, :-1])
    # Create a flow direction grid
    # N    NE    E    SE    S    SW    W    NW
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
    grid.flowdir(data='inflated_dem', out_name='dir', dirmap=dirmap)
    plotFigure(grid.dir, 'Flow Direction', 'viridis')
    # Specify discharge point
    x, y = -53.51613, -23.17931
    # Delineate the catchment
    grid.catchment(data='dir', x=x, y=y, dirmap=dirmap, out_name='catch',
                   recursionlimit=15000, xytype='label', nodata_out=0)
    # Clip the bounding box to the catchment
    grid.clip_to('catch')
    # Get a view of the catchment
    demView = grid.view('dem', nodata=np.nan)
    plotFigure(demView, 'Elevation')
    # export selected raster
    grid.to_raster(demView, '{}/clippedElevations_WGS84.tif'.format(folder_master))
    # Define the stream network

    grid.accumulation(data='catch', dirmap=dirmap, pad_inplace=False, out_name='acc')

    accView = grid.view('acc', nodata=np.nan)
    plotFigure(accView, "Cell Number", 'PuRd')
    streams = grid.extract_river_network('catch', 'acc', threshold=200, dirmap=dirmap)
    streams["features"][:2]

    def saveDict(dic, file):
        f = open(file, 'w')
        f.write(str(dic))
        f.close()

    # save geojson as separate file
    saveDict(streams, '{}/streams_WGS84.geojson'.format(folder_master))
    # Some functions to plot the json on jupyter notebook
    streamNet = gpd.read_file('{}/streams_WGS84.geojson'.format(folder_master))
    streamNet.crs = {'init': 'epsg:4326'}
    # The polygonize argument defaults to the grid mask when no arguments are supplied
    shapes = grid.polygonize()

    # Plot catchment boundaries
    fig, ax = plt.subplots(figsize=(6.5, 6.5))

    for shape in shapes:
        coords = np.asarray(shape[0]['coordinates'][0])
        ax.plot(coords[:, 0], coords[:, 1], color='cyan')

    ax.set_xlim(grid.bbox[0], grid.bbox[2])
    ax.set_ylim(grid.bbox[1], grid.bbox[3])
    ax.set_title('Catchment boundary (vector)')
    gpd.plotting.plot_dataframe(streamNet, None, cmap='Blues', ax=ax)
    # ax = streamNet.plot()
    mplleaflet.display(fig=ax.figure, crs=streamNet.crs, tiles='esri_aerial')
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

