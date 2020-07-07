from django.urls import path
from .views import index, contato, mapa, teste, grafico, get
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('', index, name='index'),
    path('/busca', get, name='busca'),
    path('/contato/', contato, name='contato'),
    path('/mapa', mapa, name='mapa'),
    path('/teste', teste, name='teste'),
    path('/grafico/', grafico, name='grafico'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
