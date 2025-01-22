import os
import uuid
import tempfile
import docx

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph


def generate_file(text: str, fmt: str) -> str:
    tmp_dir = tempfile.gettempdir()
    unique_name = str(uuid.uuid4())

    if fmt == "pdf":
        font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
        file_path = os.path.join(tmp_dir, f"{unique_name}.pdf")
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        # Создаём объект "SimpleDocTemplate"
        doc = SimpleDocTemplate(file_path, pagesize=A4)

        # Берём пример стилей и настраиваем один для русского текста
        styles = getSampleStyleSheet()
        style_normal = styles["Normal"]
        style_normal.fontName = 'DejaVuSans'
        style_normal.fontSize = 14
        # leading = высота строки.
        style_normal.leading = 20
        # spaceBefore = отступ сверху перед абзацем.
        # spaceAfter  = отступ снизу после абзаца.
        style_normal.spaceBefore = 10
        style_normal.spaceAfter = 10

        # Формируем "story" (список элементов). Paragraph автоматически переносит строки
        story = [Paragraph(text, style_normal)]

        # Генерируем PDF
        doc.build(story)
        return file_path
    elif fmt == "docx":
        file_path = os.path.join(tmp_dir, f"{unique_name}.docx")
        doc = docx.Document()
        doc.add_paragraph(text)
        doc.save(file_path)
        return file_path
    else:
        file_path = os.path.join(tmp_dir, f"{unique_name}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        return file_path
