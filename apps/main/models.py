from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
import os

class Organizations(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название организации')
    address = models.CharField(max_length=255, verbose_name='Юридический адрес')
    email = models.EmailField(verbose_name='Почта')
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Сначала сохраняем модель, чтобы получить ID (если это новое создание)
        super().save(*args, **kwargs)
        
        # Создаем папку с названием организации
        folder_name = f"{self.name}"  # Добавляем ID для уникальности
        folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)
        
        # Создаем папку, если она не существует
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Создана папка для организации: {folder_path}")

    def delete(self, *args, **kwargs):
        # Удаляем папку организации
        folder_name = f"{self.name}"
        folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)
        if os.path.exists(folder_path):
            import shutil
            shutil.rmtree(folder_path)
        
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'



class Positions(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название должности')
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, verbose_name='Организация')

    def get_name(self):
        return f'{self.name}'

    def __str__(self):
        return f'{self.name} ({self.organization.name})'

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'

def document_template_upload_to(instance, filename):
    # Создаем путь: 'organizations/<organization_name>/<filename>'
    return f'{instance.organization.name}/Шаблоны/{filename}'

class DocumentTemplate(models.Model):
    """
    Модель шаблона документа.
    """
    name = models.CharField(max_length=255,verbose_name="Название шаблона")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата события")
    file = models.FileField(upload_to=document_template_upload_to,verbose_name="Файл шаблона",blank=True,null=True)
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, verbose_name='Организация')

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.file:  # Если есть файл
            if os.path.isfile(self.file.path):  # Проверяем его существование
                os.remove(self.file.path)  # Удаляем файл
        super().delete(*args, **kwargs)  # Вызываем стандартный delete()

    class Meta:
        verbose_name = "Шаблон документа"
        verbose_name_plural = "Шаблоны документов"


class TemplateField(models.Model):
    """
    Модель поля шаблона документа.
    Позволяет добавлять динамические поля к шаблону.
    """
    template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE, related_name='fields', verbose_name="Шаблон")
    name = models.CharField(max_length=100, verbose_name="Название поля")

    def __str__(self):
        return f"{self.name} ({self.template.name})"

    class Meta:
        verbose_name = "Поле шаблона"
        verbose_name_plural = "Поля шаблонов"

class ProcessType(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название типа процесса')
    description = models.TextField(verbose_name='Описание', null=True)
    template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE, related_name='templated', verbose_name="Шаблон")
    count_position = models.PositiveIntegerField(verbose_name='Количество этапов согласования')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тип процесса'
        verbose_name_plural = 'Типы процессов'

class ProcessType_Order(models.Model):
    process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE, verbose_name='Тип процесса')
    position = models.ForeignKey(Positions, on_delete=models.CASCADE, verbose_name='Должность')
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, verbose_name='Организация') 
    comment = models.TextField(verbose_name='Комментарий', blank=True, null=True)
    order = models.PositiveIntegerField(verbose_name='Порядок согласования')

    def __str__(self):
        return f'{self.position.name}'

    class Meta:
        verbose_name = 'Порядок согласования'
        verbose_name_plural = 'Порядки согласования'
        ordering = ['order']

class Profiles(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    last_name = models.CharField('Фамилия', max_length=50)
    first_name = models.CharField('Имя', max_length=50)
    middle_name = models.CharField('Отчество', max_length=50, blank=True, null=True)

    # Поле для номера телефона с валидацией
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+79999999999'. Допускается до 15 цифр."
    )
    phone_number = models.CharField(
        'Номер телефона',
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    
    # Поле для электронной почты
    email = models.EmailField('Email', blank=True, null=True)
    
    # Поле для Telegram (может быть как username, так и номер)
    telegram = models.CharField(
        'Telegram',
        max_length=50,
        blank=True,
        null=True,
        help_text="Можно указать @username или номер телефона"
    )

    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, verbose_name='Организация')
    position = models.ForeignKey(Positions, on_delete=models.CASCADE, verbose_name='Должность')
    approve = models.BooleanField(default=False, verbose_name="Подтверждён")

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()
    
    def personal_files(self):
        return self.user.document_set.all()
    
    def delete(self, *args, **kwargs):
        print("DELETE")
        # Удаляем папку организации
        folder_name = f"{self.position.name}"
        folder_path = os.path.join(settings.MEDIA_ROOT, f'{self.organization.name}' ,folder_name)
        if os.path.exists(folder_path):
            import shutil
            shutil.rmtree(folder_path)
        
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} - {self.position}'
    

@receiver(pre_save, sender=Profiles)
def create_folder_on_approve(sender, instance, **kwargs):
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        if not old_instance.approve and instance.approve:
            # Создаем уникальное имя папки
            folder_name = f"{instance.position.name}"
            folder_path = os.path.join(settings.MEDIA_ROOT, f'{instance.organization.name}' ,folder_name)
            
            # Создаем папку, если ее нет
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                instance.folder_path = folder_path
    except sender.DoesNotExist:
        # Это новый объект, еще не сохраненный в БД
        if instance.approve:
            folder_name = f"{instance.position.name}"
            folder_path = os.path.join(settings.MEDIA_ROOT, f'{instance.organization.name}' ,folder_name)
            os.makedirs(folder_path, exist_ok=True)
            instance.folder_path = folder_path

class Document(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_IN_WORK = 'in_work'
    STATUS_APPROVING = 'approving'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_ARCHIVED = 'archived'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_IN_WORK, 'В работе'),
        (STATUS_APPROVING, 'На согласовании'),
        (STATUS_APPROVED, 'Утвержден'),
        (STATUS_REJECTED, 'Отклонен'),
        (STATUS_ARCHIVED, 'В архиве'),
    ]

    name = models.CharField(max_length=255, verbose_name='Название документа')
    author = models.ForeignKey(Profiles, on_delete=models.PROTECT, related_name='authored_documents', verbose_name="Автор документа")
    workflow = models.ForeignKey(ProcessType, on_delete=models.CASCADE, verbose_name='Тип процесса', blank=True, null=True)
    recipient = models.ForeignKey(Profiles, on_delete=models.PROTECT, verbose_name="Получатель документа (Не обязательно)", blank=True, null=True)
    order = models.ForeignKey(ProcessType_Order, on_delete=models.PROTECT, verbose_name="Этап", blank=True, null=True)
    comment = models.TextField(verbose_name='Описание', null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, verbose_name="Статус документа")
    file = models.FileField(upload_to='documents/%Y/%m/%d/', blank=True, null=True, verbose_name="Файл документа")

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name}"

    
class DocumentHistory(models.Model):
    """История изменений документа"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='history', verbose_name="Документ")
    user = models.ForeignKey(Profiles, on_delete=models.PROTECT, verbose_name="Пользователь")
    action = models.CharField(max_length=100, verbose_name="Действие")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата события")
    
    class Meta:
        verbose_name = "История документа"
        verbose_name_plural = "Истории документов"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.document} ({self.created_at})"
    
