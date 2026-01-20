from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse, FileResponse
from django.db.models import Q, F, Max
from django.db import transaction 
from django.contrib import messages 
from decimal import Decimal
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
import json
from datetime import datetime

# MODELOS
from .models import Inventario, StockMovement, Factura, FacturaProducto, Proveedor

# UTILIDADES
from .utils import extraer_datos_pdf, generar_pdf_registro_factura
# IMPORTACIÓN DE MODELOS EXISTENTES
from .models import Inventario, StockMovement
from .models import Proveedor
# IMPORTACIÓN DE MODELOS NUEVOS (Facturas)
from .models import Factura, FacturaProducto



# IMPORTACIÓN DE UTILIDADES
from .utils import extraer_datos_pdf, generar_pdf_registro_factura

# ==========================================================
# ⚠️ IMPORTANTE: Todas las vistas existentes quedan igual
# Solo se reemplaza facturas_view() y se agregan 3 nuevas
# ==========================================================

# ==========================================================
# 1. DASHBOARD GENERAL (SIN CAMBIOS)
# ==========================================================
def compras_dashboard(request):
    """Renderiza el dashboard principal del módulo de Compras/Adquisiciones."""
    return render(request, 'compras/compras_dashboard.html', {})

# ==========================================================
# 2. VISTA DE INVENTARIO Y DEPÓSITO (SIN CAMBIOS)
# ==========================================================
def deposito_view(request):
    """Maneja la vista de Inventario y Depósito con filtros."""
    
    inventario_qs = Inventario.objects.all() 
    
    # 1. Obtener ubicaciones únicas
    ubicaciones_list = Inventario.objects.exclude(Ubicacion__isnull=True).values_list('Ubicacion', flat=True).distinct().order_by('Ubicacion')

    # 2. Manejo de filtros de la solicitud GET
    search_query = request.GET.get('search')
    exact_code_query = request.GET.get('exact_code') 
    ubicacion_query = request.GET.get('ubicacion')
    estado_query = request.GET.get('estado')

    if exact_code_query:
        inventario_qs = inventario_qs.filter(CodigoProducto=exact_code_query)
    elif search_query:
        inventario_qs = inventario_qs.filter(
            Q(Producto__icontains=search_query) |
            Q(CodigoProducto__icontains=search_query) |
            Q(Marca__icontains=search_query) |
            Q(Modelo__icontains=search_query)
        )
    if ubicacion_query:
        inventario_qs = inventario_qs.filter(Ubicacion=ubicacion_query)
    if estado_query:
        if estado_query == 'critico':
            inventario_qs = inventario_qs.filter(Cantidad__lte=F('MinimoAdmisible'))
        elif estado_query == 'bajo':
            inventario_qs = inventario_qs.filter(
                Cantidad__gt=F('MinimoAdmisible'), 
                Cantidad__lte=F('MinimoAdmisible') + 10
            )
        elif estado_query == 'optimo':
            inventario_qs = inventario_qs.filter(Cantidad__gt=F('MinimoAdmisible') + 10)

    context = {
        'inventario_list': inventario_qs,
        'ubicaciones_list': ubicaciones_list,
        'search_query': search_query,
        'ubicacion_query': ubicacion_query,
        'estado_query': estado_query,
        'exact_code_query': exact_code_query,
    }

    return render(request, 'compras/deposito.html', context)

# ==========================================================
# 3. VISTA DE DETALLE DE PRODUCTO (SIN CAMBIOS)
# ==========================================================
def detalle_producto_view(request, pk):
    """Muestra el detalle y movimientos de un producto específico."""
    
    producto = get_object_or_404(Inventario, CodigoProducto=pk)
    
    try:
        movimientos = StockMovement.objects.filter(producto=producto).order_by('-fecha_movimiento')[:20]
    except Exception as e:
        print(f"Advertencia: No se pudieron obtener movimientos de stock para {pk}. {e}")
        movimientos = []

    context = {
        'producto': producto,
        'movimientos': movimientos,
    }
    
    return render(request, 'compras/detalle_producto.html', context)

# ==========================================================
# 4. VISTAS DE MOVIMIENTO DE STOCK (SIN CAMBIOS)
# ==========================================================

def search_products_ajax(request): 
    """Busca productos en el inventario por código o nombre para jQuery UI Autocomplete."""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip() 
        
        if len(query) < 3:
            return JsonResponse([], safe=False)

        productos_encontrados = Inventario.objects.filter(
            Q(CodigoProducto__icontains=query) | Q(Producto__icontains=query)
        ).values(
            'CodigoProducto',
            'Producto',
            'Marca', 
            'Modelo', 
            'Cantidad', 
        )[:15] 

        data = []
        for p in productos_encontrados:
            stock_display = Decimal(p['Cantidad']).quantize(Decimal('0.01')) if p['Cantidad'] is not None else Decimal('0.00')
            marca = p['Marca'] or 'S/M'
            
            item = {
                'value': p['CodigoProducto'], 
                'label': f"[{p['CodigoProducto']}] {p['Producto']} (Stock: {stock_display} | Marca: {marca})",
                'codigo': p['CodigoProducto'],
                'nombre': p['Producto'],
                'stock': stock_display,
                'unidad': p['Modelo'] or 'N/A',
            }
            data.append(item)

        return JsonResponse(data, safe=False)
    
    raise Http404

