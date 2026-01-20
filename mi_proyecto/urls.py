from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect 
# ==========================================================
# 🛑 IMPORTS NECESARIOS PARA SERVIR ARCHIVOS DE MEDIA 🛑
from django.conf import settings
from django.conf.urls.static import static 
# ==========================================================

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirige la URL principal (http://127.0.0.1:8000/) a la página de login
    path('', lambda r: redirect('SYM/login/'), name='root_redirect'),
    
    # Incluye todas las URLs de las aplicaciones
    path('', include('control_horas.urls')),
    path('SYM/compras/', include('compras.urls')),
    path('SYM/rrhh/', include('rrhh.urls')),
    path('SYM/comercial/', include('comercial.urls')),
     path('clientes/', include('clientes.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# ==========================================================
# 🛑 CÓDIGO CRÍTICO PARA SERVIR ARCHIVOS DE MEDIA EN DESARROLLO 🛑
# La línea `if settings.DEBUG:` asegura que esta configuración solo se aplique 
# cuando estás ejecutando el servidor de desarrollo local, no en producción.
# ==========================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    