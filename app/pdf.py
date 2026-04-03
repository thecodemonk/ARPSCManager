import io

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_ics309_pdf(comm_log):
    """Generate an ICS-309 Communications Log PDF. Returns a BytesIO buffer."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ICSTitle', parent=styles['Heading1'], fontSize=14,
        alignment=1, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'ICSSubtitle', parent=styles['Normal'], fontSize=8,
        alignment=1, spaceAfter=12,
    )
    label_style = ParagraphStyle(
        'ICSLabel', parent=styles['Normal'], fontSize=7, textColor=colors.grey,
    )
    value_style = ParagraphStyle(
        'ICSValue', parent=styles['Normal'], fontSize=9,
    )
    small_style = ParagraphStyle(
        'ICSSmall', parent=styles['Normal'], fontSize=8,
    )

    elements = []

    # Title
    elements.append(Paragraph('ICS 309 — COMMUNICATIONS LOG', title_style))
    elements.append(Paragraph(
        'Use this form to record radio traffic during an incident or event.',
        subtitle_style
    ))

    # Header info table
    op_start = comm_log.op_period_start.strftime('%Y-%m-%d %H:%M') if comm_log.op_period_start else ''
    op_end = comm_log.op_period_end.strftime('%Y-%m-%d %H:%M') if comm_log.op_period_end else ''

    header_data = [
        [
            Paragraph('<b>1. Incident Name / Activation #</b>', label_style),
            Paragraph('<b>2. Operational Period</b>', label_style),
        ],
        [
            Paragraph(f'{comm_log.incident_name or ""}'
                      f'{" / " + comm_log.activation_number if comm_log.activation_number else ""}',
                      value_style),
            Paragraph(f'From: {op_start}  To: {op_end}', value_style),
        ],
        [
            Paragraph('<b>3. Net Name / Position / Tactical Call</b>', label_style),
            Paragraph('<b>4. Radio Operator (Name, Call Sign)</b>', label_style),
        ],
        [
            Paragraph(comm_log.net_name_or_position or '', value_style),
            Paragraph(f'{comm_log.operator_name or ""}'
                      f'{", " + comm_log.operator_callsign if comm_log.operator_callsign else ""}',
                      value_style),
        ],
    ]

    header_table = Table(header_data, colWidths=[3.75 * inch, 3.75 * inch])
    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    # Communications log table
    log_header = [
        Paragraph('<b>Time</b>', small_style),
        Paragraph('<b>From Call Sign</b>', small_style),
        Paragraph('<b>From Msg #</b>', small_style),
        Paragraph('<b>To Call Sign</b>', small_style),
        Paragraph('<b>To Msg #</b>', small_style),
        Paragraph('<b>Message</b>', small_style),
    ]

    log_data = [log_header]
    for entry in comm_log.entries:
        time_str = entry.time.strftime('%H:%M') if entry.time else ''
        log_data.append([
            Paragraph(time_str, small_style),
            Paragraph(entry.from_callsign or '', small_style),
            Paragraph(entry.from_msg_num or '', small_style),
            Paragraph(entry.to_callsign or '', small_style),
            Paragraph(entry.to_msg_num or '', small_style),
            Paragraph(entry.message or '', small_style),
        ])

    # Add empty rows to fill page if few entries
    while len(log_data) < 25:
        log_data.append(['', '', '', '', '', ''])

    col_widths = [0.7 * inch, 1.0 * inch, 0.7 * inch, 1.0 * inch, 0.7 * inch, 3.4 * inch]
    log_table = Table(log_data, colWidths=col_widths, repeatRows=1)
    log_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e0e0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    elements.append(log_table)
    elements.append(Spacer(1, 12))

    # Footer
    prepared_date = comm_log.prepared_date.strftime('%Y-%m-%d') if comm_log.prepared_date else ''
    footer_data = [
        [
            Paragraph('<b>6. Prepared By</b>', label_style),
            Paragraph('<b>7. Date/Time Prepared</b>', label_style),
        ],
        [
            Paragraph(comm_log.prepared_by or comm_log.operator_name or '', value_style),
            Paragraph(prepared_date, value_style),
        ],
    ]

    footer_table = Table(footer_data, colWidths=[3.75 * inch, 3.75 * inch])
    footer_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(footer_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
