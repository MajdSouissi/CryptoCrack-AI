from cipher_utils import encrypt_message, decrypt_message


def test_cipher_difference():
    """Test that Caesar and Vigenère ciphers produce different results"""

    # Test word
    test_word = "bonjour"
    print(f"Original text: {test_word}")

    # Caesar with shift 3
    caesar_key = 3
    caesar_encrypted = encrypt_message(test_word, 'caesar', caesar_key)
    print(f"\nCaesar (shift={caesar_key}):")
    print(f"Encrypted: {caesar_encrypted}")
    print(f"Decrypted: {decrypt_message(caesar_encrypted, 'caesar', caesar_key)}")

    # Vigenère with key "secret"
    vigenere_key = "secret"
    vigenere_encrypted = encrypt_message(test_word, 'vigenere', vigenere_key)
    print(f"\nVigenère (key='{vigenere_key}'):")
    print(f"Encrypted: {vigenere_encrypted}")
    print(f"Decrypted: {decrypt_message(vigenere_encrypted, 'vigenere', vigenere_key)}")

    # Compare results
    print("\nResults comparison:")
    print(f"Caesar encrypted: {caesar_encrypted}")
    print(f"Vigenère encrypted: {vigenere_encrypted}")
    print(f"Are they different? {'Yes' if caesar_encrypted != vigenere_encrypted else 'No'}")

    # Expected values calculation (for verification)
    print("\nDetailed Vigenère encryption steps:")
    key = "secret"
    print(f"Key: {key}")
    text = "bonjour"

    result = []
    key_index = 0

    for char in text:
        if 'a' <= char <= 'z':
            # Get the shift from the key
            shift = ord(key[key_index % len(key)]) - ord('a')
            print(f"Character: '{char}', Key letter: '{key[key_index % len(key)]}', Shift: {shift}")

            # Calculate encrypted character
            encrypted_char = chr(((ord(char) - ord('a') + shift) % 26) + ord('a'))
            print(f"  Calculation: ({ord(char)}-{ord('a')}+{shift})%26+{ord('a')} = {encrypted_char}")

            result.append(encrypted_char)
            key_index += 1
        else:
            result.append(char)

    expected_vigenere = ''.join(result)
    print(f"\nManually calculated Vigenère result: {expected_vigenere}")
    print(f"Does it match our function? {'Yes' if expected_vigenere == vigenere_encrypted else 'No'}")


# Run the test
if __name__ == "__main__":
    test_cipher_difference()