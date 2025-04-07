# quizapp/models.py
from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    text = models.TextField()
    option1 = models.CharField(max_length=100)
    option2 = models.CharField(max_length=100)
    option3 = models.CharField(max_length=100)
    option4 = models.CharField(max_length=100)
    # Store the correct option number (1, 2, 3, or 4)
    correct_option = models.PositiveSmallIntegerField(choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')])

    def __str__(self):
        return self.text[:50] # Display first 50 chars in admin

class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Make user optional
    score = models.IntegerField()
    total_questions = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - Score: {self.score}/{self.total_questions}"

    def percentage(self):
        if self.total_questions > 0:
            return round((self.score / self.total_questions) * 100, 2)
        return 0