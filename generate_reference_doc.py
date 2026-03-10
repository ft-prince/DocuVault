"""
DocuVault Client Reference Guide – PDF Generator
Theme: Renata IoT Reference Guide (Renata_IoT_Reference_Guide.docx)
Colors: H1=#E84C25, H2=#2C3E50, Accent=#4472C4, Orange=#ED7D31
Logo: Logo.png (768x256 RGBA)
"""

import os, math, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib import colors

# ── Brand Colors (from Renata_IoT_Reference_Guide.docx) ──────────────────────
H1_COLOR    = HexColor('#E84C25')   # Heading 1 orange-red
H2_COLOR    = HexColor('#2C3E50')   # Heading 2 dark navy
H3_COLOR    = HexColor('#2E74B5')   # Heading 3 blue
ACCENT      = HexColor('#4472C4')   # Primary blue accent
ORANGE      = HexColor('#ED7D31')   # Secondary orange
NAVY        = HexColor('#44546A')   # Dark navy (table headers, footer)
LIGHT_BLUE  = HexColor('#5B9BD5')   # Light blue
BODY_TEXT   = HexColor('#2C2C2C')   # Body text
MID_GRAY    = HexColor('#6B7280')   # Secondary text
BORDER      = HexColor('#D1D5DB')   # Table borders
LIGHT_BG    = HexColor('#F8F9FA')   # Alternating row background
ORANGE_PALE = HexColor('#FFF3ED')   # Light orange background
BLUE_PALE   = HexColor('#EFF6FF')   # Light blue background
WHITE       = white

PAGE_W, PAGE_H = A4   # 595 x 842 pt
LOGO_PATH = r'D:\AI_Model_Renata\Document-management\Group\V2\DocuVault\Logo.png'

# ── Custom Flowables ──────────────────────────────────────────────────────────

class OrangeLine(Flowable):
    """Thick orange underline for H1 sections."""
    def __init__(self, width=440, thickness=3, color=None):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color or H1_COLOR
        self.height = thickness + 2

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


class ThinLine(Flowable):
    """Thin divider line."""
    def __init__(self, width=440, color=None):
        Flowable.__init__(self)
        self.width = width
        self.color = color or BORDER
        self.height = 1

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 0, self.width, 0)


class NumberedStep(Flowable):
    """Pill with step number + label."""
    def __init__(self, number, label, width=440, fill=None):
        Flowable.__init__(self)
        self.number = str(number)
        self.label  = label
        self.width  = width
        self.fill   = fill or ACCENT
        self.height = 28

    def draw(self):
        c = self.canv
        h = self.height
        # Circle
        c.setFillColor(self.fill)
        c.circle(h / 2, h / 2, h / 2, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(h / 2, h / 2 - 4, self.number)
        # Label
        c.setFillColor(H2_COLOR)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(h + 10, h / 2 - 4, self.label)


class SimpleFlowBox(Flowable):
    """Simple 5-step horizontal flow diagram."""
    def __init__(self, width, steps, colors_list=None):
        Flowable.__init__(self)
        self.width  = width
        self.steps  = steps
        self.colors = colors_list or [ACCENT] * len(steps)
        self.height = 80

    def draw(self):
        c  = self.canv
        W  = self.width
        H  = self.height
        n  = len(self.steps)
        bw = (W - (n - 1) * 18) / n  # box width
        bh = 46

        for i, (label, sub) in enumerate(self.steps):
            x   = i * (bw + 18)
            by  = (H - bh) / 2
            col = self.colors[i] if i < len(self.colors) else ACCENT

            # Box
            c.setFillColor(col)
            c.setStrokeColor(WHITE)
            c.setLineWidth(0)
            c.roundRect(x, by, bw, bh, 6, fill=1, stroke=0)

            # Label
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 7.5)
            cy = by + bh / 2 + (4 if sub else 0)
            c.drawCentredString(x + bw / 2, cy, label)
            if sub:
                c.setFont('Helvetica', 6.5)
                c.setFillColor(HexColor('#dbeafe'))
                c.drawCentredString(x + bw / 2, by + bh / 2 - 8, sub)

            # Arrow (not after last)
            if i < n - 1:
                ax = x + bw + 2
                ay = by + bh / 2
                c.setFillColor(H2_COLOR)
                c.setStrokeColor(H2_COLOR)
                c.setLineWidth(1.2)
                c.line(ax, ay, ax + 14, ay)
                p = c.beginPath()
                p.moveTo(ax + 14, ay)
                p.lineTo(ax + 9,  ay + 4)
                p.lineTo(ax + 9,  ay - 4)
                p.close()
                c.drawPath(p, fill=1, stroke=0)


