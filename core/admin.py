from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your models here.
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('role', 'nome_completo', 'bilhete_identidade', 'idade', 'genero', 'morada', 'funcao', 'photo'),
        }),
    )

    list_display = (
    'username', 'email', 'role', 'nome_completo', 'bilhete_identidade', 'idade', 'genero', 'funcao', 'is_staff')


admin.site.register(CustomUser, CustomUserAdmin)