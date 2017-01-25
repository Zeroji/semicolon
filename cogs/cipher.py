"""Cipher cog for semicolon."""
import math
import random
import string
import gearbox
import os
cog = gearbox.Cog()
_ = cog.gettext

BIGRAMS = {}
NGRAMS_PATH = 'data/cipher.ngrams/'


@cog.init
def load_files():
    """Load bigram files."""
    if not os.path.exists(NGRAMS_PATH):
        return

    # Files are text files named `language_bigrams.txt` in folder `data/cipher.ngrams`
    # They contain one ngram per line, followed by a space then its count or frequency
    # Example: `EN 4569` then `ER 1532`
    global BIGRAMS
    files = [name for name in os.listdir(NGRAMS_PATH) if 'bigrams' in name]
    for file in files:
        lines = open(NGRAMS_PATH + file).read().splitlines()
        total = sum([int(line.split()[1]) for line in lines])
        lang = file.split('_')[0].lower()
        BIGRAMS[lang] = {}
        for line in lines:
            ngram, freq = line.split()
            BIGRAMS[lang][ngram.upper()] = float(freq) / total


def analyze_frequency(message):
    """Analyze bigram frequency of a message to detect its language.

    Return a sorted list of (score, language) tuples, lower score means higher probability."""

    def first_ngrams(freq_dict, count):
        """Sort a ngram dictionary and return the 'count' most frequent items."""
        freq_list = [(freq, ngram) for ngram, freq in freq_dict.items()]
        freq_list.sort(reverse=True)
        return [ngram for freq, ngram in freq_list[:count]]

    def out_of_place(target, sample):
        """Calculate the out-of-place score of a sample text against a target."""
        distance = 0
        for index, ngram in enumerate(sample):
            try:
                err = abs(index - target.index(ngram))
            except ValueError:
                err = len(target)
            distance += (len(target) - index) * err
        return distance

    bigrams = {}
    bi_count = 0
    for i, char in enumerate(message):
        if char.lower() != char.upper():  # Keep only letters
            char = char.upper()
            if i + 1 < len(message):
                char2 = message[i+1].upper()
                if char2.lower() != char2.upper():
                    bigrams[char + char2] = bigrams.get(char + char2, 0) + 1
                    bi_count += 1
    for bigram in bigrams:
        bigrams[bigram] /= bi_count
    distances = []
    first_bigrams = first_ngrams(bigrams, 40)
    for lang, frequencies in BIGRAMS.items():
        distances.append((out_of_place(first_ngrams(frequencies, 40), first_bigrams), lang))
    distances.sort()
    return distances


def shift(letter, number):
    """Shift a letter by a numeric offset."""
    if 'A' <= letter <= 'Z':
        return chr((ord(letter) - ord('A') + number) % 26 + ord('A'))
    if 'a' <= letter <= 'z':
        return chr((ord(letter) - ord('a') + number) % 26 + ord('a'))
    return letter  # If it's not a letter don't change it


def encode_rot(message, offset, reverse=False):
    """Encode text using Caesar's ROT cipher."""
    result = ''
    for char in message:
        if 'A' <= char <= 'Z' or 'a' <= char <= 'z':
            result += shift(char, -offset if reverse else offset)
        else:
            result += char
    return result


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
                    return (x + 1), (y + 1)

    def decode(self, x, y):
        """Decode a letter."""
        if 0 < x <= self.size and 0 < y <= self.size:
            return self.mat[x-1][y-1]
        return ''


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


@cog.command(fulltext=True, flags={'d': 'decode', 'e': 'encode'})
@cog.alias('rot')
def caesar(offset: int, text, flags):
    """Encode text using Caesar's ROT cipher.

    Use an offset of 0 for automatic detection."""
    if 'd' in flags and 'e' in flags:
        return _('Mutually exclusive flags: -d and -e')
    if offset:
        return encode_rot(text, offset, reverse='d' in flags)
    else:
        scores = [(analyze_frequency(encode_rot(text, off)), off) for off in range(26)]
        scores.sort()
        output = ''
        for freq, offset in scores[:3]:
            output += f"`ROT{offset:02}` {encode_rot(text, offset)} `[{freq[0][1]}]`\n"
        return output


