from django.contrib import admin
from .models import (Organizations, Positions, ProcessType, Profiles, ProcessType_Order, 
                     Document, DocumentHistory, DocumentTemplate, TemplateField)

# Register your models here.
@admin.register(Organizations)
class OrganizationsAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'email', 'phone')

@admin.register(Positions)
class PositionsAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization')

@admin.register(ProcessType)
class ProcessTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'template','description', 'count_position', 'created_at')

@admin.register(ProcessType_Order)
class ProcessType_OrderAdmin(admin.ModelAdmin):
    list_display = ('organization','process_type', 'profile', 'order', 'status', 'comment')
    list_editable = ('order',)  # Позволяет редактировать порядок прямо в списке

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id','name','author', 'status', 'created_at', 'updated_at')
    readonly_fields = ('id',)

@admin.register(DocumentHistory)
class DocumentHistoryAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'action', 'description', 'created_at')

class TemplateFieldInline(admin.TabularInline):  # или admin.StackedInline для другого вида отображения
    model = TemplateField
    extra = 1  # Количество пустых форм для добавления новых полей

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    inlines = [TemplateFieldInline]

@admin.register(TemplateField)
class TemplateFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'template')
    list_filter = ('template',)

admin.site.register(Profiles)
