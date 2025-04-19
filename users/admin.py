from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

# Register your models here.
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informazioni Personali', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permessi', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ("Ruolo & TeoCoin", {"fields": ("role", "teo_coins")}),
        ('Date importanti', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'role', 'teo_coins', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    
    # Aggiungi questo metodo per filtrare l'autocomplete
    def get_search_results(self, request, queryset, search_term):
        if 'autocomplete' in request.path:
            model_name = request.GET.get('model_name', '')
            field_name = request.GET.get('field_name', '')
            if model_name == 'course' and field_name == 'students':
                queryset = queryset.filter(role='student')
            elif model_name == 'course' and field_name == 'teacher':
                queryset = queryset.filter(role='teacher')
        return super().get_search_results(request, queryset, search_term)
    
admin.site.register(User, UserAdmin)