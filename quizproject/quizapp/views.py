# quizapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import UserRegisterForm, QuestionForm
from .models import Question, Result
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .serializers import QuestionSerializer, ResultSerializer, UserSerializer
# --- Authentication Views ---

def home(request):
    return render(request, 'home.html')


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # login(request, user) # Optional: Log user in directly after registration
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
        else:
             messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Welcome back, {username}!")
                # Redirect to 'next' page if exists, otherwise home
                next_url = request.POST.get('next', '/') # Use '/' or 'home' as default
                # Ensure next_url is safe before redirecting (basic check)
                if next_url and not next_url.startswith('//') and ':' not in next_url:
                     return redirect(next_url)
                else:
                     return redirect('home')

            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    else:
        form = AuthenticationForm()
    # Pass 'next' parameter to template if it exists
    next_url = request.GET.get('next')
    return render(request, 'login.html', {'form': form, 'next': next_url})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')

# --- Quiz Views ---

@login_required
def quiz_view(request):
    questions = Question.objects.all() # Fetch all questions
    if not questions:
         messages.warning(request, "No questions available in the quiz yet.")
         return redirect('home')

    if request.method == 'POST':
        score = 0
        total_questions = 0
        for question in questions:
            total_questions += 1
            submitted_answer = request.POST.get(f'question_{question.id}')
            # Ensure submitted_answer is not None and can be converted to int
            try:
                if submitted_answer and int(submitted_answer) == question.correct_option:
                    score += 1
            except (ValueError, TypeError):
                # Handle case where submitted_answer is not a valid number
                pass # Or log an error

        # Save the result
        result = Result.objects.create(
            user=request.user,
            score=score,
            total_questions=total_questions
        )
        # Redirect to the result page for this specific attempt
        return redirect('result', result_id=result.id)

    # If GET request, display the quiz form
    return render(request, 'quiz.html', {'questions': questions})

@login_required
def result_view(request, result_id):
    # Ensure the user can only see their own results
    result = get_object_or_404(Result, id=result_id, user=request.user)
    return render(request, 'result.html', {'result': result})

@login_required
def view_scores_view(request):
    results = Result.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'view_scores.html', {'results': results})


# --- Superuser Views ---

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser, login_url='login') # Redirect non-superusers to login
def add_question_view(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question added successfully!')
            return redirect('add_question') # Redirect back to add another
        else:
             messages.error(request, 'Failed to add question. Please check the form.')
    else:
        form = QuestionForm()
    return render(request, 'add_question.html', {'form': form})

# --- API Views ---

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # Allow anyone to register/login

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [AllowAny]  # Allow anyone to view questions

    def list(self, request, *args, **kwargs):
        questions = self.get_queryset()
        serializer = self.get_serializer(questions, many=True)
        return Response(serializer.data)

class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = [AllowAny]  # Allow anyone to submit quiz answers

    def get_queryset(self):
        return Result.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def submit_quiz(self, request):
        answers = request.data.get('answers', {})
        score = 0
        total_questions = 0
        
        for question_id, answer in answers.items():
            try:
                question = Question.objects.get(id=question_id)
                total_questions += 1
                if int(answer) == question.correct_option:
                    score += 1
            except (Question.DoesNotExist, ValueError):
                continue
        
        result = Result.objects.create(
            user=request.user if request.user.is_authenticated else None,
            score=score,
            total_questions=total_questions
        )
        serializer = self.get_serializer(result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)