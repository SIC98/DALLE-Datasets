from database import MySQLAPI

if __name__ == '__main__':

    db = MySQLAPI()
    db.create_table_if_not_exist()
    db.close()
