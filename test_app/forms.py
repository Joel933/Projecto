from django import forms
from .models import Test, Question, Option, TestAssignment, TestResult
from core.models import CustomUser


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'duration_minutes', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'correct_option', 'points']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['label', 'text']


class QuestionWithOptionsForm(forms.ModelForm):
    option_a = forms.CharField(max_length=255, label='Opção A')
    option_b = forms.CharField(max_length=255, label='Opção B')
    option_c = forms.CharField(max_length=255, label='Opção C')
    option_d = forms.CharField(max_length=255, label='Opção D')

    class Meta:
        model = Question
        fields = ['text', 'correct_option', 'points']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }


class TestAssignmentForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role__in=['colaborador', 'canditato']),
        widget=forms.CheckboxSelectMultiple,
        label='Selecionar Usuários'
    )

    class Meta:
        model = TestAssignment
        fields = ['test', 'due_date', 'users']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        user_role = kwargs.pop('user_role', None)
        super().__init__(*args, **kwargs)

        if user_role == 'rh':
            self.fields['users'].queryset = CustomUser.objects.filter(
                role__in=['colaborador', 'canditato']
            )
        else:
            self.fields['users'].queryset = CustomUser.objects.none()


class FilterTestResultsForm(forms.Form):
    test = forms.ModelChoiceField(
        queryset=Test.objects.all(),
        required=False,
        empty_label="Todos os Testes"
    )
    user_type = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('colaborador', 'Colaboradores'),
            ('canditato', 'Candidatos')
        ],
        required=False
    )
    completed_only = forms.BooleanField(required=False, label="Apenas Concluídos")


class AnswerForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = []  # Empty as we'll dynamically add fields

    def __init__(self, *args, test=None, **kwargs):
        super().__init__(*args, **kwargs)

        if test:
            for i, question in enumerate(test.questions.all()):
                choices = [(option.label, f"{option.label}. {option.text}")
                           for option in question.options.all()]
                self.fields[f'question_{question.id}'] = forms.ChoiceField(
                    choices=choices,
                    label=f"{i + 1}. {question.text}",
                    widget=forms.RadioSelect
                )

class TestImportForm(forms.Form):
    file = forms.FileField(label='Arquivo CSV', help_text='Selecione um arquivo CSV contendo os testes.')