@cog.command(fulltext=True, flags={'d': 'decode', 'e': 'encode'})
def rot7879(text, flags):
    """Encode text using 7879's custom cipher."""
    if 'd' in flags and 'e' in flags:
        return _('Mutually exclusive flags: -d and -e')
    return encode_7879(text, reverse='d' in flags)


@cog.command(fulltext=True, flags={'d': 'decode', 'e': 'encode'})
@cog.alias('vig')
def vigenere(key: 'Vigenere encryption key', text, flags):
    """Encode a text with Vigenere cipher."""
    if 'd' in flags and 'e' in flags:
        return _('Mutually exclusive flags: -d and -e')
    return encode_vigenere(text, key, reverse='d' in flags)


@cog.command(fulltext=True, flags={'d': 'decode', 'e': 'encode'})
def morse(text, flags):
    """Encode text into Morse code."""
    if 'd' in flags and 'e' in flags:
        return _('Mutually exclusive flags: -d and -e')
    return encode_morse(text, reverse='d' in flags)


@cog.command(fulltext=True)
def null(pattern: 'Comma-separated list of numbers (default 0)', text=''):
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


@cog.command(fulltext=True, flags={'d': 'decode', 'e': 'encode'})
def box(size: 'Box size', flags, text=''):
    """Encode text using cipher boxes."""
    if 'd' in flags and 'e' in flags:
        return _('Mutually exclusive flags: -d and -e')
    try:
        size = int(size)
    except ValueError:
        text = size
        size = 0
    return encode_cipher_box(text, size, reverse='d' in flags)


@cog.command(fulltext=True)
def pad_block(size: '"word" size', text):
    """Format text into blocks of letters."""
    size = int(size)
    text = ''.join([c for c in text.upper() if c in string.ascii_uppercase])
    while len(text) % size:
        text += random.choice(text)
    return ' '.join([text[i:i + size] for i in range(0, len(text), size)])


@cog.command(fulltext=True, flags={'d': 'decode', 'e': 'encode'})
def mixed(key: 'Alphabet key (no duplicate letters)', text, flags):
    """Encode using a mixed alphabet (ZEBRAS-like)."""
    if 'd' in flags and 'e' in flags:
        return _('Mutually exclusive flags: -d and -e')
    return encode_mixed_alphabet(key, text, reverse='d' in flags)


@cog.command(fulltext=True, flags={'d': 'decode', 'e': 'encode'})
def subs(alphabet: 'Substitute alphabet (all 26 letters)', text, flags):
    """Encode using alphabet substitution."""
    if 'd' in flags and 'e' in flags:
        return _('Mutually exclusive flags: -d and -e')
    return encode_substitute(alphabet, text)


@cog.command(fulltext=True, flags={'d': 'decode', 'e': 'encode'})
def taptap(text, flags):
    """Encode text using the tap code."""
    if 'd' in flags and 'e' in flags:
        return _('Mutually exclusive flags: -d and -e')
    return encode_tap_code(text, reverse='d' in flags)


@cog.command(fulltext=True)
def language(text):
    """Determine language of text (not all are supported)."""
    distances = analyze_frequency(text)
    upper = distances[0][0] + (distances[-1][0] - distances[0][0]) / 10
    langs = [lang for dist, lang in distances if dist <= upper]
    if len(langs) == 1:
        return _("This message is most likely in {language}").format(language=langs[0])
    elif len(langs) < 3:
        return _("This message seems to be in {language}, or maybe in {language2}").format(language=langs[0],
                                                                                           language2=langs[1])
    else:
        return _("Multiple languages have been detected: {languages}").format(gearbox.pretty(langs, final=_('and')))


# TODO hash functions (md5, sha1/224/256/384/512)
# TODO base conversion (2, 10, 16, 64, 256)
