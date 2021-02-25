
from db.db import DB


def fill_languages(db: DB = None):
    db = db or DB()
    db.upsert_lang('BAR', 'BAR-BAR', None)
    db.upsert_lang('GUG', 'GUG-GUG', None)


def fill_words(db: DB = None):
    db = db or DB()
    db.upsert_word('BAR-BAR', 'Boaric', 'BAR', '<script>')
    db.upsert_word('GUG-GUG', 'Guaraní', 'GUG', '<script>')

    db.upsert_word(None, 'huad', 'BAR', '<script>')
    db.upsert_word(None, 'bua', 'BAR', '<script>')
    db.upsert_word(None, 'mo', 'BAR', '<script>')
    db.upsert_word(None, 'frau', 'BAR', '<script>')

    db.upsert_word(None, "akã rehegua", 'GUG', '<script>')
    db.upsert_word(None, "mita", 'GUG', '<script>')
    db.upsert_word(None, "kuimba'e", 'GUG', '<script>')
    db.upsert_word(None, 'kuña', 'GUG', '<script>')


if __name__ == '__main__':
    fill_languages()
    fill_words()
