# Generated by Django 5.2 on 2025-04-08 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_customuser_funcao_customuser_genero_customuser_idade_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='bilhete_identidade',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='nome_completo',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
