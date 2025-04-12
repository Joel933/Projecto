from django.contrib import admin
from .models import Test, Question, Option

# Register your models here.
class OptionInline(admin.TabularInline):
    model = Option
    extra = 2

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
    list_display = ['text', 'test', 'correct_option']

class TestAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ['title', 'created_by']
    search_fields = ['title']
    list_filter = ['created_by']

admin.site.register(Test, TestAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option)