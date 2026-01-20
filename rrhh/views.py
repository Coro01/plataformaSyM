from django.shortcuts import render
from django.contrib.auth.decorators import login_required # ¡Asegúrate de tener esta importación!

@login_required
def rrhh_dashboard_view(request):
    """
    Vista principal del Módulo RR.HH. (HUB Nivel 2).
    Redirige a 'salarios' o muestra botones de navegación.
    """
    # Usaremos esta vista como el punto de entrada para mostrar la navegación.
    return render(request, 'rrhh/rrhh_dashboard.html')

@login_required
def salarios_view(request):
    """Muestra la tabla de salarios y la barra de navegación del módulo."""
    # Lógica para salarios...
    return render(request, 'rrhh/salarios.html', {'titulo_seccion': 'Gestión de Salarios'})

@login_required
def vacaciones_view(request):
    """Muestra la gestión de vacaciones y la barra de navegación del módulo."""
    # Lógica para vacaciones...
    return render(request, 'rrhh/vacaciones.html', {'titulo_seccion': 'Gestión de Vacaciones'})

# Nota: He cambiado 'salarios_view' por 'rrhh_dashboard_view' como la principal. 
# Si el botón del Dashboard Global apunta a 'rrhh:salarios', repara esa URL más abajo.