class SimpleArchDiagram(Flowable):
    """Clean, client-friendly architecture diagram (3 layers, simple boxes)."""
    def __init__(self, width, height):
        Flowable.__init__(self)
        self.width  = width
        self.height = height

    def draw(self):
        c = self.canv
        W = self.width
        H = self.height

        # Background
        c.setFillColor(HexColor('#F8FAFC'))
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, W, H, 8, fill=1, stroke=1)

        def box(x, y, w, h, label, sub, fill, text_col=WHITE, sub_col=None):
            c.setFillColor(fill)
            c.setStrokeColor(WHITE)
            c.setLineWidth(1)
            c.roundRect(x, y, w, h, 6, fill=1, stroke=1)
            c.setFillColor(text_col)
            c.setFont('Helvetica-Bold', 8.5)
            label_y = y + h / 2 + (5 if sub else 0)
            c.drawCentredString(x + w / 2, label_y, label)
            if sub:
                c.setFont('Helvetica', 7)
                c.setFillColor(sub_col or HexColor('#CBD5E1'))
                c.drawCentredString(x + w / 2, y + h / 2 - 8, sub)

        def v_arrow(cx, y_top, y_bot, col=HexColor('#94A3B8'), label=''):
            c.setStrokeColor(col)
            c.setLineWidth(1.3)
            c.line(cx, y_top, cx, y_bot + 7)
            c.setFillColor(col)
            p = c.beginPath()
            p.moveTo(cx,     y_bot)
            p.lineTo(cx - 5, y_bot + 9)
            p.lineTo(cx + 5, y_bot + 9)
            p.close()
            c.drawPath(p, fill=1, stroke=0)
            if label:
                c.setFillColor(MID_GRAY)
                c.setFont('Helvetica', 6.5)
                c.drawCentredString(cx + 22, (y_top + y_bot) / 2 + 2, label)

        def h_arrow(y, x_left, x_right, col=HexColor('#94A3B8')):
            c.setStrokeColor(col)
            c.setLineWidth(1.3)
            c.line(x_left, y, x_right - 7, y)
            c.setFillColor(col)
            p = c.beginPath()
            p.moveTo(x_right,     y)
            p.lineTo(x_right - 9, y + 4)
            p.lineTo(x_right - 9, y - 4)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

        def section_tag(x, y, label, col):
            tw = len(label) * 6 + 12
            c.setFillColor(col)
            c.roundRect(x, y, tw, 14, 3, fill=1, stroke=0)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 6.5)
            c.drawString(x + 6, y + 3, label)

        margin = 20
        # ── Row Y positions (bottom of each row, canvas bottom = 0) ──
        R3y = H - 65    # User layer (top)
        R2y = H - 155   # Application layer
        R1y = H - 245   # AI + Storage layer

        bh  = 36
        bw3 = 90   # user box
        bw2 = 95   # app boxes
        bw1 = 100  # bottom boxes

        # ─── Row 3: User ─────────────────────────────────────────────
        section_tag(margin, R3y + bh + 8, 'YOU', H1_COLOR)
        ux = W / 2 - bw3 / 2
        box(ux, R3y, bw3, bh, 'Your Web Browser', 'Any device, any browser', ACCENT)

        # ─── Row 2: Application ──────────────────────────────────────
        section_tag(margin, R2y + bh + 8, 'DOCUVAULT PLATFORM', H2_COLOR)
        app_boxes = [
            ('Login & Accounts',  '',       HexColor('#7C3AED')),
            ('Document Manager',  '',       H2_COLOR),
            ('AI Assistant',      'Chatbot', H1_COLOR),
            ('Admin & Reports',   '',       HexColor('#0891B2')),
        ]
        spacing2 = (W - 2 * margin) / len(app_boxes)
        R2_centers = []
        for i, (lbl, sub, col) in enumerate(app_boxes):
            bx = margin + i * spacing2 + (spacing2 - bw2) / 2
            box(bx, R2y, bw2, bh, lbl, sub, col)
            R2_centers.append(bx + bw2 / 2)

        # Arrow browser -> platform center
        v_arrow(W / 2, R3y, R2y + bh, ACCENT, '')

        # ─── Row 1: AI + Storage ─────────────────────────────────────
        section_tag(margin, R1y + bh + 8, 'AI ENGINE & STORAGE', HexColor('#059669'))
        bottom_boxes = [
            ('Document Storage',  'Your files & versions',  HexColor('#1D4ED8')),
            ('AI Search Engine',  'Finds relevant content', HexColor('#059669')),
            ('AI Answer Model',   'Generates the response', H1_COLOR),
            ('User & Role Store', 'Accounts & permissions', NAVY),
        ]
        spacing1 = (W - 2 * margin) / len(bottom_boxes)
        R1_centers = []
        for i, (lbl, sub, col) in enumerate(bottom_boxes):
            bx = margin + i * spacing1 + (spacing1 - bw1) / 2
            box(bx, R1y, bw1, bh, lbl, sub, col)
            R1_centers.append(bx + bw1 / 2)

        # Arrows: App → Storage
        # Doc Manager → Document Storage
        v_arrow(R2_centers[1], R2y, R1y + bh, HexColor('#6B7280'))
        # AI Assistant → AI Search + AI Model
        v_arrow(R2_centers[2], R2y, R1y + bh, H1_COLOR)
        # Login → User Store
        v_arrow(R2_centers[0], R2y, R1y + bh, HexColor('#7C3AED'))

        # ─── Legend ──────────────────────────────────────────────────
        ly = 8
        legend_items = [
            (ACCENT,              'User → Platform'),
            (H1_COLOR,            'AI Query Flow'),
            (HexColor('#6B7280'), 'Data Storage Flow'),
        ]
        total_lw = len(legend_items) * 130
        lx_start = (W - total_lw) / 2
        for i, (col, lbl) in enumerate(legend_items):
            lx = lx_start + i * 130
            c.setFillColor(col)
            c.circle(lx + 6, ly + 6, 5, fill=1, stroke=0)
            c.setFillColor(MID_GRAY)
            c.setFont('Helvetica', 6.5)
            c.drawString(lx + 14, ly + 3, lbl)


class QueryFlowDiagram(Flowable):
    """Simple linear query flow: User → Platform → AI → Answer."""
    def __init__(self, width, height=60):
        Flowable.__init__(self)
        self.width  = width
        self.height = height

    def draw(self):
        c  = self.canv
        W  = self.width
        H  = self.height
        steps = [
            ('User Types\nQuestion',    H2_COLOR),
            ('Platform\nSearches Docs', ACCENT),
            ('AI Reads\nRelevant Parts', HexColor('#059669')),
            ('AI Writes\nthe Answer',    H1_COLOR),
            ('User Receives\nAnswer',   HexColor('#7C3AED')),
        ]
        n  = len(steps)
        bw = (W - (n - 1) * 20) / n
        bh = H - 6

        for i, (label, col) in enumerate(steps):
            x  = i * (bw + 20)
            lines = label.split('\n')
            c.setFillColor(col)
            c.setStrokeColor(HexColor('#E2E8F0'))
            c.setLineWidth(0.5)
            c.roundRect(x, 3, bw, bh, 5, fill=1, stroke=1)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 7.5)
            if len(lines) == 2:
                c.drawCentredString(x + bw / 2, 3 + bh / 2 + 4, lines[0])
                c.setFont('Helvetica', 7)
                c.setFillColor(HexColor('#E2E8F0'))
                c.drawCentredString(x + bw / 2, 3 + bh / 2 - 7, lines[1])
            else:
                c.drawCentredString(x + bw / 2, 3 + bh / 2 - 3, label)

            if i < n - 1:
                ax = x + bw + 2
                ay = 3 + bh / 2
                c.setFillColor(H2_COLOR)
                c.setStrokeColor(H2_COLOR)
                c.setLineWidth(1.5)
                c.line(ax, ay, ax + 15, ay)
                p = c.beginPath()
                p.moveTo(ax + 15, ay)
                p.lineTo(ax + 9, ay + 4)
                p.lineTo(ax + 9, ay - 4)
                p.close()
                c.drawPath(p, fill=1, stroke=0)


