import logging
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


def save_md_as_pdf(markdown: str, output_path: str) -> str:
    """Convert markdown text into a formatted PDF.

    Args:
        markdown: The article text in markdown format.
        output_path: Full path (including filename) to write the PDF to.

    Returns:
        The output_path the PDF was written to.
    """
    logger.info("Converting markdown to PDF: %d words -> %s", len(markdown.split()), output_path)
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for line in markdown.split("\n"):
        if line.startswith("### "):
            story.append(Paragraph(_inline_format(line[4:]), styles["Heading3"]))
        elif line.startswith("## "):
            story.append(Paragraph(_inline_format(line[3:]), styles["Heading2"]))
        elif line.startswith("# "):
            story.append(Paragraph(_inline_format(line[2:]), styles["Heading1"]))
        elif line.startswith("```"):
            continue
        elif line.strip() == "":
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(_inline_format(line), styles["Normal"]))

    doc.build(story)
    logger.info("PDF conversion complete: %s", output_path)
    return output_path


def _inline_format(line: str) -> str:
    """Convert inline markdown (bold/italic/code) to ReportLab's markup,
    escaping raw XML-special characters first so stray <, >, & in the
    article text don't break Paragraph parsing."""
    line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
    line = re.sub(r"\*(.+?)\*", r"<i>\1</i>", line)
    line = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', line)
    return line