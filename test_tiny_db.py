from models.phrase import Phrase
from models.word import Word


Word.clear()
Phrase.clear()

i = Word(word="i", tags=["pronoun"], foreign_description={"eng": "I"})
print(i)
i.commit()
be = Word(word="sei", tags=["verb"], foreign_description={"eng": "to be"})
print(be)
be.commit()
am = Word(word="bin", tags=["verb"], foreign_description={"eng": "am"}, word_base=be.id)
print(am)
am.commit()
a = Word(word="a", tags=["article"], foreign_description={"eng": "a"})
print(a)
a.commit()
boy = Word(word="bua", tags=["noun"], foreign_description={"eng": "boy"})
print(boy)
boy.commit()
words = Word.all()
print(words)

# phrase = Phrase(raw_text=f"Hi there, this is a {{{{{word.id}:t}}}} phrase with lots of {{{{{word.id}:u}}}}")
phrase = Phrase(raw_text=f"{{{{{i.id}:t}}}} {{{{{am.id}}}}} {{{{{a.id}}}}} {{{{{boy.id}}}}}.")
phrase.commit()
print(Phrase.all())
print("TEXT:", phrase.text)
