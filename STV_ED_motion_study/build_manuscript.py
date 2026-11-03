from pathlib import Path
import json,re,shutil
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
root=Path(__file__).resolve().parents[1]
source=root/'STV_ED_motion_study/manuscript.md'
dest=root/'STV_ED_reproducible_pilot_bundle/rural_narrow_road_research/STV_ED_english_pilot_manuscript.docx'
doc=Document();sec=doc.sections[0]
sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
sec.top_margin=sec.bottom_margin=Inches(.75)
sec.left_margin=sec.right_margin=Inches(.8)
normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(10.5)
normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.08
for name,size in [('Title',19),('Heading 1',13),('Heading 2',11)]:
    s=doc.styles[name];s.font.name='Times New Roman';s.font.size=Pt(size);s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_before=Pt(10);s.paragraph_format.space_after=Pt(5)
lines=source.read_text(encoding='utf-8').splitlines();i=0
while i<len(lines):
    line=lines[i].strip();i+=1
    if not line:continue
    if line.startswith('# '):
        p=doc.add_paragraph(line[2:],'Title')
        borders=OxmlElement('w:pBdr');bottom=OxmlElement('w:bottom');bottom.set(qn('w:val'),'nil');borders.append(bottom);p._p.get_or_add_pPr().append(borders)
        for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(19)
        continue
    if line.startswith('## '):
        p=doc.add_heading(line[3:],1)
        if line[3:]=='References':p.paragraph_format.page_break_before=True
        continue
    if line.startswith('### '):doc.add_heading(line[4:],2);continue
    if line.startswith('|'):
        rows=[line]
        while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i].strip());i+=1
        rows=[r for r in rows if not re.match(r'^\|[\s|:-]+\|$',r)]
        data=[[c.strip() for c in r.strip('|').split('|')] for r in rows]
        table=doc.add_table(rows=0,cols=len(data[0]));table.style='Table Grid'
        for ri,row in enumerate(data):
            cells=table.add_row().cells
            for c,t in zip(cells,row):
                c.text=t
                for p in c.paragraphs:
                    p.paragraph_format.space_after=Pt(3)
                    if ri==0:p.paragraph_format.keep_with_next=True
                    for run in p.runs:run.font.size=Pt(8 if len(row)>4 else 9);run.bold=(ri==0)
            trpr=table.rows[-1]._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
            if ri==0:trpr.append(OxmlElement('w:tblHeader'))
        doc.add_paragraph();continue
    if line.startswith('EQ: '):
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        math=OxmlElement('m:oMath');r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=line[4:];r.append(t);math.append(r);p._p.append(math)
        continue
    if line.startswith('FIGURE: '):
        path,caption=line[8:].split(' | ',1);p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next=True
        pic=(source.parent/path).resolve();assert pic.is_file(),pic
        p.add_run().add_picture(str(pic),width=Inches(6.45))
        cap=doc.add_paragraph(caption);cap.paragraph_format.space_after=Pt(8)
        for r in cap.runs:r.font.size=Pt(9)
        continue
    p=doc.add_paragraph(line)
    if line.startswith('['):
        for r in p.runs:r.font.size=Pt(9)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
doc.core_properties.title='Temporal Admission and Execution Limits in Dynamic Narrow-Road Passage'
doc.core_properties.subject='Synthetic temporal admission and vehicle execution study'
doc.save(dest)
print(dest)
