#!/usr/bin/env python3
"""
generate_exports.py
Generate DOCX and PDF from the finalized manuscript Markdown.
Usage: python3 generate_exports.py
"""

import re
import sys
from pathlib import Path

MANUSCRIPT = Path('/home/dhuzard/Docs/Constraint Is Not a Limitation.md')
OUT_DIR    = Path('/home/dhuzard/Docs/export/manuscript')

# ─────────────────────────────────────────────────────────────────────────────
# Markdown → structured blocks
# ─────────────────────────────────────────────────────────────────────────────

def read_blocks(path):
    """Split the manuscript into structured blocks."""
    text = path.read_text(encoding='utf-8')
    raw_blocks = re.split(r'\n{2,}', text.strip())
    blocks = []
    for b in raw_blocks:
        b = b.strip()
        if not b or b == '---':
            continue
        if b.startswith('# '):
            blocks.append(('h1', clean_md_heading(b[2:])))
        elif b.startswith('## '):
            blocks.append(('h2', clean_md_heading(b[3:])))
        elif b.startswith('### '):
            blocks.append(('h3', clean_md_heading(b[4:])))
        elif b.startswith('**Authors:**'):
            blocks.append(('authors', b.replace('**Authors:**', '').strip()))
        else:
            blocks.append(('p', b))
    return blocks


def clean_md_heading(text):
    """Strip **bold** markers from heading text."""
    return re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', text)


def inline_parts(text):
    """
    Parse inline markdown into list of (str, bold, italic).
    Handles ***bi***, **bold**, *italic*, plain.
    """
    parts = []
    pattern = re.compile(
        r'(\*\*\*(.+?)\*\*\*'   # bold+italic
        r'|\*\*(.+?)\*\*'        # bold
        r'|\*(.+?)\*'            # italic
        r'|([^*\[]+)'            # plain
        r'|\[([^\]]+)\])'        # [citation] → keep as plain
    )
    for m in pattern.finditer(text):
        if m.group(2):
            parts.append((m.group(2), True, True))
        elif m.group(3):
            parts.append((m.group(3), True, False))
        elif m.group(4):
            parts.append((m.group(4), False, True))
        elif m.group(5):
            parts.append((m.group(5), False, False))
        elif m.group(6):
            parts.append((f'[{m.group(6)}]', False, False))
    return parts or [(text, False, False)]


# ─────────────────────────────────────────────────────────────────────────────
# DOCX
# ─────────────────────────────────────────────────────────────────────────────