class IngestionFlowDiagram(Flowable):
    """Simple document ingestion flow."""
    def __init__(self, width, height=60):
        Flowable.__init__(self)
        self.width  = width
        self.height = height

    def draw(self):
        c  = self.canv
        W  = self.width
        H  = self.height
        steps = [
            ('Upload\nDocument',     ACCENT),
            ('Platform\nValidates',  H2_COLOR),
            ('AI Reads &\nProcesses',HexColor('#059669')),
            ('Saved to\nSearch Index',H1_COLOR),
            ('Ready for\nAI Queries', HexColor('#7C3AED')),
        ]
        n  = len(steps)
        bw = (W - (n - 1) * 20) / n
        bh = H - 6

        for i, (label, col) in enumerate(steps):
            x  = i * (bw + 20)
            lines = label.split('\n')
            c.setFillColor(col)
            c.setStrokeColor(HexColor('#E2E8F0'))
            c.setLineWidth(0.5)
            c.roundRect(x, 3, bw, bh, 5, fill=1, stroke=1)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 7.5)
            if len(lines) == 2:
                c.drawCentredString(x + bw / 2, 3 + bh / 2 + 4, lines[0])
                c.setFont('Helvetica', 7)
                c.setFillColor(HexColor('#E2E8F0'))
                c.drawCentredString(x + bw / 2, 3 + bh / 2 - 7, lines[1])
            else:
                c.drawCentredString(x + bw / 2, 3 + bh / 2 - 3, label)

            if i < n - 1:
                ax = x + bw + 2
                ay = 3 + bh / 2
                c.setFillColor(H2_COLOR)
                c.setStrokeColor(H2_COLOR)
                c.setLineWidth(1.5)
                c.line(ax, ay, ax + 15, ay)
                p = c.beginPath()
                p.moveTo(ax + 15, ay)
                p.lineTo(ax + 9, ay + 4)
                p.lineTo(ax + 9, ay - 4)
                p.close()
                c.drawPath(p, fill=1, stroke=0)


# ── Page callbacks ────────────────────────────────────────────────────────────

def on_cover(canvas_obj, doc):
    """Cover page background — no header bar."""
    canvas_obj.saveState()
    W, H = PAGE_W, PAGE_H

    # White background
    canvas_obj.setFillColor(WHITE)
    canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)

    # Orange top band
    canvas_obj.setFillColor(H1_COLOR)
    canvas_obj.rect(0, H - 90, W, 90, fill=1, stroke=0)

    # Navy bottom band
    canvas_obj.setFillColor(H2_COLOR)
    canvas_obj.rect(0, 0, W, 50, fill=1, stroke=0)

    # Small orange accent bar at bottom
    canvas_obj.setFillColor(H1_COLOR)
    canvas_obj.rect(0, 50, W, 4, fill=1, stroke=0)

    canvas_obj.restoreState()
    # Inner pages get header/footer
    if doc.page > 1:
        on_page(canvas_obj, doc)


def on_page(canvas_obj, doc):
    """Header and footer for all pages after cover."""
    if doc.page == 1:
        return
    canvas_obj.saveState()
    W = PAGE_W

    # Header
    canvas_obj.setFillColor(H2_COLOR)
    canvas_obj.rect(0, PAGE_H - 36, W, 36, fill=1, stroke=0)
    canvas_obj.setFillColor(H1_COLOR)
    canvas_obj.rect(0, PAGE_H - 38, W, 2, fill=1, stroke=0)

    # Header text
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont('Helvetica-Bold', 9)
    canvas_obj.drawString(18, PAGE_H - 22, 'Renata AI')
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(HexColor('#94A3B8'))
    canvas_obj.drawRightString(W - 18, PAGE_H - 22, 'DocuVault  |  Client Reference Guide')

    # Logo in header (small)
    if os.path.exists(LOGO_PATH):
        try:
            canvas_obj.drawImage(LOGO_PATH, 18, PAGE_H - 33, width=60, height=20,
                                 mask='auto', preserveAspectRatio=True)
        except Exception:
            pass

    # Footer
    canvas_obj.setFillColor(LIGHT_BG)
    canvas_obj.rect(0, 0, W, 30, fill=1, stroke=0)
    canvas_obj.setFillColor(H1_COLOR)
    canvas_obj.rect(0, 30, W, 1.5, fill=1, stroke=0)
    canvas_obj.setFillColor(MID_GRAY)
    canvas_obj.setFont('Helvetica', 7.5)
    canvas_obj.drawString(18, 10, f'Renata Envirocom Pvt. Ltd.  |  Confidential  |  {datetime.date.today().strftime("%B %Y")}')
    canvas_obj.drawRightString(W - 18, 10, f'Page {doc.page}')

    canvas_obj.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────

