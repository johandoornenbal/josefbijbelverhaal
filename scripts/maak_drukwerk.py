#!/usr/bin/env python3
"""Maak een A3-PDF en contactblad zonder de oorspronkelijke illustraties te wijzigen."""
from pathlib import Path
from io import BytesIO
import hashlib
import json

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'documentatie/platen.json').read_text())
OUT = ROOT / 'drukwerk'
OUT.mkdir(exist_ok=True)
PAGE = (420 * mm, 297 * mm)
pdf_path = OUT / 'jozef-vertelplaten-A3.pdf'
pdf = canvas.Canvas(str(pdf_path), pagesize=PAGE, pageCompression=1)
pdf.setTitle('Jozef — twaalf A3-kamishibai-vertelplaten')
pdf.setAuthor('johandoornenbal / josefbijbelverhaal')
pdf.setSubject('AI-gegenereerde illustraties bij Genesis 37–47; print op A3 liggend, 100%')
font_path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
try:
    font = ImageFont.truetype(str(font_path), 22)
except OSError:
    font = ImageFont.load_default(size=22)
contact = Image.new('RGB', (1500, 1640), '#f4eddf')
draw = ImageDraw.Draw(contact)
report = []
for index, plate in enumerate(DATA['platen']):
    file = ROOT / plate['bestand']
    with Image.open(file) as image:
        image.verify()
    with Image.open(file) as image:
        width, height = image.size
        assert width > height, f'Geen liggende plaat: {file}'
        assert abs(width / height - 420 / 297) < .01, f'Verkeerde verhouding: {file}'
        # Plaats de oorspronkelijke pixels op de juiste papiermaat; geen
        # verscherping, uitsnede, kleurcorrectie of kunstmatige opschaling.
        scale = min(PAGE[0] / width, PAGE[1] / height)
        w, h = width * scale, height * scale
        pdf.drawImage(str(file), (PAGE[0]-w)/2, (PAGE[1]-h)/2, w, h)
        pdf.showPage()
        # Alleen het overzicht krijgt kleine voorvertoningen en onderschriften.
        thumb = image.convert('RGB')
        thumb.thumbnail((460, 326), Image.Resampling.LANCZOS)
        col, row = index % 3, index // 3
        x, y = 20 + col * 500, 22 + row * 410
        contact.paste(thumb, (x + (460-thumb.width)//2, y))
        draw.text((x, y+338), f"{plate['nummer']:02}. {plate['titel']}", fill='#302c28', font=font)
        report.append({'nummer': plate['nummer'], 'bestand': plate['bestand'],
                       'pixels': [width, height], 'ppi_bij_A3': round(width/(420/25.4), 1),
                       'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
pdf.save()
contact.save(OUT / 'overzicht.jpg', quality=92, subsampling=0)
summary = canvas.Canvas(str(OUT / 'overzicht-A3.pdf'), pagesize=PAGE)
summary.setTitle('Jozef — overzicht van de twaalf vertelplaten')
buffer = BytesIO()
contact.save(buffer, format='JPEG', quality=92)
from reportlab.lib.utils import ImageReader
summary.drawImage(ImageReader(buffer), 5*mm, 5*mm, PAGE[0]-10*mm, PAGE[1]-10*mm, preserveAspectRatio=True, anchor='c')
summary.showPage()
summary.save()
reader = PdfReader(pdf_path)
assert len(reader.pages) == 12, 'Druk-PDF moet twaalf pagina’s bevatten'
for page in reader.pages:
    assert abs(float(page.mediabox.width)-PAGE[0]) < .02
    assert abs(float(page.mediabox.height)-PAGE[1]) < .02
    assert '/XObject' in page['/Resources'], 'Ontbrekende afbeelding in PDF'
(OUT / 'controle.json').write_text(json.dumps({'papier_mm':[420,297], 'pdf_paginas':len(reader.pages), 'platen':report}, ensure_ascii=False, indent=2)+'\n')
print(f'Gereed: {len(report)} PNG-platen gecontroleerd; 12 A3-pagina’s; overzicht JPG/PDF.')
print(f'Werkelijke bronresolutie: {report[0]["pixels"]}; circa {report[0]["ppi_bij_A3"]} ppi op A3.')
