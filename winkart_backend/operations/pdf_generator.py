from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

def generate_invoice_pdf(bill_data):
    """Generates a professional PDF invoice in memory using ReportLab."""
    buffer = BytesIO()
    
    # Page setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1A237E'), # Dark Indigo
        spaceAfter=15
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#FFFFFF')
    )
    
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12
    )
    
    cell_bold_style = ParagraphStyle(
        'CellBoldStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12
    )
    
    right_cell_style = ParagraphStyle(
        'RightCellStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        alignment=2 # Right align
    )
    
    right_bold_style = ParagraphStyle(
        'RightBoldStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        alignment=2 # Right align
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )

    # 1. Header (Logo / Shop Branding)
    shop_info = f"<b>{bill_data['shop_name']}</b><br/>{bill_data.get('shop_address', 'In-Store Checkout')}"
    title_text = "<b>WINKART DIGITAL BILL</b>"
    
    header_table_data = [
        [Paragraph(title_text, title_style), Paragraph(shop_info, meta_style)]
    ]
    header_table = Table(header_table_data, colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT')
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # Divider
    divider = Table([['']], colWidths=[530], rowHeights=[2])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A237E')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 15))
    
    # 2. Bill Metadata & Customer Info
    created_at_str = bill_data['created_at']
    if isinstance(created_at_str, datetime):
        created_at_str = created_at_str.strftime('%d-%b-%Y %I:%M %p')
        
    bill_info = (
        f"<b>Bill Number:</b> {bill_data['bill_number']}<br/>"
        f"<b>Date:</b> {created_at_str}<br/>"
        f"<b>Status:</b> <font color='{'green' if bill_data['status'] == 'Paid' else 'red'}'><b>{bill_data['status']}</b></font>"
    )
    
    customer_info = (
        f"<b>Customer Name:</b> {bill_data['customer_name']}<br/>"
        f"<b>Phone:</b> {bill_data['customer_phone']}<br/>"
        f"<b>Checkout Type:</b> In-Store Catalog self-checkout"
    )
    
    meta_table_data = [
        [Paragraph(bill_info, meta_style), Paragraph(customer_info, meta_style)]
    ]
    meta_table = Table(meta_table_data, colWidths=[265, 265])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10)
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # 3. Items Table
    table_data = [
        [
            Paragraph("Item Name", header_style),
            Paragraph("Price", header_style),
            Paragraph("Qty", header_style),
            Paragraph("Discount", header_style),
            Paragraph("Total", header_style)
        ]
    ]
    
    for item in bill_data['items']:
        discount = item.get('discount_price', 0.0) or 0.0
        # Calculate single discount per item
        single_discount = item['price'] - discount if discount > 0 else 0.0
        
        table_data.append([
            Paragraph(item['name'], cell_style),
            Paragraph(f"₹{item['price']:.2f}", cell_style),
            Paragraph(str(item['quantity']), cell_style),
            Paragraph(f"₹{single_discount * item['quantity']:.2f}" if single_discount > 0 else "₹0.00", cell_style),
            Paragraph(f"₹{item['total_price']:.2f}", cell_style)
        ])
        
    # Table calculations
    subtotal = bill_data['subtotal']
    discount_total = bill_data['discount']
    tax = bill_data['tax']
    total_amount = bill_data['total_amount']
    
    # Add pricing calculations to table
    table_data.append([Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("<b>Subtotal</b>", cell_bold_style), Paragraph(f"₹{subtotal:.2f}", right_cell_style)])
    table_data.append([Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("<b>Total Discount</b>", cell_bold_style), Paragraph(f"₹{discount_total:.2f}", right_cell_style)])
    table_data.append([Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("<b>Taxes (GST)</b>", cell_bold_style), Paragraph(f"₹{tax:.2f}", right_cell_style)])
    table_data.append([Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("<b>Grand Total</b>", right_bold_style), Paragraph(f"₹{total_amount:.2f}", right_bold_style)])
    
    items_table = Table(table_data, colWidths=[240, 70, 45, 85, 90])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A237E')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-5), 0.5, colors.HexColor('#E0E0E0')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        # Total formatting
        ('LINEABOVE', (3,-4), (4,-4), 1, colors.HexColor('#1A237E')),
        ('BACKGROUND', (3,-1), (4,-1), colors.HexColor('#E8EAF6')),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 40))
    
    # 4. Footer
    footer_text = "<para align='center'>This is a computer generated bill. No signature is required.<br/><b>Thank you for shopping with us! Check all products at WINKART.</b></para>"
    story.append(Paragraph(footer_text, meta_style))
    
    # Build document
    doc.build(story)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content
from datetime import datetime
