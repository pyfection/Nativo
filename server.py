from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db, models, schemas

app = FastAPI()


@app.post('/user/create', response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    data = user.dict()
    password = data.pop('password')
    db_user = models.User(**data)
    db_user.set_password(password)
    db.add(db_user)
    db.commit()

    return db_user


@app.get('/user/{id}', response_model=schemas.User)
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).get(id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.language_ids = [lang.id for lang in user.languages]
    user.word_ids = [word.id for word in user.words]
    user.document_ids = [doc.id for doc in user.documents]
    return user


@app.get('/users', response_model=List[schemas.User])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@app.get('/word/{id}', response_model=schemas.Word)
async def get_word(id: int, db: Session = Depends(get_db)):
    word = db.query(models.Word).get(id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return word


@app.get('/words', response_model=List[schemas.Word])
async def get_words(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    words = db.query(models.Word).offset(skip).limit(limit).all()
    return words


@app.put('/word', response_model=schemas.Word)
async def upsert_word(word: schemas.WordCreate, db: Session = Depends(get_db)):
    if word.id is not None:
        db_word = db.query(models.Word).get(word.id)
        db_word.word = word.word
        db_word.description.text = word.description
    else:
        db_word = models.Word(**word.dict())
        creator_id = 1  # ToDo: should be set to user who sent the request
        description = models.Document(text=word.description, creator_id=creator_id, language_id=word.language_id)
        db_word.description = description
        db_word.creator_id = creator_id
        db.add(db_word)
        db.add(description)
    db.commit()
    db.refresh(db_word)

    return db_word


@app.post('/language/create', response_model=schemas.Language)
async def create_language(language: schemas.LanguageCreate, db: Session = Depends(get_db)):
    db_language = db.query(models.Language).filter(models.Language.iso_639_3 == language.iso_639_3).first()
    if db_language:
        raise HTTPException(status_code=400, detail="Language already exists")
    data = language.dict()
    default_translation = data.pop('default_translation')
    db_language = models.Language(**data)
    translation = models.Word(word=default_translation, language=db_language)
    db_language.translations.append(translation)
    db.add(translation)
    db.add(db_language)
    db.commit()
    db.refresh(db_language)

    return db_language


def _update_language_attributes(language):
    language.translations = [word for word in language.translations]
    language.user_ids = [lang.id for lang in language.users]
    language.word_ids = [word.id for word in language.words]
    language.document_ids = [doc.id for doc in language.documents]


@app.get('/language/{id}', response_model=schemas.Language)
async def get_language(id: int, db: Session = Depends(get_db)):
    language = db.query(models.Language).get(id)
    if language is None:
        raise HTTPException(status_code=404, detail="Language not found")
    _update_language_attributes(language)
    return language


@app.get('/languages', response_model=List[schemas.Language])
async def get_languages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    languages = db.query(models.Language).offset(skip).limit(limit).all()
    for language in languages:
        _update_language_attributes(language)
    return languages


@app.get('/document/{id}', response_model=schemas.Document)
async def get_document(id: int, db: Session = Depends(get_db)):
    document = db.query(models.Document).get(id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.get('/documents', response_model=List[schemas.Document])
async def get_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    documents = db.query(models.Document).offset(skip).limit(limit).all()
    return documents


@app.put('/document', response_model=schemas.Document)
async def upsert_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    if document.id is not None:
        db_document = db.query(models.Document).get(document.id)
        db_document.title = document.title
        db_document.text = document.text
    else:  # New Document
        db_document = models.Document(**document.dict())
        creator_id = 1  # ToDo: should be set to user who sent the request
        db_document.creator_id = creator_id
        db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return db_document
