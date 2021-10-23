from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from db import Base


association_table = Table('association', Base.metadata,
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('language_id', ForeignKey('languages.id'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(120), index=True, unique=True)
    password_hash = Column(String(128))
    is_active = Column(Boolean, default=True)
    about = Column(String, default='')
    languages = relationship("Language", secondary=association_table, back_populates="users")
    words = relationship("Word", back_populates="creator")
    documents = relationship("Document", back_populates="creator")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    iso_639_3 = Column(String(3), index=True, unique=True)  # 3 letter ISO 639-3 code for language
    users = relationship("User", secondary=association_table, back_populates="languages")
    words = relationship("Word", back_populates="language")
    translations = relationship("Word", viewonly=True)
    documents = relationship("Document", back_populates="language")

    def name(self, iso_639_3=None):
        return next((t for t in self.translations if t.language.iso_639_3 == iso_639_3), 'No translation')


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String)
    language_id = Column(Integer, ForeignKey('languages.id'))
    language = relationship("Language", back_populates="words")
    creator_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship("User", back_populates="words")
    description_id = Column(Integer, ForeignKey('documents.id'))
    description = relationship("Document")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default='')
    text = Column(String, default='')
    language_id = Column(Integer, ForeignKey('languages.id'))
    language = relationship("Language", back_populates="documents")
    creator_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship("User", back_populates="documents")
