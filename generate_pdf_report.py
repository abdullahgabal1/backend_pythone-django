from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.units import inch
import re

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'backend_report.md'
OUTPUT = ROOT / 'backend_full_project_report.pdf'

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCentered', parent=styles['Title'], alignment=1, fontSize=22, leading=26, spaceAfter=20))
styles.add(ParagraphStyle(name='Section', parent=styles['Heading2'], fontSize=14, leading=18, spaceBefore=12, spaceAfter=8, textColor='#1f2937'))
styles.add(ParagraphStyle(name='SubSection', parent=styles['Heading3'], fontSize=11.5, leading=14, spaceBefore=8, spaceAfter=6, textColor='#374151'))
styles.add(ParagraphStyle(name='Body', parent=styles['BodyText'], fontSize=9.4, leading=13.5, spaceAfter=6))


def clean_md_text(line: str) -> str:
    line = line.replace('`', '')
    line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', line)
    return line.rstrip()


story = []
content = INPUT.read_text(encoding='utf-8')
lines = content.splitlines()

current_bullets = []
current_paragraph = []

def flush_paragraph():
    global current_paragraph
    if current_paragraph:
        text = ' '.join(clean_md_text(part) for part in current_paragraph if clean_md_text(part).strip())
        if text.strip():
            story.append(Paragraph(text, styles['Body']))
        current_paragraph = []


def flush_bullets():
    global current_bullets
    if current_bullets:
        story.append(ListFlowable([ListItem(Paragraph(item, styles['Body'])) for item in current_bullets], bulletType='bullet', leftIndent=20, bulletFontName='Helvetica', bulletFontSize=8))
        current_bullets = []

for raw in lines:
    line = raw.rstrip()
    if not line.strip():
        flush_paragraph()
        flush_bullets()
        continue

    if line.startswith('```'):
        flush_paragraph()
        flush_bullets()
        continue

    if line.startswith('# '):
        flush_paragraph()
        flush_bullets()
        story.append(Paragraph(clean_md_text(line[2:]), styles['TitleCentered']))
        story.append(Spacer(1, 6))
        continue

    if line.startswith('## '):
        flush_paragraph()
        flush_bullets()
        story.append(Paragraph(clean_md_text(line[3:]), styles['Section']))
        continue

    if line.startswith('### '):
        flush_paragraph()
        flush_bullets()
        story.append(Paragraph(clean_md_text(line[4:]), styles['SubSection']))
        continue

    if line.startswith('- '):
        flush_paragraph()
        current_bullets.append(clean_md_text(line[2:]))
        continue

    if line.startswith('* '):
        flush_paragraph()
        current_bullets.append(clean_md_text(line[2:]))
        continue

    if line.startswith('> '):
        flush_paragraph()
        story.append(Paragraph(clean_md_text(line[2:]), styles['Body']))
        continue

    current_paragraph.append(line)

flush_paragraph()
flush_bullets()

pdf = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
pdf.build(story)
print(f'PDF created: {OUTPUT}')
