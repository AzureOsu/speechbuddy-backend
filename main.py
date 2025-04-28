import json
import random
from groq import Groq

groq = Groq(api_key="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")

def load_word_list(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_word_list(filename, word_list):
    with open(filename, 'w') as file:
        json.dump(word_list, file)

def evaluate_pronunciation(target, spoken):
    target = target.lower().strip()
    spoken = spoken.lower().strip()
    

def generate_therapy_words(correct_words, incorrect_words):
    # Sample word lists (simplified)
    easy_words = ["cat", "dog", "bat", "hat", "mat"]
    medium_words = ["jump", "cake", "fish", "ship", "ball"]
    hard_words = ["rocket", "sunset", "garden", "pencil", "window"]

    # Remove known words from the pool
    available_easy = [w for w in easy_words if w not in correct_words and w not in incorrect_words]
    available_medium = [w for w in medium_words if w not in correct_words and w not in incorrect_words]
    available_hard = [w for w in hard_words if w not in correct_words and w not in incorrect_words]

    # Fallback if lists are empty
    if not available_easy:
        available_easy = easy_words
    if not available_medium:
        available_medium = medium_words
    if not available_hard:
        available_hard = hard_words

    # Select 2 easy, 2 medium, 1 hard
    easy = random.sample(available_easy, min(2, len(available_easy)))
    medium = random.sample(available_medium, min(2, len(available_medium)))
    hard = random.sample(available_hard, min(1, len(available_hard)))

    return easy, medium, hard
