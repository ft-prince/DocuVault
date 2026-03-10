"""
DocuVault Client Reference Guide — DOCX Generator
Theme: Renata IoT Reference Guide
Colors: H1=#E84C25, H2=#2C3E50, Accent=#4472C4
Logo: Logo.png
"""

import os, datetime
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

LOGO_PATH = r'D:\AI_Model_Renata\Document-management\Group\V2\DocuVault\Logo.png'

# ── Colors ────────────────────────────────────────────────────────────────────
H1_COLOR   = RGBColor(0xE8, 0x4C, 0x25)   # orange-red
H2_COLOR   = RGBColor(0x2C, 0x3E, 0x50)   # dark navy
H3_COLOR   = RGBColor(0x2E, 0x74, 0xB5)   # blue
ACCENT     = RGBColor(0x44, 0x72, 0xC4)   # primary blue
ORANGE     = RGBColor(0xED, 0x7D, 0x31)   # orange
NAVY       = RGBColor(0x44, 0x54, 0x6A)   # dark table header
MID_GRAY   = RGBColor(0x6B, 0x72, 0x80)
BODY_TEXT  = RGBColor(0x2C, 0x2C, 0x2C)
WHITE_RGB  = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG   = RGBColor(0xF8, 0xF9, 0xFA)
BORDER_COL = RGBColor(0xD1, 0xD5, 0xDB)

# ── Hex helpers ───────────────────────────────────────────────────────────────
def rgb_hex(r, g, b):
    return f'{r:02X}{g:02X}{b:02X}'

H1_HEX  = 'E84C25'
H2_HEX  = '2C3E50'
H3_HEX  = '2E74B5'
ACC_HEX = '4472C4'
NAV_HEX = '44546A'
WH_HEX  = 'FFFFFF'
LB_HEX  = 'F8F9FA'
BD_HEX  = 'D1D5DB'
OR_HEX  = 'FFF3ED'


# ── XML Helpers ───────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  hex_color)
    tcPr.append(shd)


def set_cell_border(cell, top=None, bottom=None, left=None, right=None):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    borders = OxmlElement('w:tcBorders')
    for side, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        if val:
            el = OxmlElement(f'w:{side}')
            el.set(qn('w:val'),   val.get('val', 'single'))
            el.set(qn('w:sz'),    val.get('sz', '4'))
            el.set(qn('w:space'), '0')
            el.set(qn('w:color'), val.get('color', 'auto'))
            borders.append(el)
    tcPr.append(borders)


def set_para_border_bottom(para, hex_color='E84C25', sz='12'):
    pPr  = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bot  = OxmlElement('w:bottom')
    bot.set(qn('w:val'),   'single')
    bot.set(qn('w:sz'),    sz)
    bot.set(qn('w:space'), '1')
    bot.set(qn('w:color'), hex_color)
    pBdr.append(bot)
    pPr.append(pBdr)


def set_para_shading(para, hex_fill, hex_color='auto'):
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), hex_color)
    shd.set(qn('w:fill'),  hex_fill)
    pPr.append(shd)


def set_run_highlight(run, hex_color):
    rPr = run._r.get_or_add_rPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  hex_color)
    rPr.append(shd)


def add_page_break(doc):
    doc.add_page_break()


def set_table_style(table):
    """Remove default table style borders, we set them manually."""
    tbl  = table._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    # Remove existing borders
    for b in tblPr.findall(qn('w:tblBorders')):
        tblPr.remove(b)
    borders = OxmlElement('w:tblBorders')
    for side in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:val'),   'single')
        el.set(qn('w:sz'),    '4')
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), BD_HEX)
        borders.append(el)
    tblPr.append(borders)


def set_col_widths(table, widths_cm):
    """Set column widths."""
    tbl = table._tbl
    tblGrid = tbl.find(qn('w:tblGrid'))
    if tblGrid is None:
        tblGrid = OxmlElement('w:tblGrid')
        tbl.insert(0, tblGrid)
    else:
        for col in tblGrid.findall(qn('w:gridCol')):
            tblGrid.remove(col)
    for w in widths_cm:
        gc = OxmlElement('w:gridCol')
        gc.set(qn('w:w'), str(int(w * 567)))   # 1 cm ≈ 567 twips
        tblGrid.append(gc)


# ── Document Setup ────────────────────────────────────────────────────────────

def setup_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width    = Cm(21)
    sec.page_height   = Cm(29.7)
    sec.left_margin   = Cm(2.2)
    sec.right_margin  = Cm(2.2)
    sec.top_margin    = Cm(2.5)
    sec.bottom_margin = Cm(2.0)

    # Default paragraph style
    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'
    normal.font.size = Pt(10)
    normal.font.color.rgb = BODY_TEXT

    return doc


# ── Style Helpers ─────────────────────────────────────────────────────────────

def add_h1(doc, text):
    """H1 — orange-red, 16pt bold, with orange bottom border."""
    p   = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold       = True
    run.font.size  = Pt(16)
    run.font.color.rgb = H1_COLOR
    run.font.name  = 'Calibri'
    set_para_border_bottom(p, H1_HEX, '12')
    return p


def add_h2(doc, text):
    """H2 — dark navy, 12pt bold."""
    p   = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold       = True
    run.font.size  = Pt(12)
    run.font.color.rgb = H2_COLOR
    run.font.name  = 'Calibri'
    return p


