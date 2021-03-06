from bs4 import BeautifulSoup
import configparser
from datetime import datetime, timedelta
import requests
from sqlalchemy import create_engine, Column, inspect, Integer, LargeBinary, MetaData, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from wikimedia_commons_api import crawl_image, crawl_caption, offset_to_url
import time

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

    def find_links(self, offset):

        start_offset, end_offset = offset

        while start_offset < end_offset:
            res = requests.get(offset_to_url(start_offset))
            soup = BeautifulSoup(res.content, 'html.parser')
            lists = []
            for a in soup.find_all('a', href=True):
                if a['href'].startswith('/wiki/File:'):
                    lists.append(a['href'][11:])

            self.bulk_insert_title(list(set(lists)))
            self.commit()

            for a in soup.find_all('a', href=True):
                if a['href'].startswith('/w/index.php?title=Special:NewFiles') and 'limit=500' in a['href'] and \
                        'offset' in a['href'] and 'dir=prev' in a['href']:
                    if a['href'][52:66] != start_offset:
                        start_offset = a['href'][52:66]
                        break

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
                print('finish!')
                break

            yield rec
            firstid = pk_attr.__get__(rec[-1], pk_attr) if rec else None

    async def crawl_caption(self, maxrq, start_idx, end_idx, processes, seconds):
        query = self.session.query(TableClass)

        now = datetime.now()
        for idx, rec in enumerate(self._yield_limit(query, TableClass.id, maxrq=maxrq, skip=start_idx * maxrq)):
            if (end_idx - start_idx) > idx >= 0:
                await crawl_caption(rec, processes, seconds)
                self.commit()
                loop_time = datetime.now() - now
                print(f'index: {idx + start_idx} | time taken: {loop_time}')
                remain_seconds = (timedelta(seconds=seconds) - loop_time).total_seconds()
                if remain_seconds > 0:
                    time.sleep(remain_seconds)
                    print(f'sleep: {remain_seconds}')

            else:
                print(f'index: {idx + start_idx} | finish!')
                break

            now = datetime.now()

    async def crawl_image(self, maxrq, start_idx, end_idx, seconds):
        query = self.session.query(TableClass)

        now = datetime.now()
        for idx, rec in enumerate(self._yield_limit(query, TableClass.id, maxrq=maxrq, skip=start_idx * maxrq)):
            if (end_idx - start_idx) > idx >= 0:
                await crawl_image(rec, seconds)
                self.commit()
                loop_time = datetime.now() - now
                print(f'index: {idx + start_idx} | time taken: {loop_time}')
                remain_seconds = (timedelta(seconds=seconds) - loop_time).total_seconds()
                if remain_seconds > 0:
                    time.sleep(remain_seconds)
                    print(f'sleep: {remain_seconds}')

            else:
                print(f'index: {idx + start_idx} | finish!')
                break

            now = datetime.now()

    def is_table_exist(self):
        return self.engine.dialect.has_table(self.engine, table)

    def create_table_if_not_exist(self):
        if not inspect(self.engine).has_table(table):
            Table(table, self.metadata,
                  Column('id', Integer, primary_key=True, nullable=False, autoincrement=True),
                  Column('title', String(1000), nullable=False),
                  Column('image', LargeBinary(length=(2**24)-1), nullable=True),
                  Column('mime', String(50), nullable=True),
                  Column('url', String(1000), nullable=True),
                  Column('caption', String(2000), nullable=True)),

            self.metadata.create_all()
            print(f'new table {table} created')

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
            print('session rollback', e)
            raise


class TableClass(Base):

    __tablename__ = table

    id = Column(Integer(), primary_key=True)
    title = Column(String(1000))
    image = Column(LargeBinary)
    mime = Column(String(50))
    url = Column(String(1000))
    caption = Column(String(2000))

    def __repr__(self):
        return f'TableClass(id={self.id}, title={self.title}, mime={self.mime}, url={self.url}, caption={self.caption})'
