from django.db import models
from core.models import CustomUser
from django.utils import timezone


class Test(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_tests')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_total_questions(self):
        return self.questions.count()


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    OPTION_CHOICES = [
        ('A', 'Opção A'),
        ('B', 'Opção B'),
        ('C', 'Opção C'),
        ('D', 'Opção D'),
    ]
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    points = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.test.title} - Questão {self.id}"


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=1)  # A, B, C, D
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.question.text[:30]} - Opção {self.label}"


class TestAssignment(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='assigned_tests')
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='test_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('expirado', 'Expirado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    class Meta:
        unique_together = ['test', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.test.title}"


class TestResult(models.Model):
    assignment = models.OneToOneField(TestAssignment, on_delete=models.CASCADE, related_name='result')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_score = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Resultado: {self.assignment.user.username} - {self.assignment.test.title}"

    def calculate_score(self):
        total_points = sum(question.points for question in self.assignment.test.questions.all())
        self.max_score = total_points

        correct_points = sum(
            answer.question.points
            for answer in self.answers.all()
            if answer.selected_option == answer.question.correct_option
        )

        if total_points > 0:
            self.score = (correct_points / total_points) * 100
        else:
            self.score = 0

        self.save()
        return self.score


class Answer(models.Model):
    result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)

    class Meta:
        unique_together = ['result', 'question']

    def __str__(self):
        return f"{self.result.assignment.user.username} - {self.question.text[:30]}"