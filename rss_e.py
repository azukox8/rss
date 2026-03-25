import feedparser
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import datetime

RSS_FEEDS = {
    "BBC news": "https://feeds.bbci.co.uk/polska/rss.xml",
    "Polsat News": "http://www.polsatnews.pl/rss/wszystkie.xml",
    "RMF": "http://www.rmf.fm/rss/rss.xml",
    "WP": "http://wiadomosci.wp.pl/rss.xml"
    
}

book = epub.EpubBook()
book.set_title('News')
book.set_language('pl')

all_chapters = []
toc = []

for portal_name, rss_url in RSS_FEEDS.items():
    feed = feedparser.parse(rss_url)

    safe_name = portal_name.replace(" ", "_")

    section_page = epub.EpubHtml(
        title=f"--- {portal_name} ---",
        file_name=f'{safe_name}_section.xhtml',
        content=f"<h1>--- {portal_name} ---</h1>"
    )

    book.add_item(section_page)

    portal_chapters = [section_page]
    all_chapters.append(section_page)

    for i, entry in enumerate(feed.entries[:15]):
        res = requests.get(entry.link)

        content = res.content  # raw bytes
        soup = BeautifulSoup(content, 'html.parser', from_encoding=res.apparent_encoding)

        paragraphs = soup.find_all('p')
        content = "".join(f"<p>{p.text}</p>" for p in paragraphs)

        chapter = epub.EpubHtml(
            title=entry.title,
            file_name=f'{portal_name}_{i}.xhtml',
            content=f"<h1>{entry.title}</h1>{content}"
        )

        book.add_item(chapter)
        portal_chapters.append(chapter)
        all_chapters.append(chapter)

    # 🔥 TU tworzymy sekcję nadrzędną
    toc.append((epub.Section(portal_name), portal_chapters))

# TOC z sekcjami
book.toc = toc

book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

book.spine = ['nav'] + all_chapters
now = datetime.datetime.now()
today = datetime.datetime.strftime(now, "%m_%d_%y-%H")
epub.write_epub(f'news{today}.epub', book)
