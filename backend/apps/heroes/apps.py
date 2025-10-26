from django.apps import AppConfig

class HeroesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.heroes"          # <-- important
    verbose_name = "Heroes"