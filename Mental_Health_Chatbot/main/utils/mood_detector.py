import logging

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# Use the GoEmotions model which actually supports 27 emotion labels
# The previous model (twitter-roberta-base-emotion) only supports 4 labels
MODEL_NAME = "SamLowe/roberta-base-go_emotions"

logger.info("Loading mood detection model: %s", MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
logger.info("Mood detection model loaded successfully")

# Correct 27+1 emotion labels for the GoEmotions model
labels = [
    'admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring',
    'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval',
    'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief',
    'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization',
    'relief', 'remorse', 'sadness', 'surprise', 'neutral'
]


def detect_mood(text):
    """
    Detect the dominant emotion in the given text.

    Returns:
        tuple: (emotion_label, confidence_score)
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)

    top_idx = torch.argmax(probs, dim=1).item()
    confidence = probs[0][top_idx].item()

    return labels[top_idx], confidence
