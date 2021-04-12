import configparser
from datetime import datetime
import logging
from sqlalchemy import create_engine, Column, Integer, LargeBinary, MetaData, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from wikimedia_commons_api import update_table

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
        self.db_url = f'mysql+mysqlconnector://{user}:{password}@{host}/{database}?charset=utf8mb4'
        self.engine = create_engine(self.db_url, encoding='utf-8', pool_recycle=-1, max_overflow=0)
        session = sessionmaker(bind=self.engine)
        self.session = session()
        self.metadata = MetaData(self.engine)

    def check_duplicate(self, title):
        exists = self.session.query(TableClass.id).filter_by(title=title).scalar() is not None
        return exists

    @staticmethod
    def _yield_limit(qry, pk_attr, maxrq, skip):

        if skip == 0:
            firstid = None
        else:
            q = qry
            rec = q.order_by(pk_attr).limit(1).offset(skip-1)
            firstid = pk_attr.__get__(rec[-1], pk_attr) if rec else None

        while True:
            q = qry
            if firstid is not None:
                q = qry.filter(pk_attr > firstid)

            rec = q.order_by(pk_attr).limit(maxrq)

            if rec.count() == 0:
                break

            yield rec
            firstid = pk_attr.__get__(rec[-1], pk_attr) if rec else None

    async def update_table(self, maxrq, start_idx, end_idx, processes):
        query = self.session.query(TableClass)

        now = datetime.now()
        for idx, rec in enumerate(self._yield_limit(query, TableClass.id, maxrq=maxrq, skip=start_idx * maxrq)):
            if (end_idx - start_idx) > idx >= 0:
                await update_table(rec, processes)
                self.commit()
                print(f'index: {idx + start_idx} | time taken: {datetime.now() - now}')
                with open('log.txt', 'a') as f:
                    print(f'index: {idx + start_idx} | time taken: {datetime.now() - now}', file=f)
            else:
                print(f'index: {idx + start_idx} | finish!')
                with open('log.txt', 'a') as f:
                    print(f'index: {idx + start_idx} | time taken: {datetime.now() - now}', file=f)
                break

            now = datetime.now()

    def is_table_exist(self):
        return self.engine.dialect.has_table(self.engine, table)

    def create_table_if_not_exist(self):
        if not self.engine.dialect.has_table(self.engine, table):
            Table(table, self.metadata,
                  Column('id', Integer, primary_key=True, nullable=False, autoincrement=True),
                  Column('title', String(1000), nullable=False),
                  Column('raw_image', LargeBinary, nullable=True),
                  Column('image', LargeBinary, nullable=True),
                  Column('url', String(1000), nullable=True),
                  Column('caption', String(2000), nullable=True)),

            self.metadata.create_all()
            logging.info(f'new table {table} created')

    def insert_title(self, title):
        data = TableClass(title=title)
        self.session.add(data)

    def bulk_insert_title(self, titles):
        data = [TableClass(title=title) for title in titles]
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
    title = Column(String(1000))
    raw_image = Column(LargeBinary)
    image = Column(LargeBinary)
    mediatype = Column(String(50))
    mime = Column(String(50))
    url = Column(String(1000))
    caption = Column(String(2000))

    def __repr__(self):
        return f'TableClass(id={self.id}, title={self.title}, caption={self.caption})'
