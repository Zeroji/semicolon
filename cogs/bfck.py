"""Brainf*ck interpreter."""
import time
import gearbox
cog = gearbox.Cog()

MEM_SIZE = 30000
MAX_TICK = 200000


@cog.command
def bf(code, word=''):
    code = code.strip(' `\nbf')
    memory = [0] * MEM_SIZE
    head = 0
    code_ptr = 0
    output = ''
    message = ''
    t1 = time.time()
    ticks = 0
    while code_ptr < len(code) and ticks < MAX_TICK:
        ticks += 1
        c = code[code_ptr]
        if c == '+':
            memory[head] += 1
            memory[head] %= 256
        elif c == '-':
            memory[head] -= 1
            memory[head] %= 256
        elif c == '>':
            head += 1
            head %= MEM_SIZE
        elif c == '<':
            head -= 1
            head %= MEM_SIZE
        elif c == '.':
            output += chr(memory[head])
        elif c == ',':
            memory[head] = 0 if len(word) == 0 else ord(word[0])
            word = word[1:]
        elif c == '[':
            if not memory[head]:
                nested = 1
                while nested:
                    code_ptr += 1
                    if code_ptr == len(code):
                        message += 'No matching `]`\n'
                        break
                    if code[code_ptr] == '[':
                        nested += 1
                    if code[code_ptr] == ']':
                        nested -= 1
        elif c == ']':
            if memory[head]:
                nested = 1
                while nested:
                    code_ptr -= 1
                    if code_ptr <= 0:
                        code_ptr = len(code)
                        message += 'No matching `[`\n'
                        break
                    if code[code_ptr] == ']':
                        nested += 1
                    if code[code_ptr] == '[':
                        nested -= 1
        code_ptr += 1
    t2 = time.time() - t1
    status = 'Executed' if ticks < MAX_TICK else 'Aborted'
    if output:
        output = output.replace('`', '\`')
        if len(output) > 1800:
            output = output[:1800] + ' **Too long (%d), truncated to 1800**' % len(output)
        output = '%s\n' % output
    return output + message + status + ' in %d ticks (%.3fs)' % (ticks, t2)