def generate_docx(blocks, out_path):
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # --- page layout ---
    sec = doc.sections[0]
    sec.page_width  = Inches(8.5)
    sec.page_height = Inches(11)
    sec.left_margin = sec.right_margin = Inches(1)
    sec.top_margin  = sec.bottom_margin = Inches(1)

    # --- running head in header ---
    from docx.oxml.ns import qn
    header = sec.header
    hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    hp.clear()
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    hr = hp.add_run('CONSTRAINT IS NOT A LIMITATION')
    _style_run(hr, bold=False)

    # --- body style defaults ---
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(12)
    pf = normal.paragraph_format
    pf.line_spacing = Pt(24)
    pf.space_before = Pt(0)
    pf.space_after  = Pt(0)

    in_abstract       = False
    in_references     = False
    past_abstract     = False
    first_h2          = True
    page_break_before = False

    for kind, content in blocks:

        # Title page elements
        if kind == 'h1':
            _add_centered_bold(doc, content)
            continue

        if kind == 'authors':
            _add_centered(doc, content)
            _add_centered(doc, 'Independent Scholars')
            _add_centered(doc, 'Correspondence: damien@metadatapp.net')
            continue

        if kind == 'h2':
            heading_text = content.strip().strip('*')

            if 'Abstract' in heading_text:
                doc.add_page_break()
                _add_centered_bold(doc, 'Abstract')
                in_abstract = True
                continue

            if 'References' in heading_text:
                doc.add_page_break()
                _add_centered_bold(doc, 'References')
                in_references = True
                continue

            # First body section → page break from abstract
            if first_h2 and past_abstract:
                doc.add_page_break()
            first_h2 = False
            past_abstract = True
            in_abstract = False

            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _fmt_para(p, no_indent=True)
            r = p.add_run(heading_text)
            _style_run(r, bold=True)
            continue

        if kind == 'h3':
            heading_text = content.strip().strip('*')
            if 'Peer-reviewed' in heading_text or 'Industry' in heading_text:
                # Reference sub-headings: italic left
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                _fmt_para(p, no_indent=True)
                r = p.add_run(heading_text)
                _style_run(r, bold=True, italic=True)
            else:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                _fmt_para(p, no_indent=True)
                r = p.add_run(heading_text)
                _style_run(r, bold=True)
            continue

        if kind == 'p':
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if in_abstract:
                _fmt_para(p, no_indent=True)
            elif in_references:
                # hanging indent style
                p.paragraph_format.first_line_indent = Inches(-0.5)
                p.paragraph_format.left_indent        = Inches(0.5)
                p.paragraph_format.line_spacing = Pt(24)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after  = Pt(0)
            else:
                _fmt_para(p, no_indent=False)

            for txt, bold, italic in inline_parts(content):
                r = p.add_run(txt)
                _style_run(r, bold=bold, italic=italic)
            continue

    doc.save(str(out_path))
    print(f'  DOCX → {out_path}')


def _style_run(run, bold=False, italic=False):
    from docx.shared import Pt
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.bold   = bold
    run.italic = italic


def _fmt_para(p, no_indent=False):
    from docx.shared import Pt, Inches
    pf = p.paragraph_format
    pf.line_spacing = Pt(24)
    pf.space_before = Pt(0)
    pf.space_after  = Pt(0)
    if no_indent:
        pf.first_line_indent = Pt(0)
    else:
        pf.first_line_indent = Inches(0.5)


def _add_centered_bold(doc, text):
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _fmt_para(p, no_indent=True)
    r = p.add_run(text)
    _style_run(r, bold=True)
    return p


def _add_centered(doc, text):
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _fmt_para(p, no_indent=True)
    r = p.add_run(text)
    _style_run(r)
    return p


