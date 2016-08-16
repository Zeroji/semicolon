"""Cipher cog for semicolon."""
import math
import random
import string
import gearbox
cog = gearbox.Cog()


def shift(letter, number):
    """Shift a letter by a numeric offset."""
    if 'A' <= letter <= 'Z':
        return chr((ord(letter) - ord('A') + number) % 26 + ord('A'))
    if 'a' <= letter <= 'z':
        return chr((ord(letter) - ord('a') + number) % 26 + ord('a'))
    return letter  # If it's not a letter don't change it


def encode_7879(message, reverse=False):
    """Encode text using 7879's custom cipher."""
    return ' '.join([
        ''.join([
            shift(char, (-1 if reverse else 1) * (i + 1) * len(word)) for i, char in enumerate(word)
        ]) for word in message.split(' ')
    ])


def encode_vigenere(message, key, reverse=False):
    """Encode a text with Vigenere cipher."""
    key = key.upper()
    result = ''
    i = 0
    for char in message:
        if 'A' <= char <= 'Z' or 'a' <= char <= 'z':
            result += shift(char, (-1 if reverse else 1) * (ord(key[i]) - ord('A')))
            i = (i + 1) % len(key)
        else:
            result += char
    return result


MORSE = {'0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
         '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
         'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.',
         'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.',
         'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-',
         'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..'}


def encode_morse(text, reverse=False):
    """Encode text into Morse code."""
    result = ''
    if not reverse:
        for char in text.upper():
            if char in MORSE:
                result += MORSE[char] + ' '
            elif char == ' ':
                result += '/ '
    else:
        text = text.replace('0', '.').replace('1', '-')
        for word in text.split():
            for char, mrs in MORSE.items():
                if word == mrs:
                    result += char
                    break
            if word == '/':
                result += ' '
    return result.strip()


def encode_cipher_box(text, size=0, reverse=False):
    """Encode text using cipher boxes."""
    if size == 0:
        size = math.ceil(math.sqrt(len(text)))
        length = size
    else:
        length = math.ceil(len(text) / size)
    if reverse:
        size, length = length, size
    mat = [''] * size
    for i in range(0, size * length, size):
        for j in range(size):
            mat[j] += text[i+j] if i + j < len(text) else random.choice(text)
    return ''.join(mat)


def decode_null(pattern, text):
    """Decode text with the null cipher."""
    i = 0
    result = ''
    for word in text.split():
        result += word.strip('.,;:!?')[pattern[i]]
        i = (i + 1) % len(pattern)
    return result


def encode_mixed_alphabet(key, text, reverse=False):
    """Encode using a mixed alphabet (ZEBRAS-like)."""
    key = ''.join([a for a in key.upper() if a in string.ascii_uppercase])
    key += ''.join([a for a in string.ascii_uppercase if a not in key])
    return encode_substitute(key, text, reverse)


def encode_substitute(alphabet, text, reverse=False):
    """Encode using alphabet substitution."""
    result = ''
    source = string.ascii_uppercase
    alphabet = alphabet.upper()
    if reverse:
        source, alphabet = alphabet, source
    for char in text:
        lower = 'a' <= char <= 'z'
        char = char.upper()
        if 'A' <= char <= 'Z':
            char = alphabet[source.find(char)]
        if lower:
            char = char.lower()
        result += char
    return result


class Polybius:
    """Use Polybius squares for ciphers."""

    def __init__(self, size=5, replace='J', replace_by='I'):
        """Initialization."""
        self.size = size
        self.mat = [[None] * size for _ in range(size)]
        self.replace = replace or ''
        self.replace_by = replace_by or ''

    def fill(self, alphabet='ABCDEFGHIKLMNOPQRSTUVWXYZ'):
        """Initialize the cipher."""
        for x in range(self.size):
            for y in range(self.size):
                self.mat[x][y] = alphabet[x * self.size + y]

    def encode(self, letter):
        """Encode a letter."""
        letter = letter.upper()
        if letter == self.replace:
            letter = self.replace_by
        for x in range(self.size):
            for y in range(self.size):
                if self.mat[x][y] == letter:
                    return ((x+1), (y+1))

    def decode(self, x, y):
        """Decode a letter."""
        if 0 < x <= self.size and 0 < y <= self.size:
            return self.mat[x-1][y-1]


