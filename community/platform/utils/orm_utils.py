from sqlalchemy.orm import sessionmaker

from community.models import engine

_SessionFactory = sessionmaker(bind=engine)
SESSION = None


def session_factory():
    # return _SessionFactory()

    global SESSION

    if SESSION is None:
        SESSION = _SessionFactory(expire_on_commit=False)
    return SESSION


def get_or_create(model, defaults=None, **kwargs):
    # with session_factory() as session:
        session = session_factory()
        instance = session.query(model).filter_by(**kwargs).one_or_none()
        if instance:
            return instance
        else:
            params = kwargs | (defaults or {})
            instance = model(**params)
            session.add(instance)
            session.commit()
            return session.query(model).filter_by(**kwargs).one()
