import aiohttp
import asyncio
from bs4 import BeautifulSoup
import requests
import json
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


def query_url(title):
    return f'https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&titles=File:{title}&utf8=' \
           f'1&iiprop=comment|url|mediatype|mime&iilimit=1'


def parse_url(title):
    return f'https://commons.wikimedia.org/w/api.php?action=parse&format=json&page=File:{title}&prop=wikitext&utf8=1'


def wikimeida_commons(title):
    return f'https://commons.wikimedia.org/wiki/File:{title}'


async def fetch(url, return_type):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            if res.status != 200:
                print(res.status)
            assert res.status == 200
            if return_type == 'html':
                return await res.read()
            elif return_type =='json':
                return await res.json()


def get_url(res):
    soup = BeautifulSoup(res, 'html.parser')
    td = soup.find('td', class_='description')

    if not td:
        return None

    if td.find('div', class_=['description', 'mw-content-ltr']):
        english_tag = td.find('div', class_='description mw-content-ltr en')
        if english_tag:
            if english_tag.text.startswith('English:'):
                return english_tag.text[8:].strip()
            return english_tag.text.strip()
        return None

    try:
        if detect(td.text) == 'en':
            return td.text.strip()
    except LangDetectException:
        print(td.text)
    finally:
        return None


def get_caption(res):
    soup = BeautifulSoup(res, 'html.parser')
    for a in soup.find_all('a', href=True):
        if a['href'].startswith('https://upload.wikimedia.org/wikipedia/commons'):
            return a['href']


async def update_table(tables):
    titles = [table.title for table in tables]
    urls = [wikimeida_commons(title) for title in titles]

    results = await asyncio.gather(*[fetch(url, 'html') for url in urls])
    results = [(get_caption(result), get_url(result)) for result in results]

    for (caption, url), table in zip(results, tables):
        table.url = url
        if caption and len(caption) > 2000:
            print(table.title)
        table.caption = caption[:2000] if caption else caption


async def update_table_using_api(tables):

    titles = [table.title for table in tables]
    urls = [f(title) for title in titles for f in (parse_url, query_url)]

    results = await asyncio.gather(*[fetch(url, 'json') for url in urls])
    parse_results = results[::2]
    query_results = results[1::2]

    parse_results = [result['parse']['wikitext']['*'] for result in parse_results]
    query_results = [next(iter(result['query']['pages'].values())) for result in query_results]

    for parse_result, query_result, table in zip(parse_results, query_results, tables):

        table.url = query_result['imageinfo'][0]['url']
        table.mediatype = query_result['imageinfo'][0]['mediatype']
        table.mime = query_result['imageinfo'][0]['mime']
        if '{{en|1=' in parse_result:
            table.caption = parse_result.split('{{en|1=')[-1].split('}}')[0]
        elif '|Description=' in parse_result:
            table.caption = parse_result.split('|Description=')[-1].split('|')[0].strip()
        else:
            table.caption = None


if __name__ == '__main__':

    asyncio.run(
        update_table(
            [
                wikimeida_commons('Ber Chayim Temple 1923.jpg'),
                wikimeida_commons('Singapore Zoo Elephant-01 (8322881775).jpg')
            ]
        )
    )
