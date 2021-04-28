# DALLE-Datasets

## Crawling image-caption pair dataset from Wikimedia Commons for training DALL·E

<img width="1477" alt="스크린샷 2021-04-11 오후 8 06 43" src="https://user-images.githubusercontent.com/51232785/114301895-a32f7100-9b01-11eb-846f-200efe292850.png">

## 📚 Data

### Download data

- Download link: [wikimedia_commons.csv](https://drive.google.com/file/d/1_plT6RgEiag6IqepKMJphq2wyxnc5hI5/view?usp=sharing)
- File size: 8.42GB

### File summary

- id: unique identifier
- title: name of image. Detail information of image: `https://commons.wikimedia.org/wiki/File:$title`
- mime: `image/png`, `image/jpeg`, `image/svg+xml`, `image/gif`, `image/tiff`, `image/x-xcf`, or `image/webp`
- url: can downlaod image from `url`
- caption: caption of iamge

### Head of file

```bash
head -n 5 wikimedia_commons.csv
```

```
id,title,mime,url,caption
5637467,Ph_locator_cotabato_carmen.png,image/png,https://upload.wikimedia.org/wikipedia/commons/a/a8/Ph_locator_cotabato_carmen.png,Map of the Cotabato showing the location of Carmen
5637468,Ph_locator_tarlac_san_clemente.png,image/png,https://upload.wikimedia.org/wikipedia/commons/2/27/Ph_locator_tarlac_san_clemente.png,Map of Tarlac showing the location of San Clemente
5637470,Ph_locator_sultan_kudarat_isulan.png,image/png,https://upload.wikimedia.org/wikipedia/commons/d/d7/Ph_locator_sultan_kudarat_isulan.png,Map of the Sultan Kudarat showing the location of Isulan
5637471,Ph_locator_lanao_del_sur_balabagan.png,image/png,https://upload.wikimedia.org/wikipedia/commons/d/d4/Ph_locator_lanao_del_sur_balabagan.png,Map of the Lanao del Sur showing the location of Balabagan
```

## ⚗️ Steps for crawling

1. Use `mysql` to store crawled data

2. Create a `config.ini` file based on `config.ini.example` to connect to your `mysql`

3. Install requirenemts.txt dependencies

```bash
pip install -r requirements.txt
``` 

4. Create table

```bash
python dalle_datasets/create_table.py
```

5. Check the table structure

```mysql
DESC $table;
```
```
+---------+---------------+------+-----+---------+----------------+
| Field   | Type          | Null | Key | Default | Extra          |
+---------+---------------+------+-----+---------+----------------+
| id      | int(11)       | NO   | PRI | NULL    | auto_increment |
| title   | varchar(1000) | NO   |     | NULL    |                |
| image   | mediumblob    | YES  |     | NULL    |                |
| mime    | varchar(50)   | YES  |     | NULL    |                |
| url     | varchar(1000) | YES  |     | NULL    |                |
| caption | varchar(2000) | YES  |     | NULL    |                |
+---------+---------------+------+-----+---------+----------------+
```

6. Crawl title

```bash
python dalle_datasets/crawl_title.py
```

7. Check the number of rows in the table

```mysql
SELECT count(*) FROM $table;
```

```
+----------+
| count(*) |
+----------+
| 63024034 |
+----------+
```

8. Crawl image url and caption

```bash
python dalle_datasets/crawl_caption.py
```

This script takes too long to run on only one machine. So I split the task into 10 gcp instances.

For example, if you number each instance from 0 to 9 as variable i, you can run the script for each instance as shown below.

```bash
# start = 7879 * i
# end = 7879 * (i+1)
python dalle_datasets/crawl_caption.py -s $start -e $end
```


9. Delete row with `NULL` caption

```mysql
DELETE FROM $table WHERE caption IS NULL;
SELECT count(*) FROM $table;
```

```
+----------+
| count(*) |
+----------+
| 30246704 |
+----------+
```

10. Selecting `mime` column in group by

```mysql
SELECT mime, count(mime) AS count FROM $table GROUP BY mime;
```

```
+---------------+----------+
| mime          | count    |
+---------------+----------+
| image/png     |  1469744 |
| image/jpeg    | 27229537 |
| image/svg+xml |  1089487 |
| image/gif     |    71366 |
| image/tiff    |   383288 |
| image/x-xcf   |      680 |
| image/webp    |     2602 |
+---------------+----------+
```

11. Crawl image

```bash
python dalle_datasets/crawl_image.py
```
