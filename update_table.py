import asyncio
import argparse
from database import MySQLAPI

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bulk', type=int, default=800)
    parser.add_argument('-s', '--start_idx', type=int, default=0)
    parser.add_argument('-e', '--end_idx', type=int, default=2000)
    parser.add_argument('-p', '--processes', type=int, default=4)
    a = parser.parse_args()

    db = MySQLAPI()
    asyncio.run(db.update_table(a.bulk, start_idx=a.start_idx, end_idx=a.end_idx, processes=a.processes))
    db.commit()
    db.close()
