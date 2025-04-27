import os
import speech_recognition as sr
from groq import Groq
import io
import pygame  # For audio playback
import random
import json
import re

# Load API key
groq = Groq(api_key="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")

recognizer = sr.Recognizer()

# Persistent storage for progress
CORRECT_WORDS_FILE = "correct_words.json"
INCORRECT_WORDS_FILE = "incorrect_words.json"


def load_word_list(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []


def save_word_list(filename, words):
    with open(filename, "w") as f:
        json.dump(words, f)


def generate_therapy_words(correct_words, incorrect_words):
    prompt = (
        "Generate exactly 2 easy (1-syllable), 2 medium (2-syllable), and 1 hard words for a child with speech delay "
        "words should be relative for a kid with autism/down syndrome. Return the result using this exact Python format:\n"
        "easy = ['word1', 'word2']\n"
        "medium = ['word3', 'word4']\n"
        "hard = ['word5']\n"
        f"Avoid these words: {correct_words}\n"
        f"Prioritize these tricky ones for review: {incorrect_words}\n"
        "ONLY REPLY WITH THE LISTS Do not include any notes or explanations. Only return the Python format variables with no additional commentary."
    )

    response = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )

    content = response.choices[0].message.content.strip()

    # Remove unwanted explanations or non-Python output from Groq's response
    clean_content = "\n".join([line for line in content.split("\n") if not line.startswith("Note:") and line.strip()])

    # Execute the AI's Python-style variable assignments
    local_vars = {}
    try:
        exec(clean_content, {}, local_vars)
    except Exception as e:
        print(f"Error executing content: {e}")
        return [], [], []

    easy_words = local_vars.get("easy", [])
    medium_words = local_vars.get("medium", [])
    hard_words = local_vars.get("hard", [])
    return easy_words, medium_words, hard_words


def speak_word_with_groq(word):
    print(f"🔈 Speaking: {word}")
    # Simulated Groq TTS (this can be replaced with a real TTS solution later)
    # Since TTS is removed, we'll skip the TTS part for now.


def play_audio(file_path):
    """Play audio using pygame."""
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()


def transcribe_user_speech(timeout=10):
    with sr.Microphone() as source:
        print("🎤 Speak the word now...")
        audio = recognizer.listen(source, timeout=timeout)
        try:
            print("🧠 Transcribing...")
            text = recognizer.recognize_whisper(audio, model="small", language="en")
            print("📝 You said:", text)
            return text
        except sr.UnknownValueError:
            print("❌ Could not understand.")
            return ""
        except sr.RequestError as e:
            print(f"API error: {e}")
            return ""


def evaluate_pronunciation(target_word, spoken_sentence):
    prompt = f"""
    The child was supposed to say the word: "{target_word}"
    They said: "{spoken_sentence}"

    Assume the role of an AI speech therapist. The user input is determined by speech recognition software which may be inaccurate,
    so be lenient with case, spelling, and extra words. Pass if the target word is present anywhere in the spoken sentence
    (e.g., if the target is "apple", pass for "I said apple pie" or "apple is good").
    Examples:
    - Word: apple, Said: appel pie, Aple is, Opple fruit, apul yum → PASS
    - Word: pin, Said: I spin fast → PASS
    - Word: apple, Said: oranges bananas, anul, annele, apend → FAIL
    Consider that the kids have Down syndrome or speech delay, so be very lenient.
    Only respond with 1 word: either 'PASS' or 'FAIL'. Do not add any extra output.
    """

    response = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def demo_run():
    print("📚 Loading progress...")
    correct_words = load_word_list(CORRECT_WORDS_FILE)
    incorrect_words = load_word_list(INCORRECT_WORDS_FILE)

    print("📚 Generating new words...")
    easy, medium, hard = generate_therapy_words(correct_words, incorrect_words)
    all_words = easy + medium + hard

    session_correct = []
    session_incorrect = []

    for word in all_words:
        print(f"🎯 Your word: {word}")
        speak_word_with_groq(word)

        user_word = transcribe_user_speech()
        if user_word:
            result = evaluate_pronunciation(word, user_word)
            print("✅ Result:", result)

            if "pass" in result.lower():
                session_correct.append(word)
            else:
                session_incorrect.append(word)

    # Update persistent lists
    correct_words = list(set(correct_words + session_correct))
    incorrect_words = list(set(incorrect_words + session_incorrect))

    save_word_list(CORRECT_WORDS_FILE, correct_words)
    save_word_list(INCORRECT_WORDS_FILE, incorrect_words)

    print("🏁 Session complete!")
    print("✔️ Correct words:", session_correct)
    print("❌ Words to improve:", session_incorrect)


if __name__ == "__main__":
    demo_run()