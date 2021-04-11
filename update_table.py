import asyncio
from database import MySQLAPI

if __name__ == '__main__':

    db = MySQLAPI()
    asyncio.run(db.update_table(1000, start_idx=0, processes=8))
    db.commit()
    db.close()
