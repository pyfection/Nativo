from pygments.lexer import Lexer
from pygments.token import *


class SentenceLexer(Lexer):
    name = 'Sentence'
    aliases = ['sentence']
    lines = []
    links_positions = []

    def get_tokens(self, text, unfiltered=False):
        tokens = []
        # if text not in self.lines:
        #     return tokens

        last_end = 0
        for start, end in self.links_positions:
            txt = text[last_end:start]
            link = text[start:end]
            if txt:
                tokens.append((Comment, txt))
            if not link:
                break
            tokens.append((Text, link))
            last_end = end
        else:
            txt = text[last_end:]
            if txt:
                tokens.append((Comment, txt))
        return tokens


if __name__ == '__main__':
    lexer = SentenceLexer()
    lexer.links_positions = [[(1, 3), (5, 8), (50, 100)], [(4, 5)]]
    print(list(lexer.get_tokens("Hello there + - @ test")))
    print(list(lexer.get_tokens("Another line of text")))
