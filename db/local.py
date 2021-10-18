from uuid import uuid4
import random
import re
import difflib

from tinydb import TinyDB, Query


class DB(TinyDB):
    def __init__(self, path='db/localdb.json'):
        super().__init__(path)
        self.token = ''
        self.user = ''
        self.user_lang = 'ENG'

    # - Auth - #
    def create_user(self, email, password, bio=''):
        User = Query()
        table = self.table('user')
        users = table.search(User.email == email)
        if users:
            raise KeyError(f"User already exists with email {email}")
        table.insert({'email': email, 'password': password, 'bio': bio})

    def verify_user(self, email, password):
        user = self.get_user(email)
        if user.get('password') == password:  # ToDo: hash password
            self.token = str(uuid4())
            self.user = email
            return True
        print('(Password is)', user.get('password'))
        return False

    def get_user(self, email):
        User = Query()
        table = self.table('user')
        users = table.search(User.email == email)
        return users[0] if users else None

    # - Language - #
    def upsert_lang(self, uid, users=None):
        # uid is 3 letter ISO 639-3 code for language
        # name is id of word for language (e.g. BAR-BAR means Bavarian name of Bavarian
        table = self.table('lang')
        data = {
            'uid': uid,
            'users': users or [],  # uid's of users who use it
        }
        Lang = Query()
        return table.upsert(data, Lang.uid == uid)

    def get_lang(self, uid):
        Lang = Query()
        table = self.table('lang')
        return table.get(Lang.uid == uid)

    def trans_lang(self, uid, to=None):
        to = to or self.user_lang
        options = [f'{to}-{uid}', f'{to}-{uid}']
        for option in options:
            word = self.get_word(option)
            if word:
                break
        else:
            raise IndexError(f"{uid} does not have a suitable translation in {to} nor in {uid}!")
        return word['word']

    def get_langs(self):
        lang_table = self.table('lang')
        langs = {}
        for lang in lang_table.all():
            lang = lang['uid']
            langs[lang] = self.get_word(self.trans_lang(lang))
        return langs

    # - Word - #
    def upsert_word(self, uid, word, lang, creator, description='', phrases=None):
        # ToDo: add decorator to check if word is valid
        table = self.table('word')
        data = {
            'uid': uid or str(uuid4()),
            'word': word,
            'lang': lang,
            'creator': creator,
            'description': description,  # uid of a document
            'phrases': phrases or [],  # uid's of phrases in which it is contained
        }
        Word = Query()
        table.upsert(data, Word.uid == uid)
        return data['uid']

    def get_word(self, uid, lang=None):
        Word = Query()
        query = [
            Word.uid == uid,
        ]
        if lang:
            query.append(Word.lang == lang)
        table = self.table('word')
        return table.get(*query)

    def get_words(self, auto_translate=True):
        table = self.table('word')
        words = table.all()
        for word in words:
            if auto_translate:
                word['lang'] = self.trans_lang(word['lang'])
        return words

    def get_similar_words(self, word):
        words = [w['word'] for w in self.get_words()]
        return difflib.get_close_matches(word, words)

    def random_word(self):
        table = self.table('word')
        return random.choice(table.all())

    # - Document - #
    def upsert_doc(self, uid, title, text, lang, creator):
        # ToDo: add decorator to check if word is valid
        table = self.table('doc')
        data = {
            'uid': uid or str(uuid4()),
            'title': title,
            'text': text,
            'lang': lang,
            'creator': creator,
        }
        Doc = Query()
        table.upsert(data, Doc.uid == uid)
        return data['uid']

    def get_doc(self, uid):
        Doc = Query()
        query = [
            Doc.uid == uid,
        ]
        table = self.table('doc')
        return table.get(*query)

    def translate_doc_text(self, text):
        def trans(uid):
            word = self.get_word(uid)
            if word:
                return word['word']
            else:
                return uid
        return re.sub(r'\[\[([\w-]+(?::\w)?)]]', lambda m: trans(m.group(1)), text)

    def get_doc_trans(self, uid):
        # Gets translated doc
        doc = self.get_doc(uid)
        doc['text'] = self.translate_doc_text(doc['text'])
        return doc

    def get_docs_short(self):
        table = self.table('doc')
        docs = table.all()
        return [
            {'uid': doc['uid'], 'title': doc['title'], 'desc': f'{self.translate_doc_text(doc["text"])[:50]}...'}
            for doc in docs
        ]


if __name__ == '__main__':
    db = DB(path='localdb.json')
    db.upsert_lang('BAR')
    db.upsert_lang('ENG')
    db.upsert_doc('BAR-BAR_desc', 'Boaric', 'De cdándard boarice cbráh.', 'BAR', 'Matumaros')
    db.upsert_doc('ENG-BAR_desc', 'Bavarian', 'The standard bavarian language.', 'ENG', 'Matumaros')
    db.upsert_doc('ENG-ENG_desc', 'English', 'The standard english language.', 'ENG', 'Matumaros')
    db.upsert_word('BAR-BAR', 'Boaric', 'BAR', 'Matumaros', 'BAR-BAR_desc')
    db.upsert_word('ENG-BAR', 'Bavarian', 'ENG', 'Matumaros', 'ENG-BAR_desc')
    db.upsert_word('ENG-ENG', 'English', 'ENG', 'Matumaros', 'ENG-ENG_desc')
    print(db.get_word('BAR-BAR'))
