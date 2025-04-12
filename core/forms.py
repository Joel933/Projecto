from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'role',  'nome_completo', 'bilhete_identidade', 'idade', 'genero', 'morada', 'funcao','photo',
            'password1', 'password2'
        )

    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, label="Tipo de Usuário")
    genero = forms.ChoiceField(choices=CustomUser.GENDER_CHOICES, label="Gênero")