def add_h3(doc, text):
    """H3 — blue, 11pt bold."""
    p   = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(3)
    run = p.add_run(text)
    run.bold       = True
    run.font.size  = Pt(11)
    run.font.color.rgb = H3_COLOR
    run.font.name  = 'Calibri'
    return p


def add_body(doc, text, bold_prefix=''):
    """Normal body paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.space_before = Pt(0)
    if bold_prefix:
        r = p.add_run(bold_prefix + ' ')
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = BODY_TEXT
        r.font.name = 'Calibri'
    run = p.add_run(text)
    run.font.size  = Pt(10)
    run.font.color.rgb = BODY_TEXT
    run.font.name  = 'Calibri'
    return p


def add_bullet(doc, text, bold_prefix='', level=0):
    """Bullet point paragraph."""
    p   = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after  = Pt(3)
    p.paragraph_format.left_indent  = Cm(0.6 + level * 0.5)
    if bold_prefix:
        r = p.add_run(bold_prefix + ': ')
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = H2_COLOR
        r.font.name = 'Calibri'
    run = p.add_run(text)
    run.font.size  = Pt(10)
    run.font.color.rgb = BODY_TEXT
    run.font.name  = 'Calibri'
    return p


def add_note(doc, text):
    """Italic note paragraph with light blue background."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.left_indent  = Cm(0.3)
    p.paragraph_format.right_indent = Cm(0.3)
    set_para_shading(p, 'EFF6FF')
    run = p.add_run('Note: ' + text)
    run.italic     = True
    run.font.size  = Pt(9.5)
    run.font.color.rgb = H3_COLOR
    run.font.name  = 'Calibri'
    return p


def add_info_box(doc, title, body_text, fill_hex='EFF6FF'):
    """Shaded info box with bold title and body."""
    p1 = doc.add_paragraph()
    p1.paragraph_format.space_before = Pt(6)
    p1.paragraph_format.space_after  = Pt(2)
    p1.paragraph_format.left_indent  = Cm(0.3)
    set_para_shading(p1, fill_hex)
    r = p1.add_run(title)
    r.bold = True
    r.font.size = Pt(10)
    r.font.color.rgb = H2_COLOR
    r.font.name = 'Calibri'

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after  = Pt(8)
    p2.paragraph_format.left_indent  = Cm(0.3)
    p2.paragraph_format.right_indent = Cm(0.3)
    set_para_shading(p2, fill_hex)
    r2 = p2.add_run(body_text)
    r2.font.size = Pt(10)
    r2.font.color.rgb = BODY_TEXT
    r2.font.name = 'Calibri'


