import re
import base64
import numpy as np
from collections import Counter
import langdetect
from langdetect import detect
import warnings
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

warnings.filterwarnings('ignore')

# Enhanced French letter frequencies (including accented characters)
FRENCH_LETTER_FREQ = {
    'a': 0.0811, 'b': 0.0081, 'c': 0.0338, 'd': 0.0367, 'e': 0.1578,
    'f': 0.0106, 'g': 0.0107, 'h': 0.0074, 'i': 0.0724, 'j': 0.0031,
    'k': 0.0008, 'l': 0.0546, 'm': 0.0301, 'n': 0.0713, 'o': 0.0536,
    'p': 0.0301, 'q': 0.0099, 'r': 0.0671, 's': 0.0793, 't': 0.0726,
    'u': 0.0599, 'v': 0.0131, 'w': 0.0011, 'x': 0.0038, 'y': 0.0031,
    'z': 0.0015,
    'à': 0.0045, 'â': 0.0012, 'ç': 0.0018, 'è': 0.0027, 'é': 0.0152,
    'ê': 0.0018, 'ë': 0.0001, 'î': 0.0006, 'ï': 0.0001, 'ô': 0.0008,
    'ù': 0.0006, 'û': 0.0006, 'ü': 0.0001, 'ÿ': 0.0001
}

# Common French words for better detection
COMMON_FRENCH_WORDS = {
    'le', 'la', 'les', 'un', 'une', 'des', 'et', 'est', 'dans', 'que',
    'pour', 'avec', 'sur', 'pas', 'vous', 'nous', 'ils', 'elle', 'mais',
    'son', 'sa', 'ses', 'aux', 'au', 'du', 'de', 'en', 'par', 'qui',
    'quoi', 'quand', 'comment', 'pourquoi', 'oui', 'non', 'je', 'tu'
}


def clean_text(text):
    """Normalize and clean text for analysis"""
    text = text.lower()
    text = re.sub(r'[^a-zà-ÿ]', '', text)
    return text


def analyze_frequencies(text):
    """Analyze letter frequencies in the text"""
    # Clean the text (keep only letters)
    text = text.lower()
    clean_text_str = ''.join(char for char in text if char.isalpha())

    if not clean_text_str:
        return {}

    # Count letter occurrences
    letter_counts = {}
    total_letters = len(clean_text_str)

    for char in clean_text_str:
        letter_counts[char] = letter_counts.get(char, 0) + 1

    # Calculate frequencies
    frequencies = {char: count / total_letters for char, count in letter_counts.items()}

    # Sort frequencies in descending order
    sorted_freq = dict(sorted(frequencies.items(), key=lambda x: x[1], reverse=True))

    return sorted_freq


def get_letter_frequency(text):
    """Calculate letter frequencies with better normalization"""
    clean_txt = clean_text(text)
    if not clean_txt:
        return {}
    counter = Counter(clean_txt)
    total = sum(counter.values())
    return {char: count / total for char, count in counter.items()}


def index_of_coincidence(text):
    """More accurate index of coincidence calculation"""
    clean_txt = clean_text(text)
    if len(clean_txt) <= 1:
        return 0
    n = len(clean_txt)
    freqs = Counter(clean_txt)
    sum_fi = sum(f * (f - 1) for f in freqs.values())
    return sum_fi / (n * (n - 1))


def detect_cipher(text):
    """Improved cipher detection with better heuristics"""
    # Handle edge cases
    if not text or len(text.strip()) == 0:
        return {'type': 'plaintext', 'confidence': 0.9, 'key': None}

    # Check for base64
    if re.match(r'^[A-Za-z0-9+/=]+$', text) and len(text) % 4 == 0:
        try:
            decoded = base64.b64decode(text).decode('utf-8')
            if len(decoded) > 0 and any(c.isprintable() for c in decoded):
                return {'type': 'base64', 'confidence': 0.95, 'key': None}
        except:
            pass

    clean_input = clean_text(text)
    if len(clean_input) < 10:
        return {'type': 'plaintext', 'confidence': 0.5, 'key': None}

    # Compute index of coincidence
    ioc = index_of_coincidence(clean_input)

    # Caesar and Vigenère checks
    caesar_key = find_caesar_key(clean_input)
    caesar_decrypted = caesar_decrypt(clean_input, caesar_key)

    vigenere_key = find_vigenere_key(clean_input)
    vigenere_decrypted = vigenere_decrypt(clean_input, vigenere_key)

    # Score decrypted results
    caesar_score = score_text_french(caesar_decrypted)
    vigenere_score = score_text_french(vigenere_decrypted)

    # Determine most likely cipher
    if caesar_score > vigenere_score and caesar_score > -1:
        return {'type': 'caesar', 'confidence': 0.8, 'key': caesar_key}
    elif vigenere_score > caesar_score and vigenere_score > -1:
        return {'type': 'vigenere', 'confidence': 0.8, 'key': vigenere_key}

    # Check for Playfair
    playfair_key = "KEYWORD"  # Default key for detection
    playfair_decrypted = playfair_decrypt(clean_input, playfair_key)
    playfair_score = score_text_french(playfair_decrypted)

    if playfair_score > caesar_score and playfair_score > vigenere_score:
        return {'type': 'playfair', 'confidence': 0.7, 'key': playfair_key}

    return {'type': 'plaintext', 'confidence': 0.9, 'key': None}


