from .models import DocumentTemplate, TemplateField, Document, ProcessType_Order
from docxtpl import DocxTemplate

def update_process_document(document):
    order = ProcessType_Order.objects.filter(process_type=document.workflow)
    current_order = document.order.order
    all_order = len(ProcessType_Order.objects.filter(process_type=document.workflow)) - 1
    if document.status == 'approving':
        if current_order < all_order:
            Document.objects.filter(id=document.id).update(order=order[current_order + 1], status='approving')
        else:
            Document.objects.filter(id=document.id).update(order=None, status='approved')


def create_document(title, author, organization, comment, file=None, template_name=None, field=None, workflow=None, recipient=None):
    if workflow is not None and recipient is None: 
        template = DocumentTemplate.objects.get(name=template_name)
        template_field = [field.name for field in TemplateField.objects.filter(template=DocumentTemplate.objects.get(name=template_name))]
        path_template = template.file
        save_path = organization + "/" + author.position.name + "/" + title + ".docx"
        order = ProcessType_Order.objects.filter(process_type=workflow)
        doc = DocxTemplate(path_template)
        context = {}

        for index, value in enumerate(template_field):
            context[value] = field[index]

        doc.render(context)
        doc.save("media/" + save_path)

        document = Document.objects.create(name=title, author=author, workflow=workflow, comment=comment, status='approving', order=order[0], file=save_path)
    else:
        Document.objects.create(name=title, author=author, recipient=recipient, comment=comment, status='approving', file=file)

