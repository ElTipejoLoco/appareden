"""
    Minor string utilities for Appareden.
"""
import re
from .rominfo import S_CONTROL_CODES

WAITS = ['[WAIT%s]' % n for n in range(1, 7)]
NAMES = ['Gento', 'Benimaru', 'Haley', 'Tamamo', 'Okitsugu', 'Masamune', 'Flame Dragon',
         'Ice Dragon', 'Thunder Dragon', 'Shir[o]', 'Hanz[o]', 'Genpaku', 
         'Izunokami', 'Gennai', 'Ginpei', 'King Shikai', 'O-Toki', 'Benkei']

def effective_length(s):
    """The length of a string, ignoring the control codes."""

    # TODO: Rough so far. Only removes stuff in brackets.

    #pattern = rb'\[.*?\]'
    #print (s, re.sub(pattern, b'', s))
    #return len(re.sub(pattern, b'', s))
    original = s
    s = s.replace(b'[LN]', b' ')
    for w in WAITS:
        s = s.replace(bytes(w, encoding='ascii'), b'')

    for cc in (b'[o]', b'[O]', b'[u]', b'[U]'):
        # Overlined vowels are just one character, not [3]
        s = s.replace(cc, b'x')
    #print(original, s)
    return len(s)


def typeset(s, width=37):
    s_safe = s.replace('\u014d', '[o]').replace('\u016b', '[u]')

    #print(s_safe)
    # SJIS lines, like Haley's, must be split by SJIS spaces
    prefix = ''
    #print(s_safe)
    #print(s_safe.split('[LN]'))
    for n in NAMES:

        if s_safe.split('[LN]')[0] == n:
            if s_safe.split('[LN]')[1] != '':
                prefix = n
                s_safe = s_safe.lstrip(n)
                #print("Prefix")

    sjis = s_safe.encode('shift-jis')

    #print(sjis.split(b'[LN]'))

    if effective_length(sjis) <= width:
        # Indent stuff
        #s = s.replace('[LN]', '[LN] ')
        return s

    if b'\x82' in sjis:
        space = b'\x81\x40'
        width = 40
    else:
        space = b' '

    # LNs are breaks too. Let's replace them with spaces and see what happens
    #sjis = sjis.replace(b'[LN]', space)

    manual_lines = sjis.split(b'[LN]')

    for i, manual_line in enumerate(manual_lines):
        words = manual_line.split(space)

        lines = []

        #print(words)
        while words:
            #print(words)
            #if len(lines) > 0:
            #    line = b' '
            #else:

            # Indent non-initial lines (unless they start with a quote)
            # Example: *clears throat*/n"The Dragon Gems...
                # TODO: Still not working for throat-clearing lines.

            #if len(lines) > 0 and not words[0].startswith(b'"'):
            if not words[0].startswith(b'"'):
                # Yes, it's a space. 
                line = b' '
            else:
                line = b''

            while effective_length(line) <= width and words:
                if effective_length(line + words[0] + space) > width:
                    break
                line += words.pop(0) + space

            line = line.rstrip()

            # Remove initial spaces from first line.
            # Not sure if a good idea?
            if len(lines) == 0:
                line = line.lstrip()

            if len(lines) > 0:
                if line == lines[-1]:
                    print("That line is the same as the last one. Continuing onward")
                    break
            lines.append(line)

        lines = [l.decode('shift-jis') for l in lines]
        lines = [l.replace('[o]', '\u014d') for l in lines]
        lines = [l.replace('[u]', '\u016b') for l in lines]

        # Re-join the lines that weren't manually broken
        manual_lines[i] = '[LN]'.join(lines)

    # Join the segments of the string that were manually broken
    return prefix + '[LN] '.join(manual_lines)

def sjis_punctuate(s):
    s_safe = s.replace('\u014d', '[o]').replace('\u016b', '[u]')

    sjis = s_safe.encode('shift-jis')
    if b'\x82' not in sjis:
        return s

    #print(s)
    sjis = sjis.replace(b' ', b'\x81\x40')
    #s = s.replace(b'"', b'\x81\x56')

    s_safe = sjis.decode('shift-jis')

    s = s_safe.replace('[o]', '\u014d')

    return s


def shadoff_compress(s):
    #print(s)
    # Definitely don't compress filenames!
    if b'.GEM' in s:
        return s
    # If it's all spaces, keep it the same
    if s.count(b' ') == len(s):
        return s
    # If it's a fullwidth Latin char SJIS string, keep it the same
    if b'\x82' in s:
        return s

    # Don't further compress the dictionary
    if b'\xff' in s:
        return s

    s = s.decode('shift-jis')
    compressed = ''

    chars = list(s)

    # TODO: Remove the continuous-spaces processing

    continuous_spaces = 0
    first_number = True

    while chars:
        c = chars.pop(0)
        if c == ' ':
            first_number = True
            continuous_spaces += 1
            if not chars:
                compressed += c
        elif c.isupper():
            #if continuous_spaces > 2:
            #    compressed += '_' + chr(continuous_spaces)
            first_number = True
            if continuous_spaces > 0:
                compressed += ' '*(continuous_spaces)
            continuous_spaces = 0
            compressed += '^'
            compressed += c
        elif c.isdigit():
            if first_number:
                if len(compressed) > 0:
                    if compressed[-1] != '&' and compressed[-1] != '}' and compressed[-1] != '0':
                        compressed += ' '
                        compressed += c
                        first_number = False
                    else:
                        compressed += c
                else:
                    compressed += c
            else:
                compressed += c
        else:
            first_number = True
            if continuous_spaces > 0:
                compressed += ' '*(continuous_spaces-1)
                c = c.upper()
            continuous_spaces = 0
            compressed += c
        #print(bytes(compressed, encoding='shift-jis'))

    return bytes(compressed, encoding='shift-jis')

def replace_control_codes(s):
    s = s.decode('shift-jis')
    cursor = 0
    while cursor < len(s):
        c = s[cursor]
        if c == 'n':
            if s[cursor-1] != '>':
                s = s[:cursor] + S_CONTROL_CODES['n'] + s[cursor+1:]
        if c == 'w':
            # TODO: Why am I replacing the >w control codes here as well? Let's try not doing that
            #if s[cursor-1] != '>':
            s = s[:cursor] + S_CONTROL_CODES['w'] + s[cursor+1:]
        if c == 'c':
            if s[cursor-1] != '>':
                s = s[:cursor] + S_CONTROL_CODES['c'] + s[cursor+1:]
        cursor += 1
    s = s.encode('shift-jis')
    return s

# Deprecated, no longer necessary
#def properly_space_waits(s):
    """
        Every [WAIT*] control code interferes with the spacing a bit.
        (More accurately, Shadoff compression interferes with their spacing)
        Need to add (n-1) spaces after or before every WAIT,
        where n = the number of lowercase words that preceded it on the same line.
    """
    # No longer necessary after removing Shadoff compression
#    return s

    """
    result = ''
    wait_segments = s.split('[WAIT')
    if len(wait_segments) <= 1:
        return s
    else:
        for i, w in enumerate(wait_segments):
            if i == len(wait_segments)-1:
                result += w
                break
            ln_segments = w.split('[LN]')
            for j, l in enumerate(ln_segments):
                if j == len(ln_segments)-1:
                    words = l.split()
                    lowercase_count = len([word for word in words if word[0].islower()]) + 1
                    result += l + ' '*(lowercase_count) + '[WAIT'
                else:
                    result += l + '[LN]'
    return result
    """