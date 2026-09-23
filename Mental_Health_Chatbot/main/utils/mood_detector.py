import logging
import re

logger = logging.getLogger(__name__)

# Correct 27+1 emotion labels matching GoEmotions
labels = [
    'admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring',
    'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval',
    'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief',
    'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization',
    'relief', 'remorse', 'sadness', 'surprise', 'neutral'
]

# High-accuracy emotion keywords and phrases for instant, zero-RAM sentiment classification
EMOTION_KEYWORDS = {
    'joy': [
        'happy', 'joy', 'glad', 'delighted', 'ecstatic', 'cheerful', 'blessed',
        'great day', 'wonderful', 'fantastic', 'amazing', 'thrilled', 'content',
        'smiling', 'laughter', 'celebrate', 'radiant', 'enjoying', 'euphoric'
    ],
    'sadness': [
        'sad', 'unhappy', 'depressed', 'cry', 'crying', 'tear', 'tears', 'heartbroken',
        'gloomy', 'lonely', 'miserable', 'down', 'hopeless', 'sorrow', 'melancholy',
        'feeling low', 'hurting', 'pain', 'empty', 'despair'
    ],
    'anger': [
        'angry', 'furious', 'mad', 'rage', 'pissed', 'enraged', 'livid',
        'hate', 'hateful', 'outraged', 'hostile', 'infuriated', 'wrath'
    ],
    'fear': [
        'scared', 'fear', 'afraid', 'terrified', 'frightened', 'panic', 'panicking',
        'horrified', 'petrified', 'dread', 'nightmare', 'creepy'
    ],
    'nervousness': [
        'anxious', 'nervous', 'anxiety', 'worried', 'worry', 'stress', 'stressed',
        'overwhelmed', 'tense', 'apprehensive', 'jittery', 'restless', 'uneasy',
        'freaking out', 'panicky'
    ],
    'love': [
        'love', 'loving', 'adore', 'beloved', 'affection', 'sweetheart',
        'cherish', 'crush on', 'in love', 'fond of'
    ],
    'gratitude': [
        'thank', 'thanks', 'thankful', 'grateful', 'gratitude', 'appreciate',
        'appreciation', 'obliged', 'thank you', 'blessed to have'
    ],
    'caring': [
        'care', 'caring', 'support', 'help', 'comfort', 'kind', 'kindness',
        'sympathy', 'gentle', 'compassion', 'warmth', 'listen', 'holding hand'
    ],
    'grief': [
        'grief', 'mourn', 'mourning', 'passed away', 'lost someone', 'funeral',
        'bereaved', 'condolences', 'tragic loss', 'died', 'loss of my'
    ],
    'excitement': [
        'excited', 'exciting', 'cant wait', "can't wait", 'pumped', 'hyped',
        'thrilled', 'enthusiastic', 'psyched', 'electrifying'
    ],
    'optimism': [
        'hope', 'hopeful', 'optimistic', 'better days', 'bright future',
        'positive', 'look forward', 'it will be okay', 'promising', 'confident'
    ],
    'amusement': [
        'funny', 'hilarious', 'lol', 'haha', 'lmao', 'rofl', 'joke', 'chuckle',
        'humor', 'laugh', 'giggle', 'comedic'
    ],
    'relief': [
        'relieved', 'relief', 'thank goodness', 'glad it is over', 'weight lifted',
        'breathe easily', 'at ease', 'phew'
    ],
    'admiration': [
        'admire', 'inspired', 'impressive', 'role model', 'hero', 'respect',
        'look up to', 'phenomenal', 'brilliant', 'genius'
    ],
    'pride': [
        'proud', 'accomplished', 'achieved', 'milestone', 'victory', 'won',
        'hard work paid off', 'success', 'triumph'
    ],
    'remorse': [
        'guilty', 'guilt', 'sorry', 'apologize', 'regret', 'shame', 'my fault',
        'forgive me', 'remorseful'
    ],
    'disappointment': [
        'disappointed', 'disappointing', 'let down', 'bummed', 'frustrating',
        'didnt work out', "didn't work out", 'wasted effort'
    ],
    'annoyance': [
        'annoyed', 'irritated', 'bothered', 'frustrated', 'aggravated', 'bugging',
        'getting on my nerves', 'nuisance', 'pet peeve'
    ],
    'confusion': [
        'confused', 'confusing', 'puzzled', 'dont understand', "don't understand",
        'lost', 'perplexed', 'baffled', 'what does this mean', 'mixed signals'
    ],
    'curiosity': [
        'curious', 'wondering', 'interested', 'why does', 'how come', 'inquisitive',
        'tell me more', 'want to know', 'explore'
    ],
    'surprise': [
        'surprised', 'shocked', 'unexpected', 'astonished', 'stunned', 'speechless',
        'wow', 'omg', 'unbelievable', 'whoa'
    ],
    'disgust': [
        'disgusting', 'gross', 'nasty', 'repulsed', 'sickening', 'revolting', 'yuck'
    ],
    'embarrassment': [
        'embarrassed', 'awkward', 'cringe', 'humiliated', 'mortified', 'fool of myself'
    ],
    'approval': [
        'agree', 'agreed', 'correct', 'right', 'good job', 'well done', 'approve',
        'sounds good', 'fair enough'
    ],
    'disapproval': [
        'disagree', 'wrong', 'unacceptable', 'disapprove', 'objection', 'bad idea',
        'not cool'
    ],
    'desire': [
        'desire', 'wish', 'crave', 'craving', 'longing', 'want', 'wishing'
    ],
    'realization': [
        'realized', 'realize', 'figured out', 'it hit me', 'aha', 'makes sense now',
        'suddenly understood'
    ],
}


def detect_mood(text):
    """
    Detect the dominant emotion in the given text using lightweight,
    high-speed pattern and keyword matching (0 extra RAM overhead, ideal for cloud deploy).

    Returns:
        tuple: (emotion_label, confidence_score)
    """
    if not text or not isinstance(text, str):
        return 'neutral', 0.50

    cleaned = text.lower().strip()
    words = set(re.findall(r'\b[a-z\']+\b', cleaned))

    scores = {}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if ' ' in kw:
                if kw in cleaned:
                    score += 2.0
            elif kw in words:
                score += 1.0

        if score > 0:
            scores[emotion] = score

    if not scores:
        return 'neutral', 0.70

    # Pick dominant emotion
    top_emotion = max(scores, key=scores.get)
    max_score = scores[top_emotion]

    # Calculate normalized confidence
    confidence = min(0.60 + (max_score * 0.15), 0.95)

    return top_emotion, round(confidence, 2)
