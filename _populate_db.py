import os

os.environ['NATIVO_DB'] = 'sqlite:///./server.db'


from db import engine
from db.models import Base

Base.metadata.create_all(bind=engine)


from db import get_db, models

db = next(get_db())

# Create admin
admin = models.User(email='admin@nativo.org')
admin.set_password('12345')
db.add(admin)

# Create languages
lang_bar = models.Language(iso_639_3="BAR")
lang_eng = models.Language(iso_639_3="ENG")

# Create translations
desc_bar = models.Document(language=lang_bar, creator=admin)
desc_eng = models.Document(language=lang_eng, creator=admin)
word_bar = models.Word(word="Boaric", language=lang_bar, creator=admin, description=desc_bar)
word_eng = models.Word(word="English", language=lang_eng, creator=admin, description=desc_eng)
lang_bar.translations.append(word_bar)
lang_eng.translations.append(word_eng)

db.commit()
