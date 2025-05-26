from django.contrib.auth import authenticate, login as user_login, logout as user_logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import ProcessType, Organizations, Profiles, Positions, ProcessType_Order, DocumentTemplate, TemplateField, DocumentHistory
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import localtime
from .create_template import *
from .create_document import *

@login_required
def work_view(request):
    user = request.user
    return render(request, 'work/work.html', { 'user':user })

@login_required
def profile_view(request):
    user = request.user
    return render(request, 'work/profile.html', { 'user':user })


@require_http_methods(["GET", "POST"])
def documents_view(request):
    user = Profiles.objects.get(user=request.user.id)
    organization = user.organization

    process_type = ProcessType.objects.all()
    template_fields = TemplateField.objects.all()
    templates_list = []

    position = Positions.objects.filter(organization=organization)
    positions_list = []
    
    indocuments = Document.objects.filter(order=ProcessType_Order.objects.get(position=Positions.objects.get(name=user.position.name)))
    indocument_list = []

    documentHistory_list = []

    for value in position:
        positions_list.append(value.name)  

    for value in process_type:
        template_data = {
            'id': value.id,
            'name': value.name,
            'field': [
                field.name for field in template_fields 
                if field.template.name == value.template.name
            ]
        }
        templates_list.append(template_data)  

    for value in indocuments:
        documentHistory = DocumentHistory.objects.filter(document=value).order_by('created_at')

        indocument_data = {
            'id': value.id,
            'name': value.workflow.template.name,
            'author': value.author.position.name,
            'type': f'Шаблон: {value.workflow.template.name}' if value.workflow is not None else 'Личный документ',
            'created_at': localtime(value.created_at).strftime('%d.%m.%Y %H:%M'),
            'updated_at': localtime(value.updated_at).strftime('%d.%m.%Y %H:%M'),
            'status': value.get_status_display(),
            'comment': value.comment,
            'order': value.order.position.name,
            'workflow_order': [value.position.name for value in ProcessType_Order.objects.filter(process_type=ProcessType.objects.get(name='Заявление на отпуск'))]
        }
        indocument_list.append(indocument_data)

        for history in documentHistory:
            documentHistory_data = {
                'document_id': value.id,
                'user': history.user.position.name,
                'action': history.action,
                'description': history.description,
                'created_at': localtime(history.created_at).strftime('%d.%m.%Y %H:%M')
            }
            documentHistory_list.append(documentHistory_data)  

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'template':
            name = request.POST.get('name')
            template = request.POST.get('template')
            field = request.POST.getlist('field')
            comment = request.POST.get('comment')
            workflow = ProcessType.objects.get(template=DocumentTemplate.objects.get(name=template))

            create_document(title=name, author=user, organization=organization.name,template_name=template, field=field, comment=comment, workflow=workflow)
        elif action == 'my_document':
            name = request.POST.get('name')
            recipient = Profiles.objects.get(position=Positions.objects.get(name=request.POST.get('user')))
            comment = request.POST.get('comment')
            file = request.FILES.get('file')

            create_document(title=name, author=user, organization=organization.name,comment=comment, recipient=recipient, file=file)
        elif action == 'approve_document':
            approved_id = request.POST.get('approved_id')
            comment = request.POST.get('comment')
            document = Document.objects.get(id=approved_id)
            #order = len(ProcessType_Order.objects.filter(process_type=ProcessType.objects.get(name="Заявление на отпуск")))

            print(approved_id)
            print(comment)
            #print(order)
            DocumentHistory.objects.create(document=document, user=user, action="Согласованно", description=comment)
            update_process_document(document)

        return redirect('/documents')

    templates_json = json.dumps(templates_list)
    indocument_json = json.dumps(indocument_list, cls=DjangoJSONEncoder)
    documentHistory_json = json.dumps(documentHistory_list, cls=DjangoJSONEncoder)
    
    return render(request, 'work/documents.html', {
        'templates': templates_list,
        'templates_json': templates_json,
        'positions_list': positions_list,
        'indocument_list': indocument_list,
        'indocument_json': indocument_json,
        'documentHistory_json': documentHistory_json
    })

def login_view(request):
    if request.method == 'POST':
        login = request.POST.get('login')
        password = request.POST.get('password')

        user = authenticate(request, username=login, password=password)
        if user is not None:
            user_login(request, user)
            return redirect('/')
        else:
            return render(request, 'auth/login.html')
        
    return render(request, 'auth/login.html')

def reg_view(request):
    if request.method == 'POST':
        login = request.POST.get('login')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password == password2:
            User.objects.create_user(username=login, password=password)

            user = authenticate(request, username=login, password=password)
            if user is not None:
                user_login(request, user)
                return HttpResponse('')
            else:
                return render(request, 'auth/login.html')
    return render(request, 'auth/reg.html')


