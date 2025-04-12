from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('rh', 'RH'),
        ('colaborador', 'Colaborador'),
        ('canditato', 'Candidato')
    )
    GENDER_CHOICES = (
        ('masculino', 'Masculino'),
        ('feminino', 'Feminino')
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    nome_completo = models.CharField(max_length=255, null=True, blank=True)
    bilhete_identidade = models.CharField(max_length=100, null=True, blank=True)
    idade = models.PositiveIntegerField(null=True, blank=True)
    genero = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    morada = models.CharField(max_length=255, null=True, blank=True)
    funcao = models.CharField(max_length=100, null=True, blank=True)