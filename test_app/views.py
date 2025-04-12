from django.shortcuts import render, redirect, get_object_or_404
from core.models import CustomUser
import csv
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from .models import Test, Question, Option, TestAssignment, TestResult, Answer
from .forms import (
    TestForm, QuestionForm, QuestionWithOptionsForm, TestAssignmentForm,
    FilterTestResultsForm, AnswerForm,TestImportForm,
)

# Create your views here.

class RHRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'rh'


class TestListView(LoginRequiredMixin, ListView):
    model = Test
    template_name = 'test_list.html'
    context_object_name = 'tests'

    def get_queryset(self):
        if self.request.user.role == 'rh':
            return Test.objects.all().order_by('-created_at')
        else:
            # For collaborators and candidates, show only tests assigned to them
            return Test.objects.filter(
                assignments__user=self.request.user
            ).distinct().order_by('-created_at')


class TestDetailView(LoginRequiredMixin, DetailView):
    model = Test
    template_name = 'test_detail.html'
    context_object_name = 'test'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        test = self.get_object()

        if self.request.user.role == 'rh':
            # For RH, show all assignments for this test
            context['assignments'] = test.assignments.all()
        else:
            # For others, show only their assignment
            try:
                assignment = test.assignments.get(user=self.request.user)
                context['assignment'] = assignment

                # If the test has been started/completed
                try:
                    result = assignment.result
                    context['result'] = result
                except TestResult.DoesNotExist:
                    context['result'] = None
            except TestAssignment.DoesNotExist:
                context['assignment'] = None

        return context


class TestCreateView(RHRequiredMixin, CreateView):
    model = Test
    form_class = TestForm
    template_name = 'test_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Teste criado com sucesso.")
        return reverse('test_detail', kwargs={'pk': self.object.pk})


class TestUpdateView(RHRequiredMixin, UpdateView):
    model = Test
    form_class = TestForm
    template_name = 'test_form.html'

    def get_success_url(self):
        messages.success(self.request, "Teste atualizado com sucesso.")
        return reverse('test_detail', kwargs={'pk': self.object.pk})


