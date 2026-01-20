from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Empresa, ReporteAsistencia, ArchivoReporte
from .forms import EmpresaForm, ReporteAsistenciaForm, ArchivoReporteFormSet
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
import os
from django.conf import settings
from django.template.loader import get_template
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from xhtml2pdf import pisa
from .models import ReporteAsistencia
import io
from django.core.files.storage import default_storage
from PyPDF2 import PdfMerger
from django.utils.text import slugify
from django.http import FileResponse, Http404, HttpResponse
import mimetypes
@login_required
def clientes_dashboard(request):
    """Dashboard principal del módulo de clientes"""
    total_empresas = Empresa.objects.filter(activo=True).count()
    total_reportes = ReporteAsistencia.objects.count()
    # Ordenamos por fecha de generación descendente para ver lo más nuevo primero
    reportes_recientes = ReporteAsistencia.objects.select_related('empresa', 'usuario').order_by('-fecha_generacion')[:5]
    
    context = {
        'total_empresas': total_empresas,
        'total_reportes': total_reportes,
        'reportes_recientes': reportes_recientes,
    }
    return render(request, 'clientes/dashboard.html', context)

@login_required
def asistencias_lista(request): # Nombre corregido para el urls.py
    """Lista de todos los reportes de asistencia con búsqueda y filtros"""
    reportes_list = ReporteAsistencia.objects.select_related(
        'empresa', 'usuario'
    ).prefetch_related('archivos').order_by('-fecha_asistencia')
    
    # Búsqueda
    search_query = request.GET.get('search', '')
    if search_query:
        reportes_list = reportes_list.filter(
            Q(numero_reporte__icontains=search_query) |
            Q(empresa__nombre__icontains=search_query) |
            Q(maquina__icontains=search_query) |
            Q(persona_solicita__icontains=search_query)
        )
    
    # Filtro por empresa
    empresa_id = request.GET.get('empresa', '')
    if empresa_id:
        reportes_list = reportes_list.filter(empresa_id=empresa_id)
    
    # Paginación
    paginator = Paginator(reportes_list, 15)
    page_number = request.GET.get('page')
    reportes = paginator.get_page(page_number)
    
    empresas = Empresa.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'reportes': reportes,
        'empresas': empresas,
        'search_query': search_query,
        'empresa_id': empresa_id,
    }
    return render(request, 'clientes/asistencias_lista.html', context)

@login_required
def empresas_lista(request): # Nombre corregido para el urls.py
    """Lista de empresas clientes"""
    empresas = Empresa.objects.annotate(
        total_reportes=Count('reportes')
    ).order_by('nombre')
    
    search_query = request.GET.get('search', '')
    if search_query:
        empresas = empresas.filter(nombre__icontains=search_query)
    
    context = {
        'empresas': empresas,
        'search_query': search_query,
    }
    return render(request, 'clientes/empresas_lista.html', context)

@login_required
def crear_reporte(request):
    """Vista para crear un nuevo reporte de asistencia"""
    if request.method == 'POST':
        form = ReporteAsistenciaForm(request.POST)
        formset = ArchivoReporteFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            # Guardar el reporte
            reporte = form.save(commit=False)
            reporte.usuario = request.user
            reporte.save()
            
            # Guardar los archivos adjuntos
            formset.instance = reporte
            formset.save()
            
            messages.success(
                request, 
                f'Reporte {reporte.numero_reporte} creado exitosamente.'
            )
            return redirect('clientes:detalle_reporte', pk=reporte.pk)
    else:
        form = ReporteAsistenciaForm()
        formset = ArchivoReporteFormSet()
    
    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'clientes/crear_reporte.html', context)

@login_required
def detalle_reporte(request, pk):
    """Vista detallada de un reporte de asistencia"""
    reporte = get_object_or_404(
        ReporteAsistencia.objects.select_related('empresa', 'usuario')
                                  .prefetch_related('archivos'),
        pk=pk
    )
    
    context = {
        'reporte': reporte,
    }
    return render(request, 'clientes/detalle_reporte.html', context)

@login_required
def editar_reporte(request, pk):
    """Vista para editar un reporte existente"""
    reporte = get_object_or_404(ReporteAsistencia, pk=pk)
    
    if request.method == 'POST':
        form = ReporteAsistenciaForm(request.POST, instance=reporte)
        formset = ArchivoReporteFormSet(request.POST, request.FILES, instance=reporte)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            messages.success(request, f'Reporte {reporte.numero_reporte} actualizado.')
            return redirect('clientes:detalle_reporte', pk=reporte.pk)
    else:
        form = ReporteAsistenciaForm(instance=reporte)
        formset = ArchivoReporteFormSet(instance=reporte)
    
    context = {
        'form': form,
        'formset': formset,
        'reporte': reporte,
        'editing': True,
    }
    return render(request, 'clientes/crear_reporte.html', context)

@login_required
def eliminar_reporte(request, pk):
    """Vista para eliminar un reporte"""
    reporte = get_object_or_404(ReporteAsistencia, pk=pk)
    
    if request.method == 'POST':
        numero = reporte.numero_reporte
        reporte.delete()
        messages.success(request, f'Reporte {numero} eliminado correctamente.')
        return redirect('clientes:asistencias')
    
    context = {
        'reporte': reporte,
    }
    return render(request, 'clientes/eliminar_reporte.html', context)

