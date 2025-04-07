from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Question, Result
from .serializers import QuestionSerializer, ResultSerializer

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class ResultViewSet(viewsets.ModelViewSet):
    serializer_class = ResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    basename = 'result'

    def get_queryset(self):
        return Result.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def submit_quiz(self, request):
        questions = Question.objects.all()
        score = 0
        total_questions = len(questions)
        
        for question in questions:
            submitted_answer = request.data.get(f'question_{question.id}')
            if submitted_answer and int(submitted_answer) == question.correct_option:
                score += 1

        result = Result.objects.create(
            user=request.user,
            score=score,
            total_questions=total_questions
        )
        
        return Response({
            'result_id': result.id,
            'score': score,
            'total_questions': total_questions
        }, status=status.HTTP_201_CREATED) 