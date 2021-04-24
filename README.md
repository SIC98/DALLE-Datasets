# DALLE-Datasets

## Crawled image-caption pair dataset from Wikimedia Commons for training DALL·E
<img width="1477" alt="스크린샷 2021-04-11 오후 8 06 43" src="https://user-images.githubusercontent.com/51232785/114301895-a32f7100-9b01-11eb-846f-200efe292850.png">


## Steps for crawling

1. Use `mysql` to store crawled data

2. Create a `config.ini` file based on `config.ini.example` to connect to your `mysql`

3. Install requirenemts.txt dependencies

```
pip install -r requirements.txt
``` 

4. Create table

```
python dalle_datasets/create_table.py
```

5. Check the table structure

```mysql
DESC $table
```
```
+---------+---------------+------+-----+---------+----------------+
| Field   | Type          | Null | Key | Default | Extra          |
+---------+---------------+------+-----+---------+----------------+
| id      | int(11)       | NO   | PRI | NULL    | auto_increment |
| title   | varchar(1000) | YES  |     | NULL    |                |
| image   | mediumblob    | YES  |     | NULL    |                |
| mime    | varchar(50)   | YES  |     | NULL    |                |
| url     | varchar(1000) | YES  |     | NULL    |                |
| caption | text          | YES  |     | NULL    |                |
+---------+---------------+------+-----+---------+----------------+
```

6. Crawl title

```
python dalle_datasets/crawl_title.py
```

7. Check the number of rows in the table

```mysql
SELECT COUNT(*) from $table;
```

```
+----------+
| count(*) |
+----------+
| 63024034 |
+----------+
```

8. Crawl image url and caption

```
python dalle_datasets/crawl_caption.py
```

9. Delete row with `NULL` caption

```mysql
DELETE FROM $table WHERE caption IS NULL;
SELECT COUNT(*) from $table;
```

```
+----------+
| count(*) |
+----------+
| 30246704 |
+----------+
```
