import asyncio
from database import MySQLAPI

if __name__ == '__main__':

    db = MySQLAPI()
    asyncio.run(db.update_table(1000, start_idx=0, end_idx=1000, processes=16))
    db.commit()
    db.close()
