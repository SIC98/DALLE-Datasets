import asyncio
import argparse
from database import MySQLAPI

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bulk', type=int, default=800)
    parser.add_argument('-s', '--start_idx', type=int, default=0)
    parser.add_argument('-e', '--end_idx', type=int, default=2000)
    parser.add_argument('-t', '--seconds', type=int, default=32)
    a = parser.parse_args()

    db = MySQLAPI()
    asyncio.run(db.crawl_image(a.bulk, start_idx=a.start_idx, end_idx=a.end_idx, seconds=a.seconds))
    db.commit()
    db.close()
