import configparser
import logging
from sqlalchemy import create_engine, Column, Integer, LargeBinary, MetaData, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


config = configparser.ConfigParser()
config.read('config.ini')

table = config['DATABASE']['TABLE']
user = config['DATABASE']['USER']
password = config['DATABASE']['PASSWORD']
host = config['DATABASE']['HOST']
database = config['DATABASE']['DATABASE']

Base = declarative_base()


class MySQLAPI:
    def __init__(self):
        self.db_url = f'mysql+mysqlconnector://{user}:{password}@{host}/{database}?charset=utf8'
        self.engine = create_engine(self.db_url, encoding='utf-8', pool_recycle=-1, max_overflow=0)
        session = sessionmaker(bind=self.engine)
        self.session = session()
        self.metadata = MetaData(self.engine)

    def check_duplicate(self, title):
        exists = self.session.query(TableClass.id).filter_by(title=title).scalar() is not None
        return exists

    def is_table_exist(self):
        return self.engine.dialect.has_table(self.engine, table)

    def create_table_if_not_exist(self):
        if not self.engine.dialect.has_table(self.engine, table):
            Table(table, self.metadata,
                  Column('id', Integer, primary_key=True, nullable=False, autoincrement=True),
                  Column('url', String(1000), nullable=False),
                  Column('raw_image', LargeBinary, nullable=True),
                  Column('image', LargeBinary, nullable=True),
                  Column('caption', String(1000), nullable=True))

            self.metadata.create_all()
            logging.info(f'new table {table} created')

    def insert_url(self, url):
        data = TableClass(url=url)
        self.session.add(data)

    def bulk_insert_url(self, urls):
        data = [TableClass(url=url) for url in urls]
        self.session.bulk_save_objects(data)

    def delete_is_deleted_column(self):
        self.session.query(TableClass).filter(TableClass.is_deleted is True).delete()

    def close(self):
        self.session.close()

    def commit(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logging.info('session rollback', e)
            raise


class TableClass(Base):

    __tablename__ = table

    id = Column(Integer(), primary_key=True)
    url = Column(String(1000))
    raw_image = Column(LargeBinary)
    image = Column(LargeBinary)
    caption = Column(String(1000))

    def __repr__(self):
        return f'TableClass(id={self.id}, url={self.url}, caption={self.caption})'
