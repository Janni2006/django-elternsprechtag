from django.apps import AppConfig


class CustomBackupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "custom_backup"

    def ready(self):
        import custom_backup.signals