class TestDeleteView(RHRequiredMixin, DeleteView):
    model = Test
    template_name = 'test_confirm_delete.html'
    success_url = reverse_lazy('test_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Teste excluído com sucesso.")
        return super().delete(request, *args, **kwargs)


class QuestionCreateView(RHRequiredMixin, CreateView):
    model = Question
    form_class = QuestionWithOptionsForm
    template_name = 'question_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.test = get_object_or_404(Test, pk=self.kwargs['test_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test'] = self.test
        return context

    def form_valid(self, form):
        with transaction.atomic():
            question = form.save(commit=False)
            question.test = self.test
            question.save()

            # Create options
            Option.objects.create(
                question=question, label='A', text=form.cleaned_data['option_a']
            )
            Option.objects.create(
                question=question, label='B', text=form.cleaned_data['option_b']
            )
            Option.objects.create(
                question=question, label='C', text=form.cleaned_data['option_c']
            )
            Option.objects.create(
                question=question, label='D', text=form.cleaned_data['option_d']
            )

        messages.success(self.request, "Questão adicionada com sucesso.")
        return redirect('test_detail', pk=self.test.pk)


class QuestionUpdateView(RHRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionWithOptionsForm
    template_name = 'question_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test'] = self.object.test
        return context

    def get_initial(self):
        initial = super().get_initial()
        question = self.get_object()
        options = question.options.all()

        if options.count() >= 4:
            initial['option_a'] = options.get(label='A').text
            initial['option_b'] = options.get(label='B').text
            initial['option_c'] = options.get(label='C').text
            initial['option_d'] = options.get(label='D').text

        return initial

    def form_valid(self, form):
        with transaction.atomic():
            question = form.save()

            # Update options
            question.options.filter(label='A').update(text=form.cleaned_data['option_a'])
            question.options.filter(label='B').update(text=form.cleaned_data['option_b'])
            question.options.filter(label='C').update(text=form.cleaned_data['option_c'])
            question.options.filter(label='D').update(text=form.cleaned_data['option_d'])

        messages.success(self.request, "Questão atualizada com sucesso.")
        return redirect('test_detail', pk=question.test.pk)


class QuestionDeleteView(RHRequiredMixin, DeleteView):
    model = Question
    template_name = 'question_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, "Questão excluída com sucesso.")
        return reverse('test_detail', kwargs={'pk': self.object.test.pk})


class TestAssignmentView(RHRequiredMixin, View):
    template_name = 'test_assignment_form.html'

    def get(self, request, *args, **kwargs):
        test = get_object_or_404(Test, pk=kwargs.get('test_id'))
        form = TestAssignmentForm(user_role=request.user.role)

        return render(request, self.template_name, {
            'form': form,
            'test': test
        })

    def post(self, request, *args, **kwargs):
        test = get_object_or_404(Test, pk=kwargs.get('test_id'))
        form = TestAssignmentForm(request.POST, user_role=request.user.role)

        if form.is_valid():
            users = form.cleaned_data['users']
            due_date = form.cleaned_data['due_date']

            for user in users:
                # Create or update assignment
                TestAssignment.objects.update_or_create(
                    test=test,
                    user=user,
                    defaults={
                        'assigned_by': request.user,
                        'due_date': due_date,
                        'status': 'pendente'
                    }
                )

            messages.success(request, f"Teste atribuído a {len(users)} usuários com sucesso.")
            return redirect('test_detail', pk=test.pk)

        return render(request, self.template_name, {
            'form': form,
            'test': test
        })


class UserAssignmentsView(LoginRequiredMixin, ListView):
    model = TestAssignment
    template_name = 'testassignment_list.html'
    context_object_name = 'assignments'

    def get_queryset(self):
        return TestAssignment.objects.filter(
            user=self.request.user
        ).order_by('-assigned_at')


class TakeTestView(LoginRequiredMixin, View):
    template_name = 'take_test.html'

    def get(self, request, *args, **kwargs):
        assignment = get_object_or_404(
            TestAssignment,
            pk=kwargs.get('assignment_id'),
            user=request.user
        )

        if assignment.status == 'concluido':
            messages.warning(request, "Este teste já foi concluído por você.")
            return redirect('user_assignments')

        # Check if the test is expired
        if assignment.due_date and timezone.now() > assignment.due_date:
            assignment.status = 'expirado'
            assignment.save()
            messages.error(request, "O prazo para realização deste teste expirou.")
            return redirect('user_assignments')

        # Start the test if not already started
        test_result, created = TestResult.objects.get_or_create(assignment=assignment)

        if created:
            assignment.status = 'em_andamento'
            assignment.save()

        form = AnswerForm(test=assignment.test)

        # Pre-fill form with existing answers
        answers = Answer.objects.filter(result=test_result)
        initial_data = {}

        for answer in answers:
            initial_data[f'question_{answer.question.id}'] = answer.selected_option

        if initial_data:
            form = AnswerForm(initial=initial_data, test=assignment.test)

        return render(request, self.template_name, {
            'assignment': assignment,
            'test': assignment.test,
            'form': form,
            'result': test_result,
            'time_remaining': None if not assignment.due_date else max(0, (
                        assignment.due_date - timezone.now()).total_seconds())
        })

    def post(self, request, *args, **kwargs):
        assignment = get_object_or_404(
            TestAssignment,
            pk=kwargs.get('assignment_id'),
            user=request.user
        )

        if assignment.status == 'concluido':
            messages.warning(request, "Este teste já foi concluído por você.")
            return redirect('user_assignments')

        test_result = get_object_or_404(TestResult, assignment=assignment)

        # Save all answers
        with transaction.atomic():
            for key, value in request.POST.items():
                if key.startswith('question_'):
                    question_id = int(key.split('_')[1])
                    question = get_object_or_404(Question, id=question_id)

                    Answer.objects.update_or_create(
                        result=test_result,
                        question=question,
                        defaults={'selected_option': value}
                    )

            # If submitted, mark as completed
            if 'submit_test' in request.POST:
                test_result.completed_at = timezone.now()
                test_result.save()

                # Calculate score
                test_result.calculate_score()

                # Update assignment status
                assignment.status = 'concluido'
                assignment.save()

                messages.success(request, "Teste concluído com sucesso!")
                return redirect('test_result', result_id=test_result.id)

            # If just saving progress
            messages.info(request, "Progresso salvo com sucesso.")
            return redirect('take_test', assignment_id=assignment.id)


class TestResultView(LoginRequiredMixin, DetailView):
    model = TestResult
    template_name = 'test_result.html'
    context_object_name = 'result'
    pk_url_kwarg = 'result_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = self.get_object()

        if self.request.user.role == 'rh' or self.request.user == result.assignment.user:
            answers = result.answers.all()
            context['answers'] = answers
            context['test'] = result.assignment.test
            context['questions'] = result.assignment.test.questions.all()
            context['answers_dict'] = {a.question_id: a for a in answers}  # <- ESSA LINHA ADICIONADA
            return context
        else:
            messages.warning(self.request, "Você não tem permissão para ver este resultado.")
            return {}

    def dispatch(self, request, *args, **kwargs):
        result = self.get_object()
        if request.user.role != 'rh' and request.user != result.assignment.user:
            messages.warning(request, "Você não tem permissão para ver este resultado.")
            return redirect('user_assignments')
        return super().dispatch(request, *args, **kwargs)

class AllResultsView(RHRequiredMixin, ListView):
    model = TestResult
    template_name = 'all_results.html'
    context_object_name = 'results'

    def get_queryset(self):
        queryset = TestResult.objects.filter(
            completed_at__isnull=False
        ).select_related('assignment', 'assignment__user', 'assignment__test')

        # Apply filters
        form = FilterTestResultsForm(self.request.GET)
        if form.is_valid():
            filters = {}

            if form.cleaned_data.get('test'):
                filters['assignment__test'] = form.cleaned_data['test']

            if form.cleaned_data.get('user_type'):
                filters['assignment__user__role'] = form.cleaned_data['user_type']

            if form.cleaned_data.get('completed_only'):
                filters['completed_at__isnull'] = False

            if filters:
                queryset = queryset.filter(**filters)

        return queryset.order_by('-completed_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = FilterTestResultsForm(self.request.GET)
        return context

class AssignTestByUserTypeView(RHRequiredMixin, View):
    template_name = 'assign_test_by_user_type.html'

    def get(self, request, *args, **kwargs):
        test = get_object_or_404(Test, pk=kwargs.get('test_id'))
        user_type = request.GET.get('user_type')
        users = []

        # ✅ Correção: "candidato" em vez de "canditato"
        if user_type in ['colaborador', 'candidato']:
            users = CustomUser.objects.filter(role=user_type)

        return render(request, self.template_name, {
            'test': test,
            'users': users,
            'user_type': user_type,
        })

    def post(self, request, *args, **kwargs):
        test = get_object_or_404(Test, pk=kwargs.get('test_id'))
        user_ids = request.POST.getlist('user_ids')
        due_date_str = request.POST.get('due_date')

        try:
            due_date = timezone.datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        except ValueError:
            messages.error(request, "Data de vencimento inválida.")
            return redirect(request.path)

        assigned_count = 0
        for user_id in user_ids:
            user = get_object_or_404(CustomUser, pk=user_id)
            TestAssignment.objects.update_or_create(
                test=test,
                user=user,
                defaults={
                    'assigned_by': request.user,
                    'due_date': due_date,
                    'status': 'pendente'
                }
            )
            assigned_count += 1

        messages.success(request, f"Teste atribuído a {assigned_count} usuários com sucesso.")
        return redirect('test_detail', pk=test.pk)

class TestImportView(RHRequiredMixin, View):
    template_name = 'import_tests.html'

    def get(self, request, *args, **kwargs):
        form = TestImportForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = TestImportForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data['file']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            current_test = None
            for row in reader:
                test_title = row.get('test_title')
                test_description = row.get('test_description')
                test_duration = int(row.get('test_duration', 60))

                # Se for um novo teste
                if not current_test or current_test.title != test_title:
                    current_test, _ = Test.objects.get_or_create(
                        title=test_title,
                        defaults={
                            'description': test_description,
                            'duration_minutes': test_duration,
                            'created_by': request.user,
                            'created_at': timezone.now(),
                            'is_active': True
                        }
                    )

                # Criar a questão
                question = Question.objects.create(
                    test=current_test,
                    text=row.get('question_text'),
                    correct_option=row.get('correct_option'),
                    points=int(row.get('points', 1))
                )

                # Criar as opções
                for label in ['A', 'B', 'C', 'D']:
                    Option.objects.create(
                        question=question,
                        label=label,
                        text=row.get(f'option_{label}')
                    )

            messages.success(request, "Testes e questões importados com sucesso.")
            return redirect('test_list')
        return render(request, self.template_name, {'form': form})