def caesar_encrypt(text, shift):
    """Caesar encryption implementation"""
    result = []
    for char in text.lower():
        if 'a' <= char <= 'z':
            # Apply the shift to alphabetic characters
            result.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
        else:
            # Keep non-alphabetic characters unchanged
            result.append(char)
    return ''.join(result)


def caesar_decrypt(text, shift):
    """Caesar decryption implementation"""
    return caesar_encrypt(text, -shift)


def vigenere_encrypt(text, key):
    """Vigenère encryption implementation"""
    # Check for empty inputs
    if not text:
        return ""
    if not key:
        raise ValueError("Key cannot be empty for Vigenère cipher")

    # Filter key to only include valid alphabetic characters
    key = ''.join(c for c in key.lower() if 'a' <= c <= 'z')
    if not key:
        raise ValueError("Key must contain at least one alphabetic character")

    result = []
    key_index = 0
    key_length = len(key)

    for char in text.lower():
        if 'a' <= char <= 'z':  # Encrypt only alphabetic characters
            # Get the shift value from the key character
            shift = ord(key[key_index % key_length]) - ord('a')
            # Apply the shift to the current character
            encrypted_char = chr(((ord(char) - ord('a') + shift) % 26) + ord('a'))
            result.append(encrypted_char)
            key_index += 1  # Only increment key index for letters
        else:
            result.append(char)  # Keep other characters unchanged

    return ''.join(result)


def vigenere_decrypt(text, key):
    """Vigenère decryption implementation"""
    # Check for empty inputs
    if not text:
        return ""
    if not key:
        raise ValueError("Key cannot be empty for Vigenère cipher")

    # Filter key to only include valid alphabetic characters
    key = ''.join(c for c in key.lower() if 'a' <= c <= 'z')
    if not key:
        raise ValueError("Key must contain at least one alphabetic character")

    result = []
    key_index = 0
    key_length = len(key)

    for char in text.lower():
        if 'a' <= char <= 'z':  # Decrypt only alphabetic characters
            # Get the shift value from the key character
            shift = ord(key[key_index % key_length]) - ord('a')
            # Apply the reverse shift to the current character
            decrypted_char = chr(((ord(char) - ord('a') - shift) % 26) + ord('a'))
            result.append(decrypted_char)
            key_index += 1  # Only increment key index for letters
        else:
            result.append(char)  # Keep other characters unchanged

    return ''.join(result)


# RSA Encryption and Decryption
def generate_rsa_keys():
    """Generate RSA key pair"""
    # Generate a 2048-bit RSA key pair
    key = RSA.generate(2048)

    # Export the private key in PEM format
    private_key = key.export_key().decode('utf-8')

    # Export the public key in PEM format
    public_key = key.publickey().export_key().decode('utf-8')

    return {'private_key': private_key, 'public_key': public_key}


def rsa_encrypt(text, public_key_pem):
    """RSA Encryption using public key"""
    try:
        # Import the public key
        public_key = RSA.import_key(public_key_pem)

        # Create a cipher object using the public key
        cipher = PKCS1_OAEP.new(public_key)

        # Break the text into chunks of appropriate size
        text_bytes = text.encode('utf-8')
        max_length = 190  # A safe size for RSA 2048-bit
        chunks = [text_bytes[i:i + max_length] for i in range(0, len(text_bytes), max_length)]

        # Encrypt each chunk
        encrypted_chunks = [cipher.encrypt(chunk) for chunk in chunks]

        # Combine encrypted chunks and encode them in base64
        combined = b''.join(encrypted_chunks)
        encoded = base64.b64encode(combined).decode('utf-8')

        return encoded
    except Exception as e:
        return f"Encryption error: {str(e)}"