def get_styles():
    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        # Cover
        'cover_product': ps('cover_product',
            fontName='Helvetica-Bold', fontSize=32, textColor=WHITE,
            alignment=TA_LEFT, leading=38, spaceAfter=6),
        'cover_sub': ps('cover_sub',
            fontName='Helvetica', fontSize=16, textColor=HexColor('#FECACA'),
            alignment=TA_LEFT, leading=22, spaceAfter=4),
        'cover_tagline': ps('cover_tagline',
            fontName='Helvetica', fontSize=11, textColor=HexColor('#CBD5E1'),
            alignment=TA_LEFT, leading=16),
        'cover_footer': ps('cover_footer',
            fontName='Helvetica', fontSize=9, textColor=HexColor('#94A3B8'),
            alignment=TA_LEFT, leading=14),

        # Body headings
        'h1': ps('h1',
            fontName='Helvetica-Bold', fontSize=16, textColor=H1_COLOR,
            spaceBefore=18, spaceAfter=4, leading=20),
        'h2': ps('h2',
            fontName='Helvetica-Bold', fontSize=12, textColor=H2_COLOR,
            spaceBefore=14, spaceAfter=4, leading=16),
        'h3': ps('h3',
            fontName='Helvetica-Bold', fontSize=10.5, textColor=H3_COLOR,
            spaceBefore=10, spaceAfter=3, leading=14),

        # Body
        'body': ps('body',
            fontName='Helvetica', fontSize=9.5, textColor=BODY_TEXT,
            spaceAfter=6, leading=14, alignment=TA_JUSTIFY),
        'body_plain': ps('body_plain',
            fontName='Helvetica', fontSize=9.5, textColor=BODY_TEXT,
            spaceAfter=5, leading=14),
        'bullet': ps('bullet',
            fontName='Helvetica', fontSize=9.5, textColor=BODY_TEXT,
            spaceAfter=3, leading=13, leftIndent=16, bulletIndent=6),
        'bullet_sub': ps('bullet_sub',
            fontName='Helvetica', fontSize=9, textColor=MID_GRAY,
            spaceAfter=2, leading=12, leftIndent=30, bulletIndent=20),

        # Table
        'th': ps('th',
            fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, leading=12),
        'td': ps('td',
            fontName='Helvetica', fontSize=8.5, textColor=BODY_TEXT, leading=12),
        'td_bold': ps('td_bold',
            fontName='Helvetica-Bold', fontSize=8.5, textColor=H2_COLOR, leading=12),
        'td_url': ps('td_url',
            fontName='Helvetica-Bold', fontSize=8, textColor=ACCENT, leading=11),

        # Misc
        'caption': ps('caption',
            fontName='Helvetica-Oblique', fontSize=8, textColor=MID_GRAY,
            alignment=TA_CENTER, spaceAfter=6, leading=10),
        'note': ps('note',
            fontName='Helvetica-Oblique', fontSize=9, textColor=H3_COLOR,
            spaceAfter=4, leading=13),
        'toc': ps('toc',
            fontName='Helvetica', fontSize=10.5, textColor=H2_COLOR,
            spaceAfter=5, leading=15),
        'toc_sub': ps('toc_sub',
            fontName='Helvetica', fontSize=9.5, textColor=MID_GRAY,
            spaceAfter=3, leading=13, leftIndent=18),
    }


def bul(text, st, bold_part=''):
    if bold_part:
        text = f'<b>{bold_part}</b> {text}'
    return Paragraph(f'<bullet color="#E84C25">&#9679;</bullet> {text}', st['bullet'])


def note(text, st):
    return Paragraph(f'<i>Note: {text}</i>', st['note'])


def std_table(rows, st, col_widths, header_color=None):
    hcol = header_color or H2_COLOR
    data = []
    for i, row in enumerate(rows):
        if i == 0:
            data.append([Paragraph(str(c), st['th']) for c in row])
        else:
            data.append([Paragraph(str(c), st['td']) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',      (0, 0), (-1, 0),  hcol),
        ('ROWBACKGROUNDS',  (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ('GRID',            (0, 0), (-1, -1), 0.4, BORDER),
        ('VALIGN',          (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',      (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',   (0, 0), (-1, -1), 5),
        ('LEFTPADDING',     (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',    (0, 0), (-1, -1), 8),
    ]))
    return t


def info_box(paragraphs, fill=None, stroke=None):
    fill   = fill   or BLUE_PALE
    stroke = stroke or ACCENT
    data   = [[p] for p in paragraphs]
    t = Table(data, colWidths=[440])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), fill),
        ('BOX',           (0, 0), (-1, -1), 1, stroke),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    return t


# ── Cover ─────────────────────────────────────────────────────────────────────

def build_cover(elements, st):
    # Logo in orange header area
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=180, height=60)
        logo.hAlign = 'LEFT'
        elements.append(Spacer(1, 15))
        elements.append(logo)
    else:
        elements.append(Spacer(1, 40))
        elements.append(Paragraph('Renata AI', ParagraphStyle('lg',
            fontName='Helvetica-Bold', fontSize=28, textColor=WHITE, spaceAfter=4)))

    # White spacer to push below orange band
    elements.append(Spacer(1, 50))

    # Document title block
    elements.append(Paragraph('DocuVault', st['cover_product']))
    elements.append(Paragraph('Knowledge Management AI Platform', st['cover_sub']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph('Client Reference Guide', st['cover_tagline']))
    elements.append(Spacer(1, 10))
    elements.append(OrangeLine(200, 3, H1_COLOR))
    elements.append(Spacer(1, 14))

    # Meta block
    meta_rows = [
        ['Version',   'DocuVault v2.0'],
        ['Date',      datetime.date.today().strftime('%B %d, %Y')],
        ['Prepared by', 'Renata AI'],
        ['Classification', 'Confidential – Client Use Only'],
    ]
    meta_data = [[Paragraph(r[0], ParagraphStyle('mk', fontName='Helvetica-Bold',
                             fontSize=9, textColor=MID_GRAY, leading=13)),
                  Paragraph(r[1], ParagraphStyle('mv', fontName='Helvetica',
                             fontSize=9, textColor=BODY_TEXT, leading=13))]
                 for r in meta_rows]
    meta_t = Table(meta_data, colWidths=[110, 280])
    meta_t.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1),'TOP'),
        ('TOPPADDING',   (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
    ]))
    elements.append(meta_t)

    # Push to bottom for footer
    elements.append(Spacer(1, 14 * cm))

    # Cover bottom (navy band area text)
    elements.append(Paragraph('Renata Envirocom Pvt. Ltd.  |  renataiot.com', st['cover_footer']))
    elements.append(PageBreak())