def add_spacer(doc, pts=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after  = Pt(pts)
    p.paragraph_format.space_before = Pt(0)


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(8.5)
    run.font.color.rgb = MID_GRAY
    run.font.name = 'Calibri'


# ── Table Builder ─────────────────────────────────────────────────────────────

def add_table(doc, rows, col_widths_cm, header_hex=None):
    """
    rows: list of lists of strings. rows[0] = header.
    col_widths_cm: list of column widths in cm.
    """
    hcol = header_hex or H2_HEX
    n_cols = len(rows[0])
    table  = doc.add_table(rows=len(rows), cols=n_cols)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    set_table_style(table)
    set_col_widths(table, col_widths_cm)

    for i, row_data in enumerate(rows):
        row = table.rows[i]
        row.height = Cm(0.75)
        for j, cell_text in enumerate(row_data):
            cell = row.cells[j]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(1)
            p.paragraph_format.left_indent  = Cm(0.15)

            # Handle multiline cell text
            lines = str(cell_text).split('\n')
            for li, line in enumerate(lines):
                if li > 0:
                    p.add_run('\n')
                run = p.add_run(line)
                run.font.name = 'Calibri'
                if i == 0:
                    run.bold = True
                    run.font.size  = Pt(9.5)
                    run.font.color.rgb = WHITE_RGB
                    set_cell_bg(cell, hcol)
                else:
                    run.font.size  = Pt(9)
                    run.font.color.rgb = BODY_TEXT
                    if i % 2 == 0:
                        set_cell_bg(cell, LB_HEX)
                    else:
                        set_cell_bg(cell, WH_HEX)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table


# ── Flow Diagram (text-based table) ──────────────────────────────────────────

def add_flow_diagram(doc, steps, colors_hex, label):
    """
    Render a horizontal flow as a single-row table with arrows.
    steps: list of (title, subtitle) tuples
    colors_hex: list of hex strings for each step box
    """
    n = len(steps)
    # Build a single-row table: step | arrow | step | arrow | ...
    n_cols = n * 2 - 1
    table  = doc.add_table(rows=1, cols=n_cols)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Remove all table borders
    tbl   = table._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    for b in tblPr.findall(qn('w:tblBorders')):
        tblPr.remove(b)
    bdr = OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:val'), 'none')
        bdr.append(el)
    tblPr.append(bdr)

    # Page width minus margins ≈ 16.6 cm
    avail  = 16.6
    bw     = (avail - (n - 1) * 0.8) / n
    row    = table.rows[0]
    row.height = Cm(1.3)

    for i, (title, sub) in enumerate(steps):
        ci   = i * 2
        cell = row.cells[ci]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        col  = colors_hex[i] if i < len(colors_hex) else ACC_HEX
        set_cell_bg(cell, col)

        # Remove cell borders
        tc   = cell._tc
        tcPr = tc.get_or_add_tcPr()
        cb   = OxmlElement('w:tcBorders')
        for side in ['top','left','bottom','right']:
            el = OxmlElement(f'w:{side}')
            el.set(qn('w:val'), 'none')
            cb.append(el)
        tcPr.append(cb)

        # Set cell width
        tcW = OxmlElement('w:tcW')
        tcW.set(qn('w:w'),    str(int(bw * 567)))
        tcW.set(qn('w:type'), 'dxa')
        tcPr.append(tcW)

        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after  = Pt(1)
        r1 = p.add_run(title)
        r1.bold = True
        r1.font.size = Pt(8)
        r1.font.color.rgb = WHITE_RGB
        r1.font.name = 'Calibri'
        if sub:
            r2 = p.add_run('\n' + sub)
            r2.font.size = Pt(7)
            r2.font.color.rgb = RGBColor(0xDB, 0xEA, 0xFE)
            r2.font.name = 'Calibri'

        # Arrow cell
        if i < n - 1:
            acell = row.cells[ci + 1]
            acell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_bg(acell, 'F8F9FA')

            atc   = acell._tc
            atcPr = atc.get_or_add_tcPr()
            acb   = OxmlElement('w:tcBorders')
            for side in ['top','left','bottom','right']:
                el = OxmlElement(f'w:{side}')
                el.set(qn('w:val'), 'none')
                acb.append(el)
            atcPr.append(acb)
            atcW = OxmlElement('w:tcW')
            atcW.set(qn('w:w'),    str(int(0.8 * 567)))
            atcW.set(qn('w:type'), 'dxa')
            atcPr.append(atcW)

            ap = acell.paragraphs[0]
            ap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            ar = ap.add_run('\u2192')    # →
            ar.font.size = Pt(14)
            ar.font.color.rgb = H2_COLOR
            ar.font.name = 'Calibri'

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    add_caption(doc, label)


# ── Arch diagram (text table) ─────────────────────────────────────────────────

def add_arch_table(doc):
    """Three-layer architecture as a formatted table."""
    data = [
        ['Layer',              'What it is',                                 'What it does for you'],
        ['Your Browser',       'The web interface — open on any device.',    'Where you upload, search, chat with AI, and manage settings.'],
        ['DocuVault Platform', 'The server application behind the scenes.',  'Handles login, stores documents, controls who sees what, and connects to AI.'],
        ['AI & Storage',       'The AI engine and databases.',               'Reads and indexes documents, answers questions, and stores all data securely.'],
    ]
    add_table(doc, data, [3.5, 5.5, 7.6], H2_HEX)


# ── Header / Footer ───────────────────────────────────────────────────────────

def add_header_footer(doc):
    section = doc.sections[0]

    # ── Header ──
    header = section.header
    header.is_linked_to_previous = False
    # Clear default content
    for p in header.paragraphs:
        for run in p.runs:
            run.text = ''

    htable = header.add_table(1, 2, Cm(16.6))
    htable.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Remove table borders
    htbl  = htable._tbl
    htblP = htbl.find(qn('w:tblPr'))
    if htblP is None:
        htblP = OxmlElement('w:tblPr')
        htbl.insert(0, htblP)
    hbdr = OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:val'), 'none')
        hbdr.append(el)
    htblP.append(hbdr)

    hrow  = htable.rows[0]
    hrow.height = Cm(0.9)

    # Left cell — logo
    lcell = hrow.cells[0]
    lcell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_bg(lcell, H2_HEX)
    lp = lcell.paragraphs[0]
    lp.paragraph_format.left_indent = Cm(0.2)
    if os.path.exists(LOGO_PATH):
        lrun = lp.add_run()
        lrun.add_picture(LOGO_PATH, width=Cm(3.5))
    else:
        lr = lp.add_run('Renata AI')
        lr.bold = True
        lr.font.size = Pt(11)
        lr.font.color.rgb = WHITE_RGB
        lr.font.name = 'Calibri'

    # Right cell — doc title
    rcell = hrow.cells[1]
    rcell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_bg(rcell, H2_HEX)
    rp = rcell.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rp.paragraph_format.right_indent = Cm(0.3)
    rr = rp.add_run('DocuVault  |  Client Reference Guide')
    rr.font.size = Pt(8.5)
    rr.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    rr.font.name = 'Calibri'

    # Orange accent line below header
    hp = header.add_paragraph()
    hp.paragraph_format.space_before = Pt(0)
    hp.paragraph_format.space_after  = Pt(0)
    set_para_border_bottom(hp, H1_HEX, '8')

    # ── Footer ──
    footer = section.footer
    footer.is_linked_to_previous = False
    for p in footer.paragraphs:
        for run in p.runs:
            run.text = ''

    fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    fp.clear()
    fp.paragraph_format.space_before = Pt(4)
    fp.paragraph_format.space_after  = Pt(0)
    set_para_border_bottom(fp, 'E2E8F0', '4')

    fl = fp.add_run(
        f'Renata Envirocom Pvt. Ltd.  |  Confidential  |  '
        f'{datetime.date.today().strftime("%B %Y")}')
    fl.font.size = Pt(8)
    fl.font.color.rgb = MID_GRAY
    fl.font.name = 'Calibri'

    # Page number (right side via tab)
    fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pr = fp.add_run('\t\tPage ')
    pr.font.size = Pt(8)
    pr.font.color.rgb = MID_GRAY
    pr.font.name = 'Calibri'

    # Insert PAGE field
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.text = 'PAGE'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run_el = OxmlElement('w:r')
    run_el.append(fldChar1)
    run_el.append(instrText)
    run_el.append(fldChar2)
    fp._p.append(run_el)

    # Tab stops for right-aligned page number
    pPr = fp._p.get_or_add_pPr()
    tabs = OxmlElement('w:tabs')
    tab = OxmlElement('w:tab')
    tab.set(qn('w:val'), 'right')
    tab.set(qn('w:pos'), '9350')
    tabs.append(tab)
    pPr.append(tabs)


# ── Cover Page ────────────────────────────────────────────────────────────────

def build_cover(doc):
    # Orange header block
    p_logo = doc.add_paragraph()
    p_logo.paragraph_format.space_before = Pt(0)
    p_logo.paragraph_format.space_after  = Pt(0)
    set_para_shading(p_logo, H1_HEX)
    if os.path.exists(LOGO_PATH):
        run = p_logo.add_run()
        run.add_picture(LOGO_PATH, width=Cm(7))
    else:
        r = p_logo.add_run('Renata AI')
        r.bold = True
        r.font.size = Pt(24)
        r.font.color.rgb = WHITE_RGB
        r.font.name = 'Calibri'

    # Orange tagline bar
    p_tag = doc.add_paragraph()
    p_tag.paragraph_format.space_before = Pt(0)
    p_tag.paragraph_format.space_after  = Pt(0)
    set_para_shading(p_tag, H1_HEX)
    rt = p_tag.add_run('IoT  ·  AI  ·  Automation')
    rt.font.size = Pt(10)
    rt.font.color.rgb = RGBColor(0xFE, 0xCA, 0xCA)
    rt.font.name = 'Calibri'

    # Spacer
    for _ in range(4):
        doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Title
    p1 = doc.add_paragraph()
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after  = Pt(6)
    r1 = p1.add_run('DocuVault')
    r1.bold = True
    r1.font.size = Pt(36)
    r1.font.color.rgb = H1_COLOR
    r1.font.name = 'Calibri'

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(4)
    r2 = p2.add_run('Knowledge Management AI Platform')
    r2.bold = True
    r2.font.size = Pt(16)
    r2.font.color.rgb = H2_COLOR
    r2.font.name = 'Calibri'

    p3 = doc.add_paragraph()
    p3.paragraph_format.space_after = Pt(16)
    r3 = p3.add_run('Client Reference Guide')
    r3.font.size = Pt(13)
    r3.font.color.rgb = MID_GRAY
    r3.font.name = 'Calibri'

    # Orange divider
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(20)
    set_para_border_bottom(p_div, H1_HEX, '16')

    # Meta table
    meta = [
        ['Version',         'DocuVault v2.0'],
        ['Date',            datetime.date.today().strftime('%B %d, %Y')],
        ['Prepared by',     'Renata AI'],
        ['Classification',  'Confidential – Client Use Only'],
    ]
    mt = doc.add_table(rows=len(meta), cols=2)
    mt.alignment = WD_TABLE_ALIGNMENT.LEFT
    set_col_widths(mt, [3.5, 10])
    tbl = mt._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    for b in tblPr.findall(qn('w:tblBorders')):
        tblPr.remove(b)
    bdr = OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:val'), 'none')
        bdr.append(el)
    tblPr.append(bdr)

    for row_data in meta:
        r_idx = meta.index(row_data)
        row   = mt.rows[r_idx]
        c0    = row.cells[0]
        c1    = row.cells[1]
        p0    = c0.paragraphs[0]
        p1    = c1.paragraphs[0]
        rl    = p0.add_run(row_data[0])
        rl.bold = True
        rl.font.size = Pt(9.5)
        rl.font.color.rgb = MID_GRAY
        rl.font.name = 'Calibri'
        rv = p1.add_run(row_data[1])
        rv.font.size = Pt(9.5)
        rv.font.color.rgb = BODY_TEXT
        rv.font.name = 'Calibri'
        for c in [c0, c1]:
            c.paragraphs[0].paragraph_format.space_before = Pt(3)
            c.paragraphs[0].paragraph_format.space_after  = Pt(3)

    # Footer area
    for _ in range(8):
        doc.add_paragraph().paragraph_format.space_after = Pt(14)

    p_co = doc.add_paragraph()
    r_co = p_co.add_run('Renata Envirocom Pvt. Ltd.  |  renataiot.com')
    r_co.font.size = Pt(9)
    r_co.font.color.rgb = MID_GRAY
    r_co.font.name = 'Calibri'

    doc.add_page_break()


# ── TOC ───────────────────────────────────────────────────────────────────────

def build_toc(doc):
    add_h1(doc, 'Contents')
    add_spacer(doc, 8)

    toc_items = [
        ('1.', 'System Overview', []),
        ('2.', 'Key Features', [
            ('2.1', 'Document Management'),
            ('2.2', 'AI Knowledge Assistant'),
            ('2.3', 'Users, Roles & Access Control'),
            ('2.4', 'Collaboration & Sharing'),
            ('2.5', 'Search & Organisation'),
            ('2.6', 'Audit Trail & Notifications'),
        ]),
        ('3.', 'Accessing System Features', []),
        ('4.', 'Architecture Overview', [
            ('4.1', 'How the System is Structured'),
            ('4.2', 'How Documents are Indexed'),
            ('4.3', 'How the AI Answers Questions'),
        ]),
        ('5.', 'Technical Reference', []),
        ('6.', 'Support & Contact', []),
    ]

    for num, title, subs in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_after  = Pt(4)
        p.paragraph_format.space_before = Pt(0)
        r = p.add_run(f'{num}   {title}')
        r.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = H2_COLOR
        r.font.name = 'Calibri'
        for snum, stitle in subs:
            sp = doc.add_paragraph()
            sp.paragraph_format.space_after  = Pt(2)
            sp.paragraph_format.left_indent  = Cm(0.8)
            sr = sp.add_run(f'{snum}   {stitle}')
            sr.font.size = Pt(10)
            sr.font.color.rgb = MID_GRAY
            sr.font.name = 'Calibri'

    doc.add_page_break()


# ── 1. Overview ───────────────────────────────────────────────────────────────

def build_overview(doc):
    add_h1(doc, '1.  System Overview')
    add_spacer(doc, 6)

    add_body(doc,
        'DocuVault is Renata AI\'s Knowledge Management Platform. It gives your organisation '
        'one place to store, organise, and query all your documents — using plain English, not search keywords.')
    add_body(doc,
        'At its core is an AI assistant that reads your documents and answers questions instantly. '
        'No more hunting through folders or opening file after file.')

    add_h2(doc, 'What you can do with DocuVault')
    bullets = [
        'Upload and organise your documents in one secure place.',
        'Control who can see each document — from fully public to private or role-restricted.',
        'Ask the AI assistant questions in plain English and get answers drawn from your own documents.',
        'Collaborate with your team through comments, shared links, and notifications.',
        'Track every action with a complete audit trail.',
        'Manage users and roles with fine-grained permission levels.',
    ]
    for b in bullets:
        add_bullet(doc, b)

    add_spacer(doc, 8)
    add_table(doc, [
        ['Item',               'Details'],
        ['Platform',           'DocuVault v2.0 — web-based, no installation required'],
        ['Supported Files',    'PDF, Word, text files, images, and more'],
        ['Max File Size',      '100 MB per upload'],
        ['AI Knowledge Modes', 'Hybrid (default)  ·  Strict (documents only)  ·  Indicated'],
        ['Access Control',     'Public  ·  Private  ·  Role-Based  ·  Custom (per user)'],
        ['Supported Devices',  'Any modern web browser on desktop, tablet, or mobile'],
    ], [5.0, 11.6])
    doc.add_page_break()


# ── 2. Features ───────────────────────────────────────────────────────────────

def build_features(doc):
    add_h1(doc, '2.  Key Features')
    add_spacer(doc, 6)

    # 2.1
    add_h2(doc, '2.1  Document Management')
    add_body(doc, 'Everything you need to manage documents throughout their full lifecycle.')
    add_table(doc, [
        ['Feature',           'What it does'],
        ['Upload',            'Add documents from your computer. Supported types include PDF, Word, images, and more.'],
        ['Access Control',    'Choose who can see each document: Public, Private, Role-Based, or shared with specific people.'],
        ['Version History',   'Every time a document is edited, the previous version is saved. You can view or restore any past version.'],
        ['Document Locking',  'Lock a document while editing so no one else can make changes at the same time.'],
        ['Categories & Tags', 'Organise documents into categories (with sub-categories) and tag them for flexible grouping.'],
        ['Metadata',          'Track view count, download count, file size, and upload date automatically.'],
        ['Soft Delete',       'Deleted documents can be recovered by an administrator before permanent removal.'],
    ], [4.0, 12.6])
    add_spacer(doc, 8)

    # 2.2
    add_h2(doc, '2.2  AI Knowledge Assistant')
    add_body(doc,
        'The AI assistant lets you ask questions about your documents in plain English. '
        'It reads through all indexed documents, finds the most relevant parts, and writes a clear answer.')
    add_table(doc, [
        ['Feature',                'What it does'],
        ['Ask in Plain English',   'Type a question naturally — the AI understands context, not just keywords.'],
        ['Answers from Your Docs', 'The AI draws from documents stored in DocuVault, so answers are grounded in your data.'],
        ['Follow-up Questions',    'Ask follow-up questions in the same conversation. The AI remembers context.'],
        ['Three Answer Modes',
            'Hybrid (default): Uses your documents first, fills gaps with general knowledge.\n'
            'Strict: Only answers from your documents — refuses if the answer is not in any document.\n'
            'Indicated: Labels which parts come from your documents and which from general knowledge.'],
        ['Permission-Aware',       'The AI only uses documents the logged-in user is allowed to access.'],
        ['Source Transparency',    'Each answer shows which documents and pages were used, so you can verify the information.'],
    ], [4.0, 12.6])
    add_spacer(doc, 8)

    # 2.3
    add_h2(doc, '2.3  Users, Roles & Access Control')
    add_table(doc, [
        ['User Type',    'What they can do'],
        ['Guest',        'View documents that are set to Public only. Cannot upload or edit.'],
        ['Regular User', 'Upload and manage their own documents. Access documents based on their role level. Comment and collaborate.'],
        ['Admin',        'Full access to all documents, all users, and all system settings.'],
    ], [3.5, 13.1])
    add_spacer(doc, 4)
    add_body(doc,
        'Administrators can create custom roles (e.g. "Team Lead", "Department Head") and assign a numeric level to each. '
        'Documents set to Role-Based access are visible only to users whose role level meets or exceeds the requirement.')
    add_spacer(doc, 8)

    # 2.4
    add_h2(doc, '2.4  Collaboration & Sharing')
    add_table(doc, [
        ['Feature',         'What it does'],
        ['Comments',        'Add comments to any document. Replies are threaded for easy reading.'],
        ['Shared Links',    'Generate a link to share a document. Optionally add a password, set an expiry date, or limit how many times it can be opened.'],
        ['Direct Sharing',  'Share a document directly with specific registered users.'],
        ['Notifications',   'The system automatically alerts you when a document is shared with you, updated, or commented on.'],
        ['Favourites',      'Bookmark documents you use often for quick access from your sidebar.'],
    ], [3.5, 13.1])
    add_spacer(doc, 8)

    # 2.5
    add_h2(doc, '2.5  Search & Organisation')
    add_table(doc, [
        ['Feature',    'What it does'],
        ['Search Bar', 'Search by title, description, or content. Results rank the most relevant documents first.'],
        ['Filters',    'Narrow results by owner, date, access level, category, tags, or file type.'],
        ['Sorting',    'Sort by title, upload date, last updated, view count, or file size.'],
        ['Categories', 'Organise documents into a tree of categories. Each category can have a colour and icon.'],
        ['Tags',       'Add one or more tags to a document. Search and filter by tag across all categories.'],
    ], [3.5, 13.1])
    add_spacer(doc, 8)

    # 2.6
    add_h2(doc, '2.6  Audit Trail & Notifications')
    add_body(doc,
        'Every action in DocuVault is automatically recorded. The activity log shows who did what, '
        'and when — making it easy to track changes for compliance and accountability.')
    add_table(doc, [
        ['Recorded Action',     'When it appears in the log'],
        ['Upload / Create',     'A new document is added to the system.'],
        ['View / Download',     'A user opens or downloads a document.'],
        ['Edit / Update',       'A document or its details are changed.'],
        ['Delete',              'A document is removed (soft-deleted).'],
        ['Share',               'A document is shared via link or direct user share.'],
        ['Comment',             'A comment is added to a document.'],
        ['Permission Changed',  'A document\'s access level or user role is updated.'],
    ], [4.5, 12.1])
    doc.add_page_break()


# ── 3. Accessing Features ─────────────────────────────────────────────────────

def build_access(doc):
    add_h1(doc, '3.  Accessing System Features')
    add_spacer(doc, 6)
    add_body(doc,
        'The table below shows how to navigate to each feature. '
        'All paths are relative to your system\'s base URL (e.g. https://yourdomain.com).')
    add_spacer(doc, 6)

    rows = [
        ['URL Path',                   'How to access'],
        ['/register/',                 'Open the system in your browser and click Register. Enter your name, email, and password.'],
        ['/login/',                    'Enter your username and password and click Sign In.'],
        ['/dashboard/',                'Your home screen after login. Shows recent documents, notifications, and quick links.'],
        ['/documents/',                'The full document library. Use the search bar and filter panel to narrow results.'],
        ['/documents/create/',         'Click + New Document. Select a file, fill in the details, set access level, and click Save.'],
        ['/documents/<id>/',           'Click any document title to open it — preview, download, comment, version history, and share.'],
        ['/documents/<id>/edit/',      'Open a document then click Edit. Save changes — the system automatically creates a new version.'],
        ['/documents/<id>/index/',     'Open a document then click Index for AI. The system reads and indexes the content for the AI assistant.'],
        ['/documents/bulk-index/',     'Admins only. From the document list, go to Actions → Bulk Index to index all unprocessed documents.'],
        ['/chatbot/',                  'Click AI Assistant in the sidebar. Type your question and press Enter.'],
        ['/search/',                   'Use the search bar in the top navigation. Add filters for date, owner, category, tags, and access level.'],
        ['/categories/',               'Navigate to Organise → Categories to create, nest, and colour-code categories.'],
        ['/favorites/',                'Click the star icon on any document. Access bookmarks via Favourites in the sidebar.'],
        ['/notifications/',            'Click the bell icon in the top bar to see all notifications.'],
        ['/activity/',                 'Go to Account → Activity Log for a complete history of all actions.'],
        ['/admin/users/',              'Admins only. Go to Admin → Users to view all accounts and update role assignments.'],
        ['/admin/roles/',              'Admins only. Go to Admin → Roles to create, edit, or remove custom roles.'],
        ['/profile/edit/',             'Click your avatar (top right) → Edit Profile to update your details.'],
    ]

    n_cols = 2
    table  = doc.add_table(rows=len(rows), cols=n_cols)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    set_table_style(table)
    set_col_widths(table, [4.5, 12.1])

    for i, row_data in enumerate(rows):
        row = table.rows[i]
        row.height = Cm(0.75)
        for j, cell_text in enumerate(row_data):
            cell = row.cells[j]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(1)
            p.paragraph_format.left_indent  = Cm(0.15)

            if i == 0:
                run = p.add_run(cell_text)
                run.bold = True
                run.font.size = Pt(9.5)
                run.font.color.rgb = WHITE_RGB
                run.font.name = 'Calibri'
                set_cell_bg(cell, H2_HEX)
            else:
                if j == 0:
                    run = p.add_run(cell_text)
                    run.bold = True
                    run.font.size = Pt(8.5)
                    run.font.color.rgb = ACCENT
                    run.font.name = 'Calibri'
                else:
                    run = p.add_run(cell_text)
                    run.font.size = Pt(9)
                    run.font.color.rgb = BODY_TEXT
                    run.font.name = 'Calibri'
                if i % 2 == 0:
                    set_cell_bg(cell, LB_HEX)
                else:
                    set_cell_bg(cell, WH_HEX)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    doc.add_page_break()


# ── 4. Architecture ───────────────────────────────────────────────────────────

def build_architecture(doc):
    add_h1(doc, '4.  Architecture Overview')
    add_spacer(doc, 6)
    add_body(doc,
        'This section gives a plain-English view of how DocuVault is structured — '
        'how it stores your documents, how the AI learns from them, and how it answers your questions.')
    add_spacer(doc, 8)

    # 4.1
    add_h2(doc, '4.1  How the System is Structured')
    add_body(doc, 'DocuVault has three main layers that work together:')
    add_spacer(doc, 4)
    add_table(doc, [
        ['Layer',              'What it is',                                  'What it does for you'],
        ['Your Browser',       'The web interface you open on any device.',   'Where you upload, search, chat with AI, and manage settings.'],
        ['DocuVault Platform', 'The server application in the background.',   'Handles login, stores documents securely, controls access, and connects you to AI.'],
        ['AI & Storage',       'The AI engine and databases.',                'Reads and indexes documents, answers questions, and stores all data.'],
    ], [3.5, 5.5, 7.6])
    add_spacer(doc, 6)

    add_h3(doc, 'System Flow')
    add_flow_diagram(doc,
        [('Your Browser', 'Any device'),
         ('DocuVault\nPlatform', 'Application'),
         ('Document\nStorage', 'Files & Data'),
         ('AI Search\nEngine', 'Find content'),
         ('AI Answer\nModel', 'Write response')],
        [H2_HEX, ACC_HEX, '1D4ED8', '059669', H1_HEX],
        'Figure 1: How the main components of DocuVault connect.')
    add_spacer(doc, 6)

    # 4.2
    add_h2(doc, '4.2  How Documents are Indexed')
    add_body(doc,
        'Before the AI can answer questions about a document, it must be "indexed" — '
        'this means the AI reads it and saves a summary in a way it can search very quickly.')
    add_spacer(doc, 6)

    add_flow_diagram(doc,
        [('Upload\nDocument', ''),
         ('Platform\nValidates', ''),
         ('AI Reads &\nProcesses', ''),
         ('Saved to\nSearch Index', ''),
         ('Ready for\nAI Queries', '')],
        [ACC_HEX, H2_HEX, '059669', H1_HEX, '7C3AED'],
        'Figure 2: The five steps from uploading a document to it being ready for AI questions.')
    add_spacer(doc, 6)

    add_h3(doc, 'Steps in plain English')
    steps = [
        ('Step 1 — Upload',         'You select a file and upload it. DocuVault saves it securely.'),
        ('Step 2 — Validate',       'The system checks the file size (must be under 100 MB) and file type.'),
        ('Step 3 — AI Reads It',    'The platform reads the document — extracting all text, tables, and if needed, running text recognition on scanned pages.'),
        ('Step 4 — Save to Index',  'The content is broken into sections and saved in the AI search index. This lets the AI find relevant parts instantly.'),
        ('Step 5 — Ready',          'The document is now available to the AI assistant for any permitted user.'),
    ]
    for title, desc in steps:
        add_body(doc, desc, title + ':')
        add_spacer(doc, 2)

    add_spacer(doc, 6)
    add_info_box(doc,
        'How to index a document',
        'Open any document, then click Index for AI. The status will update to "Indexed" once complete. '
        'Admins can also index all documents at once using the Bulk Index option.')
    add_spacer(doc, 8)

    # 4.3
    add_h2(doc, '4.3  How the AI Answers Questions')
    add_body(doc,
        'When you type a question in the AI assistant, DocuVault goes through these steps '
        'to find and write the answer:')
    add_spacer(doc, 6)

    add_flow_diagram(doc,
        [('User Types\nQuestion', ''),
         ('Platform\nSearches Docs', ''),
         ('AI Reads\nRelevant Parts', ''),
         ('AI Writes\nthe Answer', ''),
         ('User Receives\nAnswer', '')],
        [H2_HEX, ACC_HEX, '059669', H1_HEX, '7C3AED'],
        'Figure 3: How a question becomes an answer.')
    add_spacer(doc, 6)

    add_h3(doc, 'Steps in plain English')
    qsteps = [
        ('Step 1 — You type a question',
         'Ask anything in plain English, e.g. "What are the leave policy rules?"'),
        ('Step 2 — Platform searches your documents',
         'DocuVault searches all indexed documents to find the sections most relevant to your question.'),
        ('Step 3 — AI reads the relevant parts',
         'The AI reads the top matching sections. It only uses documents you have permission to access.'),
        ('Step 4 — AI writes the answer',
         'Using the content it found, the AI writes a clear, direct answer.'),
        ('Step 5 — You receive the answer',
         'The answer appears in the chat with the source documents and page numbers used. You can ask follow-up questions.'),
    ]
    for title, desc in qsteps:
        add_body(doc, desc, title + ':')
        add_spacer(doc, 2)

    add_spacer(doc, 8)
    add_h3(doc, 'The three answer modes')
    add_table(doc, [
        ['Mode',      'How it behaves',                                                         'Best for'],
        ['Hybrid',    'Uses your documents first. Fills gaps with general knowledge if needed.', 'General use — recommended for most teams.'],
        ['Strict',    'Only answers from your documents. Says so clearly if information is not found.', 'Compliance, legal, or regulated content.'],
        ['Indicated', 'Uses both sources but clearly labels which part comes from where.',        'Research, auditing, or when traceability matters.'],
    ], [2.5, 8.0, 6.1])
    doc.add_page_break()


# ── 5. Technical Reference ────────────────────────────────────────────────────

def build_technical(doc):
    add_h1(doc, '5.  Technical Reference')
    add_spacer(doc, 6)

    add_h2(doc, 'Technology Stack')
    add_table(doc, [
        ['Category',          'Technology'],
        ['Web Framework',     'Django 5.x  (Python 3.10+)'],
        ['Database',          'SQLite (development) / PostgreSQL (production)'],
        ['AI Language Model', 'Groq API — llama-3.1-8b-instant'],
        ['AI Search Engine',  'ChromaDB vector database with all-MiniLM-L6-v2 embeddings'],
        ['Document Reading',  'pdfplumber, PyMuPDF, Camelot (tables), Tesseract (OCR for scanned pages)'],
        ['AI Framework',      'LangChain, HuggingFace, PyTorch'],
        ['Max File Upload',   '100 MB per file'],
        ['Search Method',     'Hybrid — 70% semantic similarity + 30% keyword matching'],
    ], [5.0, 11.6])
    add_spacer(doc, 10)

    add_h2(doc, 'AI Configuration')
    add_table(doc, [
        ['Setting',                    'Value'],
        ['Document chunk size',        '512 characters (256 in lightweight mode)'],
        ['Overlap between chunks',     '100 characters'],
        ['Results per query',          '8 chunks (6 in lightweight mode)'],
        ['Conversation memory',        'Up to 8 turns per session'],
        ['Max response length',        '512 tokens (~380 words)'],
        ['Response consistency',       'Low variability — temperature 0.2 for reliable, repeatable answers'],
    ], [6.0, 10.6])
    add_spacer(doc, 10)

    add_h2(doc, 'User & Permission Model')
    add_table(doc, [
        ['Access Level', 'Who can see the document'],
        ['Public',       'Everyone, including guests who are not logged in.'],
        ['Private',      'The document owner and admins only.'],
        ['Role-Based',   'Users whose role level is equal to or higher than the required level set by the owner.'],
        ['Custom',       'Only specific users selected by the document owner, plus admins.'],
    ], [3.5, 13.1])
    add_spacer(doc, 10)

    add_h2(doc, 'Key Database Records')
    add_table(doc, [
        ['Record Type',        'What it stores'],
        ['Document',           'The file, title, access level, category, tags, and owner.'],
        ['Document Version',   'A snapshot of the document every time it is edited.'],
        ['Chat Session',       'A conversation thread between a user and the AI assistant.'],
        ['Chat Message',       'Each individual question and AI answer, with source references.'],
        ['Activity Log',       'An immutable record of every action in the system.'],
        ['Notification',       'Alerts sent to users for shares, comments, and updates.'],
        ['Shared Link',        'A temporary link with optional password, expiry, and access count.'],
    ], [4.5, 12.1])
    doc.add_page_break()


# ── 6. Support ────────────────────────────────────────────────────────────────

def build_support(doc):
    add_h1(doc, '6.  Support & Contact')
    add_spacer(doc, 8)

    add_body(doc,
        'For assistance, feature requests, or any questions about DocuVault, '
        'please reach out through the following channels:')
    add_spacer(doc, 8)

    add_table(doc, [
        ['Channel',        'Details'],
        ['Website',        'https://renataiot.com'],
        ['Company',        'Renata Envirocom Pvt. Ltd.'],
        ['Product',        'DocuVault v2.0 — Knowledge Management AI Platform'],
        ['Document date',  datetime.date.today().strftime('%B %Y')],
    ], [4.0, 12.6])
    add_spacer(doc, 16)

    add_info_box(doc,
        'Confidentiality Notice',
        'This document is prepared exclusively for authorised DocuVault clients. '
        'The system details and architecture described here are proprietary to Renata Envirocom Pvt. Ltd. '
        'Please do not share or distribute without written consent.',
        OR_HEX)


# ── Main ──────────────────────────────────────────────────────────────────────

def build_docx(output_path: str):
    doc = setup_document()
    add_header_footer(doc)

    build_cover(doc)
    build_toc(doc)
    build_overview(doc)
    build_features(doc)
    build_access(doc)
    build_architecture(doc)
    build_technical(doc)
    build_support(doc)

    doc.save(output_path)
    print('[OK] DOCX generated: ' + output_path)


if __name__ == '__main__':
    build_docx('DocuVault_Client_Reference_Guide.docx')
