"""Esoteric languages interpreters."""
import time
import gearbox

cog = gearbox.Cog()
_ = cog.gettext

MAX_TICK = 200000
MAX_TIME = 0.5
MAX_SIZE = 1800


class Word:
    """Wrapper for user input."""

    def __init__(self, word):
        self.word = word

    def read(self):
        val = 0
        if len(self.word) > 0:
            val = ord(self.word[0])
            self.word = self.word[1:]
        return val


class Interpreter:
    INIT = -1
    RUN = 0
    DONE = 1
    ERROR = 2
    ABORT = 3

    def __init__(self, code, word):
        self.code = code
        self.word = word
        self.state = Interpreter.INIT
        self.output = ''
        self.message = ''

    def run(self):
        self.state = Interpreter.RUN
        ticks = 0
        start = time.time()
        while self.state == Interpreter.RUN:
            if self.step():
                ticks += 1
            if ticks >= MAX_TICK:
                self.state = Interpreter.ABORT
            if time.time() - start >= MAX_TIME:
                self.state = Interpreter.ABORT
        return self.output, self.state, self.message, ticks, time.time() - start

    def step(self):
        self.state = Interpreter.DONE
        return True

class Brainfuck(Interpreter):
    """Brainfuck interpreter."""
    MEM_SIZE = 30000
    CELL_SIZE = 1<<8 # In bits
    def __init__(self, code, word):
        super().__init__(code, word)
        self.memory = [0] * self.MEM_SIZE
        self.head = 0
        self.code_ptr = 0

    def step(self):
        c = self.code[self.code_ptr]
        if c == '+':
            self.memory[self.head] += 1
            self.memory[self.head] %= self.CELL_SIZE
        elif c == '-':
            self.memory[self.head] -= 1
            self.memory[self.head] %= self.CELL_SIZE
        elif c == '>':
            self.head += 1
            self.head %= self.MEM_SIZE
        elif c == '<':
            self.head -= 1
            self.head %= self.MEM_SIZE
        elif c == '.':
            self.output += chr(self.memory[self.head])
        elif c == ',':
            self.memory[self.head] = self.word.read()
        elif c == '[':
            if not self.memory[self.head]:
                nested = 1
                while nested:
                    self.code_ptr += 1
                    if self.code_ptr >= len(self.code):
                        self.message = _('No matching `]`')
                        self.state = Interpreter.ERROR
                        return
                    if self.code[self.code_ptr] == '[':
                        nested += 1
                    if self.code[self.code_ptr] == ']':
                        nested -= 1
        elif c == ']':
            if self.memory[self.head]:
                nested = 1
                while nested:
                    self.code_ptr -= 1
                    if self.code_ptr < 0:
                        self.message = _('No matching `[`')
                        self.state = Interpreter.ERROR
                        return
                    if self.code[self.code_ptr] == ']':
                        nested += 1
                    if self.code[self.code_ptr] == '[':
                        nested -= 1
        else:
            return
        self.code_ptr += 1
        if self.code_ptr >= len(self.code):
            self.state = Interpreter.DONE
        return True
        
class Stacked_Brainfuck(Interpreter):
    """Stacked brainfuck interpreter"""
    MEM_SIZE = 30000
    CELL_SIZE = 1<<8 # in bits
    def __init__(self, code, word):
        super().__init__(code, word)
        self.memory = [0] * self.MEM_SIZE
        self.head = 0
        self.code_ptr = 0
        self.stack = []
        
    def step(self):
        c = self.code[self.code_ptr]
        if self.stack:
            if c == '$':
                self.stack.pop()
            elif c == '=':
                self.memory[self.head] += self.stack[-1]
            elif c == '_':
                self.memory[self.head] -= self.stack[-1]
            elif c == '}':
                self.memory[self.head] >>= self.stack[-1]
            elif c == '{':
                self.memory[self.head] <<= self.stack[-1]
            elif c == '|':
                self.memory[self.head] |= self.stack[-1]
            elif c == '^':
                self.memory[self.head] ^= self.stack[-1]
            elif c == '&':
                self.memory[self.head] &= self.stack[-1]
            self.memory[self.head] %= self.CELL_SIZE
        if c == '+':
            self.memory[self.head] += 1
            self.memory[self.head] %= self.CELL_SIZE
        elif c == '-':
            self.memory[self.head] -= 1
            self.memory[self.head] %= self.CELL_SIZE
        elif c == '>':
            self.head += 1
            self.head %= self.MEM_SIZE
        elif c == '<':
            self.head -= 1
            self.head %= self.MEM_SIZE
        elif c == '.':
            self.output += chr(self.memory[self.head])
        elif c == ',':
            self.memory[self.head] = self.word.read()
        elif c == '[':
            if not self.memory[self.head]:
                nested = 1
                while nested:
                    self.code_ptr += 1
                    if self.code_ptr >= len(self.code):
                        self.message = _('No matching `]`')
                        self.state = Interpreter.ERROR
                        return
                    if self.code[self.code_ptr] == '[':
                        nested += 1
                    if self.code[self.code_ptr] == ']':
                        nested -= 1
        elif c == ']':
            if self.memory[self.head]:
                nested = 1
                while nested:
                    self.code_ptr -= 1
                    if self.code_ptr < 0:
                        self.message = _('No matching `[`')
                        self.state = Interpreter.ERROR
                        return
                    if self.code[self.code_ptr] == ']':
                        nested += 1
                    if self.code[self.code_ptr] == '[':
                        nested -= 1
        elif c == ')':
            self.stack.append(self.memory[self.head])
        elif c == '(':
            self.memory[self.head] = self.stack.pop() if self.stack else 0
        elif c == '@':
            self.memory[self.head] = self.stack[-1] if self.stack else 0
        self.code_ptr += 1
        if self.code_ptr >= len(self.code):
            self.state = Interpreter.DONE
        return True
        
LANGS = {'bf': Brainfuck,
         'stbf': Stacked_Brainfuck}


@cog.command(fulltext=True, flags={'i': 'Specify input'})
def eso(flags, language, args):
    if language not in LANGS:
        return _('Unknown language, too esoteric')
    lang = LANGS[language]
    word, code = '', args
    if 'i' in flags:
        try:
            word, code = args.split(None, 1)
        except ValueError:
            return 'No input provided'
    word = word.replace('%20', ' ').replace('%27', '%')
    code = code.strip(' \r\n`')
    interpreter = lang(code, Word(word))
    output, state, message, ticks, seconds = interpreter.run()
    output = output.replace('`', '\`')
    if len(output) > MAX_SIZE:
        output = output[:MAX_SIZE] + '**Too long (%d), truncated to %d**' % (len(output), MAX_SIZE)
    if state == Interpreter.ERROR:
        footer = _('Error: ') + message
    else:
        footer = _('{finished} in {ticks} ticks ({seconds:.3f}s)').format(
            finished=_('Aborted') if state == Interpreter.ABORT else _('Executed'),
            ticks=ticks, seconds=seconds)
    return output + '\n' + footer