def rsa_decrypt(ciphertext, private_key_pem):
    """RSA Decryption using private key"""
    try:
        # Import the private key
        private_key = RSA.import_key(private_key_pem)

        # Create a cipher object using the private key
        cipher = PKCS1_OAEP.new(private_key)

        # Decode the base64-encoded ciphertext
        ciphertext_bytes = base64.b64decode(ciphertext)

        # Determine the chunk size based on the key size
        chunk_size = private_key.size_in_bytes()

        # Break the ciphertext into chunks of appropriate size
        chunks = [ciphertext_bytes[i:i + chunk_size] for i in range(0, len(ciphertext_bytes), chunk_size)]

        # Decrypt each chunk
        decrypted_chunks = [cipher.decrypt(chunk) for chunk in chunks]

        # Combine decrypted chunks and convert to string
        combined = b''.join(decrypted_chunks)
        decoded = combined.decode('utf-8')

        return decoded
    except Exception as e:
        return f"Decryption error: {str(e)}"


# Playfair Cipher
def prepare_playfair_key(key):
    """Prepare the key for the Playfair cipher"""
    # Convert to uppercase and remove non-alphabet characters
    key = ''.join(filter(str.isalpha, key.upper()))

    # Replace J with I (standard in Playfair)
    key = key.replace('J', 'I')

    # Remove duplicate letters in the key
    key_no_dups = ''
    for char in key:
        if char not in key_no_dups:
            key_no_dups += char

    # Generate the alphabet without J
    alphabet = ''.join([chr(i) for i in range(65, 91) if chr(i) != 'J'])

    # Add remaining letters to the key
    for char in alphabet:
        if char not in key_no_dups:
            key_no_dups += char

    return key_no_dups


def create_playfair_matrix(key):
    """Create the 5x5 Playfair matrix from the key"""
    matrix = []
    for i in range(0, 25, 5):
        matrix.append(key[i:i + 5])
    return matrix


def find_position(matrix, letter):
    """Find the position of a letter in the Playfair matrix"""
    for i in range(5):
        for j in range(5):
            if matrix[i][j] == letter:
                return i, j
    return -1, -1  # Should never happen if letter is in the alphabet


def playfair_encrypt(text, key):
    """Encrypt text using the Playfair cipher"""
    # Prepare the key and create the matrix
    prepared_key = prepare_playfair_key(key)
    matrix = create_playfair_matrix(prepared_key)

    # Prepare the text (uppercase, remove non-alphabet, replace J with I)
    text = ''.join(filter(str.isalpha, text.upper())).replace('J', 'I')

    # If the text has an odd length, append 'X'
    if len(text) % 2 != 0:
        text += 'X'

    # Split the text into digraphs (pairs of letters)
    digraphs = []
    i = 0
    while i < len(text):
        # If the same letter appears in a pair, insert 'X'
        if i + 1 < len(text) and text[i] == text[i + 1]:
            digraphs.append(text[i] + 'X')
            i += 1
        else:
            if i + 1 < len(text):
                digraphs.append(text[i:i + 2])
            i += 2

    # Encrypt each digraph
    encrypted_text = ''
    for digraph in digraphs:
        row1, col1 = find_position(matrix, digraph[0])
        row2, col2 = find_position(matrix, digraph[1])

        # Same row: take the letter to the right (wrapping around)
        if row1 == row2:
            encrypted_text += matrix[row1][(col1 + 1) % 5] + matrix[row2][(col2 + 1) % 5]
        # Same column: take the letter below (wrapping around)
        elif col1 == col2:
            encrypted_text += matrix[(row1 + 1) % 5][col1] + matrix[(row2 + 1) % 5][col2]
        # Rectangle: take the letter in the same row but the column of the other letter
        else:
            encrypted_text += matrix[row1][col2] + matrix[row2][col1]

    return encrypted_text


def playfair_decrypt(ciphertext, key):
    """Decrypt text using the Playfair cipher"""
    # Prepare the key and create the matrix
    prepared_key = prepare_playfair_key(key)
    matrix = create_playfair_matrix(prepared_key)

    # Prepare the ciphertext (uppercase, remove non-alphabet)
    ciphertext = ''.join(filter(str.isalpha, ciphertext.upper())).replace('J', 'I')

    # Split the ciphertext into digraphs
    digraphs = [ciphertext[i:i + 2] for i in range(0, len(ciphertext), 2)]

    # Decrypt each digraph
    decrypted_text = ''
    for digraph in digraphs:
        row1, col1 = find_position(matrix, digraph[0])
        row2, col2 = find_position(matrix, digraph[1])

        # Same row: take the letter to the left (wrapping around)
        if row1 == row2:
            decrypted_text += matrix[row1][(col1 - 1) % 5] + matrix[row2][(col2 - 1) % 5]
        # Same column: take the letter above (wrapping around)
        elif col1 == col2:
            decrypted_text += matrix[(row1 - 1) % 5][col1] + matrix[(row2 - 1) % 5][col2]
        # Rectangle: take the letter in the same row but the column of the other letter
        else:
            decrypted_text += matrix[row1][col2] + matrix[row2][col1]

    return decrypted_text


