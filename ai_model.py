import re
from collections import Counter
import numpy as np
import langdetect
from langdetect import detect
import warnings

# Ignore langdetect warnings
warnings.filterwarnings('ignore')


def analyze_frequencies(text):
    """Analyze character frequencies in the text"""
    # Clean the text (keep only letters)
    clean_text = re.sub(r'[^a-zA-ZÀ-ÿ]', '', text.lower())

    if not clean_text:
        return {}

    # Count letter occurrences
    counter = Counter(clean_text)
    total = len(clean_text)

    # Calculate frequencies
    frequencies = {char: count / total for char, count in counter.items()}

    # Sort frequencies in descending order
    sorted_freq = dict(sorted(frequencies.items(), key=lambda x: x[1], reverse=True))

    return sorted_freq


def detect_language(text):
    """Detect the language of the text"""
    clean_text = re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', text)

    if len(clean_text) < 10:
        return "unknown (text too short)"

    try:
        lang_code = detect(clean_text)
        # Convert language codes to full names
        lang_names = {
            'fr': 'French',
            'en': 'English',
            'es': 'Spanish',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'nl': 'Dutch',
            'ru': 'Russian',
            'ja': 'Japanese',
            'zh-cn': 'Chinese',
            'ar': 'Arabic'
        }
        return lang_names.get(lang_code, lang_code)
    except:
        return "unknown"


def generate_visualizations(text, visualization_type):
    """Generate visualization data for text analysis"""
    # Text cleaning
    clean_text = re.sub(r'[^a-zA-ZÀ-ÿ]', '', text.lower())

    if visualization_type == 'frequency':
        # Letter frequency analysis
        frequencies = analyze_frequencies(clean_text)

        # Format data for graph
        labels = list(frequencies.keys())
        values = list(frequencies.values())

        return {
            'type': 'bar',
            'labels': labels,
            'values': values,
            'title': 'Letter Frequency Analysis'
        }

    elif visualization_type == 'bigram':
        # Bigram (letter pair) analysis
        bigrams = [clean_text[i:i + 2] for i in range(len(clean_text) - 1)]

        if not bigrams:
            return {'error': 'Text too short for bigram analysis'}

        counter = Counter(bigrams)

        # Take top 20 most frequent bigrams
        top_bigrams = counter.most_common(20)

        labels = [b[0] for b in top_bigrams]
        values = [b[1] / len(bigrams) for b in top_bigrams]

        return {
            'type': 'bar',
            'labels': labels,
            'values': values,
            'title': 'Most Frequent Bigrams'
        }

    elif visualization_type == 'entropy':
        # Entropy calculation on sliding windows
        window_size = 20
        if len(clean_text) < window_size:
            return {'error': 'Text too short for entropy analysis'}

        entropy_values = []

        for i in range(len(clean_text) - window_size + 1):
            window = clean_text[i:i + window_size]
            entropy = calculate_entropy(window)
            entropy_values.append(entropy)

        return {
            'type': 'line',
            'labels': list(range(len(entropy_values))),
            'values': entropy_values,
            'title': 'Text Entropy (Sliding Window)'
        }

    elif visualization_type == 'autocorrelation':
        # Autocorrelation to detect periodic patterns
        if len(clean_text) < 30:
            return {'error': 'Text too short for autocorrelation analysis'}

        # Convert text to numeric values (a=0, b=1, etc.)
        text_values = [ord(c) - ord('a') for c in clean_text if 'a' <= c <= 'z']

        # Calculate autocorrelation up to a shift of 20
        max_shift = min(20, len(text_values) // 2)
        autocorr = []

        for shift in range(1, max_shift + 1):
            corr = np.corrcoef(text_values[:-shift], text_values[shift:])[0, 1]
            autocorr.append(corr if not np.isnan(corr) else 0)

        return {
            'type': 'line',
            'labels': list(range(1, max_shift + 1)),
            'values': autocorr,
            'title': 'Autocorrelation (Key Length Detection)'
        }

    else:
        return {'error': 'Unsupported visualization type'}


def calculate_entropy(text):
    """Calculate text entropy"""
    if not text:
        return 0

    # Count occurrences
    counter = Counter(text)
    length = len(text)

    # Calculate entropy
    entropy = 0
    for count in counter.values():
        probability = count / length
        entropy -= probability * np.log2(probability)

    return entropy