import aiohttp
import asyncio
from bs4 import BeautifulSoup
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from multiprocessing import Pool


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
                print(f'response status: {res.status} | url: {url}')
            if res.status == 404:
                return None
            assert res.status == 200
            if return_type == 'html':
                return await res.read()
            elif return_type == 'json':
                return await res.json()


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


async def update_table(tables, processes):
    print('Start updating table')
    titles = [table.title for table in tables]
    urls = [wikimeida_commons(title) for title in titles]

    results = await asyncio.gather(*[fetch(url, 'html') for url in urls])
    print('gathering finished')
    with Pool(processes) as p:
        results = p.map(caption_and_url, results)
    for (caption, url), table in zip(results, tables):
        table.url = url

        if caption and len(caption) > 2000:
            new_caption = caption.split('\n')[0]
            print(f'Caption is Too long | Splited caption: {new_caption}')
            if len(new_caption) > 2000:
                raise Exception(f'Too long caption\n title: {table.title}\n caption: {caption}')
            else:
                caption = new_caption
        table.caption = caption


async def test_update_table(titles):
    urls = [wikimeida_commons(title) for title in titles]

    results = await asyncio.gather(*[fetch(url, 'html') for url in urls])
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
        test_update_table(
            [
                'Ber Chayim Temple 1923.jpg',
                'Singapore Zoo Elephant-01 (8322881775).jpg',
                'Bronzen_kandelaars_-_Boven-Leeuwen_-_20038982_-_RCE.jpg',
                'Bong_Joon-ho_FilmFest_Muenchen_04Jul2019.jpg',
                'Santa_Comba_de_Gargantós.jpg'
            ]
        )
    )
