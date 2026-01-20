# En comercial/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def comercial_view(request): # <--- ¡VERIFICA ESTE NOMBRE!
    """Vista del Dashboard Principal del Módulo Comercial."""
    context = {
        'titulo_modulo': 'Comercial y Ventas',
        'subtitulo_modulo': 'Dashboard Principal de Ventas',
    }
    # Esta plantilla ya debe existir (la creamos en el paso anterior como 'comercial.html')
    return render(request, 'comercial/dashboard.html', context)
def clientes_view(request): # <--- ¡VERIFICA ESTE NOMBRE!
    """Vista del Dashboard Principal del Módulo Comercial."""
    context = {
        'titulo_modulo': 'Comercial y Ventas',
        'subtitulo_modulo': 'Dashboard Principal de Ventas',
    }
    # Esta plantilla ya debe existir (la creamos en el paso anterior como 'comercial.html')
    return render(request, 'comercial/clientes.html', context)
def reportes_view(request): # <--- ¡VERIFICA ESTE NOMBRE!
    """Vista del Dashboard Principal del Módulo Comercial."""
    context = {
        'titulo_modulo': 'Comercial y Ventas',
        'subtitulo_modulo': 'Dashboard Principal de Ventas',
    }
    # Esta plantilla ya debe existir (la creamos en el paso anterior como 'comercial.html')
    return render(request, 'comercial/reportes.html', context)
def pedidos_view(request): # <--- ¡VERIFICA ESTE NOMBRE!
    """Vista del Dashboard Principal del Módulo Comercial."""
    context = {
        'titulo_modulo': 'Comercial y Ventas',
        'subtitulo_modulo': 'Dashboard Principal de Ventas',
    }
    # Esta plantilla ya debe existir (la creamos en el paso anterior como 'comercial.html')
    return render(request, 'comercial/pedidos.html', context)