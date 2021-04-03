# DALLE-Datasets

## Steps for crawling

1. Create Cloud SQL instance for collecting crawled data

2. Create a `config.ini` file based on `config.ini.example` to connect to Cloud SQL

3. Install requirenemts.txt dependencies

```
pip install -r requirements.txt
``` 

4. Create table

```
python create_table.py
```

5. Crawl file names

```
python crawl_url.py
```

6. Delete duplicate rows using DELETE JOIN statement

```mysql
DELETE t1 FROM $table t1
INNER JOIN $table t2 
WHERE 
    t1.id < t2.id AND 
    t1.url = t2.url;
```