def find_caesar_key(text):
    """Improved Caesar key detection"""
    best_score = float('-inf')
    best_key = 0

    for shift in range(26):
        decrypted = caesar_decrypt(text, shift)
        score = score_text_french(decrypted)

        if score > best_score:
            best_score = score
            best_key = shift

    return best_key


def find_vigenere_key(text, max_key_length=10):
    """Improved Vigenère key detection"""
    # Common keys for initial tries
    common_keys = ['cle', 'secret', 'code', 'mot', 'france']

    for key in common_keys:
        decrypted = vigenere_decrypt(text, key)
        if score_text_french(decrypted) > -0.5:
            return key

    # If no common key works, return a default
    return 'secret'


def score_text_french(text):
    """Score text based on French language characteristics"""
    freq = get_letter_frequency(text)

    # Compare text frequency with expected French frequencies
    frequency_score = -sum(
        abs(freq.get(char, 0) - FRENCH_LETTER_FREQ.get(char, 0))
        for char in FRENCH_LETTER_FREQ
    )

    # Bonus for common French words
    words = re.findall(r'\w+', text.lower())
    word_score = sum(1 for word in words if word in COMMON_FRENCH_WORDS) * 0.2

    return frequency_score + word_score


def detect_language(text):
    """Language detection with fallback"""
    try:
        return detect(text)
    except:
        return 'fr'  # Default to French


def encrypt_message(text, cipher_type, key=None):
    """Unified encryption method"""
    try:
        text = text.lower()

        if cipher_type == 'caesar':
            # Ensure key is an integer with default value
            shift = 3  # Default shift if key is None
            if key is not None:
                shift = int(key)
            return caesar_encrypt(text, shift)

        elif cipher_type == 'vigenere':
            # Ensure key is a valid string with default value
            if key is None or not isinstance(key, str) or not key:
                key = 'secret'  # Default key
            return vigenere_encrypt(text, key)

        elif cipher_type == 'base64':
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')

        elif cipher_type == 'playfair':
            key = key or 'KEYWORD'
            return playfair_encrypt(text, key)

        elif cipher_type == 'rsa':
            # For RSA, the key should be a public key in PEM format
            if not key:
                # Generate a temporary key pair
                keys = generate_rsa_keys()
                key = keys['public_key']
            return rsa_encrypt(text, key)

        else:
            return text

    except Exception as e:
        # Log the error and return a helpful message
        print(f"Encryption error for {cipher_type}: {str(e)}")
        return f"Error encrypting with {cipher_type}: {str(e)}"


def decrypt_message(text, cipher_type=None, key=None):
    """Unified decryption method"""
    try:
        # If no cipher type provided, try to detect
        if not cipher_type:
            detection = detect_cipher(text)
            cipher_type = detection['type']
            key = key or detection.get('key')

        if cipher_type == 'caesar':
            shift = 3  # Default shift
            if key is not None:
                shift = int(key)
            text = clean_text(text)  # Ensure text is cleaned before decryption
            return caesar_decrypt(text, shift)

        elif cipher_type == 'vigenere':
            if key is None or not isinstance(key, str) or not key:
                key = 'secret'  # Default key
            text = clean_text(text)  # Ensure text is cleaned before decryption
            return vigenere_decrypt(text, key)

        elif cipher_type == 'base64':
            # Restore original text before base64 decoding
            text_with_padding = text + '=' * ((4 - len(text) % 4) % 4)
            return base64.b64decode(text_with_padding.encode('utf-8')).decode('utf-8')

        elif cipher_type == 'playfair':
            key = key or 'KEYWORD'
            return playfair_decrypt(text, key)

        elif cipher_type == 'rsa':
            # For RSA, the key should be a private key in PEM format
            if not key:
                return "RSA decryption requires a private key"
            return rsa_decrypt(text, key)

        else:
            return text

    except Exception as e:
        # Log the error and return a helpful message
        print(f"Decryption error for {cipher_type}: {str(e)}")
        return f"Error decrypting with {cipher_type}: {str(e)}"