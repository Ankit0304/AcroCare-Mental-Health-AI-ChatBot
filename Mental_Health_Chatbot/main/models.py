from django.db import models
from django.contrib.auth.models import User


class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    response = models.TextField()
    mood = models.CharField(max_length=100, null=True, blank=True)
    mood_confidence = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} - {self.mood} - {self.timestamp}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default.jpg')

    def __str__(self):
        return f"{self.user.username}'s Profile"


class JournalEntry(models.Model):
    CATEGORY_CHOICES = [
        ('thought_dump', 'Thought Dump'),
        ('gratitude', 'Gratitude Journal'),
        ('mood_reflection', 'Mood Reflection'),
        ('goals', 'Goals & Progress'),
        ('daily_recap', 'Daily Recap'),
        ('stress_log', 'Stress Log'),
        ('dream_log', 'Dream Log'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='thought_dump')
    content = models.TextField()
    emotion = models.CharField(max_length=50, blank=True, null=True)  # auto-detected mood
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.category} - {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name_plural = "Journal Entries"


class Psychiatrist(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    fees = models.DecimalField(max_digits=8, decimal_places=2)
    contact = models.CharField(max_length=50)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='psychiatrists/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Psychiatrists"


class MoodLog(models.Model):
    """Tracks mood entries from the therapy page mood tracker."""
    MOOD_CHOICES = [
        ('happy', '😊 Happy'),
        ('neutral', '😐 Neutral'),
        ('sad', '😢 Sad'),
        ('angry', '😠 Angry'),
        ('anxious', '😰 Anxious'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.mood} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Mood Logs"


class AssessmentResult(models.Model):
    """Stores PHQ-9 mental health assessment results."""
    SEVERITY_LEVELS = [
        ('minimal', 'Minimal (0-4)'),
        ('mild', 'Mild (5-9)'),
        ('moderate', 'Moderate (10-14)'),
        ('moderately_severe', 'Moderately Severe (15-19)'),
        ('severe', 'Severe (20-27)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_score = models.IntegerField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    answers = models.JSONField(default=dict)  # stores individual question scores
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - PHQ-9: {self.total_score} ({self.severity}) - {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Assessment Results"

