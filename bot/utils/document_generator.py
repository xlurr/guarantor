# Модуль для генерации документов (квитанций о сделке)

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from io import BytesIO
import os


# Получаем путь к текущему модулю
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def register_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    try:
        # Локальные шрифты в папке utils (приоритет)
        local_font_normal = os.path.join(CURRENT_DIR, 'DejaVuSans.ttf')
        local_font_bold = os.path.join(CURRENT_DIR, 'DejaVuSans-Bold.ttf')
        
        # Системные пути
        system_paths_normal = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',      # Linux
            '/System/Library/Fonts/Supplemental/Arial.ttf',         # macOS
            'C:\\Windows\\Fonts\\arial.ttf',                        # Windows
        ]
        
        system_paths_bold = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', # Linux
            '/System/Library/Fonts/Supplemental/Arial Bold.ttf',    # macOS
            'C:\\Windows\\Fonts\\arialbd.ttf',                      # Windows
        ]
        
        # Регистрация обычного шрифта
        font_normal_registered = False
        if os.path.exists(local_font_normal):
            pdfmetrics.registerFont(TTFont('CustomFont', local_font_normal))
            print(f"✅ Font registered: {local_font_normal}")
            font_normal_registered = True
        else:
            for path in system_paths_normal:
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont('CustomFont', path))
                    print(f"✅ System font registered: {path}")
                    font_normal_registered = True
                    break
        
        if not font_normal_registered:
            print("⚠️ No normal font found, using Helvetica")
            return False
        
        # Регистрация жирного шрифта
        font_bold_registered = False
        if os.path.exists(local_font_bold):
            pdfmetrics.registerFont(TTFont('CustomFont-Bold', local_font_bold))
            print(f"✅ Bold font registered: {local_font_bold}")
            font_bold_registered = True
        else:
            for path in system_paths_bold:
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont('CustomFont-Bold', path))
                    print(f"✅ System bold font registered: {path}")
                    font_bold_registered = True
                    break
        
        # Если Bold не найден, используем обычный
        if not font_bold_registered:
            if os.path.exists(local_font_normal):
                pdfmetrics.registerFont(TTFont('CustomFont-Bold', local_font_normal))
            else:
                for path in system_paths_normal:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont('CustomFont-Bold', path))
                        break
            print("⚠️ Using normal font for bold")
        
        # Регистрируем семейство шрифтов (важно для корректной работы!)
        registerFontFamily(
            'CustomFont',
            normal='CustomFont',
            bold='CustomFont-Bold',
            italic='CustomFont',
            boldItalic='CustomFont-Bold'
        )
        
        print("✅ Font family registered successfully")
        return True
        
    except Exception as e:
        print(f"❌ Font registration error: {e}")
        import traceback
        traceback.print_exc()
        return False


# Регистрируем шрифт при импорте модуля
font_registered = register_fonts()
FONT_NAME = 'CustomFont' if font_registered else 'Helvetica'
FONT_NAME_BOLD = 'CustomFont-Bold' if font_registered else 'Helvetica-Bold'

print(f"📝 Using fonts: {FONT_NAME} / {FONT_NAME_BOLD}")


