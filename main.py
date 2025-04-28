import json
import random

def evaluate_pronunciation(target_word, spoken_word, groq_client):
    prompt =
    f"The child was supposed to say: "{target_word}"
    f'They said: "{spoken_word}"'
    f'Considering that the kid has speech delay and accrediting error to the speech recognition software would you consider the input close enough to the actual word to allow the kid to pass this word, if yes respond with: Congrats youre correct, if wrong then say: Sorry you arent right; keep response brief'
    
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content.strip().lower()
    # Parse the response to return "pass" or "fail" as expected by app.py
    return "pass" if "congrats" in result else "fail"

def load_word_list(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_word_list(filename, word_list):
    with open(filename, 'w') as file:
        json.dump(word_list, file, indent=4)

def generate_therapy_words(correct_words, incorrect_words):
    # Define word difficulty pools
    easy_words = ["cat", "dog", "bat", "hat", "sun"]
    medium_words = ["apple", "banana", "circle", "happy", "table"]
    hard_words = ["elephant", "beautiful", "umbrella", "chocolate", "tomorrow"]

    # Remove words that the user already knows (in correct_words or incorrect_words)
    easy_words = [word for word in easy_words if word not in correct_words and word not in incorrect_words]
    medium_words = [word for word in medium_words if word not in correct_words and word not in incorrect_words]
    hard_words = [word for word in hard_words if word not in correct_words and word not in incorrect_words]

    # Ensure there are enough words to select from
    easy = random.sample(easy_words, min(2, len(easy_words))) if easy_words else ["cat", "dog"]
    medium = random.sample(medium_words, min(2, len(medium_words))) if medium_words else ["apple", "banana"]
    hard = random.sample(hard_words, min(1, len(hard_words))) if hard_words else ["elephant"]

    # Pad with default words if necessary
    while len(easy) < 2:
        easy.append(random.choice(["cat", "dog"]))
    while len(medium) < 2:
        medium.append(random.choice(["apple", "banana"]))
    while len(hard) < 1:
        hard.append("elephant")

    return easy[:2], medium[:2], hard[:1]
