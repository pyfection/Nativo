from typing import List, Optional

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
    title: str
    text: str


class DocumentCreate(DocumentBase):
    id: Optional[int]
    language_id: int


class Document(DocumentBase):
    id: int
    language: LanguageBase
    creator: UserBase


class WordBase(Base):
    word: str


class WordCreate(WordBase):
    id: Optional[int]
    language_id: int
    description: str


class Word(WordBase):
    id: int
    description_id: int
    language: LanguageBase
    creator: UserBase
    description: Document


Language.update_forward_refs()
