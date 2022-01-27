import os
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Table, ForeignKey, BigInteger, VARCHAR
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

CONNECT_STRING = os.environ.get('POSTGRES_CONNECT_STRING', 'NONE')
engine = create_engine(
    "postgresql+psycopg2://{}".format(CONNECT_STRING))

Base = declarative_base()

Session = sessionmaker(bind=engine)

user_wallet_association = Table(
    'users_wallets', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('wallet_id', Integer, ForeignKey('wallet.id'))
)


class BadDataException(Exception):
    """A Class for bad data exceptions"""


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    wallets = relationship('Wallet', secondary=user_wallet_association)

    def __init__(self, user_id):
        self.telegram_id = user_id

    @staticmethod
    def exists(user_id) -> [bool, None]:
        session = Session()
        try:
            users = session.query(User).filter(User.telegram_id == user_id).all()
            if len(users) > 1:
                # logger.error("Too Many Users with id: {}".format(user_id))
                raise BadDataException
            if len(users) == 0:
                return False
            if len(users) == 1:
                return True
        except Exception as e:
            session.rollback()

    @staticmethod
    def get_user(user_id):
        session = Session()
        try:
            users = session.query(User).filter(User.telegram_id == user_id).all()
            if len(users) > 1:
                # logger.error("Too Many Users with id: {}".format(user_id))
                raise BadDataException
            if len(users) == 0:
                return None
            if len(users) == 1:
                return users[0]
        except Exception as e:
            session.rollback()


class Wallet(Base):
    __tablename__ = 'wallet'

    id = Column(Integer, primary_key=True)
    wallet_address = Column(VARCHAR(100))

    def __init__(self, wallet_address):
        self.wallet_address = wallet_address
