import copy

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import declared_attr
from sqlalchemy.ext.declarative import declarative_base

from community.app import settings


class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @classmethod
    def get_table_columns(cls):
        return list(cls.metadata.tables[cls.__name__.lower()].c.keys())

    @staticmethod
    def session_factory():
        from community.platform.utils.orm_utils import session_factory
        return session_factory()

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        from community.platform.utils.orm_utils import get_or_create
        return get_or_create(cls, defaults=defaults, **kwargs)

    @classmethod
    def bulk_create(cls, objs):
        session = cls.session_factory()
        # session.add_all(objs)
        # session.commit()
        for obj in objs:
            session.add(obj)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()

    @classmethod
    def bulk_update(cls, objs):
        session = cls.session_factory()
        cols = cls.get_table_columns()
        for obj in objs:
            db_obj = session.query(cls).filter(cls.id == obj.id).one()
            session.add(db_obj)
            for col in cols:
                val = getattr(obj, col)
                if val is not None:
                    if isinstance(val, dict):
                        old_val = copy.copy(getattr(db_obj, col) or {})
                        old_val.update(val)
                        val = old_val
                    setattr(db_obj, col, val)
            session.commit()

    @classmethod
    def bulk_upsert(cls, objs):
        session = cls.session_factory()
        for obj in objs:
            try:
                db_obj = session.query(cls).filter(cls.id == obj.id).one()
            except NoResultFound:
                session.add(obj)
            else:
                session.add(db_obj)
                db_obj.data = db_obj.data or {}
                db_obj.data.update(obj.data)
            finally:
                session.commit()

    @classmethod
    def saving(cls):
        class CtxMgr(object):
            def __enter__(self):
                self.session = Base.session_factory()

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.session.commit()

        return CtxMgr()

    @classmethod
    def filter(cls, *args):
        session = cls.session_factory()
        return session.query(cls).filter(*args)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        session = cls.session_factory()
        session.add(obj)
        session.commit()
        return obj

    def delete(self):
        session = self.session_factory()
        session.delete(self)
        session.commit()

    @classmethod
    def query(cls, *args):
        session = cls.session_factory()
        return session.query(*args)


Base = declarative_base(cls=Base)


from community.platform.models import *  # noqa
from community.ingest.models import *  # noqa

engine = create_engine(settings.DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