@login_required
def empresas_lista(request):
    """Lista de empresas clientes"""
    empresas = Empresa.objects.annotate(
        total_reportes=Count('reportes')
    ).order_by('nombre')
    
    # Búsqueda
    search_query = request.GET.get('search', '')
    if search_query:
        empresas = empresas.filter(nombre__icontains=search_query)
    
    context = {
        'empresas': empresas,
        'search_query': search_query,
    }
    return render(request, 'clientes/empresas_lista.html', context)

@login_required
def crear_empresa(request):
    """Vista para crear una nueva empresa"""
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, f'Empresa {empresa.nombre} creada exitosamente.')
            return redirect('clientes:empresas')
    else:
        form = EmpresaForm()
    
    context = {
        'form': form,
    }
    return render(request, 'clientes/crear_empresa.html', context)
@login_required
def reporte_pdf(request, pk):
    reporte = get_object_or_404(ReporteAsistencia, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Reporte_{reporte.numero_reporte}.pdf"'
    
    p = canvas.Canvas(response)
    p.drawString(100, 800, f"REPORTE DE ASISTENCIA: {reporte.numero_reporte}")
    p.drawString(100, 780, f"Empresa: {reporte.empresa.nombre}")
    p.drawString(100, 760, f"Fecha Servicio: {reporte.fecha_asistencia}")
    p.drawString(100, 740, f"Máquina: {reporte.maquina}")
    p.drawString(100, 720, f"Problema: {reporte.problema}")
    p.drawString(100, 700, f"Solución: {reporte.solucion}")
    
    p.showPage()
    p.save()
    return response
def link_callback(uri, rel):
    """
    Convierte URIs de Media y Static en rutas de sistema de archivos absolutas
    para que xhtml2pdf pueda encontrar las imágenes.
    """
    sUrl = settings.STATIC_URL
    sRoot = settings.STATIC_ROOT
    mUrl = settings.MEDIA_URL
    mRoot = settings.MEDIA_ROOT

    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri

    # Asegurarse de que el archivo existe
    if not os.path.isfile(path):
        return uri
    return path

@login_required
def reporte_pdf(request, pk):
    reporte = get_object_or_404(ReporteAsistencia.objects.prefetch_related('archivos'), pk=pk)
    
    # 1. Generar el PDF del reporte base (HTML)
    template = get_template('clientes/reporte_pdf.html')
    html = template.render({'reporte': reporte})
    
    reporte_base_io = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=reporte_base_io, link_callback=link_callback)
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF base', status=500)

    # 2. Preparar el "Merger" para unir archivos
    merger = PdfMerger()
    
    # Añadimos el reporte base al principio
    reporte_base_io.seek(0)
    merger.append(reporte_base_io)

    # 3. Buscar adjuntos que sean PDF y unirlos
    for adjunto in reporte.archivos.all():
        if adjunto.archivo.name.lower().endswith('.pdf'):
            try:
                # Abrimos el archivo desde el almacenamiento
                path_archivo = adjunto.archivo.path
                merger.append(path_archivo)
            except Exception as e:
                print(f"No se pudo adjuntar el PDF {adjunto.archivo.name}: {e}")

    # 4. Crear la respuesta final
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Reporte_Completo_{reporte.numero_reporte}.pdf"'
    
    # Guardar todo el contenido unido en la respuesta
    merger.write(response)
    merger.close()

    return response
@login_required
def listar_documentos_red(request):
    """Explorador de archivos para la Unidad Y:"""
    subruta = request.GET.get('p', '')
    ruta_base = settings.RUTA_DATOS_EXTERNA
    ruta_objetivo = os.path.normpath(os.path.join(ruta_base, subruta))

    # Seguridad: Evitar que el usuario acceda a carpetas fuera de la base
    if not os.path.abspath(ruta_objetivo).startswith(os.path.abspath(ruta_base)):
        return redirect('clientes:listar_documentos_red')

    items = []
    try:
        with os.scandir(ruta_objetivo) as entradas:
            for entrada in entradas:
                stats = entrada.stat()
                items.append({
                    'nombre': entrada.name,
                    'es_dir': entrada.is_dir(),
                    'tamaño': round(stats.st_size / 1024, 2) if entrada.is_file() else None,
                    'ruta_relativa': os.path.join(subruta, entrada.name).replace("\\", "/")
                })
    except Exception as e:
        return render(request, 'clientes/documentos_red.html', {'error': str(e)})

    # Lógica para navegación y breadcrumbs
    context = {
        'items': sorted(items, key=lambda x: (not x['es_dir'], x['nombre'].lower())),
        'subruta': subruta,
        'subruta_partes': subruta.split('/') if subruta else [],
        'ruta_padre': os.path.dirname(subruta.rstrip('/')).replace("\\", "/"),
    }
    return render(request, 'clientes/documentos_red.html', context)

@login_required
def ver_documento_red(request, nombre_archivo):
    """Sirve archivos desde subcarpetas de la red"""
    ruta_completa = os.path.normpath(os.path.join(settings.RUTA_DATOS_EXTERNA, nombre_archivo))
    
    if not os.path.exists(ruta_completa) or os.path.isdir(ruta_completa):
        raise Http404("El archivo no existe en el servidor.")

    content_type, _ = mimetypes.guess_type(ruta_completa)
    response = FileResponse(open(ruta_completa, 'rb'), content_type=content_type or 'application/octet-stream')
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(ruta_completa)}"'
    return response