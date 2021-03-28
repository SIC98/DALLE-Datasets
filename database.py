import configparser
import logging
from sqlalchemy import create_engine, Column, Integer, MetaData, String, Table, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


config = configparser.ConfigParser()
config.read('config.ini')

table = config['DATABASE']['TABLE']
user = config['DATABASE']['USER']
password = config['DATABASE']['PASSWORD']
host = config['DATABASE']['HOST']
database = config['DATABASE']['DATABASE']
port = config['DATABASE']['PORT']

Base = declarative_base()


class MySQLAPI:
    def __init__(self):
        self.db_url = f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}?charset=utf8'
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
                  Column('time', TIMESTAMP, nullable=False))
            self.metadata.create_all()
            logging.info(f'new table {table} created')

    def insert_data(self, title, url, json_info, html):
        if not self.check_duplicate(title):
            data = TableClass(title=title, url=url, json=json_info, html=html)
            self.session.add(data)
            self.commit()

    def bulk_insert_data(self, data):
        self.session.bulk_save_objects(data)
        self.commit()

    def delete_is_deleted_column(self):
        self.session.query(TableClass).filter(TableClass.is_deleted is True).delete()
        self.commit()

    def close(self):
        self.session.close()

    def commit(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print('session rollback', e)
            raise


class TableClass(Base):

    __tablename__ = table

    id = Column(Integer(), primary_key=True)
    url = Column(String(1000))
    time = Column(TIMESTAMP)

    def __repr__(self):
        return f'<TableClass(id={self.id}, url={self.url}, time={self.time})>'
