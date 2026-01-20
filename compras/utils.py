# tu_app/utils.py - VERSIÓN SIMPLIFICADA

import pdfplumber
import re
from decimal import Decimal
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from django.utils import timezone


def limpiar_ruc(texto):
    """Extrae solo números y guion del RUC."""
    if not isinstance(texto, str):
        return "N/A"
    # Formato: 12345678-9
    match = re.search(r'(\d{8}-\d)', texto)
    return match.group(1) if match else "N/A"


def extraer_datos_pdf(uploaded_file):
    """
    VERSIÓN SIMPLIFICADA: Solo extrae datos básicos de la factura.
    - Número de Factura
    - RUC del Proveedor (para buscar en BD)
    
    Los productos se seleccionarán manualmente en el formulario.
    """
    
    uploaded_file.seek(0)
    
    extracted_data = {
        "numero_factura": "N/A",
        "ruc_proveedor": "N/A",
        "extraction_status": "FALLO"
    }
    
    try:
        print("\n" + "="*80)
        print("EXTRAYENDO DATOS BÁSICOS DEL PDF")
        print("="*80)
        
        with pdfplumber.open(uploaded_file) as pdf:
            if len(pdf.pages) == 0:
                print("❌ El PDF no tiene páginas")
                return extracted_data
            
            page = pdf.pages[0]
            text = page.extract_text()
            
            print("\n📄 PRIMERAS 500 CARACTERES:")
            print(text[:500])
            
            # ============ RUC PROVEEDOR ============
            ruc_match = re.search(r'RUC\s*:\s*(\d{8}-\d)', text)
            if ruc_match:
                ruc = ruc_match.group(1)
                extracted_data["ruc_proveedor"] = ruc
                print(f"\n✅ RUC Proveedor: {ruc}")
            else:
                print("\n⚠️ No se encontró RUC en el PDF")
            
            # ============ NÚMERO DE FACTURA ============
            # Patrón: 001-001-0000001 o similar
            factura_match = re.search(r'(\d{3}-\d{3}-\d{7})', text)
            if factura_match:
                numero = factura_match.group(1)
                extracted_data["numero_factura"] = numero
                print(f"✅ Número de Factura: {numero}")
            else:
                print("⚠️ No se encontró número de factura")
            
            # ============ VALIDACIÓN FINAL ============
            if extracted_data["ruc_proveedor"] != "N/A":
                extracted_data["extraction_status"] = "OK"
                print(f"\n✅ EXTRACCIÓN EXITOSA")
            
            return extracted_data

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return extracted_data


# ==========================================================
# FUNCIONES PARA GENERAR PDF DE REGISTRO
# ==========================================================

def generar_pdf_registro_factura(factura, items_procesados):
    """Genera un PDF de registro con los items procesados."""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#800020'),
        spaceAfter=12,
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#800020'),
        spaceAfter=8,
        spaceBefore=10
    )
    
    content = []
    content.append(Paragraph("COMPROBANTE DE FACTURA PROCESADA", title_style))
    content.append(Spacer(1, 0.2*inch))
    content.append(Paragraph("Información de la Factura", heading_style))
    
    data = [
        ['Número:', factura.numero_factura],
        ['Proveedor:', factura.proveedor.nombre],
        ['RUC:', factura.proveedor.ruc],
        ['Fecha:', str(factura.fecha_emision)],
        ['Monto Total:', f"₲ {factura.monto_total:,.2f}"],
    ]
    
    tabla = Table(data, colWidths=[2*inch, 4*inch])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    content.append(tabla)
    content.append(Spacer(1, 0.3*inch))
    
    content.append(Paragraph("Productos Ingresados al Inventario", heading_style))
    
    products = [['Código', 'Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
    total = Decimal('0')
    
    for item in items_procesados:
        sub = Decimal(str(item['cantidad'])) * Decimal(str(item['precio']))
        total += sub
        products.append([
            item['codigo'],
            item['producto'],
            f"{item['cantidad']:.2f}",
            f"₲ {item['precio']:,.2f}",
            f"₲ {float(sub):,.2f}"
        ])
    
    tabla2 = Table(products, colWidths=[1*inch, 2.5*inch, 0.8*inch, 1.3*inch, 1.2*inch])
    tabla2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#800020')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    content.append(tabla2)
    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()


def validar_pdf(archivo):
    """Valida que el archivo sea un PDF válido."""
    try:
        with pdfplumber.open(archivo) as pdf:
            return len(pdf.pages) > 0
    except:
        return False