def encode_tap_code(text, reverse=False):
    """Encode text using the tap code."""
    square = Polybius(5, 'K', 'C')
    square.fill()
    if not reverse:
        result = ''
        for char in text.replace(' ', 'X').upper():
            code = square.encode(char)
            if code is not None:
                result += '%s %s ' % ('.' * code[0], '.' * code[1])
        return result
    else:
        words = text.split()
        if len(words) % 2:
            return
        result = ''
        for i in range(0, len(words), 2):
            char = square.decode(len(words[i]), len(words[i+1]))
            if char is not None:
                result += char
        return result

@cog.command(fulltext=True)
def atbash(text):
    """Encode text using the Atbash cipher."""
    result = ''
    for char in text:
        if 'A' <= char <= 'Z':
            result += chr(ord('A') + ord('Z') - ord(char))
        elif 'a' <= char <= 'z':
            result += chr(ord('a') + ord('z') - ord(char))
        else:
            result += char
    return result

@cog.command(fulltext=True, flags='de')
def rot7879(text, flags):
    """Encode text using 7879's custom cipher."""
    if 'd' in flags and 'e' in flags:
        return 'Mutually exclusive flags: -d and -e'
    return encode_7879(text, reverse='d' in flags)

@cog.command(fulltext=True, flags='de')
@cog.alias('vig')
def vigenere(key, text, flags):
    """Encode a text with Vigenere cipher."""
    if 'd' in flags and 'e' in flags:
        return 'Mutually exclusive flags: -d and -e'
    return encode_vigenere(text, key, reverse='d' in flags)

@cog.command(fulltext=True, flags='de')
def morse(text, flags):
    """Encode text into Morse code."""
    if 'd' in flags and 'e' in flags:
        return 'Mutually exclusive flags: -d and -e'
    return encode_morse(text, reverse='d' in flags)

@cog.command(fulltext=True)
def null(pattern, text=''):
    """Decode text with the null cipher."""
    try:
        patt = [int(x.strip()) for x in pattern.split(',')]
    except ValueError:
        patt = [0]
        text = '%s %s' % (pattern, text)
    else:
        for i, index in enumerate(patt):
            if index > 0:
                patt[i] = index-1
    return decode_null(patt, text)

@cog.command(fulltext=True, flags='de')
def box(size, flags, text=''):
    """Encode text using cipher boxes."""
    if 'd' in flags and 'e' in flags:
        return 'Mutually exclusive flags: -d and -e'
    try:
        size = int(size)
    except ValueError:
        text = size
        size = 0
    return encode_cipher_box(text, size, reverse='d' in flags)

@cog.command(fulltext=True)
def pad_block(size, text):
    """Format text into blocks of letters."""
    size = int(size)
    text = ''.join([c for c in text.upper() if c in string.ascii_uppercase])
    while len(text) % size:
        text += random.choice(text)
    return ' '.join([text[i:i + size] for i in range(0, len(text), size)])

@cog.command(fulltext=True, flags='de')
def mixed(key, text, flags):
    """Encode using a mixed alphabet (ZEBRAS-like)."""
    if 'd' in flags and 'e' in flags:
        return 'Mutually exclusive flags: -d and -e'
    return encode_mixed_alphabet(key, text, reverse='d' in flags)

@cog.command(fulltext=True, flags='de')
def subs(alpha, text, flags):
    """Encode using alphabet substitution."""
    if 'd' in flags and 'e' in flags:
        return 'Mutually exclusive flags: -d and -e'
    return encode_substitute(alpha, text)

@cog.command(fulltext=True, flags='de')
def taptap(text, flags):
    """Encode text using the tap code."""
    if 'd' in flags and 'e' in flags:
        return 'Mutually exclusive flags: -d and -e'
    return encode_tap_code(text, reverse='d' in flags)


# TODO hash functions (md5, sha1/224/256/384/512)
# TODO base conversion (2, 10, 16, 64, 256)
# TODO Caesar cipher (ROT(@))
