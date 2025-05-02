from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == "POST":
        print("🔄 Signup form received!")  # Debugging

        print("Form Data:", request.POST)  # Print all form data
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        print(f"➡️ Username: {username}, Email: {email}")  # Debugging

        if not username or not email or not password or not confirm_password:
            messages.error(request, "⚠️ All fields are required.")
            print("❌ Missing fields!")
            return render(request, "signup.html")

        if password != confirm_password:
            messages.error(request, "❌ Passwords do not match!")
            print("❌ Passwords do not match!")
            return render(request, "signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "❌ Username already taken!")
            print("❌ Username exists!")
            return render(request, "signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "❌ Email already registered!")
            print("❌ Email exists!")
            return render(request, "signup.html")

        # Create the user
        try:
            print("✅ Creating user...")
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            print("✅ User created successfully!")

            # Authenticate and login user
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                print("✅ User logged in! Redirecting...")
                return redirect("dashboard")
            else:
                print("❌ Authentication failed after signup.")
                messages.error(request, "Authentication failed. Please log in.")
                return redirect("login")

        except Exception as e:
            print(f"❌ Error creating user: {e}")
            messages.error(request, "⚠️ Something went wrong. Try again.")
            return render(request, "signup.html")

    return render(request, "signup.html")

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email","").strip()
        password = request.POST.get("password","").strip()
        user = authenticate(request, email=email, password=password)

        # user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "✅ Logged in successfully!")
            return redirect("dashboard")
        else:
            messages.error(request, "❌ Invalid username or password!")
            return render(request,"login.html", {"error": "Invalid Credentials!"})

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "✅ Logged out successfully!")
    return redirect("dashboard")
from django.contrib.auth.decorators import login_required

 # Redirect to login if user is not authenticated
@login_required
def dashboard(request):
    return render(request, "dashboard.html")

@login_required
def chat(request):
    return render(request, 'chat.html')

from django.shortcuts import render
from django.http import StreamingHttpResponse
from django.http import JsonResponse
import google.generativeai as genai
from .models import ChatMessage
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
# gemini api key
genai.configure(api_key="AIzaSyBF3BK_9LnRwS6bccpUf03BwuHF9_r35G4")


@login_required
def chat_page(request):
    chat_history = ChatMessage.objects.filter(sender=request.user).order_by('timestamp')
    return render(request, "chat.html", {"chat_history": chat_history})

@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            if not user_message:
                return JsonResponse({"response": "❌ No message received!"}, status=400)

            print(f"🔄 Received message: {user_message}")

            # Mood Detection
            mood, confidence = detect_mood(user_message)
            print(f"🧠 Detected Mood: {mood} ({confidence:.2f})")

            # 🧠 Personalize prompt based on mood
            def generate_friendly_prompt(mood, user_msg):
                mood = mood.lower()
                if mood == "nervous":
                    return f"My friend is feeling nervous and said: \"{user_msg}\". Respond with warmth, empathy, and no generic advice—just be there for them like a friend would."
                elif mood == "sad":
                    return f"My friend is feeling sad and shared: \"{user_msg}\". Give a comforting, kind, and caring response like you're talking to someone close to you."
                elif mood == "happy":
                    return f"My friend is in a great mood and said: \"{user_msg}\". Celebrate with them and ask more about their joy in a casual and fun way!"
                elif mood == "angry":
                    return f"My friend is feeling angry and vented: \"{user_msg}\". Respond calmly and supportively—let them feel heard like a close friend would."
                elif mood == "anxious":
                    return f"My friend feels anxious and mentioned: \"{user_msg}\". Help ease their nerves gently, like you're talking to someone you deeply care about."
                else:
                    return f"A friend shared this with me: \"{user_msg}\". Reply in a caring and natural way—no therapy tips, just human connection."

            # 🎯 Build the mood-aware prompt
            friendly_prompt = generate_friendly_prompt(mood, user_message)

            # Gemini Streaming Response
            model = genai.GenerativeModel("gemini-1.5-pro-latest")
            response_stream = model.generate_content(friendly_prompt, stream=True)
            print("✅ Streaming response from Gemini with mood personalization...")

            # To store streamed response
            bot_response_chunks = []

            def event_stream():
                for chunk in response_stream:
                    if hasattr(chunk, "text"):
                        bot_response_chunks.append(chunk.text)
                        yield f"{chunk.text}"

                # Save chat with mood after full stream
                ChatMessage.objects.create(
                    sender=request.user if request.user.is_authenticated else None,
                    message=user_message,
                    response="".join(bot_response_chunks),
                    mood=mood,
                    mood_confidence=confidence
                )

            return StreamingHttpResponse(event_stream(), content_type="text/plain")

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return JsonResponse({"response": f"Error: {str(e)}"}, status=500)
        
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileUpdateForm

@login_required
def profile(request):
    if request.method == 'POST':
        form =ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form =ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'profile.html', {'form': form})

from django.shortcuts import render, redirect
from .models import JournalEntry
from .utils.mood_detector import detect_mood
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from .forms import JournalEntryForm
from .models import JournalEntry
from django.contrib.auth.decorators import login_required

@login_required
def journal_page(request):
    form = JournalEntryForm()
    selected_category = request.GET.get('category', None)

    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            journal_entry = form.save(commit=False)
            journal_entry.user = request.user
            # Optional: Add emotion detection here if needed
            journal_entry.save()
            return redirect('journal_page')  # Use your URL name

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

@login_required
def therapy_view(request):
    meditations = [
        {'title': 'Calm Mind', 'duration': 5, 'audio_url': '/media/calm_mind.mp3'},
        {'title': 'Evening Relaxation', 'duration': 10, 'audio_url': '/media/evening_relaxation.mp3'},
    ]
    return render(request, 'therapy.html', {'meditations': meditations})


from django.shortcuts import render
from .models import Psychiatrist

def psychiatrist_list(request):
    user_location = request.GET.get('location', '')  # or retrieve from user profile
    psychiatrists = Psychiatrist.objects.filter(location__icontains=user_location)

    return render(request, 'psychiatrist_list.html', {
        'psychiatrists': psychiatrists,
        'user_location': user_location,
    })