@require_http_methods(["GET"])
def get_product_details_ajax(request):
    """Devuelve los detalles de un producto por su código (SKU)."""
    codigo = request.GET.get('codigo', '')
    if not codigo:
        return JsonResponse({'error': 'Código no proporcionado'}, status=400)
    
    try:
        producto = Inventario.objects.get(CodigoProducto=codigo)
        
        stock_display = producto.Cantidad
        if stock_display is not None:
             stock_display = Decimal(stock_display).quantize(Decimal('0.01'))
        
        data = {
            'exists': True, 
            'codigo': producto.CodigoProducto,
            'nombre': producto.Producto,
            'marca': producto.Marca or 'N/D',
            'modelo': producto.Modelo or 'N/D',
            'ubicacion': producto.Ubicacion or 'N/D',
            'stock_actual': float(stock_display) if stock_display is not None else 0.0,
        }
        return JsonResponse(data)
        
    except Inventario.DoesNotExist:
        return JsonResponse({'exists': False, 'error': 'Producto no encontrado'}, status=200)

# ==========================================================
# 5. VISTAS DE INGRESO Y EGRESO DE STOCK (SIN CAMBIOS)
# ==========================================================

def process_stock_movement_post(request, tipo_movimiento):
    """Lógica centralizada para Ingreso y Egreso."""
    codigo_producto = request.POST.get('codigo_producto', '').strip().upper()
    cantidad_str = request.POST.get('cantidad', '').strip()
    observaciones = request.POST.get('observacion', '').strip() 
    
    is_ingreso = tipo_movimiento == 'ingreso'
    template_name = 'compras/ingreso_stock.html' if is_ingreso else 'compras/egreso_stock.html'
    accion_texto = 'Ingreso' if is_ingreso else 'Egreso'
    tipo_db = 'ENTRADA' if is_ingreso else 'SALIDA'
    
    tasa_cambio = None
    precio_unitario_gs = 0.0
    precio_unitario_usd = 0.0
    costo_total_gs = 0.0
    referencia = None
    
    context = {'codigo_producto': codigo_producto, 'cantidad': cantidad_str, 'observacion': observaciones}

    if not codigo_producto or not cantidad_str:
        messages.error(request, f"❌ El campo 'Buscar Producto' y la 'Cantidad a {accion_texto}' son obligatorios.")
        return render(request, template_name, context)

    try:
        cantidad = float(cantidad_str)
        if cantidad <= 0:
            messages.error(request, f"❌ La cantidad a {accion_texto} debe ser un número positivo.")
            return render(request, template_name, context)
    except ValueError:
        messages.error(request, f"❌ La cantidad ingresada no es un número válido.")
        return render(request, template_name, context)
        
    if is_ingreso:
        try:
            tasa_cambio = float(request.POST.get('tasa_cambio', 1.0))
            precio_unitario_gs = float(request.POST.get('precio_unitario_gs', 0.0))
            precio_unitario_usd = float(request.POST.get('precio_unitario_usd', 0.0))
            costo_total_gs = float(request.POST.get('costo_total_gs', 0.0)) 
            referencia = request.POST.get('referencia', '').strip()
            
            context.update({
                'tasa_cambio': tasa_cambio, 
                'precio_unitario_gs': precio_unitario_gs,
                'precio_unitario_usd': precio_unitario_usd,
                'costo_total_gs': costo_total_gs,
                'referencia': referencia,
            })
            
            if precio_unitario_gs <= 0 and precio_unitario_usd <= 0:
                 messages.warning(request, "⚠️ Se está registrando un ingreso con costo unitario cero. Verifique.")
                 
        except ValueError:
            messages.error(request, "❌ Error en el formato de precios/tasa de cambio.")
            return render(request, template_name, context)
    
    try:
        with transaction.atomic():
            producto = Inventario.objects.select_for_update().get(CodigoProducto=codigo_producto)
            
            if not is_ingreso:
                if cantidad > producto.Cantidad:
                    messages.error(request, f"⚠️ Stock Insuficiente. Solo hay {producto.Cantidad} unidades de '{producto.Producto}'.")
                    return render(request, template_name, context)
                
                ajuste_cantidad = -cantidad
                costo_movimiento = producto.PrecioGS * cantidad 
                
            else:
                ajuste_cantidad = cantidad
                costo_movimiento = costo_total_gs 
                
                producto.PrecioGS = precio_unitario_gs
                producto.PrecioUSD = precio_unitario_usd
            
            producto.Cantidad += ajuste_cantidad 
            producto.save()
            
            StockMovement.objects.create(
                producto=producto,
                tipo_movimiento=tipo_db,
                cantidad_movida=cantidad,
                motivo=observaciones,
                costo_unitario=precio_unitario_gs if is_ingreso else producto.PrecioGS, 
                costo_total=costo_movimiento, 
                tasa_cambio=tasa_cambio, 
                referencia=referencia, 
            )
            
            messages.success(request, f"✅ {accion_texto} de {cantidad} unidades de '{producto.Producto}' registrado con éxito.")
            
            return redirect(request.path_info)

    except Inventario.DoesNotExist:
        messages.error(request, f"❌ El producto con código '{codigo_producto}' no fue encontrado.")
        return render(request, template_name, context)

    except Exception as e:
        messages.error(request, f"❌ Ocurrió un error inesperado al procesar el stock. Error: {e}")
        return render(request, template_name, context)


