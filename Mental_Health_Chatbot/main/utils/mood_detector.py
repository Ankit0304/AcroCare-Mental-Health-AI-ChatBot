from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# Load model & tokenizer once at startup
MODEL_NAME = "cardiffnlp/twitter-roberta-base-emotion"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# Emotion labels
labels = ['admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring',
          'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval', 'disgust',
          'embarrassment', 'excitement', 'fear', 'gratitude', 'grief', 'joy', 'love',
          'nervousness', 'optimism', 'pride', 'realization', 'relief', 'remorse',
          'sadness', 'surprise', 'neutral']

def detect_mood(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)
    
    top_idx = torch.argmax(probs, dim=1).item()
    return labels[top_idx], probs[0][top_idx].item()
