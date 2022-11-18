from models.phrase import Phrase
from models.user import User
from models.word import Word


User.clear()
Word.clear()
Phrase.clear()

user = User(name="Matumaros")
user.commit()

i = Word(word="i", tags=["pronoun"], foreign_description={"eng": "I"}, creator=user.id)
print(i)
i.commit()
be = Word(word="sei", tags=["verb"], foreign_description={"eng": "to be"}, creator=user.id)
print(be)
be.commit()
am = Word(word="bin", tags=["verb"], foreign_description={"eng": "am"}, stem_id=be.id, creator=user.id)
print(am)
am.commit()
a = Word(word="a", tags=["article"], foreign_description={"eng": "a"}, creator=user.id)
print(a)
a.commit()
boy = Word(word="bua", tags=["noun"], foreign_description={"eng": "boy"}, creator=user.id)
print(boy)
boy.commit()
girl = Word(**boy.asdict())
girl.word = "deandl"
print(girl)
girl.commit()
words = list(Word.all())
print(words)

# phrase = Phrase(raw_text=f"Hi there, this is a {{{{{word.id}:t}}}} phrase with lots of {{{{{word.id}:u}}}}")
phrase = Phrase(raw_text=f"{{{{{i.id}:t}}}} {{{{{am.id}}}}} {{{{{a.id}}}}} {{{{{boy.id}}}}}.", creator=user.id)
print(phrase)
phrase.commit()
print(list(Phrase.all()))
print("TEXT:", phrase.text)