def ingreso_stock_view(request):
    """Vista principal para el Ingreso de Stock."""
    if request.method == 'POST':
        return process_stock_movement_post(request, 'ingreso')
    
    return render(request, 'compras/ingreso_stock.html', {}) 


def egreso_stock_view(request):
    """Vista principal para el Egreso de Stock."""
    if request.method == 'POST':
        return process_stock_movement_post(request, 'egreso')
    
    return render(request, 'compras/egreso_stock.html', {})

# ==========================================================
# 6. OTRAS VISTAS EXISTENTES (SIN CAMBIOS)
# ==========================================================

def deposito_dashboard_view(request):
    """Dashboard específico del depósito."""
    return render(request, 'compras/deposito_dashboard.html')

def importaciones_view(request):
    """Gestión de importaciones y seguimientos de pedidos internacionales."""
    context = {
        'titulo_vista': "Gestión de Importaciones",
        'importaciones_list': []
    }
    return render(request, 'compras/importaciones.html', context)

def locales_view(request):
    """Vista para gestión de compras locales."""
    return render(request, 'compras/locales.html')

# ==========================================================
# 7. VISTAS DE FACTURAS (NUEVAS Y MEJORADAS)
# ==========================================================
@login_required
@require_http_methods(["GET", "POST"])
def facturas_view(request):
    """
    Vista principal para gestión de facturas - VERSIÓN SIMPLIFICADA.
    1. Carga el PDF y extrae número de factura + RUC
    2. Busca el proveedor en BD, SI NO EXISTE LO CREA AUTOMÁTICAMENTE
    3. Carga datos del proveedor para editar si es necesario
    4. Usuario selecciona productos manualmente
    """
    
    context = {
        'titulo_vista': 'Gestión de Facturas',
        'factura_datos_basicos': None,
        'proveedor_encontrado': None,
        'proveedor_datos': None,  # NUEVO: datos para formulario
        'latest_pdf_url': None,
        'latest_pdf_filename': None,
        'facturas_list': Factura.objects.all().order_by('-fecha_emision')[:10],
        'productos_disponibles': Inventario.objects.all().order_by('Producto'),
    }

    if request.method == 'POST' and 'factura_file' in request.FILES:
        archivo_pdf = request.FILES['factura_file']
        
        print("\n" + "="*80)
        print("ARCHIVO RECIBIDO EN VISTA")
        print(f"Nombre: {archivo_pdf.name}")
        print(f"Tamaño: {archivo_pdf.size} bytes")
        print("="*80)
        
        # Validar que sea PDF
        if not archivo_pdf.name.lower().endswith('.pdf'):
            messages.error(request, '❌ Solo se permiten archivos PDF')
            return render(request, 'compras/facturas.html', context)

        try:
            # EXTRACCIÓN SIMPLIFICADA
            print("\n📄 Extrayendo datos básicos del PDF...")
            datos_extraidos = extraer_datos_pdf(archivo_pdf)
            
            print(f"\n✅ Resultado:")
            print(f"   Status: {datos_extraidos.get('extraction_status')}")
            print(f"   Número Factura: {datos_extraidos.get('numero_factura')}")
            print(f"   RUC Proveedor: {datos_extraidos.get('ruc_proveedor')}")
            
            # Validar extracción
            if datos_extraidos.get('extraction_status') == 'FALLO':
                messages.error(request, '❌ No se pudieron extraer datos del PDF. Verifica que sea una factura válida.')
                return render(request, 'compras/facturas.html', context)
            
            numero_factura = datos_extraidos.get('numero_factura')
            ruc_proveedor = datos_extraidos.get('ruc_proveedor')
            
            if numero_factura == 'N/A' or ruc_proveedor == 'N/A':
                messages.error(request, '❌ No se encontró el número de factura o RUC del proveedor. Verifica el PDF.')
                return render(request, 'compras/facturas.html', context)
            
            # ============ BUSCAR O CREAR PROVEEDOR ============
            print(f"\n🔍 Buscando proveedor con RUC: {ruc_proveedor}")
            
            proveedor, created = Proveedor.objects.get_or_create(
                ruc=ruc_proveedor,
                defaults={
                    'nombre': f'Proveedor {ruc_proveedor}',
                    'activo': True
                }
            )
            
            if created:
                print(f"✅ Proveedor CREADO automáticamente: {proveedor.nombre}")
                messages.info(request, f'ℹ️ Se creó un nuevo proveedor con RUC {ruc_proveedor}. Puedes editar sus datos ahora.')
            else:
                print(f"✅ Proveedor encontrado: {proveedor.nombre}")
            
            context['proveedor_encontrado'] = proveedor
            
            # NUEVO: Preparar datos del proveedor para el formulario editable
            context['proveedor_datos'] = {
                'ruc': proveedor.ruc,
                'nombre': proveedor.nombre,
                'email': proveedor.email or '',
                'telefono': proveedor.telefono or '',
                'direccion': proveedor.direccion or '',
                'contacto': proveedor.contacto or '',
            }
            
            # Crear o actualizar factura
            factura, created = Factura.objects.get_or_create(
                numero_factura=numero_factura,
                defaults={
                    'proveedor': proveedor,
                    'ruc_proveedor': ruc_proveedor,
                    'fecha_emision': timezone.now().date(),
                    'monto_total': Decimal('0'),
                    'pdf_original': archivo_pdf,
                    'usuario': request.user,
                    'estado': 'pendiente'
                }
            )
            
            if not created:
                # Actualizar si ya existe
                if factura.estado == 'procesada':
                    messages.warning(request, f'⚠️ La factura {numero_factura} ya fue procesada.')
                    return render(request, 'compras/facturas.html', context)
                
                factura.proveedor = proveedor
                factura.pdf_original = archivo_pdf
                factura.save()
                print(f"✅ Factura actualizada: {factura.id}")
            else:
                print(f"✅ Factura creada: {factura.id}")
            
            # Guardar en sesión
            request.session['factura_actual_id'] = factura.id
            context['factura_datos_basicos'] = datos_extraidos
            context['latest_pdf_url'] = factura.pdf_original.url
            context['latest_pdf_filename'] = archivo_pdf.name
            
            messages.success(request, f'✅ Factura {numero_factura} cargada. Revisa los datos del proveedor y selecciona los productos.')
                
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'❌ Error: {str(e)[:100]}')
            return render(request, 'compras/facturas.html', context)

    # Recuperar de sesión si existe
    if 'factura_actual_id' in request.session:
        try:
            factura_id = request.session['factura_actual_id']
            factura = Factura.objects.get(id=factura_id)
            context['factura_datos_basicos'] = {
                'numero_factura': factura.numero_factura,
                'ruc_proveedor': factura.ruc_proveedor
            }
            context['proveedor_encontrado'] = factura.proveedor
            
            # Cargar datos del proveedor para editar
            context['proveedor_datos'] = {
                'ruc': factura.proveedor.ruc,
                'nombre': factura.proveedor.nombre,
                'email': factura.proveedor.email or '',
                'telefono': factura.proveedor.telefono or '',
                'direccion': factura.proveedor.direccion or '',
                'contacto': factura.proveedor.contacto or '',
            }
            
            context['latest_pdf_url'] = factura.pdf_original.url if factura.pdf_original else None
            context['latest_pdf_filename'] = factura.pdf_original.name if factura.pdf_original else None
        except Exception as e:
            print(f"Error recuperando datos de sesión: {e}")

    return render(request, 'compras/facturas.html', context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def guardar_factura(request):
    """
    Procesa la asociación de productos seleccionados manualmente.
    Actualiza stock y genera movimientos.
    GUARDA EL PDF ORIGINAL, NO GENERA UNO NUEVO.
    """
    factura_id = request.POST.get('factura_id')
    factura = get_object_or_404(Factura, id=factura_id)
    
    try:
        # ============ ACTUALIZAR DATOS DEL PROVEEDOR ============
        # Obtener datos editados del formulario
        nombre_proveedor = request.POST.get('nombre_proveedor', '').strip()
        email_proveedor = request.POST.get('email_proveedor', '').strip()
        telefono_proveedor = request.POST.get('telefono_proveedor', '').strip()
        direccion_proveedor = request.POST.get('direccion_proveedor', '').strip()
        contacto_proveedor = request.POST.get('contacto_proveedor', '').strip()
        
        print("\n" + "="*80)
        print("ACTUALIZANDO PROVEEDOR")
        print(f"Proveedor RUC: {factura.proveedor.ruc}")
        print(f"Nombre antes: {factura.proveedor.nombre}")
        print(f"Nombre nuevo: {nombre_proveedor}")
        print(f"Email: {email_proveedor}")
        print(f"Teléfono: {telefono_proveedor}")
        print("="*80 + "\n")
        
        # IMPORTANTE: Actualizar TODOS los datos del proveedor
        if nombre_proveedor:
            proveedor = factura.proveedor
            proveedor.nombre = nombre_proveedor
            proveedor.email = email_proveedor if email_proveedor else None
            proveedor.telefono = telefono_proveedor if telefono_proveedor else None
            proveedor.direccion = direccion_proveedor if direccion_proveedor else None
            proveedor.contacto = contacto_proveedor if contacto_proveedor else None
            proveedor.save()
            
            # Verificar que se guardó
            proveedor_verificado = Proveedor.objects.get(ruc=proveedor.ruc)
            print(f"✅ Proveedor guardado en BD: {proveedor_verificado.nombre}")
            print(f"   Email: {proveedor_verificado.email}")
            print(f"   Teléfono: {proveedor_verificado.telefono}\n")
        else:
            print("⚠️ No se proporcionó nombre del proveedor\n")
        
        items_procesados = []
        monto_total = Decimal('0')
        
        # Iterar sobre los productos seleccionados en el formulario
        contador = 1
        while True:
            codigo_producto = request.POST.get(f'producto_id_{contador}')
            cantidad_str = request.POST.get(f'cantidad_{contador}', '0')
            precio_unitario_str = request.POST.get(f'precio_unitario_{contador}', '0')
            
            if not codigo_producto:
                contador += 1
                if contador > 50:
                    break
                continue
            
            try:
                cantidad = Decimal(str(cantidad_str))
                precio_unitario = Decimal(str(precio_unitario_str))
            except:
                contador += 1
                continue
            
            if cantidad <= 0:
                contador += 1
                continue
            
            # Obtener producto del inventario
            producto = Inventario.objects.select_for_update().get(CodigoProducto=codigo_producto)
            
            # 1. Crear detalle de factura
            FacturaProducto.objects.create(
                factura=factura,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )
            
            # 2. Actualizar Inventario
            producto.Cantidad += float(cantidad)
            producto.PrecioGS = float(precio_unitario)
            producto.FechaUltimoMovimiento = timezone.now()
            producto.save()
            
            # 3. Crear Movimiento de Stock
            costo_total = cantidad * precio_unitario
            StockMovement.objects.create(
                producto=producto,
                tipo_movimiento='ENTRADA',
                cantidad_movida=float(cantidad),
                costo_unitario=precio_unitario,
                costo_total=costo_total,
                referencia=f"FAC {factura.numero_factura}",
                motivo=f"Compra a {factura.proveedor.nombre}"
            )
            
            # Acumular para total
            monto_total += costo_total
            
            items_procesados.append({
                'codigo': producto.CodigoProducto,
                'producto': producto.Producto,
                'cantidad': float(cantidad),
                'precio': float(precio_unitario),
            })
            
            contador += 1
        
        if not items_procesados:
            messages.error(request, '❌ Debes seleccionar al menos un producto.')
            return redirect('compras:facturas')
        
        # Actualizar monto total de factura
        factura.monto_total = monto_total
        factura.estado = 'procesada'
        factura.fecha_procesamiento = timezone.now()
        
        # CAMBIO IMPORTANTE: No generar PDF de registro, usar el original
        # El pdf_registro apunta al mismo PDF original que se cargó
        if not factura.pdf_registro:
            factura.pdf_registro = factura.pdf_original
        
        factura.save()
        
        print(f"\n✅ Factura guardada: {factura.numero_factura}")
        print(f"   Proveedor: {factura.proveedor.nombre}")
        print(f"   Monto Total: {factura.monto_total}\n")
        
        # Limpieza de sesión
        request.session.pop('factura_actual_id', None)
        
        messages.success(
            request, 
            f'✅ Factura {factura.numero_factura} procesada correctamente. '
            f'{len(items_procesados)} productos ingresados al inventario.'
        )
        return redirect('compras:facturas')
        
    except Inventario.DoesNotExist as e:
        messages.error(request, f'❌ Producto no encontrado: {str(e)}')
    except Exception as e:
        messages.error(request, f'❌ Error al guardar: {str(e)[:150]}')
        import traceback
        traceback.print_exc()
    
    return redirect('compras:facturas')


@login_required
@require_http_methods(["GET"])
def descargar_factura_pdf(request, factura_id):
    """
    Descarga el PDF original de la factura.
    """
    factura = get_object_or_404(Factura, id=factura_id)
    
    # Usar pdf_registro que apunta al original
    pdf_file = factura.pdf_registro or factura.pdf_original
    
    if not pdf_file:
        messages.error(request, '❌ Esta factura no tiene PDF disponible.')
        return redirect('compras:facturas')
    
    response = FileResponse(
        pdf_file.open('rb'),
        content_type='application/pdf'
    )
    
    filename = f'factura_{factura.numero_factura.replace("-", "_")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_http_methods(["GET"])
def ver_factura_pdf(request, factura_id):
    """
    Ve el PDF original de la factura en el navegador.
    """
    factura = get_object_or_404(Factura, id=factura_id)
    
    # Usar pdf_registro que apunta al original
    pdf_file = factura.pdf_registro or factura.pdf_original
    
    if not pdf_file:
        messages.error(request, '❌ Esta factura no tiene PDF disponible.')
        return redirect('compras:facturas')
    
    response = FileResponse(
        pdf_file.open('rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = 'inline'
    
    return response
@login_required
@require_http_methods(["GET"])
def listado_facturas(request):
    """Muestra un listado completo de todas las facturas con filtros."""
    facturas = Factura.objects.all().order_by('-fecha_emision')
    
    # Filtros opcionales
    estado = request.GET.get('estado')
    if estado:
        facturas = facturas.filter(estado=estado)
    
    proveedor = request.GET.get('proveedor')
    if proveedor:
        facturas = facturas.filter(proveedor__icontains=proveedor)
    
    context = {
        'facturas': facturas,
        'titulo_vista': 'Listado de Facturas'
    }
    
    return render(request, 'compras/listado_facturas.html', context)

# ==========================================================
# 8. FUNCIONES DE GENERACIÓN Y CREACIÓN DE PRODUCTOS
# ==========================================================

def generate_next_product_code():
    """Genera el siguiente código de producto incremental."""
    max_code_result = Inventario.objects.aggregate(Max('CodigoProducto'))
    max_code = max_code_result['CodigoProducto__max']

    next_number = 1
    
    if max_code is not None:
        try:
            max_code_str = str(max_code) 
            numeric_part = re.sub(r'\D', '', max_code_str) 
            
            if numeric_part:
                next_number = int(numeric_part) + 1
        except ValueError:
            next_number = 1 

    new_code = str(next_number).zfill(5)
    
    return new_code


def crear_producto_view(request):
    """Maneja la creación de un nuevo producto con generación automática de código."""
    next_code = generate_next_product_code()
    
    if request.method == 'POST':
        codigo = request.POST.get('codigo_producto')
        producto_nombre = request.POST.get('producto_nombre')
        descripcion = request.POST.get('descripcion')
        modelo = request.POST.get('modelo') 
        ubicacion = request.POST.get('ubicacion')
        marca = request.POST.get('marca')
        minimo = request.POST.get('minimo_admisible')
        maximo = request.POST.get('maximo_admisible')
        
        context = {
            'next_code': codigo,
            'producto_nombre': producto_nombre,
            'descripcion': descripcion,
            'modelo': modelo,
            'ubicacion': ubicacion,
            'marca': marca,
            'minimo_admisible': minimo,
            'maximo_admisible': maximo,
        }

        if not all([codigo, producto_nombre, modelo, ubicacion]):
            messages.error(request, "❌ Los campos Código, Producto, Modelo y Ubicación son obligatorios.")
            return render(request, 'compras/crear_producto.html', context)
        
        if Inventario.objects.filter(CodigoProducto=codigo).exists():
            context['next_code'] = generate_next_product_code() 
            messages.error(request, f"❌ El código de producto '{codigo}' ya existe. Se ha generado uno nuevo automáticamente.")
            return render(request, 'compras/crear_producto.html', context)

        try:
            minimo_float = float(minimo) if minimo else 0.0
            maximo_float = float(maximo) if maximo else 0.0
            
            Inventario.objects.create(
                CodigoProducto=codigo,
                Producto=producto_nombre,
                Descripcion=descripcion,
                Modelo=modelo, 
                Ubicacion=ubicacion,
                Marca=marca,
                MinimoAdmisible=minimo_float,
                MaximoAdmisible=maximo_float,
                Cantidad=0.0,
            )
            messages.success(request, f"✅ Producto '{producto_nombre}' ({codigo}) creado con éxito.")
            return redirect('compras:deposito') 

        except ValueError:
            messages.error(request, "❌ Los valores de Stock Mínimo/Máximo deben ser números válidos.")
            return render(request, 'compras/crear_producto.html', context)
            
        except Exception as e:
            messages.error(request, f"❌ Error al guardar el producto en la base de datos: {e}")
            return render(request, 'compras/crear_producto.html', context)
            
    context = {
        'next_code': next_code,
    }
    return render(request, 'compras/crear_producto.html', context)
@login_required
def gestionar_proveedores(request):
    """
    Vista para listar y crear proveedores.
    """
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    
    if request.method == 'POST':
        ruc = request.POST.get('ruc', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        
        if not ruc or not nombre:
            messages.error(request, '❌ RUC y Nombre son obligatorios')
        else:
            try:
                proveedor, created = Proveedor.objects.get_or_create(
                    ruc=ruc,
                    defaults={
                        'nombre': nombre,
                        'email': email or None,
                        'telefono': telefono or None,
                    }
                )
                
                if not created:
                    # Actualizar si ya existe
                    proveedor.nombre = nombre
                    proveedor.email = email or None
                    proveedor.telefono = telefono or None
                    proveedor.save()
                    messages.success(request, f'✅ Proveedor {nombre} actualizado')
                else:
                    messages.success(request, f'✅ Proveedor {nombre} creado')
                
                return redirect('compras:gestionar_proveedores')
            
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
    
    context = {
        'proveedores': proveedores,
        'titulo_vista': 'Gestión de Proveedores'
    }
    return render(request, 'compras/proveedores.html', context)
def gestionar_proveedores_ajax(request):
    """Responde al botón 'Guardar Datos del Proveedor' del HTML"""
    ruc = request.POST.get('ruc')
    nombre = request.POST.get('nombre')
    
    proveedor = get_object_or_404(Proveedor, ruc=ruc)
    proveedor.nombre = nombre
    proveedor.email = request.POST.get('email')
    proveedor.telefono = request.POST.get('telefono')
    proveedor.direccion = request.POST.get('direccion')
    proveedor.contacto = request.POST.get('contacto')
    proveedor.save()
    
    return JsonResponse({'status': 'success', 'nombre': proveedor.nombre})

@login_required
def eliminar_proveedor(request, ruc):
    """
    Desactiva un proveedor (no lo borra, solo lo marca como inactivo).
    """
    proveedor = get_object_or_404(Proveedor, ruc=ruc)
    
    if request.method == 'POST':
        proveedor.activo = False
        proveedor.save()
        messages.success(request, f'✅ Proveedor {proveedor.nombre} desactivado')
        return redirect('compras:gestionar_proveedores')
    
    context = {'proveedor': proveedor}
    return render(request, 'compras/confirmar_eliminar_proveedor.html', context)

@require_http_methods(["POST"])
@login_required
def cargar_factura_manual(request):
    """Procesa el ingreso manual de una factura sin PDF"""
    
    numero_factura = request.POST.get('numero_factura_manual', '').strip()
    ruc_proveedor = request.POST.get('ruc_manual', '').strip()
    fecha_emision = request.POST.get('fecha_emision_manual', '')
    archivo_subido = request.FILES.get('factura_imagen_manual')
    
    # Validaciones
    if not numero_factura or not ruc_proveedor or not fecha_emision:
        messages.error(request, '❌ Completa todos los campos obligatorios.')
        return redirect('compras:facturas')
    
    try:
        # Buscar o crear el proveedor
        proveedor, created = Proveedor.objects.get_or_create(
            ruc=ruc_proveedor,
            defaults={
                'nombre': f'Proveedor {ruc_proveedor}',
                'activo': True
            }
        )
        
        print("\n" + "="*80)
        print("INGRESO MANUAL DE FACTURA")
        print("="*80)
        print(f"Número de Factura: {numero_factura}")
        print(f"RUC Proveedor: {ruc_proveedor}")
        print(f"Fecha Emisión: {fecha_emision}")
        print(f"Archivo subido: {archivo_subido.name if archivo_subido else 'NO'}")
        
        # Crear la factura
        fecha_obj = datetime.strptime(fecha_emision, '%Y-%m-%d').date()
        
        # Procesar archivo si se subió
        archivo_pdf = None
        if archivo_subido:
            print(f"\n📄 Procesando archivo: {archivo_subido.name}")
            archivo_pdf = procesar_archivo_factura(archivo_subido)
            print(f"✅ Archivo procesado: {archivo_pdf.name if archivo_pdf else 'NO'}")
        
        # Crear la factura CON el archivo si se proporcionó
        factura = Factura.objects.create(
            numero_factura=numero_factura,
            proveedor=proveedor,
            ruc_proveedor=ruc_proveedor,
            fecha_emision=fecha_obj,
            monto_total=Decimal('0'),
            pdf_original=archivo_pdf,  # Guardar el archivo procesado
            usuario=request.user,
            estado='pendiente'
        )
        
        print(f"\n✅ Factura creada: ID {factura.id}")
        if archivo_pdf:
            print(f"   PDF: {factura.pdf_original.name}")
            print(f"   URL: {factura.pdf_original.url}")
        
        # Guardar en sesión
        request.session['factura_actual_id'] = factura.id
        
        if created:
            messages.info(request, f'ℹ️ Se creó un nuevo proveedor con RUC {ruc_proveedor}.')
        
        if archivo_subido:
            messages.success(request, f'✅ Factura {numero_factura} cargada con imagen/PDF. Ahora selecciona los productos.')
        else:
            messages.success(request, f'✅ Factura {numero_factura} cargada. Ahora selecciona los productos.')
        
        print("="*80 + "\n")
        return redirect('compras:facturas')
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'❌ Error: {str(e)[:150]}')
        return redirect('compras:facturas')


def procesar_archivo_factura(archivo):
    """
    Procesa el archivo subido.
    - Si es PDF: lo guarda tal cual
    - Si es imagen: la convierte a PDF
    Retorna el archivo guardado
    """
    from PIL import Image
    from io import BytesIO
    import uuid
    
    nombre_original = archivo.name
    extension = nombre_original.split('.')[-1].lower()
    nombre_sin_extension = nombre_original.split('.')[0]
    
    print(f"   Tipo: {archivo.content_type}")
    print(f"   Extensión: {extension}")
    print(f"   Tamaño: {archivo.size / 1024:.2f} KB")
    
    # Si es PDF, guardarlo directamente
    if extension == 'pdf':
        print(f"   ✅ PDF detectado, guardando directamente...")
        # Generar nombre único para evitar conflictos
        nombre_unico = f"factura_{uuid.uuid4().hex[:8]}.pdf"
        archivo.name = nombre_unico
        return archivo
    
    # Si es imagen, convertir a PDF
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        try:
            print(f"   🖼️  Imagen detectada, convirtiendo a PDF...")
            
            # Abrir la imagen
            imagen = Image.open(archivo)
            
            # Convertir a RGB si es necesario
            if imagen.mode in ('RGBA', 'LA', 'P'):
                fondo = Image.new('RGB', imagen.size, (255, 255, 255))
                if imagen.mode == 'RGBA':
                    fondo.paste(imagen, mask=imagen.split()[-1])
                else:
                    fondo.paste(imagen)
                imagen = fondo
            
            # Crear PDF en memoria
            pdf_buffer = BytesIO()
            imagen_rgb = imagen.convert('RGB')
            imagen_rgb.save(pdf_buffer, format='PDF', quality=95)
            pdf_buffer.seek(0)
            
            # Generar nombre único para el PDF
            nombre_pdf = f"factura_{uuid.uuid4().hex[:8]}.pdf"
            
            # Crear ContentFile con el PDF generado
            archivo_convertido = ContentFile(pdf_buffer.getvalue(), name=nombre_pdf)
            print(f"   ✅ Conversión exitosa: {nombre_pdf}")
            
            return archivo_convertido
        
        except Exception as e:
            print(f"   ❌ Error al convertir: {e}")
            raise Exception(f"No se pudo procesar la imagen: {str(e)}")
    
    else:
        raise Exception(f"Formato no soportado: .{extension}. Solo se aceptan PDF, JPG, PNG, GIF, BMP, WEBP")
@login_required
def editar_producto_view(request, pk):
    """Maneja la edición de un producto existente."""
    producto = get_object_or_404(Inventario, CodigoProducto=pk)
    
    if request.method == 'POST':
        producto_nombre = request.POST.get('producto_nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        modelo = request.POST.get('modelo', '').strip()
        ubicacion = request.POST.get('ubicacion', '').strip()
        marca = request.POST.get('marca', '').strip()
        minimo = request.POST.get('minimo_admisible', '')
        maximo = request.POST.get('maximo_admisible', '')
        precio_gs = request.POST.get('precio_gs', '')
        precio_usd = request.POST.get('precio_usd', '')
        
        context = {
            'producto': producto,
            'producto_nombre': producto_nombre,
            'descripcion': descripcion,
            'modelo': modelo,
            'ubicacion': ubicacion,
            'marca': marca,
            'minimo_admisible': minimo,
            'maximo_admisible': maximo,
            'precio_gs': precio_gs,
            'precio_usd': precio_usd,
        }

        # Validaciones
        if not all([producto_nombre, modelo, ubicacion]):
            messages.error(request, "âŒ Los campos Producto, Modelo y UbicaciÃ³n son obligatorios.")
            return render(request, 'compras/editar_producto.html', context)

        try:
            minimo_float = float(minimo) if minimo else 0.0
            maximo_float = float(maximo) if maximo else 0.0
            precio_gs_float = float(precio_gs) if precio_gs else 0.0
            precio_usd_float = float(precio_usd) if precio_usd else 0.0
            
            # Actualizar el producto
            producto.Producto = producto_nombre
            producto.Descripcion = descripcion
            producto.Modelo = modelo
            producto.Ubicacion = ubicacion
            producto.Marca = marca
            producto.MinimoAdmisible = minimo_float
            producto.MaximoAdmisible = maximo_float
            producto.PrecioGS = precio_gs_float
            producto.PrecioUSD = precio_usd_float
            producto.FechaUltimoMovimiento = timezone.now()
            producto.save()
            
            messages.success(request, f"âœ… Producto '{producto_nombre}' ({pk}) actualizado con Ã©xito.")
            return redirect('compras:detalle_producto', pk=pk)

        except ValueError:
            messages.error(request, "âŒ Los valores de precios y stock deben ser nÃºmeros vÃ¡lidos.")
            return render(request, 'compras/editar_producto.html', context)
            
        except Exception as e:
            messages.error(request, f"âŒ Error al guardar los cambios: {e}")
            return render(request, 'compras/editar_producto.html', context)
    
    # Preparar valores para mostrar en el formulario
    precio_usd_value = float(producto.PrecioUSD) if producto.PrecioUSD else 0.0
    precio_gs_value = float(producto.PrecioGS) if producto.PrecioGS else 0.0
    
    context = {
        'producto': producto,
        'producto_nombre': producto.Producto,
        'descripcion': producto.Descripcion or '',
        'modelo': producto.Modelo or '',
        'ubicacion': producto.Ubicacion or '',
        'marca': producto.Marca or '',
        'minimo_admisible': producto.MinimoAdmisible or 0,
        'maximo_admisible': producto.MaximoAdmisible or 0,
        'precio_gs': precio_gs_value,
        'precio_usd': precio_usd_value,
    }
    
    return render(request, 'compras/editar_producto.html', context)