# ── Table of Contents ─────────────────────────────────────────────────────────

def build_toc(elements, st):
    elements.append(Paragraph('Contents', st['h1']))
    elements.append(OrangeLine(440))
    elements.append(Spacer(1, 10))

    toc = [
        ('1.', 'System Overview',                   None),
        ('2.', 'Key Features', [
            ('2.1', 'Document Management'),
            ('2.2', 'AI Knowledge Assistant'),
            ('2.3', 'Users, Roles & Access Control'),
            ('2.4', 'Collaboration & Sharing'),
            ('2.5', 'Search & Organisation'),
            ('2.6', 'Audit Trail & Notifications'),
        ]),
        ('3.', 'Accessing System Features',         None),
        ('4.', 'Architecture Overview', [
            ('4.1', 'How the System is Structured'),
            ('4.2', 'How Documents are Indexed'),
            ('4.3', 'How the AI Answers Questions'),
        ]),
        ('5.', 'Technical Reference',               None),
        ('6.', 'Support & Contact',                 None),
    ]

    for num, title, subs in toc:
        elements.append(Paragraph(
            f'<b>{num}</b>&nbsp;&nbsp;{title}',
            st['toc']))
        if subs:
            for snum, stitle in subs:
                elements.append(Paragraph(
                    f'{snum}&nbsp;&nbsp;&nbsp;{stitle}',
                    st['toc_sub']))
    elements.append(PageBreak())


# ── 1. Overview ───────────────────────────────────────────────────────────────

def build_overview(elements, st):
    elements.append(Paragraph('1.  System Overview', st['h1']))
    elements.append(OrangeLine(440))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        'DocuVault is Renata AI\'s Knowledge Management Platform. It gives your organisation '
        'one place to store, organise, and query all your documents — using plain English, '
        'not search keywords.',
        st['body']))
    elements.append(Paragraph(
        'At its core is an AI assistant that reads your documents and answers questions '
        'instantly. No more hunting through folders or opening file after file.',
        st['body']))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph('What you can do with DocuVault', st['h2']))
    for item in [
        'Upload and organise your documents in one secure place.',
        'Control who can see each document — from fully public to private or role-restricted.',
        'Ask the AI assistant questions in plain English and get answers drawn from your own documents.',
        'Collaborate with your team through comments, shared links, and notifications.',
        'Track every action with a complete audit trail.',
        'Manage users and roles with fine-grained permission levels.',
    ]:
        elements.append(bul(item, st))

    elements.append(Spacer(1, 10))

    summary = [
        ['Item', 'Details'],
        ['Platform',             'DocuVault v2.0 — web-based, no installation required'],
        ['Supported File Types', 'PDF, Word, text files, images, and more'],
        ['Max File Size',        '100 MB per upload'],
        ['AI Knowledge Modes',   'Hybrid (default) · Strict (documents only) · Indicated'],
        ['Access Control',       'Public · Private · Role-Based · Custom (per user)'],
        ['Supported Devices',    'Any modern web browser on desktop, tablet, or mobile'],
    ]
    elements.append(std_table(summary, st, [160, 280]))
    elements.append(PageBreak())


# ── 2. Features ───────────────────────────────────────────────────────────────

