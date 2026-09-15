from django.contrib import admin
from .models import ChatMessage, Profile, JournalEntry, MoodLog, AssessmentResult


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'mood', 'mood_confidence', 'timestamp')
    list_filter = ('mood', 'timestamp')
    search_fields = ('message', 'response')
    readonly_fields = ('timestamp',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_picture')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'emotion', 'created_at')
    list_filter = ('category', 'emotion', 'created_at')
    search_fields = ('content',)





@admin.register(MoodLog)
class MoodLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood', 'created_at')
    list_filter = ('mood', 'created_at')
    search_fields = ('user__username', 'note')


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_score', 'severity', 'created_at')
    list_filter = ('severity', 'created_at')
    search_fields = ('user__username',)