def generate_seller_receipt(deal_id: int, seller_username: str, seller_id: int, 
                           buyer_username: str, buyer_id: int, amount: float, 
                           currency: str, wallet_address: str) -> bytes:
    """Генерирует PDF-документ для продавца о завершённой сделке"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Стиль для заголовка
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME_BOLD,
        fontSize=18,
        textColor=colors.HexColor('#1F2125'),
        spaceAfter=30,
        alignment=1
    )
    
    # Стиль для обычного текста
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        textColor=colors.HexColor('#1F2125'),
        leading=18,
        spaceAfter=12
    )
    
    # Стиль для подзаголовков
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME_BOLD,
        fontSize=12,
        textColor=colors.HexColor('#134252'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    content = []
    
    # Заголовок
    title = Paragraph("🔐 EasyGarant<br/>Система гарантирования платежей", title_style)
    content.append(title)
    content.append(Spacer(1, 20*mm))
    
    # Основной заголовок документа
    doc_title = Paragraph("КВИТАНЦИЯ О ЗАВЕРШЁННОЙ СДЕЛКЕ", heading_style)
    content.append(doc_title)
    content.append(Spacer(1, 15*mm))
    
    # Информация о сделке
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
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.white]),
    ]))
    
    content.append(deal_table)
    content.append(Spacer(1, 15*mm))
    
    # Стороны сделки
    parties_header = Paragraph("Стороны сделки:", heading_style)
    content.append(parties_header)
    
    seller_info = Paragraph(
        f"Продавец (Вы):<br/>"
        f"Username: @{seller_username}<br/>"
        f"ID в системе: {seller_id}",
        normal_style
    )
    content.append(seller_info)
    content.append(Spacer(1, 10*mm))
    
    buyer_info = Paragraph(
        f"Покупатель:<br/>"
        f"Username: @{buyer_username}<br/>"
        f"ID в системе: {buyer_id}",
        normal_style
    )
    content.append(buyer_info)
    content.append(Spacer(1, 15*mm))
    
    # Информация о платеже
    payment_header = Paragraph("Информация о платеже:", heading_style)
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
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.white]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    content.append(payment_table)
    content.append(Spacer(1, 20*mm))
    
    # Завершающий текст
    footer_text = Paragraph(
        f"Спасибо за использование сервиса FastDeal!<br/><br/>"
        f"Данная квитанция подтверждает, что вами была проведена сделка по продаже "
        f"товара/услуги покупателю @{buyer_username} (ID: {buyer_id}). "
        f"На ваш кошелёк поступила сумма {amount} {currency} "
        f"на адрес {wallet_address}.<br/><br/>"
        f"Все средства защищены нашей системой гарантирования.",
        normal_style
    )
    content.append(footer_text)
    content.append(Spacer(1, 15*mm))
    
    # Футер
    footer_style = ParagraphStyle(
        'Footer', 
        parent=styles['Normal'], 
        fontName=FONT_NAME,
        fontSize=9, 
        textColor=colors.grey, 
        alignment=0
    )
    
    system_info = Paragraph(
        f"Документ сгенерирован: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}<br/>"
        f"Сервис: FastDeal - система гарантирования платежей EasyGarant<br/>"
        f"Платформа: Telegram Bot",
        footer_style
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
    """Генерирует PDF-документ для покупателя о завершённой сделке"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME_BOLD,
        fontSize=18,
        textColor=colors.HexColor('#1F2125'),
        spaceAfter=30,
        alignment=1
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        textColor=colors.HexColor('#1F2125'),
        leading=18,
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME_BOLD,
        fontSize=12,
        textColor=colors.HexColor('#134252'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    content = []
    
    title = Paragraph("🔐 EasyGarante<br/>Система гарантирования платежей", title_style)
    content.append(title)
    content.append(Spacer(1, 20*mm))
    
    doc_title = Paragraph("КВИТАНЦИЯ О ЗАВЕРШЁННОЙ СДЕЛКЕ", heading_style)
    content.append(doc_title)
    content.append(Spacer(1, 15*mm))
    
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
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.white]),
    ]))
    
    content.append(deal_table)
    content.append(Spacer(1, 15*mm))
    
    parties_header = Paragraph("Стороны сделки:", heading_style)
    content.append(parties_header)
    
    buyer_info = Paragraph(
        f"Покупатель (Вы):<br/>"
        f"Username: @{buyer_username}<br/>"
        f"ID в системе: {buyer_id}",
        normal_style
    )
    content.append(buyer_info)
    content.append(Spacer(1, 10*mm))
    
    seller_info = Paragraph(
        f"Продавец:<br/>"
        f"Username: @{seller_username}<br/>"
        f"ID в системе: {seller_id}",
        normal_style
    )
    content.append(seller_info)
    content.append(Spacer(1, 15*mm))
    
    payment_header = Paragraph("Информация о платеже:", heading_style)
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
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.white]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    content.append(payment_table)
    content.append(Spacer(1, 20*mm))
    
    footer_text = Paragraph(
        f"Спасибо за использование сервиса EasyGarant!<br/><br/>"
        f"Данная квитанция подтверждает, что вами была проведена сделка по покупке "
        f"товара/услуги у продавца @{seller_username} (ID: {seller_id}). "
        f"Вами было переведено {amount} {currency} "
        f"на адрес продавца {seller_wallet}.<br/><br/>"
        f"Все средства защищены нашей системой гарантирования FastDeal.",
        normal_style
    )
    content.append(footer_text)
    content.append(Spacer(1, 15*mm))
    
    footer_style = ParagraphStyle(
        'Footer', 
        parent=styles['Normal'], 
        fontName=FONT_NAME,
        fontSize=9, 
        textColor=colors.grey, 
        alignment=0
    )
    
    system_info = Paragraph(
        f"Документ сгенерирован: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}<br/>"
        f"Сервис: EasyGarant - система гарантирования крипто-платежей<br/>"
        f"Платформа: Telegram Bot. Владелец: @dontwritethis",
        footer_style
    )
    content.append(system_info)
    
    doc.build(content)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
