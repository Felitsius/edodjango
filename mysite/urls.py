from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.main.views import reg_view, login_view, logout_view
from apps.main.views import work_view, profile_view, documents_view, setting_procces_type_view, setting_templates_view, download_file, setting_users, dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.main.urls')),
    path('reg/', reg_view),
    path('login/', login_view),
    path('logout/', logout_view),
    path('work/', work_view),
    path('dashboard/', dashboard_view),
    path('profile/', profile_view),
    path('documents/', documents_view),
    path('setting_procces_type/', setting_procces_type_view),
    path('setting_templates/', setting_templates_view),
    path('setting_users/', setting_users),
    path('download/<int:pk>/', download_file, name='download_file'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
