from database import MySQLAPI
from multiprocessing import Pool
import argparse

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

    db = MySQLAPI()

    with Pool(a.processes) as p:
        p.map(db.find_links, offsets)

    db.close()
