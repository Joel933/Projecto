from .models import TestAssignment

def assignment_context(request):
    if request.user.is_authenticated:
        assignment = TestAssignment.objects.filter(user=request.user, status__in=['pendente', 'em_andamento']).first()
        return {'assignment': assignment}
    return {}