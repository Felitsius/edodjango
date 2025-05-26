from .models import ProcessType, Organizations, Profiles, Positions, ProcessType_Order, DocumentTemplate, TemplateField
import re
from docx import Document

def create_template(name, description, organization, template_file):
    template = DocumentTemplate.objects.create(name=name, description=description, organization=organization,file=template_file)
    doc = Document(template.file.path)
    pattern = re.compile(r'\{\{(.*?)\}\}')  # Регулярное выражение для поиска {{...}}
    fields = []

    for paragraph in doc.paragraphs:
        matches = pattern.findall(paragraph.text)
        if matches:
            fields.extend(matches)

    for field in fields:
        TemplateField.objects.create(template=template, name=field)