# Модуль для генерации документов (квитанций о сделке)

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from io import BytesIO


def generate_seller_receipt(deal_id: int, seller_username: str, seller_id: int, 
                           buyer_username: str, buyer_id: int, amount: float, 
                           currency: str, wallet_address: str) -> bytes:
    """
    Генерирует PDF-документ для продавца о завершённой сделке
    
    Args:
        deal_id: ID сделки
        seller_username: Username продавца в Telegram
        seller_id: ID продавца в системе
        buyer_username: Username покупателя в Telegram
        buyer_id: ID покупателя в системе
        amount: Сумма сделки
        currency: Валюта (BTC, TON)
        wallet_address: Адрес кошелька продавца
    
    Returns:
        bytes: PDF документ в виде бинарных данных
    """
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Стиль для заголовка
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1F2125'),
        spaceAfter=30,
        alignment=1  # Центрирование
    )
    
    # Стиль для обычного текста
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1F2125'),
        leading=18,
        spaceAfter=12
    )
    
    # Стиль для подзаголовков
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#134252'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    content = []
    
    # Логотип/Название сервиса
    title = Paragraph("<b>🔐 EasyGarante</b><br/>Система гарантирования платежей", title_style)
    content.append(title)
    content.append(Spacer(1, 20*mm))
    
    # Основной заголовок документа
    doc_title = Paragraph("<b>КВИТАНЦИЯ О ЗАВЕРШЁННОЙ СДЕЛКЕ</b>", heading_style)
    content.append(doc_title)
    content.append(Spacer(1, 15*mm))
    
    # Информация о сделке в таблице
    deal_data = [
        ['Параметр', 'Значение'],
        ['Номер сделки', f'#{deal_id}'],
        ['Дата завершения', datetime.now().strftime('%d.%m.%Y в %H:%M:%S')],
        ['Роль в сделке', 'Продавец (получатель средств)'],
    ]
    
    deal_table = Table(deal_data, colWidths=[80*mm, 80*mm])
    deal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#134252')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.white]),
    ]))
    
    content.append(deal_table)
    content.append(Spacer(1, 15*mm))
    
    # Информация о сторонах сделки
    parties_header = Paragraph("<b>Стороны сделки:</b>", heading_style)
    content.append(parties_header)
    
    seller_info = Paragraph(
        f"<b>Продавец (Вы):</b><br/>"
        f"Username: @{seller_username}<br/>"
        f"ID в системе: {seller_id}",
        normal_style
    )
    content.append(seller_info)
    content.append(Spacer(1, 10*mm))
    
    buyer_info = Paragraph(
        f"<b>Покупатель:</b><br/>"
        f"Username: @{buyer_username}<br/>"
        f"ID в системе: {buyer_id}",
        normal_style
    )
    content.append(buyer_info)
    content.append(Spacer(1, 15*mm))
    
    # Информация о платеже
    payment_header = Paragraph("<b>Информация о платеже:</b>", heading_style)
    content.append(payment_header)
    
    payment_data = [
        ['Сумма', f'{amount} {currency}'],
        ['Валюта', currency],
        ['Адрес получения', wallet_address],
    ]
    
    payment_table = Table(payment_data, colWidths=[80*mm, 80*mm])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#32B8C6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.white]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('WRAP', (1, 0), (1, -1), True),
    ]))
    
    content.append(payment_table)
    content.append(Spacer(1, 20*mm))
    
    # Завершающий текст
    footer_text = Paragraph(
        f"<b>Спасибо за использование сервиса EasyGarante!</b><br/><br/>"
        f"Данная квитанция подтверждает, что вами была проведена сделка по продаже "
        f"товара/услуги покупателю @{buyer_username} (ID: {buyer_id}). "
        f"На ваш кошелёк поступила сумма <b>{amount} {currency}</b> "
        f"на адрес <b>{wallet_address}</b>.<br/><br/>"
        f"Все средства защищены нашей системой гарантирования. "
        f"Спасибо что вы доверяете EasyGarante!",
        normal_style
    )
    content.append(footer_text)
    content.append(Spacer(1, 15*mm))
    
    # Информация о системе
    system_info = Paragraph(
        f"<i>Документ сгенерирован: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}<br/>"
        f"Сервис: EasyGarante - система гарантирования платежей<br/>"
        f"Платформа: Telegram Bot</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, 
                      textColor=colors.grey, alignment=0)
    )
    content.append(system_info)
    
    # Построение PDF
    doc.build(content)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def generate_buyer_receipt(deal_id: int, buyer_username: str, buyer_id: int, 
                          seller_username: str, seller_id: int, amount: float, 
                          currency: str, seller_wallet: str) -> bytes:
    """
    Генерирует PDF-документ для покупателя о завершённой сделке
    
    Args:
        deal_id: ID сделки
        buyer_username: Username покупателя в Telegram
        buyer_id: ID покупателя в системе
        seller_username: Username продавца в Telegram
        seller_id: ID продавца в системе
        amount: Сумма сделки
        currency: Валюта (BTC, TON)
        seller_wallet: Адрес кошелька продавца
    
    Returns:
        bytes: PDF документ в виде бинарных данных
    """
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Стиль для заголовка
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1F2125'),
        spaceAfter=30,
        alignment=1  # Центрирование
    )
    
    # Стиль для обычного текста
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1F2125'),
        leading=18,
        spaceAfter=12
    )
    
    # Стиль для подзаголовков
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#134252'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    content = []
    
    # Логотип/Название сервиса
    title = Paragraph("<b>🔐 EasyGarante</b><br/>Система гарантирования платежей", title_style)
    content.append(title)
    content.append(Spacer(1, 20*mm))
    
    # Основной заголовок документа
    doc_title = Paragraph("<b>КВИТАНЦИЯ О ЗАВЕРШЁННОЙ СДЕЛКЕ</b>", heading_style)
    content.append(doc_title)
    content.append(Spacer(1, 15*mm))
    
    # Информация о сделке в таблице
    deal_data = [
        ['Параметр', 'Значение'],
        ['Номер сделки', f'#{deal_id}'],
        ['Дата завершения', datetime.now().strftime('%d.%m.%Y в %H:%M:%S')],
        ['Роль в сделке', 'Покупатель (инициатор платежа)'],
    ]
    
    deal_table = Table(deal_data, colWidths=[80*mm, 80*mm])
    deal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#134252')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.white]),
    ]))
    
    content.append(deal_table)
    content.append(Spacer(1, 15*mm))
    
    # Информация о сторонах сделки
    parties_header = Paragraph("<b>Стороны сделки:</b>", heading_style)
    content.append(parties_header)
    
    buyer_info = Paragraph(
        f"<b>Покупатель (Вы):</b><br/>"
        f"Username: @{buyer_username}<br/>"
        f"ID в системе: {buyer_id}",
        normal_style
    )
    content.append(buyer_info)
    content.append(Spacer(1, 10*mm))
    
    seller_info = Paragraph(
        f"<b>Продавец:</b><br/>"
        f"Username: @{seller_username}<br/>"
        f"ID в системе: {seller_id}",
        normal_style
    )
    content.append(seller_info)
    content.append(Spacer(1, 15*mm))
    
    # Информация о платеже
    payment_header = Paragraph("<b>Информация о платеже:</b>", heading_style)
    content.append(payment_header)
    
    payment_data = [
        ['Переведено', f'{amount} {currency}'],
        ['Валюта', currency],
        ['На адрес продавца', seller_wallet],
    ]
    
    payment_table = Table(payment_data, colWidths=[80*mm, 80*mm])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#32B8C6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.white]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('WRAP', (1, 0), (1, -1), True),
    ]))
    
    content.append(payment_table)
    content.append(Spacer(1, 20*mm))
    
    # Завершающий текст
    footer_text = Paragraph(
        f"<b>Спасибо за использование сервиса EasyGarante!</b><br/><br/>"
        f"Данная квитанция подтверждает, что вами была проведена сделка по покупке "
        f"товара/услуги у продавца @{seller_username} (ID: {seller_id}). "
        f"Вами было переведено <b>{amount} {currency}</b> "
        f"на адрес продавца <b>{seller_wallet}</b>.<br/><br/>"
        f"Все средства защищены нашей системой гарантирования. "
        f"Спасибо что вы доверяете EasyGarante!",
        normal_style
    )
    content.append(footer_text)
    content.append(Spacer(1, 15*mm))
    
    # Информация о системе
    system_info = Paragraph(
        f"<i>Документ сгенерирован: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}<br/>"
        f"Сервис: EasyGarante - система гарантирования платежей<br/>"
        f"Платформа: Telegram Bot</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, 
                      textColor=colors.grey, alignment=0)
    )
    content.append(system_info)
    
    # Построение PDF
    doc.build(content)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
