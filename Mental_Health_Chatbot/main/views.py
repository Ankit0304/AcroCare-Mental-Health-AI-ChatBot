import os
import json
import logging

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseBadRequest
import google.generativeai as genai

from .models import ChatMessage, JournalEntry, Profile, MoodLog, AssessmentResult
from .forms import ProfileUpdateForm, JournalEntryForm
from .utils.mood_detector import detect_mood

logger = logging.getLogger(__name__)

# Configure Gemini with API key from environment
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ──────────────────────────────────────────────
# Auth Views
# ──────────────────────────────────────────────

def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        logger.info("Signup attempt for username=%s, email=%s", username, email)

        if not username or not email or not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return render(request, "signup.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, "signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return render(request, "signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, "signup.html")

        # Create the user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            logger.info("User created successfully: %s", username)

            # Authenticate and login user
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect("dashboard")
            else:
                logger.error("Authentication failed after signup for %s", username)
                messages.error(request, "Authentication failed. Please log in.")
                return redirect("login")

        except Exception as e:
            logger.error("Error creating user: %s", str(e))
            messages.error(request, "Something went wrong. Try again.")
            return render(request, "signup.html")

    return render(request, "signup.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid email or password!")
            return render(request, "login.html", {"error": "Invalid Credentials!"})

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("home")


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

@login_required
def dashboard(request):
    # Gather user stats for a meaningful dashboard
    chat_count = ChatMessage.objects.filter(sender=request.user).count()
    journal_count = JournalEntry.objects.filter(user=request.user).count()
    recent_journals = JournalEntry.objects.filter(user=request.user).order_by('-created_at')[:5]

    # Get recent moods from chat
    recent_moods = ChatMessage.objects.filter(
        sender=request.user, mood__isnull=False
    ).order_by('-timestamp').values_list('mood', flat=True)[:10]

    context = {
        'chat_count': chat_count,
        'journal_count': journal_count,
        'recent_journals': recent_journals,
        'recent_moods': list(recent_moods),
    }
    return render(request, "dashboard.html", context)


# ──────────────────────────────────────────────
# Chat Views
# ──────────────────────────────────────────────

@login_required
def chat_page(request):
    chat_history = ChatMessage.objects.filter(sender=request.user).order_by('timestamp')
    return render(request, "chat.html", {"chat_history": chat_history})


def _generate_friendly_prompt(mood, user_msg):
    """Generate a mood-aware prompt for the Gemini model."""
    mood_lower = mood.lower()

    mood_prompts = {
        # Negative emotions
        "anger": "My friend is feeling angry and vented: \"{msg}\". Respond calmly and supportively—let them feel heard like a close friend would.",
        "sadness": "My friend is feeling sad and shared: \"{msg}\". Give a comforting, kind, and caring response like you're talking to someone close to you.",
        "fear": "My friend is feeling fearful and said: \"{msg}\". Respond with reassurance, warmth, and empathy—help them feel safe.",
        "disgust": "My friend is upset and shared: \"{msg}\". Acknowledge their feelings and respond with understanding and care.",
        "annoyance": "My friend is feeling annoyed and said: \"{msg}\". Let them vent and respond supportively without dismissing their frustration.",
        "disappointment": "My friend is feeling disappointed and shared: \"{msg}\". Respond with empathy and help them see the situation in perspective.",
        "disapproval": "My friend is bothered by something and said: \"{msg}\". Listen to their concern and respond thoughtfully.",
        "embarrassment": "My friend is feeling embarrassed and shared: \"{msg}\". Be gentle and reassuring—help them feel it's okay.",
        "grief": "My friend is grieving and said: \"{msg}\". Be deeply compassionate and present—no advice, just hold space for them.",
        "remorse": "My friend is feeling regretful and shared: \"{msg}\". Respond with understanding and help them be kinder to themselves.",
        "nervousness": "My friend is feeling nervous and said: \"{msg}\". Respond with warmth, empathy, and no generic advice—just be there for them.",

        # Positive emotions
        "joy": "My friend is in a great mood and said: \"{msg}\". Celebrate with them and ask more about their joy in a casual and fun way!",
        "optimism": "My friend is feeling hopeful and shared: \"{msg}\". Encourage their positivity and engage with their optimism genuinely!",
        "admiration": "My friend is feeling impressed and shared: \"{msg}\". Join in their admiration and have a fun conversation about it!",
        "approval": "My friend is feeling good about something and said: \"{msg}\". Affirm their feelings and engage warmly.",
        "caring": "My friend is showing care and shared: \"{msg}\". Appreciate their compassion and respond warmly.",
        "excitement": "My friend is excited and shared: \"{msg}\". Match their energy and get excited with them!",
        "gratitude": "My friend is feeling grateful and said: \"{msg}\". Acknowledge their gratitude and share in the warmth.",
        "love": "My friend is feeling loving and shared: \"{msg}\". Respond warmly and appreciate the beautiful sentiment.",
        "pride": "My friend is feeling proud and said: \"{msg}\". Celebrate their achievement and be genuinely happy for them!",
        "relief": "My friend is feeling relieved and shared: \"{msg}\". Share in their relief and be happy things worked out.",

        # Neutral / cognitive emotions
        "confusion": "My friend is feeling confused and said: \"{msg}\". Help them think through it gently, without being condescending.",
        "curiosity": "My friend is curious and asked: \"{msg}\". Engage with their curiosity in a fun and informative way!",
        "desire": "My friend is wanting something and shared: \"{msg}\". Encourage them and help them think about it positively.",
        "realization": "My friend had a realization and said: \"{msg}\". Engage with their insight and explore it together.",
        "surprise": "My friend is surprised and said: \"{msg}\". React naturally and explore what surprised them!",
        "neutral": "A friend shared this with me: \"{msg}\". Reply in a caring and natural way—no therapy tips, just human connection.",
    }

    prompt_template = mood_prompts.get(
        mood_lower,
        "A friend shared this with me: \"{msg}\". Reply in a caring and natural way—no therapy tips, just human connection."
    )
    return prompt_template.format(msg=user_msg)


CHATBUDDY_SYSTEM_INSTRUCTION = (
    "You are ChatBuddy, a compassionate, empathetic, and attentive mental health companion. "
    "Your purpose is to provide a safe, soothing, and non-judgmental space. "
    "Listen deeply, validate feelings with genuine empathy, and offer gentle perspectives or practical grounding techniques when helpful. "
    "Speak like a caring, emotionally intelligent friend—not an impersonal machine or clinical textbook. "
    "Keep replies readable, human, and comforting. Use gentle Markdown formatting (e.g. bold highlights, clear line breaks, and bullet lists when appropriate). "
    "CRITICAL SAFETY RULE: If the user indicates self-harm, suicidal ideation, or extreme crisis, respond with heartfelt care, urge them to stay safe, and provide crisis helpline resources:\n"
    "- India: Tele-MANAS (14416 or 1800-891-4416), Vandrevala Foundation (+91 9999 666 555)\n"
    "- US/International: 988 Suicide & Crisis Lifeline (call/text 988), or findahelpline.com"
)


def _generate_fallback_response(mood, user_msg):
    """Empathetic and conversational fallback response when remote AI is unreachable or API key suspended."""
    m = (mood or "neutral").lower()
    msg_lower = user_msg.lower().strip()

    # Safety checks first
    if any(k in msg_lower for k in ["suicide", "kill myself", "end my life", "self harm", "want to die"]):
        return (
            "I hear how much pain you are carrying right now, and I care deeply about your safety. "
            "Please know that you do not have to carry this alone. Please reach out to someone who can help right now:\n\n"
            "- **Tele-MANAS (India):** Call 14416 or 1800-891-4416 (24/7 free toll-free)\n"
            "- **Vandrevala Foundation:** Call +91 9999 666 555\n"
            "- **US/Canada Lifeline:** Call or text 988\n\n"
            "Please reach out to them. There are people who want to listen and walk with you through this."
        )

    # Identity and self-introduction
    if any(k in msg_lower for k in ["who are you", "what are you", "who r u", "your name", "tell me about yourself"]):
        return (
            "I'm **ChatBuddy**, your AI mental health and emotional wellness companion on AcroCare. 🌸\n\n"
            "I'm here to offer a safe, confidential space where you can share your thoughts, talk through stress, "
            "and practice calming exercises without any judgment. How are you feeling today?"
        )

    # Capabilities and help
    if any(k in msg_lower for k in ["what can you do", "how can you help", "what do you do", "features"]):
        return (
            "Here are some ways I can support you:\n\n"
            "- 💬 **Listening & Venting:** Talk openly about your day, stress, work, or relationships.\n"
            "- 🌿 **Calming Breathing:** Guide you through relaxation and grounding techniques.\n"
            "- 📝 **Journal Reflection:** Help unpack and understand what's on your mind.\n"
            "- 🛡️ **Crisis Helplines:** Connect you with professional resources whenever needed.\n\n"
            "What would feel most helpful for you right now?"
        )

    # Greeting / check-in
    if any(k in msg_lower for k in ["hello", "hi", "hey", "hola", "namaste", "good morning", "good evening", "good afternoon"]):
        return (
            "Hello! It's really wonderful to connect with you. I'm right here with you in this quiet space. "
            "How has your day been treating you so far?"
        )

    # Inquiries about bot's status
    if any(k in msg_lower for k in ["how are you", "how r u", "how are you doing", "how's it going"]):
        return (
            "Thank you so much for asking! I'm doing well, and I'm glad you're here. "
            "More importantly, how are you feeling inside today?"
        )

    # Creator inquiries
    if any(k in msg_lower for k in ["who created you", "who made you", "who developed you"]):
        return (
            "I was created as part of the **AcroCare** mental wellness platform to provide accessible, "
            "empathetic emotional support for anyone seeking a safe place to share."
        )

    # Gratitude
    if any(k in msg_lower for k in ["thank you", "thanks", "thx", "appreciate it"]):
        return (
            "You are so very welcome! It means a lot to share this space with you. "
            "Remember to take things one step at a time today."
        )

    if any(k in msg_lower for k in ["exhaust", "tired", "long day", "hard day", "drained", "sleepy"]):
        return (
            "I hear you. Long and exhausting days take a real toll on both your mind and body. "
            "Right now, please give yourself permission to set that heavy backpack down. "
            "You made it through today, and that is more than enough.\n\n"
            "Would you like to talk about what made today so draining, or would you prefer a quick soothing reset?"
        )

    if any(k in msg_lower for k in ["breathe", "breathing", "anxiety", "anxious", "panic", "overwhelm"]):
        return (
            "I hear that things feel overwhelming right now. Let's take a calm pause together 🌿\n\n"
            "1. **Breathe in** gently through your nose for 4 seconds.\n"
            "2. **Hold** that stillness for 4 seconds.\n"
            "3. **Exhale slowly** through your mouth for 6 seconds.\n\n"
            "Relax your shoulders and unclench your jaw. You are safe right now in this moment. How does that feel?"
        )

    if any(k in msg_lower for k in ["vent", "just listen", "rant"]):
        return (
            "I am completely here to listen—no unwanted advice, no judgment, just an open ear. "
            "Whenever you're ready, let it all out."
        )

    mood_replies = {
        "sadness": (
            "I can hear how heavy things feel right now, and I want you to know it's completely okay to feel this way. "
            "You don't have to carry this burden alone. What's sitting most heavily on your mind right now?"
        ),
        "anger": (
            "It sounds like you're dealing with something intensely frustrating. Your feelings are valid, and you have every right to feel upset. "
            "I'm here to listen without judgment—feel free to vent as much as you need."
        ),
        "fear": (
            "It's understandable to feel nervous or afraid when things feel uncertain. In this moment, take a slow breath. You are safe here. "
            "What feels like the biggest worry right now?"
        ),
        "joy": (
            "That is so wonderful to hear! Celebrating the bright moments is so important. What was the best part of it for you?"
        ),
        "optimism": (
            "I love that forward-looking hope! Holding onto positive momentum is so powerful. Tell me more about it!"
        ),
        "gratitude": (
            "Gratitude has such a grounding warmth to it. Holding onto those small moments of grace makes a big difference."
        ),
        "nervousness": (
            "It's completely natural to feel nervous. Be gentle with yourself right now. Let's take it one step at a time."
        ),
        "neutral": (
            "I'm listening closely. Please take your time—tell me whatever is on your mind."
        ),
    }

    return mood_replies.get(m, "I'm listening and I'm here with you. Please take your time—tell me whatever is on your mind.")


@login_required
def chatbot_response(request):
    """Handle chat messages — streams Gemini response with conversation memory and mood-awareness."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()

            if not user_message:
                return JsonResponse({"response": "No message received!"}, status=400)

            logger.info("Chat message received from user=%s", request.user.username)

            # Mood Detection
            mood, confidence = detect_mood(user_message)
            logger.info("Detected mood: %s (%.2f) for user=%s", mood, confidence, request.user.username)

            # Fetch recent conversation context (last 6 messages)
            recent_chats = ChatMessage.objects.filter(sender=request.user).order_by('-timestamp')[:6]
            history_lines = []
            for c in reversed(recent_chats):
                if c.message:
                    history_lines.append(f"User: {c.message}")
                if c.response:
                    snippet = c.response[:250] + ("..." if len(c.response) > 250 else "")
                    history_lines.append(f"ChatBuddy: {snippet}")

            history_str = "\n".join(history_lines) if history_lines else "No prior history in this session."

            # Build the mood-aware prompt
            mood_guidance = _generate_friendly_prompt(mood, user_message)

            full_prompt = (
                f"{CHATBUDDY_SYSTEM_INSTRUCTION}\n\n"
                f"### Recent Conversation Context:\n{history_str}\n\n"
                f"### Detected User Emotion:\nMood: {mood} (Confidence: {confidence:.2f})\n"
                f"Empathy Guidance: {mood_guidance}\n\n"
                f"### User's Current Message:\n{user_message}\n\n"
                f"Respond warmly and directly to the user as ChatBuddy:"
            )

            # Dynamically read and configure Gemini API key
            api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
            response_stream = None
            gemini_error = None

            if api_key:
                genai.configure(api_key=api_key)
                candidate_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"]
                for model_name in candidate_models:
                    try:
                        gemini_model = genai.GenerativeModel(model_name)
                        response_stream = gemini_model.generate_content(full_prompt, stream=True)
                        logger.info("Successfully generated response using model=%s", model_name)
                        break
                    except Exception as err:
                        gemini_error = str(err)
                        logger.warning("Gemini model %s failed: %s", model_name, gemini_error)
            else:
                logger.warning("GEMINI_API_KEY is not configured in environment.")

            if response_stream is not None:
                bot_response_chunks = []

                def event_stream():
                    for chunk in response_stream:
                        if hasattr(chunk, "text") and chunk.text:
                            bot_response_chunks.append(chunk.text)
                            yield chunk.text

                    final_response = "".join(bot_response_chunks).strip()
                    if final_response:
                        ChatMessage.objects.create(
                            sender=request.user,
                            message=user_message,
                            response=final_response,
                            mood=mood,
                            mood_confidence=confidence
                        )

                response = StreamingHttpResponse(event_stream(), content_type="text/plain; charset=utf-8")
                response["X-Detected-Mood"] = mood
                response["X-Mood-Confidence"] = str(round(confidence, 2))
                return response
            else:
                # Fallback empathetic response
                logger.warning("Falling back to conversational fallback. Last Gemini error: %s", gemini_error)
                fallback_reply = _generate_fallback_response(mood, user_message)

                ChatMessage.objects.create(
                    sender=request.user,
                    message=user_message,
                    response=fallback_reply,
                    mood=mood,
                    mood_confidence=confidence
                )

                def fallback_stream():
                    words = fallback_reply.split(" ")
                    for i, w in enumerate(words):
                        yield w + (" " if i < len(words) - 1 else "")

                response = StreamingHttpResponse(fallback_stream(), content_type="text/plain; charset=utf-8")
                response["X-Detected-Mood"] = mood
                response["X-Mood-Confidence"] = str(round(confidence, 2))
                return response

        except Exception as e:
            logger.error("Chatbot fatal error: %s", str(e))
            return JsonResponse({"response": "I'm right here with you. Please take a deep breath and tell me a bit more."}, status=200)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
@require_POST
def clear_chat_history(request):
    """Clear all chat messages for the current user."""
    try:
        deleted_count, _ = ChatMessage.objects.filter(sender=request.user).delete()
        logger.info("Cleared %d chat messages for user=%s", deleted_count, request.user.username)
        return JsonResponse({"status": "success", "message": "Conversation history cleared successfully."})
    except Exception as e:
        logger.error("Failed to clear chat history: %s", str(e))
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# ──────────────────────────────────────────────
# Profile
# ──────────────────────────────────────────────

@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile photo updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Could not update profile photo. Please try again.")
    else:
        form = ProfileUpdateForm(instance=profile_obj)
    return render(request, 'profile.html', {'form': form})


# ──────────────────────────────────────────────
# Journal
# ──────────────────────────────────────────────

@login_required
def journal_page(request):
    form = JournalEntryForm()
    selected_category = request.GET.get('category', None)

    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            journal_entry = form.save(commit=False)
            journal_entry.user = request.user

            # Auto-detect emotion from journal content
            try:
                emotion, _ = detect_mood(journal_entry.content)
                journal_entry.emotion = emotion
            except Exception:
                logger.warning("Emotion detection failed for journal entry")

            journal_entry.save()
            return redirect('journal_page')

    # Filter by selected category if chosen
    if selected_category:
        entries = JournalEntry.objects.filter(user=request.user, category=selected_category).order_by('-created_at')
    else:
        entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'form': form,
        'entries': entries,
        'selected_category': selected_category,
    }
    return render(request, 'journal_page.html', context)


# ──────────────────────────────────────────────
# Therapy
# ──────────────────────────────────────────────

@login_required
def therapy_view(request):
    meditations = [
        {'title': 'Calm Mind', 'duration': 5, 'audio_url': '/media/calm_mind.mp3'},
        {'title': 'Evening Relaxation', 'duration': 10, 'audio_url': '/media/evening_relaxation.mp3'},
    ]
    return render(request, 'therapy.html', {'meditations': meditations})





# ──────────────────────────────────────────────
# Mood Tracker (Therapy page)
# ──────────────────────────────────────────────

@login_required
def save_mood(request):
    """Save a mood entry from the therapy page mood tracker."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            mood = data.get("mood", "")
            note = data.get("note", "")

            if mood not in ['happy', 'neutral', 'sad', 'angry', 'anxious']:
                return JsonResponse({"error": "Invalid mood"}, status=400)

            MoodLog.objects.create(user=request.user, mood=mood, note=note)
            return JsonResponse({"status": "saved", "mood": mood})
        except Exception as e:
            logger.error("Error saving mood: %s", str(e))
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
def mood_history(request):
    """Return mood history as JSON for chart rendering."""
    logs = MoodLog.objects.filter(user=request.user).order_by('-created_at')[:30]
    data = [
        {
            "mood": log.mood,
            "note": log.note or "",
            "date": log.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for log in logs
    ]
    return JsonResponse({"moods": data})


# ──────────────────────────────────────────────
# PHQ-9 Assessment
# ──────────────────────────────────────────────

PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading or watching television",
    "Moving or speaking so slowly that other people could have noticed — or the opposite",
    "Thoughts that you would be better off dead, or of hurting yourself in some way",
]


def _get_phq9_severity(score):
    """Map PHQ-9 total score to severity level."""
    if score <= 4:
        return 'minimal'
    elif score <= 9:
        return 'mild'
    elif score <= 14:
        return 'moderate'
    elif score <= 19:
        return 'moderately_severe'
    else:
        return 'severe'


SEVERITY_MESSAGES = {
    'minimal': {
        'title': 'Minimal Depression',
        'message': 'Your responses suggest minimal depression symptoms. Keep up the good work with self-care!',
        'color': 'green',
    },
    'mild': {
        'title': 'Mild Depression',
        'message': 'Your responses suggest mild depression symptoms. Consider using our journaling and breathing exercises regularly.',
        'color': 'yellow',
    },
    'moderate': {
        'title': 'Moderate Depression',
        'message': 'Your responses suggest moderate depression symptoms. We recommend speaking with a mental health professional.',
        'color': 'orange',
    },
    'moderately_severe': {
        'title': 'Moderately Severe Depression',
        'message': 'Your responses suggest moderately severe depression symptoms. Please consider reaching out to a mental health professional soon.',
        'color': 'red',
    },
    'severe': {
        'title': 'Severe Depression',
        'message': 'Your responses suggest severe depression symptoms. We strongly recommend seeking professional help. If you are in crisis, please contact a helpline immediately.',
        'color': 'red',
    },
}


@login_required
def assessment_view(request):
    """Handle PHQ-9 mental health assessment."""
    result = None

    if request.method == "POST":
        answers = {}
        total_score = 0

        for i in range(9):
            key = f"q{i}"
            score = int(request.POST.get(key, 0))
            answers[key] = score
            total_score += score

        severity = _get_phq9_severity(total_score)

        # Save result
        AssessmentResult.objects.create(
            user=request.user,
            total_score=total_score,
            severity=severity,
            answers=answers,
        )

        result = {
            'total_score': total_score,
            'severity': severity,
            'info': SEVERITY_MESSAGES[severity],
        }

    # Get past results
    past_results = AssessmentResult.objects.filter(user=request.user)[:5]

    context = {
        'questions': PHQ9_QUESTIONS,
        'result': result,
        'past_results': past_results,
    }
    return render(request, 'assessment.html', context)


@login_required
def contact_view(request):
    """Contact and help page."""
    return render(request, 'contact.html')
