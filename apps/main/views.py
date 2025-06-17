from django.contrib.auth import authenticate, login as user_login, logout as user_logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import ProcessType, Organizations, Profiles, Positions, ProcessType_Order, DocumentTemplate, TemplateField, DocumentHistory, Document
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import localtime
from django.db.models import Q
from .create_template import *
from .create_document import *
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

@login_required
def work_view(request):
    user = Profiles.objects.get(user=request.user.id)
    return render(request, 'work/work.html', { 'user': user })

@login_required
def dashboard_view(request):
    user = Profiles.objects.get(user=request.user.id)
    return render(request, 'work/dashboard.html', { 'user': user })

@login_required
def profile_view(request):
    user = Profiles.objects.get(user=request.user.id)
    send_documents = len(Document.objects.filter(author=user))
    signed_documents = len(DocumentHistory.objects.filter(user=user))
    all_documents = send_documents + signed_documents

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'setting':
            last_name = request.POST.get('last_name')
            first_name = request.POST.get('first_name')
            middle_name = request.POST.get('middle_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            position = request.POST.get('position')

            user.last_name = last_name
            user.first_name = first_name
            user.middle_name = middle_name
            user.email = email 
            user.phone_number = phone_number
            posit = Positions.objects.get(name=user.position.name)
            posit.name = position
            posit.save()
            user.position = Positions.objects.get(name=user.position.name)
            user.save()
        elif action == 'security':
            us = User.objects.get(username=request.user)
            old_password = request.POST.get('old_password')

            if us.check_password(old_password):
                password = request.POST.get('password')
                password2 = request.POST.get('password2')
                if password == password2:
                    us.set_password(password)
                    us.save()


    return render(request, 'work/profile.html', { 
        'user':user,
        'send_documents': send_documents,
        'signed_documents': signed_documents,
        'all_documents': all_documents
    })

@require_http_methods(["GET", "POST"])
def documents_view(request):
    user = Profiles.objects.get(user=request.user.id)
    organization = user.organization

    process_type = ProcessType.objects.all()
    template_fields = TemplateField.objects.all()
    templates_list = []

    position = Positions.objects.filter(organization=organization)
    positions_list = []

    try:
        posit = Positions.objects.get(name=user.position.name)
        profile = Profiles.objects.get(position=posit)
        
        # Получаем ПЕРВЫЙ подходящий ProcessType_Order или None
        indocument_process = ProcessType_Order.objects.filter(profile=profile).first()
        
        # Если не найден, устанавливаем -1
        if indocument_process is None:
            indocument_process = -1
        
        # Фильтруем документы
        indocuments = Document.objects.filter( Q(order=indocument_process) | Q(recipient=user, status='approving'))

    except Positions.DoesNotExist:
        indocuments = Document.objects.filter(recipient=user, status='approving')
    except Profiles.DoesNotExist:
        indocuments = Document.objects.filter(recipient=user, status='approving')

    indocument_list = []

    outdocuments = Document.objects.filter(author=user, status='approving')
    outdocument_list = []

    approve_documents = Document.objects.filter(author=user, status__in=['approved', 'rejected'])
    approve_documents_list = []
   
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
            process = ProcessType_Order.objects.get(process_type=document.workflow, profile=user)
            
            if process.status == "Согласование":
                status = 'Согласованно'
            elif process.status == "Исполнение":
                status = 'Исполненно'
            elif process.status == "Регистрация":
                status = 'Зарегистрированно'
            elif process.status == "Ознакомление":   
                status = 'Ознакомлен' 

            DocumentHistory.objects.create(document=document, user=user, action=status, description=comment)

            if document.workflow:
                update_process_document(document)
            elif document.recipient:
                Document.objects.filter(id=document.id).update(order=None, status='approved')
        elif action == 'reject_document':
            approved_id = request.POST.get('approved_id')
            comment = request.POST.get('comment')
            document = Document.objects.get(id=approved_id)

            DocumentHistory.objects.create(document=document, user=user, action="Отказано", description=comment)
            Document.objects.filter(id=approved_id).update(order=None,status='rejected')
        elif action == 'cancel_document':
            id_document = request.POST.get('id_document')
            Document.objects.get(id=id_document).delete()

        return redirect('/documents')


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
        route_approve = []
        first = True
        reject = False
        documentHistory = DocumentHistory.objects.filter(document=value).order_by('created_at')
        data = ProcessType_Order.objects.filter(process_type=ProcessType.objects.get(name=value.workflow.name)) if value.workflow else range(1)

        for user_route in data:
            name = user_route.profile.position.name if value.workflow else value.recipient.position.name
            document_id = value.id
            action = ''
            description = ''
            created_at = ''
            
            if first and reject == False:
                action = 'В работе'
                first = False
            else:
                action = 'В ожидание'

            for history in documentHistory:
                if history.document.id == document_id and history.user.position.name == name:
                    action = history.action
                    description = history.description
                    created_at = localtime(history.created_at).strftime('%d.%m.%Y %H:%M')
                    first = True
                    if history.action == 'Отказано':
                        reject = True

            routeApprove_data = {
                'position': name,
                'name': user_route.profile.short_name() if value.workflow else value.recipient.short_name(),
                'document_id': document_id,
                'action': action,
                'process': user_route.get_status_display(),
                'description': description,
                'created_at': created_at
            }
            route_approve.append(routeApprove_data)

        indocument_data = {
            'id': value.id,
            'name': value.name,
            'author': value.author.position.name,
            'type': f'Шаблон: {value.workflow.template.name}' if value.workflow is not None else 'Личный документ',
            'created_at': localtime(value.created_at).strftime('%d.%m.%Y %H:%M'),
            'updated_at': localtime(value.updated_at).strftime('%d.%m.%Y %H:%M'),
            'status': value.get_status_display(),
            'comment': value.comment,
            'pdf': value.pdf.url if value.pdf.url else None,
            'history': route_approve
        }
        indocument_list.append(indocument_data)
    
    for value in outdocuments:
        route_approve = []
        first = True
        reject = False
        documentHistory = DocumentHistory.objects.filter(document=value).order_by('created_at')
        data = ProcessType_Order.objects.filter(process_type=ProcessType.objects.get(name=value.workflow.name)) if value.workflow else range(1)

        for user_route in data:
            name = user_route.profile.position.name if value.workflow else value.recipient.position.name
            document_id = value.id
            action = ''
            description = ''
            created_at = ''
            
            if first and reject == False:
                action = 'В работе'
                first = False
            else:
                action = 'В ожидание'

            for history in documentHistory:
                if history.document.id == document_id and history.user.position.name == name:
                    action = history.action
                    description = history.description
                    created_at = localtime(history.created_at).strftime('%d.%m.%Y %H:%M')
                    first = True
                    if history.action == 'Отказано':
                        reject = True

            routeApprove_data = {
                'position': name,
                'name': user_route.profile.short_name() if value.workflow else value.recipient.short_name(),
                'document_id': document_id,
                'action': action,
                'process': user_route.get_status_display(),
                'description': description,
                'created_at': created_at
            }
            route_approve.append(routeApprove_data)


        outdocument_data = {
            'id': value.id,
            'name': value.name,
            'author': value.author.position.name,
            'type': f'Шаблон: {value.workflow.template.name}' if value.workflow is not None else 'Личный документ',
            'created_at': localtime(value.created_at).strftime('%d.%m.%Y %H:%M'),
            'updated_at': localtime(value.updated_at).strftime('%d.%m.%Y %H:%M'),
            'status': value.get_status_display(),
            'comment': value.comment,
            'pdf': value.pdf.url if value.pdf.url else None,
            'history': route_approve
        }
        outdocument_list.append(outdocument_data)


    for value in approve_documents:
        route_approve = []
        first = True
        reject = False
        documentHistory = DocumentHistory.objects.filter(document=value).order_by('created_at')
        data = ProcessType_Order.objects.filter(process_type=ProcessType.objects.get(name=value.workflow.name)) if value.workflow else range(1)

        for user_route in data:
            name = user_route.profile.position.name if value.workflow else value.recipient.position.name
            document_id = value.id
            action = ''
            description = ''
            created_at = ''
            
            if first and reject == False:
                action = 'В работе'
                first = False
            else:
                action = 'В ожидание'

            for history in documentHistory:
                if history.document.id == document_id and history.user.position.name == name:
                    action = history.action
                    description = history.description
                    created_at = localtime(history.created_at).strftime('%d.%m.%Y %H:%M')
                    first = True
                    if history.action == 'Отказано':
                        reject = True

            routeApprove_data = {
                'position': name,
                'name': user_route.profile.short_name() if value.workflow else value.recipient.short_name(),
                'document_id': document_id,
                'action': action,
                'process': user_route.get_status_display(),
                'description': description,
                'created_at': created_at
            }
            route_approve.append(routeApprove_data)

        approve_document_data = {
            'id': value.id,
            'name': value.name,
            'author': value.author.position.name,
            'type': f'Шаблон: {value.workflow.template.name}' if value.workflow is not None else 'Личный документ',
            'created_at': localtime(value.created_at).strftime('%d.%m.%Y %H:%M'),
            'updated_at': localtime(value.updated_at).strftime('%d.%m.%Y %H:%M'),
            'status': value.get_status_display(),
            'comment': value.comment,
            'pdf': value.pdf.url if value.pdf.url else None,
            'history': route_approve
        }
        approve_documents_list.append(approve_document_data)

    templates_json = json.dumps(templates_list)
    indocument_json = json.dumps(indocument_list)
    outdocument_json = json.dumps(outdocument_list)
    approve_document_json = json.dumps(approve_documents_list)

    return render(request, 'work/documents.html', {
        'user': user,
        'templates': templates_list,
        'templates_json': templates_json,
        'positions_list': positions_list,
        'indocument_list': indocument_list,
        'indocument_json': indocument_json,
        'outdocument_list': outdocument_list,
        'outdocument_json': outdocument_json,
        'approve_documents_list': approve_documents_list,
        'approve_document_json': approve_document_json
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
    organizations = Organizations.objects.all()

    if request.method == 'POST':
        login = request.POST.get('login')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        organization = request.POST.get('organization')
        position = request.POST.get('position')

        if password == password2:
            us = User.objects.create_user(username=login, password=password)
            org = Organizations.objects.get(name=organization)
            posit = Positions.objects.create(name=position, organization=org)
            Profiles.objects.create(user=us, last_name=last_name, first_name=first_name, middle_name=middle_name, phone_number=phone_number, email=email, organization=org, position=posit)
            user = authenticate(request, username=login, password=password)
            if user is not None:
                user_login(request, user)
                return HttpResponse('')
            else:
                return render(request, 'auth/login.html')
    return render(request, 'auth/reg.html', { 'organizations': organizations })

@login_required
def setting_procces_type_view(request):
    user = Profiles.objects.get(user=request.user.id)
    if user.user.is_superuser:
        users_list = [users.name for users in Positions.objects.all()]
        doctemplate = DocumentTemplate.objects.all()
        doctemplate_list = [list.name for list in DocumentTemplate.objects.all()]
        process = ProcessType.objects.all()
        order_process = ProcessType_Order.objects.all()
        process_choice = [te for chek, te in ProcessType_Order.PROCESS_CHOICES]
        process_list = []

        for value in process:
            process_data = {
                'id': value.id,
                'name': value.name,
                'description': value.description,
                'template': value.template.name,
                'created_at': value.created_at,
                'users_approve': [
                    users.profile.position.name for users in order_process 
                    if users.process_type == value
                ],
                'users_comment': [
                    users.comment for users in order_process 
                    if users.process_type == value
                ],
                'process': [
                    process_order.get_status_display() for process_order in ProcessType_Order.objects.filter(process_type=value)
                ]
            }
            print(process_order.process for process_order in ProcessType_Order.objects.filter(process_type=value))
            process_list.append(process_data)  

        if request.method == 'POST':
            action = request.POST.get('action')
            organization = Profiles.objects.get(user=request.user.id).organization

            if action == 'create_process':
                name = request.POST.get('name')
                description = request.POST.get('description')
                template = DocumentTemplate.objects.get(name=request.POST.get('template'))
                list_user = request.POST.getlist('user')
                list_process = request.POST.getlist('process')
                comment = request.POST.getlist('comment')
                order = 0

                process_type = ProcessType.objects.create(name=name, description=description, template=template,count_position=len(list_user))
                for i in range(len(list_user)):
                    profile = Profiles.objects.get(position=Positions.objects.get(name=list_user[i]))
                    ProcessType_Order.objects.create(process_type=process_type, profile=profile, organization=organization, comment= comment[i], order=i, status=list_process[i])
            elif action == 'delete_process':
                deleteID = request.POST.get('deleteID')
                ProcessType.objects.get(id=deleteID).delete()
            elif action == 'edit_process':
                saveID = request.POST.get('saveID')
                name = request.POST.get('name')
                description = request.POST.get('description')
                template = DocumentTemplate.objects.get(name=request.POST.get('template'))
                list_user = request.POST.getlist('user')
                list_process = request.POST.getlist('process')
                comment = request.POST.getlist('comment')
                order = 0

                ProcessType.objects.get(id=saveID).delete()
                process_type = ProcessType.objects.create(name=name, description=description, template=template,count_position=len(list_user))
                
                for i in range(len(list_user)):
                    order = i + 1
                    position = Positions.objects.get(name=list_user[i])
                    ProcessType_Order.objects.create(process_type=process_type, position=position, organization=organization, comment= comment[i], order=order, status=list_process[i])

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
            'user': user,
            'users_list': users_list,
            'users_json': users_json,
            'process_list': process_list, 
            'process_json': process_json,
            'process_choice': process_choice,
            'doctemplate_list': doctemplate, 
            'doctemplate_json': doctemplate_json
        })
    else:
        return HttpResponse('')
        
@login_required
def setting_templates_view(request):
    user = Profiles.objects.get(user=request.user.id)
    if user.user.is_superuser:
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
            'user': user,
            'templates': templates_list,
            'templates_json': templates_json,
        })   
    else:
        return HttpResponse('')

@login_required
def logout_view(request):
    user_logout(request)
    return redirect('/')

def home(request):
    users = request.user
    return render(request, 'home/home.html', { 'users': users })

def setting_users(request):
    user = Profiles.objects.get(user=request.user.id)
    profiles = Profiles.objects.all()


    if request.method == "POST":
        accept = request.POST.get('accept')
        reject = request.POST.get('reject')

        if accept:
            obj = Profiles.objects.get(id=accept)
            obj.approve = True
            obj.save()
        elif reject:
            obj = Profiles.objects.get(id=reject)
            obj.approve = False
            obj.save()
        
        return redirect('/setting_users')

    return render(request, 'work/setting_users.html', { 'user': user, 'profiles': profiles })

@login_required
def download_file(request, pk):
    document = get_object_or_404(Document, pk=pk)
    
    if document.file:
        response = FileResponse(document.file.open(), as_attachment=True, filename=document.file.name)
        return response
    else:
        raise Http404("Файл не найден")