# ─────────────────────────────────────────────────────────────────────────────
# HTML → PDF via weasyprint
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
@page {
    size: letter;
    margin: 1in;
}
@page :right {
    @top-right {
        content: counter(page);
        font-family: "Times New Roman", serif;
        font-size: 12pt;
    }
}
body {
    font-family: "Times New Roman", serif;
    font-size: 12pt;
    line-height: 2;
    color: #000000;
    orphans: 3;
    widows: 3;
}
/* Title page */
.title-block {
    text-align: center;
    margin-top: 4in;
}
.title {
    font-weight: bold;
}
.authors {
    font-weight: normal;
}
.affiliation {
    font-weight: normal;
}
/* Abstract */
.abstract-heading {
    text-align: center;
    font-weight: bold;
    page-break-before: always;
}
.abstract-body p {
    text-indent: 0;
}
/* Section headings (Level 1) */
h2 {
    text-align: center;
    font-size: 12pt;
    font-weight: bold;
    page-break-before: always;
    margin-top: 0;
    margin-bottom: 0;
}
h2.no-break {
    page-break-before: avoid;
}
/* Subsection headings (Level 2) */
h3 {
    text-align: left;
    font-size: 12pt;
    font-weight: bold;
    font-style: normal;
    margin-top: 0;
    margin-bottom: 0;
}
h3.italic {
    font-style: italic;
}
/* Body paragraphs */
p {
    text-align: left;
    text-indent: 0.5in;
    margin: 0;
}
p.no-indent {
    text-indent: 0;
}
/* Reference list */
.references h2 {
    page-break-before: always;
}
.ref-entry {
    text-indent: -0.5in;
    margin-left: 0.5in;
    margin-top: 0;
    margin-bottom: 0;
}
"""


def md_to_html_body(blocks):
    """Convert parsed blocks to HTML body."""
    lines = []
    in_abstract     = False
    in_references   = False
    abstract_open   = False
    section_count   = 0

    for kind, content in blocks:
        if kind == 'h1':
            lines.append('<div class="title-block">')
            lines.append(f'<p class="title no-indent">{_html_inline(content)}</p>')
            continue

        if kind == 'authors':
            lines.append(f'<p class="authors no-indent">{_html_esc(content)}</p>')
            lines.append('<p class="affiliation no-indent">Independent Scholars</p>')
            lines.append('<p class="affiliation no-indent">Correspondence: damien@metadatapp.net</p>')
            lines.append('</div>')
            continue

        if kind == 'h2':
            heading_text = content.strip().strip('*')
            if 'Abstract' in heading_text:
                if abstract_open:
                    lines.append('</div>')
                lines.append(f'<h2 class="abstract-heading">{_html_esc(heading_text)}</h2>')
                lines.append('<div class="abstract-body">')
                in_abstract = True
                abstract_open = True
                continue

            if abstract_open:
                lines.append('</div>')
                abstract_open = False

            if 'References' in heading_text:
                lines.append('<div class="references">')
                lines.append(f'<h2>{_html_esc(heading_text)}</h2>')
                in_references = True
                in_abstract = False
                continue

            in_abstract = False
            section_count += 1
            cls = 'no-break' if section_count == 1 else ''
            lines.append(f'<h2 class="{cls}">{_html_esc(heading_text)}</h2>')
            continue

        if kind == 'h3':
            heading_text = content.strip().strip('*')
            if in_references and ('Peer-reviewed' in heading_text or 'Industry' in heading_text):
                lines.append(f'<h3 class="italic">{_html_esc(heading_text)}</h3>')
            else:
                lines.append(f'<h3>{_html_esc(heading_text)}</h3>')
            continue

        if kind == 'p':
            if in_references:
                lines.append(f'<p class="ref-entry">{_html_inline(content)}</p>')
            elif in_abstract:
                lines.append(f'<p class="no-indent">{_html_inline(content)}</p>')
            else:
                lines.append(f'<p>{_html_inline(content)}</p>')
            continue

    if abstract_open:
        lines.append('</div>')
    if in_references:
        lines.append('</div>')

    return '\n'.join(lines)


def _html_esc(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _html_inline(text):
    """Convert markdown inline formatting to HTML."""
    # Escape HTML special chars first
    text = _html_esc(text)
    # Bold+italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Escaped brackets (markdown source has \[ \])
    text = text.replace(r'\[', '[').replace(r'\]', ']')
    return text


def generate_pdf(blocks, out_path):
    import weasyprint

    body_html = md_to_html_body(blocks)
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Constraint Is Not a Limitation</title>
<style>{CSS}</style>
</head>
<body>
{body_html}
</body>
</html>"""

    # Write debug HTML too
    html_path = out_path.with_suffix('.html')
    html_path.write_text(full_html, encoding='utf-8')

    try:
        doc = weasyprint.HTML(string=full_html).write_pdf()
        out_path.write_bytes(doc)
        print(f'  PDF  → {out_path}')
    except Exception as e:
        print(f'  PDF generation error: {e}', file=sys.stderr)
        print(f'  HTML saved for manual inspection → {html_path}')


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Reading manuscript…')
    blocks = read_blocks(MANUSCRIPT)
    print(f'  Parsed {len(blocks)} blocks')

    docx_path = OUT_DIR / 'Constraint_Is_Not_a_Limitation.docx'
    pdf_path  = OUT_DIR / 'Constraint_Is_Not_a_Limitation.pdf'

    print('Generating DOCX…')
    generate_docx(blocks, docx_path)

    print('Generating PDF…')
    generate_pdf(blocks, pdf_path)

    print('Done.')