def build_features(elements, st):
    elements.append(Paragraph('2.  Key Features', st['h1']))
    elements.append(OrangeLine(440))
    elements.append(Spacer(1, 8))

    # 2.1 Document Management
    elements.append(Paragraph('2.1  Document Management', st['h2']))
    elements.append(ThinLine())
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        'Everything you need to manage documents throughout their full lifecycle.',
        st['body_plain']))

    dm_rows = [
        ['Feature',           'What it does'],
        ['Upload',            'Add documents from your computer. Supported types include PDF, Word, images, and more.'],
        ['Access Control',    'Choose who can see each document: Public, Private, Role-Based, or shared with specific people.'],
        ['Version History',   'Every time a document is edited, the previous version is saved. You can view or restore any past version.'],
        ['Document Locking',  'Lock a document while you are editing so no one else can make changes at the same time.'],
        ['Categories & Tags', 'Organise documents into categories (with sub-categories) and tag them for flexible grouping.'],
        ['Metadata',          'Track view count, download count, file size, and upload date automatically.'],
        ['Soft Delete',       'Deleted documents can be recovered by an administrator before permanent removal.'],
    ]
    elements.append(std_table(dm_rows, st, [130, 310]))
    elements.append(Spacer(1, 14))

    # 2.2 AI Assistant
    elements.append(Paragraph('2.2  AI Knowledge Assistant', st['h2']))
    elements.append(ThinLine())
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        'The AI assistant lets you ask questions about your documents in plain English. '
        'It reads through all indexed documents, finds the most relevant parts, and writes a clear answer.',
        st['body_plain']))

    ai_rows = [
        ['Feature',                'What it does'],
        ['Ask in Plain English',   'Type a question naturally — the AI understands context, not just keywords.'],
        ['Answers from Your Docs', 'The AI only draws from documents stored in DocuVault, so answers are grounded in your data.'],
        ['Follow-up Questions',    'Ask follow-up questions in the same conversation. The AI remembers the context.'],
        ['Three Answer Modes',
            'Hybrid (default): Uses your documents first, fills gaps with general knowledge.\n'
            'Strict: Only answers from your documents — refuses if the answer is not in any document.\n'
            'Indicated: Clearly labels which parts come from your documents and which from general knowledge.'],
        ['Permission-Aware',       'The AI only uses documents the logged-in user is permitted to access.'],
        ['Source Transparency',    'Each answer shows which documents and pages were used, so you can verify the information.'],
    ]
    elements.append(std_table(ai_rows, st, [130, 310]))
    elements.append(Spacer(1, 14))

    # 2.3 Users & Roles
    elements.append(Paragraph('2.3  Users, Roles & Access Control', st['h2']))
    elements.append(ThinLine())
    elements.append(Spacer(1, 4))

    user_rows = [
        ['User Type',    'What they can do'],
        ['Guest',        'View documents that are set to Public only. Cannot upload or edit.'],
        ['Regular User', 'Upload and manage their own documents. Access documents based on their role level. Comment and collaborate.'],
        ['Admin',        'Full access to all documents, all users, and all system settings.'],
    ]
    elements.append(std_table(user_rows, st, [100, 340]))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        'Administrators can create custom roles (e.g. "Team Lead", "Department Head") and assign '
        'a numeric level to each. Documents set to Role-Based access are visible only to users '
        'whose role level meets or exceeds the requirement.',
        st['body_plain']))
    elements.append(Spacer(1, 14))

    # 2.4 Collaboration
    elements.append(Paragraph('2.4  Collaboration & Sharing', st['h2']))
    elements.append(ThinLine())
    elements.append(Spacer(1, 4))

    collab_rows = [
        ['Feature',         'What it does'],
        ['Comments',        'Add comments to any document. Replies are threaded for easy reading.'],
        ['Shared Links',    'Generate a link to share a document. Optionally add a password, set an expiry date, or limit how many times it can be opened.'],
        ['Direct Sharing',  'Share a document directly with specific registered users by selecting them from the system.'],
        ['Notifications',   'The system automatically alerts you when a document is shared with you, updated, or commented on.'],
        ['Favourites',      'Bookmark documents you use often for quick access from your sidebar.'],
    ]
    elements.append(std_table(collab_rows, st, [120, 320]))
    elements.append(Spacer(1, 14))

    # 2.5 Search
    elements.append(Paragraph('2.5  Search & Organisation', st['h2']))
    elements.append(ThinLine())
    elements.append(Spacer(1, 4))

    search_rows = [
        ['Feature',         'What it does'],
        ['Search Bar',      'Search by title, description, or content. Results rank the most relevant documents first.'],
        ['Filters',         'Narrow results by owner, date, access level, category, tags, or file type.'],
        ['Sorting',         'Sort by title, upload date, last updated, view count, or file size.'],
        ['Categories',      'Organise documents into a tree of categories. Each category can have a colour and icon.'],
        ['Tags',            'Add one or more tags to a document. Search and filter by tag across all categories.'],
    ]
    elements.append(std_table(search_rows, st, [110, 330]))
    elements.append(Spacer(1, 14))

    # 2.6 Audit
    elements.append(Paragraph('2.6  Audit Trail & Notifications', st['h2']))
    elements.append(ThinLine())
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        'Every action in DocuVault is automatically recorded. The activity log shows who did '
        'what, and when — making it easy to track changes for compliance and accountability.',
        st['body_plain']))

    audit_rows = [
        ['Recorded Action',      'When it appears in the log'],
        ['Upload / Create',      'A new document is added to the system.'],
        ['View / Download',      'A user opens or downloads a document.'],
        ['Edit / Update',        'A document or its details are changed.'],
        ['Delete',               'A document is removed (soft-deleted).'],
        ['Share',                'A document is shared via link or direct user share.'],
        ['Comment',              'A comment is added to a document.'],
        ['Permission Changed',   'A document\'s access level or user role is updated.'],
    ]
    elements.append(std_table(audit_rows, st, [150, 290]))
    elements.append(PageBreak())


# ── 3. Accessing Features ─────────────────────────────────────────────────────

