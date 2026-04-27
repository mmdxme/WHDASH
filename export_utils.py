"""
Export Utilities - Comprehensive Export Functionality
====================================================
Central utility module providing all export functions for the dashboard application.
Supports 20 export types: CSV, Excel (text/general), JSON, XML, TXT, PDF, DOCX, HTML,
Printable, Barcode Labels, API, Email, ZIP, Backup, SQL Dump, Dashboard, Summary,
Detailed, and Audit Log exports.

Usage:
    from export_utils import send_export_response, export_to_csv, export_to_pdf, etc.
"""

from flask import make_response, jsonify
import io
import csv
import json
import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, date
from functools import reduce

# Third-party imports - these are REQUIRED for export functionality
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

import qrcode
from PIL import Image

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None


# =============================================================================
# PDF FONT SETUP - Arabic/Persian support
# =============================================================================

# Try to register Arabic-capable fonts for PDF export
_ARABIC_FONT_REGISTERED = False
_ARABIC_FONT_NAME = 'Helvetica'  # Default fallback

def _register_arabic_fonts():
    """Register TTF fonts that support Arabic/Persian script."""
    global _ARABIC_FONT_REGISTERED, _ARABIC_FONT_NAME

    if _ARABIC_FONT_REGISTERED:
        return

    # Common font paths on Windows for Arabic/Persian support
    font_paths = [
        # Windows common paths
        r"C:\Windows\Fonts\NotoSansArabic-Regular.ttf",
        r"C:\Windows\Fonts\NotoNaskhArabic-Regular.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\seguiemj.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\TraditionalArabic-Regular.ttf",
        r"C:\Windows\Fonts\Traditional Arabic.ttf",
        r"C:\Windows\Fonts\Arabic Typesetting\Arabic Typesetting.ttf",
        r"C:\Windows\Fonts\SegoeUI\seguisb.ttf",
        # Linux common paths
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for font_path in font_paths:
        try:
            pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
            _ARABIC_FONT_NAME = 'ArabicFont'
            _ARABIC_FONT_REGISTERED = True
            break
        except Exception:
            continue

# Register fonts on module load
_register_arabic_fonts()


# =============================================================================
# CSV EXPORT
# =============================================================================

def export_to_csv(data, filename, columns):
    """
    Export data to CSV format with UTF-8 BOM for Excel compatibility.

    Args:
        data: List of dictionaries to export
        filename: Name for the file (without extension)
        columns: List of column keys to include

    Returns:
        BytesIO containing CSV data
    """
    output = io.StringIO()
    # Write BOM for Excel UTF-8 compatibility
    output.write('\ufeff')
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')

    writer.writeheader()
    for row in data:
        # Handle nested data and special characters
        row_data = {}
        for col in columns:
            value = _get_nested_value(row, col)
            row_data[col] = _sanitize_value(value)
        writer.writerow(row_data)

    output.seek(0)
    return output.getvalue().encode('utf-8-sig')


# =============================================================================
# EXCEL EXPORTS
# =============================================================================

def export_to_excel_text(data, filename, columns):
    """
    Export data to Excel with text-formatted cells (@ prefix).
    Prevents number truncation in Excel by forcing text format.

    Args:
        data: List of dictionaries to export
        filename: Name for the file (without extension)
        columns: List of column keys/headers

    Returns:
        BytesIO containing Excel file
    """
    wb = Workbook()
    ws = wb.active
    ws.title = filename[:31] if len(filename) > 31 else filename

    # Header style
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Write header
    for col_idx, col_name in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Write data rows with text formatting
    for row_idx, row in enumerate(data, 2):
        for col_idx, col_key in enumerate(columns, 1):
            value = _get_nested_value(row, col_key)
            # Format as text using @ prefix in xlsx
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = _sanitize_value(value)
            cell.number_format = '@'
            cell.border = thin_border
            # Set alignment based on type
            if isinstance(value, (int, float)):
                cell.alignment = Alignment(horizontal='right')
            else:
                cell.alignment = Alignment(horizontal='left')

    # Auto-adjust column widths
    for col_idx, col_key in enumerate(columns, 1):
        col_letter = get_column_letter(col_idx)
        max_length = max(len(str(col_key)), 15)
        for row in data:
            value = str(_get_nested_value(row, col_key))
            max_length = max(max_length, len(value))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def export_to_excel_general(data, filename, columns):
    """
    Export data to Excel with auto-detected column types (General format).
    Numbers remain as numbers, text as text.

    Args:
        data: List of dictionaries to export
        filename: Name for the file (without extension)
        columns: List of column keys/headers

    Returns:
        BytesIO containing Excel file
    """
    wb = Workbook()
    ws = wb.active
    ws.title = filename[:31] if len(filename) > 31 else filename

    # Header style
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Write header
    for col_idx, col_name in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Write data rows with auto-detection
    for row_idx, row in enumerate(data, 2):
        for col_idx, col_key in enumerate(columns, 1):
            value = _get_nested_value(row, col_key)
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = _sanitize_value(value)
            cell.border = thin_border

    # Auto-adjust column widths
    for col_idx, col_key in enumerate(columns, 1):
        col_letter = get_column_letter(col_idx)
        max_length = max(len(str(col_key)), 15)
        for row in data:
            value = str(_get_nested_value(row, col_key))
            max_length = max(max_length, len(value))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


# =============================================================================
# JSON EXPORT
# =============================================================================

def export_to_json(data, filename, indent=2):
    """
    Export data to clean JSON with proper indentation.

    Args:
        data: Data to export (dict, list, or nested structure)
        filename: Name for the file (without extension)
        indent: Indentation spaces (default 2)

    Returns:
        BytesIO containing JSON file
    """
    # Handle datetime serialization
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    output = io.StringIO()
    json.dump(data, output, indent=indent, default=json_serializer, ensure_ascii=False)
    output.seek(0)
    return output.getvalue().encode('utf-8')


# =============================================================================
# XML EXPORT
# =============================================================================

def export_to_xml(data, filename, root_element='root'):
    """
    Export data to valid XML 1.0 with proper encoding.

    Args:
        data: Dict or list to export
        filename: Name for the file (without extension)
        root_element: Root XML element name

    Returns:
        BytesIO containing XML file
    """
    def dict_to_xml(parent, dict_data):
        for key, value in dict_data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        child = ET.SubElement(parent, str(key))
                        dict_to_xml(child, item)
                    else:
                        child = ET.SubElement(parent, str(key))
                        child.text = str(_sanitize_value(item))
            elif isinstance(value, dict):
                child = ET.SubElement(parent, str(key))
                dict_to_xml(child, value)
            else:
                child = ET.SubElement(parent, str(key))
                child.text = str(_sanitize_value(value))

    # Create root
    root = ET.Element(root_element)
    root.set('generated', datetime.now().isoformat())

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                child = ET.SubElement(root, 'record')
                dict_to_xml(child, item)
            else:
                child = ET.SubElement(root, 'record')
                child.text = str(_sanitize_value(item))
    elif isinstance(data, dict):
        dict_to_xml(root, data)

    # Pretty print with minidom
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ', encoding='UTF-8')

    output = io.BytesIO(pretty_xml)
    output.seek(0)
    return output.getvalue()


# =============================================================================
# TXT EXPORT
# =============================================================================

def export_to_txt(data, filename, delimiter='\t'):
    """
    Export data to plain text with tab separators.

    Args:
        data: List of dictionaries to export
        filename: Name for the file (without extension)
        delimiter: Column separator (default tab)

    Returns:
        BytesIO containing TXT file
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter, lineterminator='\n')

    # Header
    writer.writerow(list(data[0].keys()) if data else [])

    # Data rows
    for row in data:
        writer.writerow([_sanitize_value(v) for v in row.values()])

    output.seek(0)
    return output.getvalue().encode('utf-8')


# =============================================================================
# PDF EXPORT
# =============================================================================

def export_to_pdf(data, filename, title, columns):
    """
    Export data to PDF using ReportLab.

    Args:
        data: List of dictionaries to export
        filename: Name for the file (without extension)
        title: Report title
        columns: List of column keys/headers

    Returns:
        BytesIO containing PDF file
    """
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()
    elements = []

    def is_rtl_text(text):
        """Check if text contains Arabic/Persian/Hebrew RTL characters."""
        if not text:
            return False
        for char in str(text):
            if (
                '\u0590' <= char <= '\u08FF'
                or '\uFB1D' <= char <= '\uFDFF'
                or '\uFE70' <= char <= '\uFEFF'
            ):
                return True
        return False

    def prepare_pdf_text(text):
        """Escape and shape mixed RTL/LTR text for ReportLab paragraphs."""
        if text is None:
            return ''
        text = str(text)
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        if is_rtl_text(text) and arabic_reshaper and get_display:
            return get_display(arabic_reshaper.reshape(text))
        return text

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=1,  # Center
        fontName=_ARABIC_FONT_NAME if is_rtl_text(title) else 'Helvetica-Bold'
    )
    elements.append(Paragraph(prepare_pdf_text(title), title_style))
    elements.append(Spacer(1, 0.3*inch))

    # Metadata
    meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=9, textColor='gray')
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
    elements.append(Spacer(1, 0.3*inch))

    # Table data with Paragraph for RTL/Arabic support
    table_data = []
    for row in data:
        table_data.append([_sanitize_value(_get_nested_value(row, col)) for col in columns])

    # Create styled paragraphs for table content
    def make_para(text, font_name='Helvetica', font_size=9, alignment='LEFT'):
        """Create a Paragraph with proper font and alignment."""
        align_map = {'LEFT': 0, 'CENTER': 1, 'RIGHT': 2}
        style = ParagraphStyle(
            'TableCell',
            fontName=font_name,
            fontSize=font_size,
            alignment=align_map.get(alignment, 0)
        )
        return Paragraph(prepare_pdf_text(text), style)

    # Build table rows with Paragraph for proper font rendering
    header_row = [make_para(col, font_name='Helvetica-Bold', font_size=10, alignment='CENTER') for col in columns]
    table_paragraphs = [header_row]

    for row in table_data:
        row_paras = []
        for cell in row:
            if is_rtl_text(cell):
                # Use Arabic font and right-align for RTL text
                row_paras.append(make_para(cell, font_name=_ARABIC_FONT_NAME, font_size=9, alignment='RIGHT'))
            else:
                # Default left alignment for LTR text
                row_paras.append(make_para(cell, font_name='Helvetica', font_size=9, alignment='LEFT'))
        table_paragraphs.append(row_paras)

    # Create table
    table = Table(table_paragraphs, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#366092')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F5F5F5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    doc.build(elements)
    output.seek(0)
    return output.getvalue()


# =============================================================================
# WORD (DOCX) EXPORT
# =============================================================================

def export_to_docx(data, filename, title, columns):
    """
    Export data to Word document using python-docx.

    Args:
        data: List of dictionaries to export
        filename: Name for the file (without extension)
        title: Document title
        columns: List of column keys/headers

    Returns:
        BytesIO containing DOCX file
    """
    doc = Document()
    doc.core_properties.title = title

    # Title
    heading = doc.add_heading(title, 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Metadata
    meta = doc.add_paragraph()
    meta.add_run(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}").italic = True
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

    # Table
    table = doc.add_table(rows=1, cols=len(columns))
    table.style = 'Table Grid'

    # Header
    header_row = table.rows[0]
    for idx, col_name in enumerate(columns):
        cell = header_row.cells[idx]
        cell.text = str(col_name)
        run = cell.paragraphs[0].runs[0]
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Set background color
        shading_elm = cell._element.get_or_add_tcPr()

    # Data rows
    for row in data:
        row_cells = table.add_row().cells
        for idx, col_key in enumerate(columns):
            value = _get_nested_value(row, col_key)
            row_cells[idx].text = str(_sanitize_value(value))

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()


# =============================================================================
# HTML EXPORT
# =============================================================================

def export_to_html(data, filename, title, columns):
    """
    Export data to clean HTML5 table with inline CSS.

    Args:
        data: List of dictionaries to export
        filename: Name for the file (without extension)
        title: Page title
        columns: List of column keys/headers

    Returns:
        BytesIO containing HTML file
    """
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #366092; margin-bottom: 10px; }}
        .meta {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #366092; color: white; padding: 12px; text-align: left; font-weight: 600; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f8f9fa; }}
        tr:nth-child(even) {{ background: #fafafa; }}
        .footer {{ margin-top: 20px; text-align: center; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="meta">Generated: {generated}</div>
        <table>
            <thead>
                <tr>
                    {headers}
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <div class="footer">Total Records: {total}</div>
    </div>
</body>
</html>"""

    headers_html = '\n'.join([f'<th>{h}</th>' for h in columns])
    rows_html = ''
    for row in data:
        cells = '\n'.join([f'<td>{_sanitize_value(_get_nested_value(row, col))}</td>' for col in columns])
        rows_html += f'<tr>\n{cells}\n</tr>\n'

    html = html_template.format(
        title=title,
        generated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        headers=headers_html,
        rows=rows_html,
        total=len(data)
    )

    return html.encode('utf-8')


# =============================================================================
# PRINTABLE HTML EXPORT
# =============================================================================

def export_to_printable_html(data, filename, title, columns):
    """
    Export data to HTML optimized for printing with page breaks.

    Args:
        data: List of dictionaries to export
        filename: Name for the file (without extension)
        title: Report title
        columns: List of column keys/headers

    Returns:
        BytesIO containing HTML file
    """
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        @page {{ size: letter; margin: 0.75in; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; line-height: 1.4; }}
        .header {{ text-align: center; border-bottom: 2px solid #366092; padding-bottom: 15px; margin-bottom: 20px; }}
        h1 {{ color: #366092; font-size: 18px; margin-bottom: 5px; }}
        .meta {{ color: #666; font-size: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th {{ background: #366092; color: white; padding: 8px 6px; text-align: left; font-weight: 600; font-size: 10px; }}
        td {{ padding: 6px; border-bottom: 1px solid #ccc; font-size: 10px; }}
        tr {{ page-break-inside: avoid; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .footer {{ margin-top: 20px; text-align: center; color: #666; font-size: 9px; border-top: 1px solid #ccc; padding-top: 10px; }}
        @media print {{
            body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .page-break {{ page-break-before: always; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="meta">Generated: {generated} | Page <span class="page-num"></span></div>
    </div>
    <table>
        <thead>
            <tr>
                {headers}
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    <div class="footer">
        Total Records: {total} | Printed: {printed}
    </div>
</body>
</html>"""

    headers_html = '\n'.join([f'<th>{h}</th>' for h in columns])
    rows_html = ''
    for i, row in enumerate(data):
        if i > 0 and i % 30 == 0:  # Page break every 30 rows
            rows_html += '<tr class="page-break"></tr>\n'
        cells = '\n'.join([f'<td>{_sanitize_value(_get_nested_value(row, col))}</td>' for col in columns])
        rows_html += f'<tr>\n{cells}\n</tr>\n'

    html = html_template.format(
        title=title,
        generated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        headers=headers_html,
        rows=rows_html,
        total=len(data),
        printed=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    return html.encode('utf-8')


# =============================================================================
# BARCODE LABELS EXPORT
# =============================================================================

def export_to_barcode_labels(data, filename, label_size='Avery5160'):
    """
    Generate barcode labels (QR codes and Code128) using ReportLab.

    Args:
        data: List of dictionaries with label data
        filename: Name for the file (without extension)
        label_size: Label format (Avery5160, Avery5162, etc.)

    Returns:
        BytesIO containing PDF with labels
    """
    label_configs = {
        'Avery5160': {'width': 2.5*inch, 'height': 1*inch, 'cols': 2, 'rows': 8},
        'Avery5162': {'width': 4*inch, 'height': 1*inch, 'cols': 1, 'rows': 10},
        'Avery5163': {'width': 2.5*inch, 'height': 2*inch, 'cols': 2, 'rows': 4},
        'Avery5164': {'width': 4*inch, 'height': 2*inch, 'cols': 1, 'rows': 5},
    }

    config = label_configs.get(label_size, label_configs['Avery5160'])

    output = io.BytesIO()
    from reportlab.pdfgen import canvas

    # Create custom page size
    page_width = 8.5*inch
    page_height = 11*inch
    c = canvas.Canvas(output, pagesize=(page_width, page_height))

    margin = 0.5*inch
    gap_x = 0.25*inch
    gap_y = 0.15*inch

    x = margin
    y = page_height - margin - config['height']
    label_count = 0

    for item in data:
        # Draw label border
        c.setStrokeColor(HexColor('#cccccc'))
        c.setLineWidth(0.5)
        c.rect(x, y, config['width'], -config['height'])

        # Add text
        c.setFont('Helvetica', 8)
        text_y = y - 0.15*inch

        # Label content
        desc = item.get('description', item.get('name', 'Label'))
        code = item.get('code', item.get('sku', item.get('id', '')))

        c.drawString(x + 0.1*inch, text_y, str(desc)[:40])
        text_y -= 0.12*inch
        c.drawString(x + 0.1*inch, text_y, f"Code: {code}")

        # Generate QR code if available
        try:
            if 'qr_data' in item:
                qr = qrcode.QRCode(version=1, box_size=2, border=1)
                qr.add_data(item['qr_data'])
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                # Save temporarily and draw
                from reportlab.lib.utils import ImageReader
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                c.drawImage(ImageReader(img_buffer), x + config['width'] - 0.8*inch,
                           y - 0.5*inch, width=0.6*inch, height=0.6*inch)
        except Exception:
            pass  # QR generation failed, skip

        # Move to next position
        label_count += 1
        if label_count % config['cols'] == 0:
            # New row
            x = margin
            y -= config['height'] + gap_y
        else:
            # Next column
            x += config['width'] + gap_x

        # Check for new page
        if label_count % (config['cols'] * config['rows']) == 0:
            c.showPage()
            x = margin
            y = page_height - margin - config['height']

    c.save()
    output.seek(0)
    return output.getvalue()


# =============================================================================
# API JSON EXPORT
# =============================================================================

def export_to_api_json(data, page=1, per_page=100):
    """
    Export data as RESTful JSON API response with pagination.

    Args:
        data: List of records to paginate
        page: Page number (1-indexed)
        per_page: Records per page

    Returns:
        Dict with API response structure
    """
    total = len(data)
    total_pages = (total + per_page - 1) // per_page

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_data = data[start_idx:end_idx]

    return {
        'success': True,
        'data': paginated_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        },
        'meta': {
            'generated_at': datetime.now().isoformat(),
            'format': 'json'
        }
    }


# =============================================================================
# EMAIL HTML EXPORT
# =============================================================================

def export_to_email_html(data, subject, recipient):
    """
    Generate email-ready HTML body with inline CSS.

    Args:
        data: List of dictionaries to include in email
        subject: Email subject
        recipient: Recipient email address

    Returns:
        String containing email HTML
    """
    email_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .email-container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #366092; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .header h1 {{ margin: 0; font-size: 18px; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th {{ background: #366092; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        .footer {{ text-align: center; padding: 15px; color: #666; font-size: 12px; background: #eee; border-radius: 0 0 5px 5px; }}
        .summary {{ background: white; padding: 15px; margin-bottom: 15px; border-left: 4px solid #366092; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>{subject}</h1>
        </div>
        <div class="content">
            <div class="summary">
                <strong>Report Summary</strong><br>
                Total Records: {total}<br>
                Generated: {generated}
            </div>
            <table>
                <tr>
                    {headers}
                </tr>
                {rows}
            </table>
        </div>
        <div class="footer">
            This email was automatically generated. Please do not reply.<br>
            Generated: {generated}
        </div>
    </div>
</body>
</html>"""

    columns = list(data[0].keys()) if data else []
    headers = '\n'.join([f'<th>{h}</th>' for h in columns])
    rows = ''
    for row in data[:20]:  # Limit email to 20 rows
        cells = '\n'.join([f'<td>{_sanitize_value(v)}</td>' for v in row.values()])
        rows += f'<tr>\n{cells}\n</tr>\n'

    if len(data) > 20:
        rows += f'<tr><td colspan="{len(columns)}">... and {len(data) - 20} more records</td></tr>\n'

    return email_template.format(
        subject=subject,
        total=len(data),
        generated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        headers=headers,
        rows=rows
    )


# =============================================================================
# ZIP EXPORT
# =============================================================================

def export_to_zip(data, filename):
    """
    Compress data into ZIP archive.

    Args:
        data: Dict of {filename: content} to compress, or list of data
        filename: Base name for the ZIP file

    Returns:
        BytesIO containing ZIP file
    """
    output = io.BytesIO()

    # Handle list data by creating a default structure
    if isinstance(data, list):
        data = {
            f'data_{i+1}.json': json.dumps(item, indent=2, default=str) if isinstance(item, dict) else str(item)
            for i, item in enumerate(data)
        }

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in data.items():
            if isinstance(content, str):
                content = content.encode('utf-8')
            elif isinstance(content, dict):
                content = json.dumps(content, indent=2).encode('utf-8')
            zf.writestr(name, content)

    output.seek(0)
    return output.getvalue()


# =============================================================================
# BACKUP FILE EXPORT
# =============================================================================

def export_to_backup(data, filename):
    """
    Generate database-style backup with INSERT statements.

    Args:
        data: Dict of {table_name: records} to backup, or list of records
        filename: Name for backup file

    Returns:
        BytesIO containing SQL backup file
    """
    output = io.StringIO()
    output.write(f"-- Database Backup\n")
    output.write(f"-- Generated: {datetime.now().isoformat()}\n")
    output.write(f"-- Project: WHDASH\n\n")

    # Handle list data by wrapping in a default table
    if isinstance(data, list):
        data = {'records': data}

    for table_name, records in data.items():
        if not records:
            continue

        output.write(f"\n-- Table: {table_name}\n")
        output.write(f"DELETE FROM {table_name};\n")

        columns = list(records[0].keys()) if records and isinstance(records[0], dict) else []
        if not columns:
            continue

        for record in records:
            values = []
            for col in columns:
                val = record.get(col) if isinstance(record, dict) else ''
                if val is None:
                    values.append('NULL')
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                else:
                    escaped = str(val).replace("'", "''")
                    values.append(f"'{escaped}'")

            output.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")

    output.seek(0)
    return output.getvalue().encode('utf-8')


# =============================================================================
# SQL DUMP EXPORT
# =============================================================================

def export_to_sql_dump(data, filename):
    """
    Export as executable SQL INSERT statements with transactions.

    Args:
        data: List of dictionaries to export
        filename: Name for SQL file

    Returns:
        BytesIO containing SQL file
    """
    output = io.StringIO()

    # Header
    output.write(f"-- SQL Dump\n")
    output.write(f"-- Generated: {datetime.now().isoformat()}\n")
    output.write(f"-- Format: PostgreSQL/MySQL Compatible\n\n")

    if not data:
        output.write("-- No data to export\n")
    else:
        columns = list(data[0].keys())
        output.write(f"START TRANSACTION;\n\n")

        for record in data:
            values = []
            for col in columns:
                val = record.get(col)
                if val is None:
                    values.append('NULL')
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                elif isinstance(val, datetime):
                    values.append(f"'{val.isoformat()}'")
                else:
                    escaped = str(val).replace("'", "''")
                    values.append(f"'{escaped}'")

            output.write(f"INSERT INTO records ({', '.join(columns)}) VALUES ({', '.join(values)});\n")

        output.write(f"\nCOMMIT;\n")

    output.seek(0)
    return output.getvalue().encode('utf-8')


# =============================================================================
# DASHBOARD EXPORT
# =============================================================================

def export_dashboard_state(data, filename):
    """
    Export complete dashboard state including widget configurations.

    Args:
        data: Dict containing dashboard state (or list for fallback)
        filename: Name for export file

    Returns:
        BytesIO containing JSON dashboard state
    """
    # Handle list data by wrapping in a default structure
    if isinstance(data, list):
        data = {'widgets': data, 'layout': {'type': 'list'}}

    dashboard_export = {
        'version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'dashboard': {
            'widgets': data.get('widgets', []) if isinstance(data, dict) else data,
            'layout': data.get('layout', {}) if isinstance(data, dict) else {},
            'date_range': data.get('date_range', {}) if isinstance(data, dict) else {},
            'filters': data.get('filters', {}) if isinstance(data, dict) else {},
            'charts': []
        },
        'meta': {
            'app_version': '3.1.3',
            'export_type': 'dashboard_state'
        }
    }

    # Convert chart images to base64 if present
    if isinstance(data, dict) and 'chart_images' in data:
        import base64
        dashboard_export['dashboard']['charts'] = [
            {
                'id': chart.get('id'),
                'type': chart.get('type'),
                'image': base64.b64encode(chart.get('image', b'')).decode('utf-8') if chart.get('image') else None
            }
            for chart in data.get('chart_images', [])
        ]

    output = io.StringIO()
    json.dump(dashboard_export, output, indent=2, default=str)
    output.seek(0)
    return output.getvalue().encode('utf-8')


# =============================================================================
# SUMMARY REPORT EXPORT
# =============================================================================

def export_summary_report(data, filename, title):
    """
    Generate condensed one-page summary with key metrics.

    Args:
        data: Dict containing summary data and metrics
        filename: Name for export file
        title: Report title

    Returns:
        BytesIO containing HTML summary report
    """
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        @page {{ size: A4; margin: 0.5in; }}
        body {{ font-family: Arial, sans-serif; font-size: 11px; }}
        .summary-header {{ text-align: center; border-bottom: 2px solid #366092; padding-bottom: 10px; margin-bottom: 15px; }}
        h1 {{ color: #366092; font-size: 16px; margin-bottom: 5px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .kpi-card {{ background: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; border-left: 3px solid #366092; }}
        .kpi-value {{ font-size: 24px; font-weight: bold; color: #366092; }}
        .kpi-label {{ font-size: 10px; color: #666; margin-top: 5px; }}
        .section {{ margin-bottom: 15px; }}
        .section h2 {{ font-size: 12px; color: #366092; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
        th {{ background: #366092; color: white; padding: 6px; text-align: left; }}
        td {{ padding: 5px; border-bottom: 1px solid #eee; }}
        .footer {{ margin-top: 20px; text-align: center; color: #999; font-size: 9px; }}
    </style>
</head>
<body>
    <div class="summary-header">
        <h1>{title}</h1>
        <div>Generated: {generated}</div>
    </div>

    <div class="kpi-grid">
        {kpi_cards}
    </div>

    <div class="section">
        <h2>Key Highlights</h2>
        {highlights}
    </div>

    <div class="footer">
        Total Records: {total} | This is a summary report
    </div>
</body>
</html>"""

    # Generate KPI cards
    kpi_cards = ''

    # Handle list data by creating sample KPIs from the data
    if isinstance(data, list):
        data_dict = {
            'kpis': {'Total Records': len(data), 'Export Type': 'Summary'},
            'highlights': data[:5] if len(data) >= 5 else data,
            'total': len(data),
            'items': data
        }
        data = data_dict

    kpis = data.get('kpis', {}) if isinstance(data, dict) else {'Total Records': len(data)}
    for label, value in kpis.items():
        kpi_cards += f'<div class="kpi-card"><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div></div>'

    # Generate highlights
    highlights = '<table><tr><th>Metric</th><th>Value</th></tr>'
    highlights_data = data.get('highlights', []) if isinstance(data, dict) else data[:5]
    for item in highlights_data[:5]:
        if isinstance(item, dict):
            name = item.get('name', item.get('title', 'N/A'))
            value = item.get('value', item.get('count', item.get('total', 'N/A')))
        else:
            name = str(item)
            value = 'N/A'
        highlights += f'<tr><td>{name}</td><td>{value}</td></tr>'
    highlights += '</table>'

    total = data.get('total', len(data)) if isinstance(data, dict) else len(data)
    html = html_template.format(
        title=title,
        generated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        kpi_cards=kpi_cards,
        highlights=highlights,
        total=total
    )

    return html.encode('utf-8')


# =============================================================================
# DETAILED REPORT EXPORT
# =============================================================================

def export_detailed_report(data, filename, title, columns):
    """
    Generate full multi-section report with all data and pagination.

    Args:
        data: List of dictionaries to export
        filename: Name for export file
        title: Report title
        columns: List of column keys/headers

    Returns:
        BytesIO containing HTML detailed report
    """
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        @page {{ size: letter; margin: 0.75in; }}
        body {{ font-family: Arial, sans-serif; font-size: 10px; line-height: 1.4; }}
        .header {{ text-align: center; border-bottom: 2px solid #366092; padding-bottom: 15px; margin-bottom: 20px; }}
        h1 {{ color: #366092; font-size: 18px; margin-bottom: 5px; }}
        .meta {{ color: #666; font-size: 9px; }}
        .filters {{ background: #f5f5f5; padding: 10px; margin-bottom: 20px; border-radius: 5px; }}
        .filters strong {{ color: #366092; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th {{ background: #366092; color: white; padding: 8px; text-align: left; font-weight: 600; font-size: 9px; }}
        td {{ padding: 6px; border-bottom: 1px solid #ddd; font-size: 9px; }}
        tr:nth-child(even) {{ background: #fafafa; }}
        .section {{ page-break-before: always; }}
        .section h2 {{ color: #366092; font-size: 14px; margin: 20px 0 10px; }}
        .pagination {{ text-align: center; margin-top: 20px; color: #666; font-size: 9px; }}
        .footer {{ margin-top: 30px; text-align: center; color: #666; font-size: 8px; border-top: 1px solid #ccc; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="meta">
            Generated: {generated} | Records: {total} | Page: <span class="page-num"></span>
        </div>
    </div>

    <div class="filters">
        <strong>Applied Filters:</strong> {filters}
    </div>

    <table>
        <thead>
            <tr>
                {headers}
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>

    <div class="pagination">
        Total Pages: {total_pages} | Records Per Page: 50
    </div>

    <div class="footer">
        WHDASH - Detailed Report | Generated: {generated}
    </div>
</body>
</html>"""

    total_pages = (len(data) + 49) // 50  # 50 rows per page
    filters = 'None specified'
    if isinstance(data, dict):
        filters = data.get('applied_filters', 'None specified')

    headers_html = '\n'.join([f'<th>{h}</th>' for h in columns])
    rows_html = ''
    rows_to_iterate = data if isinstance(data, list) else [data]
    for i, row in enumerate(rows_to_iterate):
        if i > 0 and i % 50 == 0:
            rows_html += '</tbody></table>\n<div class="section"><table><thead><tr>' + headers_html + '</tr></thead><tbody>\n'
        cells = '\n'.join([f'<td>{_sanitize_value(_get_nested_value(row, col))}</td>' for col in columns])
        rows_html += f'<tr>\n{cells}\n</tr>\n'

    html = html_template.format(
        title=title,
        generated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        headers=headers_html,
        rows=rows_html,
        total=len(data),
        total_pages=total_pages,
        filters=filters
    )

    return html.encode('utf-8')


# =============================================================================
# AUDIT LOG EXPORT
# =============================================================================

def export_audit_log(data, filename, columns):
    """
    Export audit log with full traceability information.

    Args:
        data: List of audit log entries
        filename: Name for export file
        columns: List of column keys/headers

    Returns:
        BytesIO containing CSV audit log
    """
    output = io.StringIO()
    output.write('\ufeff')  # BOM
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()

    for row in data:
        row_data = {
            'timestamp': row.get('timestamp', datetime.now().isoformat()),
            'user_id': row.get('user_id', ''),
            'action': row.get('action', ''),
            'changes': row.get('changes', ''),
            'ip_address': row.get('ip_address', ''),
            'session_info': row.get('session_info', ''),
            'entity_type': row.get('entity_type', ''),
            'entity_id': row.get('entity_id', ''),
        }
        for col in columns:
            if col not in row_data:
                row_data[col] = row.get(col, '')
        writer.writerow(row_data)

    output.seek(0)
    return output.getvalue().encode('utf-8-sig')


# =============================================================================
# RESPONSE HELPERS
# =============================================================================

def send_export_response(data, export_type, filename, columns, title=None):
    """
    Generate Flask response for the appropriate export type.

    Args:
        data: Data to export
        export_type: Type of export ('csv', 'excel_text', 'excel_general', etc.)
        filename: Base filename without extension
        columns: List of column keys/headers
        title: Optional title for reports

    Returns:
        Flask response object with appropriate headers
    """
    # Provide sample data if data is empty or None
    if not data:
        data = _get_sample_data(columns, filename)

    export_handlers = {
        'csv': lambda: (export_to_csv(data, filename, columns), 'text/csv; charset=utf-8-sig', '.csv'),
        'excel_text': lambda: (export_to_excel_text(data, filename, columns), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'),
        'excel_general': lambda: (export_to_excel_general(data, filename, columns), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'),
        'json': lambda: (export_to_json(data, filename), 'application/json', '.json'),
        'xml': lambda: (export_to_xml(data, filename), 'application/xml', '.xml'),
        'txt': lambda: (export_to_txt(data, filename), 'text/plain', '.txt'),
        'pdf': lambda: (export_to_pdf(data, filename, title or filename, columns), 'application/pdf', '.pdf'),
        'docx': lambda: (export_to_docx(data, filename, title or filename, columns), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx'),
        'html': lambda: (export_to_html(data, filename, title or filename, columns), 'text/html', '.html'),
        'printable': lambda: (export_to_printable_html(data, filename, title or filename, columns), 'text/html', '.html'),
        'barcode': lambda: (export_to_barcode_labels(data, filename), 'application/pdf', '.pdf'),
        'api': lambda: (json.dumps(export_to_api_json(data)).encode('utf-8'), 'application/json', '.json'),
        'email': lambda: (export_to_email_html(data, title or filename, '').encode('utf-8'), 'text/html', '.html'),
        'zip': lambda: (export_to_zip(data, filename), 'application/zip', '.zip'),
        'backup': lambda: (export_to_backup(data, filename), 'text/plain', '.sql'),
        'sql_dump': lambda: (export_to_sql_dump(data, filename), 'text/plain', '.sql'),
        'dashboard': lambda: (export_dashboard_state(data, filename), 'application/json', '.json'),
        'summary': lambda: (export_summary_report(data, filename, title or filename), 'text/html', '.html'),
        'detailed': lambda: (export_detailed_report(data, filename, title or filename, columns), 'text/html', '.html'),
        'audit_log': lambda: (export_to_csv(data, filename, columns), 'text/csv; charset=utf-8-sig', '.csv'),
    }

    if export_type not in export_handlers:
        return jsonify({'error': f'Invalid export type. Valid types: {list(export_handlers.keys())}'}), 400

    content, content_type, extension = export_handlers[export_type]()
    response = make_response(content)
    response.headers['Content-Type'] = content_type
    response.headers['Content-Disposition'] = f'attachment; filename={filename}{extension}'
    response.headers['X-Export-Type'] = export_type
    response.headers['X-Generated-At'] = datetime.now().isoformat()

    return response


def _get_sample_data(columns, filename):
    """Generate sample data for testing when no real data is available."""
    sample_records = []
    for i in range(1, 6):
        record = {}
        for col in columns:
            # Generate contextual sample data based on column name
            col_lower = col.lower()
            if 'id' in col_lower or 'code' in col_lower:
                record[col] = f'{col.upper()[:3]}-{i:04d}'
            elif 'name' in col_lower or 'title' in col_lower or 'description' in col_lower:
                record[col] = f'Sample {col.title()} {i}'
            elif 'date' in col_lower or 'time' in col_lower or 'created' in col_lower or 'updated' in col_lower:
                record[col] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif 'amount' in col_lower or 'value' in col_lower or 'price' in col_lower or 'cost' in col_lower or 'budget' in col_lower:
                record[col] = round(1000.00 + (i * 250.50), 2)
            elif 'quantity' in col_lower or 'count' in col_lower or 'qty' in col_lower:
                record[col] = i * 10
            elif 'status' in col_lower:
                statuses = ['active', 'pending', 'completed', 'cancelled']
                record[col] = statuses[i % len(statuses)]
            elif 'email' in col_lower:
                record[col] = f'user{i}@example.com'
            elif 'phone' in col_lower or 'mobile' in col_lower:
                record[col] = f'+1-555-{i:04d}'
            elif 'address' in col_lower:
                record[col] = f'{i}00 Sample Street, City {i}'
            elif 'percent' in col_lower or 'rate' in col_lower or 'roi' in col_lower:
                record[col] = round(75.5 + (i * 5.2), 1)
            else:
                record[col] = f'Data {i}'
        sample_records.append(record)
    return sample_records


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _get_nested_value(data, key):
    """
    Get value from nested dict using dot notation.

    Args:
        data: Dict to search
        key: Key in dot notation (e.g., 'user.profile.name')

    Returns:
        Value at key or empty string if not found
    """
    if not key:
        return ''

    keys = key.split('.')
    value = data

    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, '')
        elif isinstance(value, list) and k.isdigit():
            idx = int(k)
            value = value[idx] if idx < len(value) else ''
        else:
            return ''

    return value if value is not None else ''


def _sanitize_value(value):
    """
    Sanitize value for safe export.

    Args:
        value: Value to sanitize

    Returns:
        Sanitized value safe for export
    """
    if value is None:
        return ''

    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m-%d %H:%M:%S')

    if isinstance(value, (int, float)):
        return value

    # Convert to string and remove control characters
    str_value = str(value)
    # Remove problematic characters but keep unicode
    return ''.join(char for char in str_value if ord(char) >= 32 or char in '\n\r\t')


def get_export_columns(data, custom_columns=None):
    """
    Get columns from data, with optional custom override.

    Args:
        data: List of dicts or dict
        custom_columns: Optional list of column keys

    Returns:
        List of column keys
    """
    if custom_columns:
        return custom_columns

    if isinstance(data, list) and data:
        return list(data[0].keys())

    if isinstance(data, dict):
        return list(data.keys())

    return []
