import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profiles

@receiver(post_save, sender=Profiles)
def create_profile_dirs_on_approve(sender, instance, created, **kwargs):
    """
    Создает директории при подтверждении профиля (approve=True)
    или при изменении approve с False на True
    """
    if instance.approve:
        # Проверяем, было ли изменение approve с False на True
        if not created:  # если это не создание новой записи
            try:
                old_instance = Profiles.objects.get(pk=instance.pk)
                if not old_instance.approve:  # если approve изменился с False на True
                    instance.create_profile_directories()
                    print('CREATE DIR PROFILES')
            except Profiles.DoesNotExist:
                pass
        else:  # если это новая запись и сразу approve=True
            instance.create_profile_directories()