def build_access(elements, st):
    elements.append(Paragraph('3.  Accessing System Features', st['h1']))
    elements.append(OrangeLine(440))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        'The table below shows how to navigate to each feature. All paths are relative to '
        'your system\'s base URL (e.g. https://yourdomain.com).',
        st['body_plain']))
    elements.append(Spacer(1, 8))

    def row(path, how):
        return [
            Paragraph(path, ParagraphStyle('rp', fontName='Helvetica-Bold',
                fontSize=8, textColor=ACCENT, leading=11)),
            Paragraph(how, st['td'])
        ]

    access_rows = [
        [Paragraph('URL Path', st['th']), Paragraph('How to access', st['th'])],
        row('/register/',
            'Open the system in your browser and click Register. Enter your name, email, and password.'),
        row('/login/',
            'Enter your username and password and click Sign In. You will be taken to your dashboard.'),
        row('/dashboard/',
            'Your home screen after login. Shows recent documents, unread notifications, and quick links.'),
        row('/documents/',
            'The full document library. Use the search bar at the top and the filter panel on the left to narrow results.'),
        row('/documents/create/',
            'Click + New Document from the document list or dashboard. Select a file, fill in the details, set access level, and click Save.'),
        row('/documents/<id>/',
            'Click any document title to open it. From here you can preview, download, comment, view version history, and share.'),
        row('/documents/<id>/edit/',
            'Open a document, then click Edit. Make your changes and save — the system automatically creates a new version.'),
        row('/documents/<id>/index/',
            'Open a document, then click Index for AI. The system reads and indexes the content so the AI assistant can answer questions about it.'),
        row('/documents/bulk-index/',
            'Admins only. From the document list, go to Actions → Bulk Index to index all unprocessed documents at once.'),
        row('/chatbot/',
            'Click AI Assistant in the sidebar. Type your question and press Enter. The assistant will search your documents and write an answer.'),
        row('/search/',
            'Use the search bar in the top navigation. Add filters using the panel below (date, owner, category, tags, access level).'),
        row('/categories/',
            'Navigate to Organise → Categories to create, nest, and colour-code categories.'),
        row('/favorites/',
            'Click the star icon on any document to bookmark it. Access your bookmarks via Favourites in the sidebar.'),
        row('/notifications/',
            'Click the bell icon in the top bar to see all notifications — shares, comments, and updates.'),
        row('/activity/',
            'Go to Account → Activity Log to view a complete history of all actions you and others have taken.'),
        row('/admin/users/',
            'Admins only. Go to Admin → Users to view all accounts and update role assignments.'),
        row('/admin/roles/',
            'Admins only. Go to Admin → Roles to create, edit, or remove custom roles and set their access levels.'),
        row('/profile/edit/',
            'Click your avatar (top right) → Edit Profile to update your name, photo, phone number, and department.'),
    ]

    t = Table(access_rows, colWidths=[140, 300], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0),  H2_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ('GRID',           (0, 0), (-1, -1), 0.4, BORDER),
        ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',     (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 6),
        ('LEFTPADDING',    (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)
    elements.append(PageBreak())


# ── 4. Architecture Overview ──────────────────────────────────────────────────

def build_architecture(elements, st):
    elements.append(Paragraph('4.  Architecture Overview', st['h1']))
    elements.append(OrangeLine(440))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        'This section gives a plain-English view of how DocuVault is structured — '
        'how it stores your documents, how the AI learns from them, and how it answers '
        'your questions.',
        st['body_plain']))
    elements.append(Spacer(1, 10))

    # 4.1
    elements.append(Paragraph('4.1  How the System is Structured', st['h2']))
    elements.append(ThinLine())
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        'DocuVault has three main layers that work together:',
        st['body_plain']))
    elements.append(Spacer(1, 4))

    layers = [
        ['Layer',             'What it is',                                    'What it does for you'],
        ['Your Browser',      'The web interface you open on any device.',      'Where you upload documents, search, chat with the AI, and manage settings.'],
        ['DocuVault Platform','The server application running in the background.','Handles your login, stores your documents securely, controls who can see what, and connects you to the AI.'],
        ['AI & Storage',      'The AI engine and databases behind the scenes.', 'Reads and indexes documents, answers your questions, and stores all data securely.'],
    ]
    elements.append(std_table(layers, st, [100, 140, 200]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('System Structure Diagram', st['h3']))
    elements.append(Spacer(1, 4))
    elements.append(SimpleArchDiagram(440, 275))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        'Figure 1: How your browser, the DocuVault platform, and the AI engine connect.',
        st['caption']))
    elements.append(PageBreak())

    # 4.2
    elements.append(Paragraph('4.2  How Documents are Indexed', st['h2']))
    elements.append(ThinLine())
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        'Before the AI can answer questions about a document, the document must be '
        '"indexed" — this means the AI reads it and saves a summary in a way it can '
        'search very quickly.',
        st['body_plain']))
    elements.append(Spacer(1, 8))

    elements.append(IngestionFlowDiagram(440, 68))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        'Figure 2: The five steps from uploading a document to it being ready for AI questions.',
        st['caption']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('Steps in plain English', st['h3']))
    indexing_steps = [
        ('Upload',          'You select a file and upload it. DocuVault saves it securely and checks that it is a valid file.'),
        ('Validate',        'The system checks the file size (must be under 100 MB) and the file type.'),
        ('AI Reads It',     'The platform reads the document — extracting all the text, tables, and if needed, running text recognition on scanned pages.'),
        ('Save to Index',   'The extracted content is broken into small sections and saved in the AI search index. This is what lets the AI find relevant parts instantly when you ask a question.'),
        ('Ready',           'The document is now available to the AI assistant. Any user who has permission to view the document can ask questions about it.'),
    ]
    for i, (title, desc) in enumerate(indexing_steps):
        elements.append(Paragraph(
            f'<b>Step {i+1} — {title}:</b> {desc}',
            st['body_plain']))
        elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 10))
    elements.append(info_box([
        Paragraph('<b>How to index a document</b>', ParagraphStyle('ib',
            fontName='Helvetica-Bold', fontSize=9.5, textColor=H2_COLOR, spaceAfter=4)),
        Paragraph(
            'Open any document, then click <b>Index for AI</b>. '
            'The status will update to "Indexed" once the process is complete. '
            'Admins can also index all documents at once using the Bulk Index option.',
            ParagraphStyle('ibb', fontName='Helvetica', fontSize=9.5,
                textColor=BODY_TEXT, leading=14)),
    ], BLUE_PALE, ACCENT))
    elements.append(PageBreak())

    # 4.3
    elements.append(Paragraph('4.3  How the AI Answers Questions', st['h2']))
    elements.append(ThinLine())
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        'When you type a question in the AI assistant, DocuVault goes through these steps '
        'to find and write the answer:',
        st['body_plain']))
    elements.append(Spacer(1, 8))

    elements.append(QueryFlowDiagram(440, 68))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        'Figure 3: How a question becomes an answer — from your input to the AI response.',
        st['caption']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('Steps in plain English', st['h3']))
    query_steps = [
        ('You type a question',
         'You ask the AI anything in plain English, for example: '
         '"What are the leave policy rules?" or "Summarise the maintenance report from March."'),
        ('Platform searches your documents',
         'DocuVault searches all indexed documents to find the sections most relevant to your question. '
         'It combines meaning-based search with keyword matching to get the best results.'),
        ('AI reads the relevant parts',
         'The AI reads the top matching sections from your documents. '
         'It only uses documents you have permission to access.'),
        ('AI writes the answer',
         'Using the content it found, the AI writes a clear, direct answer. '
         'The answer mode (Hybrid, Strict, or Indicated) controls whether it can also draw on general knowledge.'),
        ('You receive the answer',
         'The answer appears in the chat, along with the source documents and page numbers used. '
         'You can continue the conversation with follow-up questions.'),
    ]
    for i, (title, desc) in enumerate(query_steps):
        elements.append(Paragraph(
            f'<b>Step {i+1} — {title}:</b> {desc}',
            st['body_plain']))
        elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 10))

    elements.append(Paragraph('The three answer modes', st['h3']))
    mode_rows = [
        ['Mode',        'How it behaves',                                     'Best for'],
        ['Hybrid',      'Uses your documents first. If the documents do not fully cover the question, the AI uses its general training knowledge to fill gaps.', 'General use — recommended for most teams.'],
        ['Strict',      'Only answers from your documents. If the information is not in any document, the AI says so clearly.', 'Compliance, legal, or regulated content.'],
        ['Indicated',   'Uses both sources but clearly labels which parts of the answer come from your documents and which from general knowledge.', 'Research, auditing, or when traceability matters.'],
    ]
    elements.append(std_table(mode_rows, st, [65, 220, 155]))
    elements.append(PageBreak())


