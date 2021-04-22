import asyncio
import argparse
from database import MySQLAPI

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bulk', type=int, default=800)
    parser.add_argument('-s', '--start_idx', type=int, default=0)
    parser.add_argument('-e', '--end_idx', type=int, default=78781)
    parser.add_argument('-p', '--processes', type=int, default=4)
    parser.add_argument('-t', '--seconds', type=int, default=45)
    a = parser.parse_args()

    db = MySQLAPI()
    asyncio.run(db.crawl_caption(a.bulk, start_idx=a.start_idx, end_idx=a.end_idx, processes=a.processes, seconds=a.seconds))
    db.commit()
    db.close()
