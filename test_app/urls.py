from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Testes
    path('', views.TestListView.as_view(), name='test_list'),
    path('test/<int:pk>/', views.TestDetailView.as_view(), name='test_detail'),
    path('test/create/', views.TestCreateView.as_view(), name='test_create'),
    path('test/<int:pk>/update/', views.TestUpdateView.as_view(), name='test_update'),
    path('test/<int:pk>/delete/', views.TestDeleteView.as_view(), name='test_delete'),

    # Questões
    path('test/<int:test_id>/question/add/', views.QuestionCreateView.as_view(), name='question_add'),
    path('question/<int:pk>/update/', views.QuestionUpdateView.as_view(), name='question_update'),
    path('question/<int:pk>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),

    # Atribuição de teste
    path('test/<int:test_id>/assign/', views.TestAssignmentView.as_view(), name='test_assign'),
    path('test/<int:test_id>/assign_by_type/',views.AssignTestByUserTypeView.as_view(), name='assign_test_by_type'),
    # Atribuições do usuário
    path('my-assignments/', views.UserAssignmentsView.as_view(), name='user_assignments'),


    # Realizar teste
    path('assignment/<int:assignment_id>/take/', views.TakeTestView.as_view(), name='take_test'),

    # Resultado do teste
    path('result/<int:result_id>/', views.TestResultView.as_view(), name='test_result'),

    # Todos os resultados (RH)
    path('results/all/', views.AllResultsView.as_view(), name='all_test_results'),

    path('tests/import/', views.TestImportView.as_view(), name='import_tests'),
]