def setting_procces_type_view(request):
    users_list = [users.name for users in Positions.objects.all()]
    doctemplate = DocumentTemplate.objects.all()
    doctemplate_list = [list.name for list in DocumentTemplate.objects.all()]
    process = ProcessType.objects.all()
    order_process = ProcessType_Order.objects.all()

    process_list = []

    for value in process:
        process_data = {
            'id': value.id,
            'name': value.name,
            'description': value.description,
            'template': value.template.name,
            'created_at': value.created_at,
            'users_approve': [
                users.position.name for users in order_process 
                if users.process_type == value
            ],
            'users_comment': [
                users.comment for users in order_process 
                if users.process_type == value
            ]
        }
        process_list.append(process_data)  

    if request.method == 'POST':
        action = request.POST.get('action')
        organization = Profiles.objects.get(user=request.user.id).organization

        if action == 'create_process':
            name = request.POST.get('name')
            description = request.POST.get('description')
            template = DocumentTemplate.objects.get(name=request.POST.get('template'))
            list_user = request.POST.getlist('user')
            comment = request.POST.getlist('comment')
            order = 0
            process_type = ProcessType.objects.create(name=name, description=description, template=template,count_position=len(list_user))
            for i in range(len(list_user)):
                position = Positions.objects.get(name=list_user[i])
                ProcessType_Order.objects.create(process_type=process_type, position=position, organization=organization, comment= comment[i], order=i)
        elif action == 'delete_process':
            deleteID = request.POST.get('deleteID')
            ProcessType.objects.get(id=deleteID).delete()
        elif action == 'edit_process':
            saveID = request.POST.get('saveID')
            name = request.POST.get('name')
            description = request.POST.get('description')
            template = DocumentTemplate.objects.get(name=request.POST.get('template'))
            list_user = request.POST.getlist('user')
            comment = request.POST.getlist('comment')
            order = 0

            ProcessType.objects.get(id=saveID).delete()
            process_type = ProcessType.objects.create(name=name, description=description, template=template,count_position=len(list_user))
            
            for i in range(len(list_user)):
                order = i + 1
                position = Positions.objects.get(name=list_user[i])
                ProcessType_Order.objects.create(process_type=process_type, position=position, organization=organization, comment= comment[i], order=order)

        return redirect('/setting_procces_type')
    
    if request.method == 'GET':
        action = request.GET.get('action')
        
        if action == "search":
            search_process = request.GET.get('search_process')
            process_list = list(
                filter(
                    lambda item: (
                        search_process.lower() in item["name"].lower() 
                        or search_process.lower() in item["description"].lower()
                    ),
                    process_list
                )
            )
        elif action == "filter":
            filter1 = request.GET.get('filter_name')
            if filter1 == "last_process":
                process_list = sorted(process_list, key=lambda x: x['created_at'], reverse=True)
    
    process_json = json.dumps(process_list, cls=DjangoJSONEncoder)
    users_json = json.dumps(users_list)
    doctemplate_json = json.dumps(doctemplate_list)

    return render(request, 'work/setting_procces_type.html',{
        'users_list': users_list,
        'users_json': users_json,
        'process_list': process_list, 
        'process_json': process_json,
        'doctemplate_list': doctemplate, 
        'doctemplate_json': doctemplate_json
     })
        

def setting_templates_view(request):
    user = Profiles.objects.get(user=request.user.id)
    organization = user.organization
    doctemplate_list = DocumentTemplate.objects.all()
    docfield_list = TemplateField.objects.all()
    templates_list = []

    for value in doctemplate_list:
        template_data = {
            'id': value.id,
            'name': value.name,
            'description': value.description,
            'file': str(value.file),
            'created_at': value.created_at,
            'field': [
                field.name for field in docfield_list 
                if field.template.name == value.name
            ]
        }
        templates_list.append(template_data)  

    if request.method == 'POST':
        action = request.POST.get('action')


        if action == 'create_template':
            name = request.POST.get('name')
            description = request.POST.get('description')
            template_file = request.FILES.get('template_file')

            create_template(name=name, description=description, organization=organization, template_file=template_file)
        elif action == 'delete_template':
            deleteID = request.POST.get('deleteID')
            DocumentTemplate.objects.get(id=deleteID).delete()
        elif action == 'edit_template':
            saveID = request.POST.get('saveID')
            name = request.POST.get('name')
            description = request.POST.get('description')
            template_file = request.FILES.get('template_file')
            fields = request.POST.getlist('field')
            old_template = DocumentTemplate.objects.get(id=saveID)
            
            if template_file is None:
                load_file = old_template.file
            else:
                load_file = template_file
        
            old_template.delete()
            
            doctemplate = DocumentTemplate.objects.create(name=name, description=description, organization=organization,file=load_file)

            for field in fields:
                TemplateField.objects.create(template=doctemplate, name=field)

        return redirect('/setting_templates')
    
    if request.method == 'GET':
        action = request.GET.get('action')
        
        if action == "search":
            search_template = request.GET.get('search_template')
            templates_list = list(
                filter(
                    lambda item: (
                        search_template.lower() in item["name"].lower() 
                        or search_template.lower() in item["description"].lower()
                    ),
                    templates_list
                )
            )
        elif action == "filter":
            filter1 = request.GET.get('filter_name')
            if filter1 == "last_templates":
                templates_list = sorted(templates_list, key=lambda x: x['created_at'], reverse=True)

        
    templates_json = json.dumps(templates_list, cls=DjangoJSONEncoder)

    return render(request, 'work/setting_templates.html', {
        'templates': templates_list,
        'templates_json': templates_json,
    })   

def logout_view(request):
    user_logout(request)
    return redirect('/')
    
def home(request):
    users = request.user
    return render(request, 'home/home.html', { 'users': users })

