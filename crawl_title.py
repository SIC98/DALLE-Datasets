from bs4 import BeautifulSoup
from database import MySQLAPI
from multiprocessing import Pool
import requests
import argparse


def offset_to_url(offset):
    return f'https://commons.wikimedia.org/w/index.php?title=Special:NewFiles&dir=prev&offset={offset}&limit=500&user' \
           f'=&mediatype%5B0%5D=BITMAP&mediatype%5B1%5D=ARCHIVE&mediatype%5B2%5D=DRAWING&start=&end=&wpFormIdentifier' \
           f'=specialnewimages'


def find_links(offset):

    start_offset, end_offset = offset

    while start_offset < end_offset:
        res = requests.get(offset_to_url(start_offset))
        soup = BeautifulSoup(res.content, 'html.parser')
        lists = []
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('/wiki/File:'):
                lists.append(a['href'][11:])

        db.bulk_insert_title(list(set(lists)))
        db.commit()

        for a in soup.find_all('a', href=True):
            if a['href'].startswith('/w/index.php?title=Special:NewFiles') and 'limit=500' in a['href'] and \
                    'offset' in a['href'] and 'dir=prev' in a['href']:
                if a['href'][52:66] != start_offset:
                    start_offset = a['href'][52:66]
                    break


db = MySQLAPI()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', type=int, default=20000000000000,
                        help='Minimum value for upload date of image to crawl')
    parser.add_argument('-e', '--end', type=int, default=20220000000000,
                        help='Maximum value for upload date of image to crawl')
    parser.add_argument('-n', '--number_of_chunks', type=int, default=20, help='Number of chunks')
    parser.add_argument('-p', '--processes', type=int, default=4, help='Number of processes to crawl')
    a = parser.parse_args()

    time_gap = (a.end - a.start) / a.number_of_chunks
    offsets = [(str(int(time_gap * i + a.start)), str(int(time_gap * (i+1) + a.start))) for i in range(a.number_of_chunks)]

    with Pool(a.processes) as p:
        p.map(find_links, offsets)

    db.close()
