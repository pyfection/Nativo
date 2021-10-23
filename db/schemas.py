from typing import List

from pydantic import BaseModel, EmailStr


class Base(BaseModel):
    class Config:
        orm_mode = True


class UserBase(Base):
    id: int
    email: EmailStr
    is_active: bool
    about: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    language_ids: List[int] = []
    word_ids: List[int] = []
    document_ids: List[int] = []


class LanguageBase(Base):
    id: int
    iso_639_3: str


class LanguageCreate(LanguageBase):
    default_translation: str


class Language(LanguageBase):
    translations: List['Word'] = []
    user_ids: List[int] = []
    word_ids: List[int] = []
    document_ids: List[int] = []


class DocumentBase(Base):
    id: int
    title: str
    text: str
    language: LanguageBase
    creator: UserBase


class Document(DocumentBase):
    pass


class WordBase(Base):
    id: int
    word: str
    language_id: int
    creator_id: int


class WordCreate(WordBase):
    description: str


class Word(WordBase):
    description_id: int
    language: LanguageBase
    creator: UserBase
    description: DocumentBase


Language.update_forward_refs()
