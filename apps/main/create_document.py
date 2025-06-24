from .models import DocumentTemplate, TemplateField, Document, ProcessType_Order
from docxtpl import DocxTemplate
from docx2pdf import convert
from pdf2image import convert_from_path
import os
import datetime
import subprocess

def convert_ppt_to_pdf_linux(ppt_path, pdf_path):
    libreoffice_path = '/var/lib/libreoffice'
    subprocess.run([libreoffice_path, '--headless', '--convert-to', 'pdf', ppt_path, '--outdir', os.path.dirname(pdf_path)])

def update_process_document(document):
    order = ProcessType_Order.objects.filter(process_type=document.workflow)
    current_order = document.order.order
    all_order = len(ProcessType_Order.objects.filter(process_type=document.workflow)) - 1
    if document.status == 'in_work':
        if current_order < all_order:
            Document.objects.filter(id=document.id).update(order=order[current_order + 1], status='in_work')
        else:
            Document.objects.filter(id=document.id).update(order=None, status='approved')


def create_document(title, author, organization, comment, file=None, template_name=None, field=None, workflow=None, recipient=None, process=None):
    if workflow is not None and recipient is None: 
        template = DocumentTemplate.objects.get(name=template_name)
        template_field = [field.name for field in TemplateField.objects.filter(template=DocumentTemplate.objects.get(name=template_name))]
        path_template = template.file
        save_path = organization + "/" + author.position.name + "/" + title + ' ' + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".docx"
        order = ProcessType_Order.objects.filter(process_type=workflow)
        doc = DocxTemplate(path_template)
        context = {}

        for index, value in enumerate(template_field):
            context[value] = field[index]

        doc.render(context)
        doc.save("media/" + save_path)

        temp_pdf = organization + "/" + author.position.name + "/" + title + ' ' + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"

        #convert("media/" + save_path, "media/" + temp_pdf)

        convert_ppt_to_pdf_linux("media/" + save_path, "media/" + temp_pdf)

        Document.objects.create(name=title, author=author, workflow=workflow, comment=comment, status='in_work', order=order[0], file=save_path, pdf=temp_pdf)
    else:
        temp_pdf = ''
        if os.path.splitext(str(file))[1] != ".pdf":
            #temp_pdf = organization + "/" + author.position.name + "/" + title + ' ' + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"
            #convert(file, "media/" + temp_pdf)
            #convert_ppt_to_pdf_linux(str(file), "media/" + temp_pdf)
            print('Попытка загрузить документ: ', file)
        elif os.path.splitext(str(file))[1] == ".pdf":
            temp_pdf = file
        Document.objects.create(name=title, author=author, recipient=recipient, comment=comment, status='in_work', file=file, pdf=temp_pdf, processRecipient=process)