# ── 5. Technical Reference ────────────────────────────────────────────────────

def build_technical(elements, st):
    elements.append(Paragraph('5.  Technical Reference', st['h1']))
    elements.append(OrangeLine(440))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph('Technology Stack', st['h2']))
    stack_rows = [
        ['Category',         'Technology'],
        ['Web Framework',    'Django 5.x  (Python 3.10+)'],
        ['Database',         'SQLite (development) / PostgreSQL (production)'],
        ['AI Language Model','Groq API — llama-3.1-8b-instant'],
        ['AI Search Engine', 'ChromaDB vector database with all-MiniLM-L6-v2 embeddings'],
        ['Document Reading', 'pdfplumber, PyMuPDF, Camelot (tables), Tesseract (OCR for scanned pages)'],
        ['AI Framework',     'LangChain (orchestration), HuggingFace (embeddings), PyTorch'],
        ['Max File Upload',  '100 MB per file'],
        ['Search Method',    'Hybrid — 70% semantic similarity + 30% keyword matching'],
    ]
    elements.append(std_table(stack_rows, st, [160, 280]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph('AI Configuration', st['h2']))
    config_rows = [
        ['Setting',                    'Value'],
        ['Document chunk size',        '512 characters (256 in lightweight mode)'],
        ['Overlap between chunks',     '100 characters'],
        ['Results retrieved per query','8 chunks (6 in lightweight mode)'],
        ['Conversation memory',        'Up to 8 turns per session'],
        ['Max response length',        '512 tokens (~380 words)'],
        ['Response consistency',       'Low variability (temperature 0.2) for reliable, repeatable answers'],
    ]
    elements.append(std_table(config_rows, st, [200, 240]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph('User & Permission Model', st['h2']))
    perm_rows = [
        ['Access Level',    'Who can see the document'],
        ['Public',          'Everyone, including guests who are not logged in.'],
        ['Private',         'The document owner and admins only.'],
        ['Role-Based',      'Users whose role level is equal to or higher than the required level set by the owner.'],
        ['Custom',          'Only specific users selected by the document owner, plus admins.'],
    ]
    elements.append(std_table(perm_rows, st, [120, 320]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph('Key Database Records', st['h2']))
    db_rows = [
        ['Record Type',         'What it stores'],
        ['Document',            'The file, title, access level, category, tags, and owner.'],
        ['Document Version',    'A snapshot of the document every time it is edited.'],
        ['Chat Session',        'A conversation thread between a user and the AI assistant.'],
        ['Chat Message',        'Each individual question and AI answer, with source references.'],
        ['Activity Log',        'An immutable record of every action in the system.'],
        ['Notification',        'Alerts sent to users for shares, comments, and updates.'],
        ['Shared Link',         'A temporary link with optional password, expiry, and access count.'],
    ]
    elements.append(std_table(db_rows, st, [150, 290]))
    elements.append(PageBreak())


# ── 6. Support ────────────────────────────────────────────────────────────────

def build_support(elements, st):
    elements.append(Paragraph('6.  Support & Contact', st['h1']))
    elements.append(OrangeLine(440))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        'For assistance, feature requests, or any questions about DocuVault, '
        'please reach out through the following channels:',
        st['body_plain']))
    elements.append(Spacer(1, 10))

    contact_rows = [
        ['Channel',      'Details'],
        ['Website',      'https://renataiot.com'],
        ['Company',      'Renata Envirocom Pvt. Ltd.'],
        ['Product',      'DocuVault v2.0 — Knowledge Management AI Platform'],
        ['Document date', datetime.date.today().strftime('%B %Y')],
    ]
    elements.append(std_table(contact_rows, st, [110, 330]))
    elements.append(Spacer(1, 20))

    elements.append(info_box([
        Paragraph(
            '<b>Confidentiality Notice</b>',
            ParagraphStyle('cn', fontName='Helvetica-Bold', fontSize=10,
                           textColor=H2_COLOR, spaceAfter=5)),
        Paragraph(
            'This document is prepared exclusively for authorised DocuVault clients. '
            'The system details, configuration information, and architecture described here '
            'are proprietary to Renata Envirocom Pvt. Ltd. Please do not share or distribute '
            'without written consent.',
            ParagraphStyle('cnb', fontName='Helvetica', fontSize=9.5,
                           textColor=BODY_TEXT, leading=14)),
    ], ORANGE_PALE, H1_COLOR))


# ── Main ──────────────────────────────────────────────────────────────────────

def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.8 * cm,
        bottomMargin=2.0 * cm,
        title='DocuVault Client Reference Guide',
        author='Renata AI',
        subject='Knowledge Management AI Platform — Client Reference',
        creator='Renata AI Document Generator',
    )

    st = get_styles()
    elements = []

    build_cover(elements, st)
    build_toc(elements, st)
    build_overview(elements, st)
    build_features(elements, st)
    build_access(elements, st)
    build_architecture(elements, st)
    build_technical(elements, st)
    build_support(elements, st)

    doc.build(elements, onFirstPage=on_cover, onLaterPages=on_page)
    print('[OK] PDF generated: ' + output_path)


if __name__ == '__main__':
    build_pdf('DocuVault_Client_Reference_Guide.pdf')
