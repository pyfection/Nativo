from uuid import uuid4
import random

from tinydb import TinyDB, Query


class DB(TinyDB):
    def __init__(self, path='db/localdb.json'):
        super().__init__(path)
        self.token = ''
        self.user = ''
        self.languages_buffer = {}
        self.lang_name_trans = {}
        self.lang_trans_name = {}

    # - Auth - #
    def create_user(self, email, password):
        User = Query()
        table = self.table('user')
        users = table.search(User.email == email)
        if users:
            raise KeyError(f"User already exists with email {email}")
        table.insert({'email': email, 'password': password})

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
    def upsert_lang(self, uid, name, description, users=None):
        # uid is 3 letter ISO 639-3 code for language
        # name is int id of word
        table = self.table('lang')
        data = {
            'uid': uid,
            'name': name,
            'description': description,  # uid of a document
            'users': users or [],  # uid's of users who use it
        }
        Lang = Query()
        return table.upsert(data, Lang.uid == uid)

    def get_lang(self, uid):
        Lang = Query()
        table = self.table('lang')
        return table.get(Lang.uid == uid)

    def get_langs(self):
        if not self.languages_buffer:
            table = self.table('lang')
            self.languages_buffer = table.all()
            self.lang_name_trans = {data['name']: self.get_word(data['name'])['word'] for data in self.languages_buffer}
            self.lang_trans_name = {val: key for key, val in self.lang_name_trans.items()}
        return self.languages_buffer

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
        return table.upsert(data, Word.uid == uid)

    def get_word(self, uid, lang=None):
        Word = Query()
        query = [
            Word.uid == uid,
        ]
        if lang:
            query.append(Word.lang == lang)
        table = self.table('word')
        return table.get(*query)

    def random_word(self):
        table = self.table('word')
        return random.choice(table.all())

    # - Document - #


if __name__ == '__main__':
    db = DB(path='localdb.json')
    print(db.get_word('BAR-BAR'))
