from database import MySQLAPI

db = MySQLAPI()


if __name__ == '__main__':

    db.adding_index_to_url()
    db.close()
