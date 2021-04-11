# DALLE-Datasets

## Crawled image-caption pair dataset from Wikimedia Commons for training DALL·E
<img width="1477" alt="스크린샷 2021-04-11 오후 8 06 43" src="https://user-images.githubusercontent.com/51232785/114301895-a32f7100-9b01-11eb-846f-200efe292850.png">


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
