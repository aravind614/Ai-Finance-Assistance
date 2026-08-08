import requests
from bs4 import BeautifulSoup


def fetch_webpage(url: str) -> str:
    """
    Fetch a webpage and return readable text.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup(
        ["script", "style", "noscript", "header", "footer", "nav"]
    ):
        element.decompose()

    return soup.get_text(separator=" ", strip=True)


def fetch_links(url: str) -> list[dict]:
    """
    Extract links from a webpage.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = []

    for link in soup.find_all("a", href=True):
        title = link.get_text(" ", strip=True)
        href = link["href"]

        links.append(
            {
                "title": title,
                "url": href,
            }
        )

    return links


def fetch_pdf(url: str) -> str:
    """
    Download a PDF and extract its text.
    """

    import io
    from pypdf import PdfReader

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    reader = PdfReader(io.BytesIO(response.content))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)
