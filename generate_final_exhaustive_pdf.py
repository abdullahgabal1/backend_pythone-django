from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem

ROOT = Path(r'D:\isa htb2a haga\backend_pythone django')
INPUT = ROOT / 'backend_final_exhaustive_report.md'
OUTPUT = ROOT / 'backend_final_exhaustive_report.pdf'

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCentered', parent=styles['Title'], alignment=1, fontSize=24, leading=28, spaceAfter=18, textColor='#111827'))
styles.add(ParagraphStyle(name='Section', parent=styles['Heading2'], fontSize=15, leading=18, spaceBefore=14, spaceAfter=8, textColor='#111827'))
styles.add(ParagraphStyle(name='SubSection', parent=styles['Heading3'], fontSize=11.5, leading=14, spaceBefore=10, spaceAfter=6, textColor='#1f2937'))
styles.add(ParagraphStyle(name='Body', parent=styles['BodyText'], fontSize=9.2, leading=13, spaceAfter=5))


def clean_text(value: str) -> str:
    return value.replace('`', '').replace('**', '').rstrip()

story = []
for raw in INPUT.read_text(encoding='utf-8').splitlines():
    line = raw.rstrip()
    if not line.strip():
        continue
    if line.startswith('# '):
        story.append(Paragraph(clean_text(line[2:]), styles['TitleCentered']))
        story.append(Spacer(1, 8))
    elif line.startswith('## '):
        story.append(Paragraph(clean_text(line[3:]), styles['Section']))
    elif line.startswith('### '):
        story.append(Paragraph(clean_text(line[4:]), styles['SubSection']))
    elif line.startswith('- '):
        story.append(ListFlowable([
            ListItem(Paragraph(clean_text(line[2:]), styles['Body']))
        ], bulletType='bullet', leftIndent=18, bulletFontName='Helvetica', bulletFontSize=8))
    else:
        story.append(Paragraph(clean_text(line), styles['Body']))

pdf = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=40, bottomMargin=40)
pdf.build(story)
print(f'PDF created: {OUTPUT}')
