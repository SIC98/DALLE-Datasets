import aiohttp
from aiohttp.client_exceptions import ClientConnectorError, ClientPayloadError
import asyncio
from bs4 import BeautifulSoup
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from multiprocessing import Pool
from preprocess_image import reshape_image
import time

url_to_mime = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'bmp': 'image/bmp',
    'svg': 'image/svg+xml',
    'tif': 'image/tiff',
    'tiff': 'image/tiff',
    'xcf': 'image/x-xcf',
    'webp': 'image/webp'
}


def offset_to_url(offset):
    return f'https://commons.wikimedia.org/w/index.php?title=Special:NewFiles&dir=prev&offset={offset}&limit=500&user' \
           f'=&mediatype%5B0%5D=BITMAP&mediatype%5B1%5D=ARCHIVE&mediatype%5B2%5D=DRAWING&start=&end=&wpFormIdentifier' \
           f'=specialnewimages'


def query_url(title):
    return f'https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&titles=File:{title}&utf8=' \
           f'1&iiprop=comment|url|mediatype|mime&iilimit=1'


def parse_url(title):
    return f'https://commons.wikimedia.org/w/api.php?action=parse&format=json&page=File:{title}&prop=wikitext&utf8=1'


def wikimeida_commons(title):
    return f'https://commons.wikimedia.org/wiki/File:{title}'


async def curl(url, return_type):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            if res.status != 200:
                print(f'response status: {res.status} | url: {url}')
            if res.status == 404:
                return None
            assert res.status == 200
            if return_type == 'read':
                return await res.read()
            elif return_type == 'json':
                return await res.json()


async def try_curl_until_no_error(urls, return_type, seconds):
    while True:
        try:
            return await asyncio.gather(*[curl(url, return_type) for url in urls])
        except (AssertionError, ClientConnectorError, ClientPayloadError):
            time.sleep(seconds)
            print(f'sleep {seconds} seconds and try again')
            pass


def get_caption(res):

    if not res:
        return None

    soup = BeautifulSoup(res, 'html.parser')
    captions = soup.find('div', class_='wbmi-caption-value', lang='en', dir='ltr')

    if captions and captions.text != 'Add a one-line explanation of what this file represents':
        return captions.text

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
        print(f"Can't detect language type of caption | caption: {td.text}")
    finally:
        return None


def get_url(res):

    if not res:
        return None

    soup = BeautifulSoup(res, 'html.parser')
    for a in soup.find_all('a', href=True):
        if a['href'].startswith('https://upload.wikimedia.org/wikipedia/commons'):
            return a['href']


def caption_and_url(result):
    return get_caption(result), get_url(result)


async def crawl_caption(tables, processes, seconds):
    print('Start updating table')
    titles = [table.title for table in tables]
    urls = [wikimeida_commons(title) for title in titles]

    results = await try_curl_until_no_error(urls, 'read', seconds)
    print('gathering finished')
    with Pool(processes) as p:
        results = p.map(caption_and_url, results)
    for (caption, url), table in zip(results, tables):
        table.url = url
        table.mime = url_to_mime[url.split('.')[-1].lower()]

        if caption and len(caption) > 2000:
            new_caption = caption.split('\n')[0]
            print(f'Caption is Too long | Splited caption: {new_caption}')
            if len(new_caption) > 2000:
                print(f'Too long caption\n title: {table.title}\n caption: {caption}')
                caption = None
            else:
                caption = new_caption
        table.caption = caption


async def crawl_image(tables, seconds):
    print('Start crawling images')
    urls = [table.url for table in tables]

    results = await try_curl_until_no_error(urls, 'read', seconds)
    print('gathering finished')

    results = [reshape_image(result, table.mime) for result, table in zip(results, tables)]
    for image, table in zip(results, tables):
        table.image = image


async def test_crawl_caption(titles, seconds):
    urls = [wikimeida_commons(title) for title in titles]

    results = await try_curl_until_no_error(urls, 'read', seconds)
    results = [(get_caption(result), get_url(result)) for result in results]

    for caption, url in results:

        if caption and len(caption) > 2000:
            new_caption = caption.split('\n')[0]
            print(f'Caption is Too long | Splited caption: {new_caption}')
            if len(new_caption) > 2000:
                raise Exception(f'Too long caption\n caption: {caption}')
            else:
                caption = new_caption
        print(f'caption: {caption}')


async def crawl_caption_using_api(tables, seconds):

    titles = [table.title for table in tables]
    urls = [f(title) for title in titles for f in (parse_url, query_url)]

    results = await try_curl_until_no_error(urls, 'json', seconds)
    parse_results = results[::2]
    query_results = results[1::2]

    parse_results = [result['parse']['wikitext']['*'] for result in parse_results]
    query_results = [next(iter(result['query']['pages'].values())) for result in query_results]

    for parse_result, query_result, table in zip(parse_results, query_results, tables):
        table.url = query_result['imageinfo'][0]['url']
        table.mediatype = query_result['imageinfo'][0]['mediatype']
        table.mime = query_result['imageinfo'][0]['mime']
        if '{{en|1=' in parse_result:
            caption = parse_result.split('{{en|1=')[-1].split('}}')[0]
        elif '|Description=' in parse_result:
            caption = parse_result.split('|Description=')[-1].split('|')[0].strip()
        elif '|description=' in parse_result:
            caption = parse_result.split('|description=')[-1].split('|')[0].strip()
        else:
            caption = None

        if caption and len(caption) > 2000:
            new_caption = caption.split('\n')[0]
            if len(new_caption) > 2000:
                raise Exception(f'Too long caption\n title: {table.title}\n caption: {caption}')
            else:
                caption = new_caption
        table.caption = caption


if __name__ == '__main__':

    asyncio.run(
        test_crawl_caption(
            [
                'Ber Chayim Temple 1923.jpg',
                'Singapore Zoo Elephant-01 (8322881775).jpg',
                'Bronzen_kandelaars_-_Boven-Leeuwen_-_20038982_-_RCE.jpg',
                'Bong_Joon-ho_FilmFest_Muenchen_04Jul2019.jpg',
                'Santa_Comba_de_Gargantós.jpg'
            ],
            seconds=60
        )
    )
