import requests
from django.conf import settings
from requests.exceptions import ConnectionError
from time import sleep
from .logger import logger
from bs4 import BeautifulSoup
from urllib.parse import urlencode


def retry_request_decorator(func):
    """
    Decorator for requests functions,
    keeps on trying for a specific amount of time

    :param func: request function
    :type func: Any
    """

    def inner(*args, **kwargs):
        tries = 0

        while tries < 10:
            try:
                res = func(*args, **kwargs)
                return res
            except ConnectionError:
                tries += 1
                logger.info(f"Retrying for {func.__name__}: Tries {tries}")
                sleep(.5)

        raise ConnectionError(f"Request for {func.__name__} failed")

    return inner


@retry_request_decorator
def get_content_title_css_file(url):
    """Get the title and css file from the Gov API"""
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string
        css = soup.find('link', rel='stylesheet')
        return title, css['href'], response.text

    return None, None, None


@retry_request_decorator
def get_content_text(url):
    """Get text content from the Gov API"""
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.text
    return None, None, None


@retry_request_decorator
def get_collection_name(collection_code):
    """Get collection name from the Gov API"""
    response = requests.get(settings.GOV_API_URL)
    if response.status_code == 200:
        data: list = response.json()['collections']
        filtered = list(filter(
            lambda x: x['collectionCode'] == collection_code, data
        ))
        if len(filtered) > 0:
            return filtered[0]["collectionName"]

    return None


@retry_request_decorator
def request_data(url):
    """Request data from the Gov API"""
    response = requests.get(url, params={'fetchChildrenOnly': '1'})
    if response.status_code == 200:
        return response.json()

    return None


@retry_request_decorator
def get_cfr_json(title, date):
    url = f"/versioner/v1/structure/{date}/title-{title}.json"
    full_url = f"{settings.ECFR_API}{url}"
    response = requests.get(full_url)
    return response.json()


@retry_request_decorator
def get_cfr_titles() -> list[dict]:
    url = f"{settings.ECFR_API}/versioner/v1/titles"
    response = requests.get(url)
    return response.json().get("titles", [])


@retry_request_decorator
def cfr_full_text_search(query: str):
    """Full text search for CFR"""
    url = f"{settings.ECFR_API}/search/v1/results"

    response = requests.get(url, params={
        "query": query,
        "per_page": 20,
        "order": "relevance"
    })

    if response.status_code == 200:
        data = response.json()

        # Get the results
        results = data.get('results', [])

        # filter out sections type
        sections = list(filter(lambda x: x['type'] == 'Section', results))

        # Get the title and section from the hierarchy key
        sections = list(map(lambda x: {
            'title': x['hierarchy']['title'],
            'section': x['hierarchy']['section'],
        }, sections))

        return sections


@retry_request_decorator
def get_cfr_ancestors(
    title: str, date: str, node_type: str, identifier: str
) -> str:
    """Get the CFR Doc URL"""
    ancestor = f"{settings.ECFR_API}/versioner/v1/ancestry/{date}/title-{title}.json?{node_type}={identifier}"  # noqa: E501
    data = requests.get(ancestor)

    if data.status_code == 200:
        ancestors = data.json().get('ancestors', [])

        if len(ancestors) > 0:
            return ancestors[1:]


@retry_request_decorator
def get_cfr_html(
    title: str, date: str, node_type: str, identifier: str
) -> str:
    """Get the ECFR HTML Content"""
    ancestors = get_cfr_ancestors(title, date, node_type, identifier)

    if ancestors is None:
        return None

    query_params = map(
        lambda x: f"{x['type']}={x['identifier']}",
        ancestors
    )
    query = "&".join(query_params)

    url = f"{settings.ECFR_API}/renderer/v1/content/enhanced/{date}/title-{title}?{query}"  # noqa: E501

    response = requests.get(url)
    if response.status_code == 200:
        return response.text


def get_cfr_pdf_link(
    title: str, part: str, section_num: str = None,
    volume: str = None
) -> str:
    """Get the Gov PDF Link"""

    params = {
        'volume': volume,
        'sectionnum': section_num,
        'year': 'mostrecent',
        'link-type': 'pdf',
    }

    if volume is None:
        del params['volume']

    if section_num is None:
        del params['sectionnum']

    url = f"https://www.govinfo.gov/link/cfr/{title}/{part}?{urlencode(params)}"  # noqa: E501
    return url
