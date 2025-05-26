from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from apps.main.views import reg_view, login_view, logout_view
from apps.main.views import work_view, profile_view, documents_view, setting_procces_type_view, setting_templates_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.main.urls')),
    path('reg/', reg_view),
    path('login/', login_view),
    path('logout/', logout_view),
    path('work/', work_view),
    path('profile/', profile_view),
    path('documents/', documents_view),
    path('setting_procces_type/', setting_procces_type_view),
    path('setting_templates/', setting_templates_view),
]
