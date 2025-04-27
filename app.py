from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from groq import Groq
import base64
import random
import json
from gtts import gTTS
from main import evaluate_pronunciation, load_word_list, save_word_list, generate_therapy_words

app = Flask(__name__)

# Initialize Groq client
groq = Groq(api_key="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")

# Persistent storage for progress
CORRECT_WORDS_FILE = "correct_words.json"
INCORRECT_WORDS_FILE = "incorrect_words.json"

# Load initial word lists
correct_words = load_word_list(CORRECT_WORDS_FILE)
incorrect_words = load_word_list(INCORRECT_WORDS_FILE)

# Generate initial therapy words (2 easy, 2 medium, 1 hard)
easy, medium, hard = generate_therapy_words(correct_words, incorrect_words)
session_words = easy + medium + hard  # Exactly 5 words
current_word = None
session_index = 0
streak = 0
session_results = []  # Track correct/incorrect for summary


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    # Calculate stats for the dashboard
    total_attempts = len(correct_words) + len(incorrect_words)
    accuracy = (len(correct_words) / total_attempts * 100) if total_attempts > 0 else 0
    return render_template('dashboard.html',
                           total_attempts=total_attempts,
                           correct_count=len(correct_words),
                           incorrect_count=len(incorrect_words),
                           accuracy=accuracy,
                           best_streak=max(session_results, key=lambda x: x['streak'])[
                               'streak'] if session_results else 0)


@app.route('/app')
def learning_app():
    return render_template('app.html')


@app.route('/practice', methods=['GET'])
def practice():
    global current_word, session_index, session_words, correct_words, incorrect_words
    if session_index >= 5:
        return jsonify({
            'done': True,
            'results': session_results,
            'streak': streak
        })

    current_word = session_words[session_index]
    session_index += 1

    tts = gTTS(text=current_word, lang='en', slow=True)
    tts.save('static/current_word.mp3')

    return jsonify({'word': current_word, 'index': session_index})


@app.route('/submit', methods=['POST'])
def submit():
    global streak, correct_words, incorrect_words, session_results
    audio_data = request.json.get('audio')
    if not audio_data:
        return jsonify({'error': 'No audio data provided'}), 400

    audio_bytes = base64.b64decode(audio_data.split(',')[1])
    temp_audio_path = 'temp_audio.wav'
    with open(temp_audio_path, 'wb') as f:
        f.write(audio_bytes)

    try:
        with open(temp_audio_path, 'rb') as audio_file:
            transcription = groq.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                language="en"
            )
        spoken = transcription.text.strip().lower()
    except Exception as e:
        print(f"Transcription error: {e}")
        return jsonify({'error': 'Transcription failed'}), 500
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

    result = evaluate_pronunciation(current_word, spoken)
    correct = "pass" in result.lower()

    if correct:
        streak += 1
        correct_words.append(current_word)
    else:
        streak = 0
        incorrect_words.append(current_word)

    correct_words = list(set(correct_words))
    incorrect_words = list(set(incorrect_words))
    save_word_list(CORRECT_WORDS_FILE, correct_words)
    save_word_list(INCORRECT_WORDS_FILE, incorrect_words)

    session_results.append({
        'word': current_word,
        'spoken': spoken,
        'correct': correct,
        'streak': streak
    })

    return jsonify({
        'correct': correct,
        'streak': streak,
        'spoken': spoken,
        'result': result
    })


@app.route('/reset', methods=['POST'])
def reset():
    global session_words, session_index, streak, session_results, correct_words, incorrect_words
    easy, medium, hard = generate_therapy_words(correct_words, incorrect_words)
    session_words = easy + medium + hard
    session_index = 0
    streak = 0
    session_results = []
    return jsonify({'status': 'reset'})


@app.route('/static/<path:path>')
def static_file(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
