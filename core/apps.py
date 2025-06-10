from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals  # Assicurati che i segnali siano registrati
        import core.cache_signals  # ✅ OTTIMIZZATO - Cache invalidation signals