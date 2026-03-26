import feedparser
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import datetime
import os

def handler(request):
    RSS_FEEDS = {
        "BBC news": "https://feeds.bbci.co.uk/polska/rss.xml",
        "Polsat News": "http://www.polsatnews.pl/rss/wszystkie.xml",
        "RMF": "http://www.rmf.fm/rss/rss.xml",
        "WP": "http://wiadomosci.wp.pl/rss.xml"
    }

    # 📁 Vercel: tylko /tmp jest zapisywalne
    now = datetime.datetime.now()
    today = now.strftime("%m_%d_%y-%H")
    epub_name = f"/tmp/news_{today}.epub"

    book = epub.EpubBook()
    book.set_title('News')
    book.set_language('pl')

    all_chapters = []
    toc = []

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for portal_name, rss_url in RSS_FEEDS.items():
        feed = feedparser.parse(rss_url)

        safe_name = portal_name.replace(" ", "_")

        # 🔹 separator portalu
        section_page = epub.EpubHtml(
            title=f"--- {portal_name} ---",
            file_name=f'{safe_name}_section.xhtml',
            content=f"<h1>--- {portal_name} ---</h1><hr>"
        )

        book.add_item(section_page)

        portal_chapters = [section_page]
        all_chapters.append(section_page)

        for i, entry in enumerate(feed.entries[:15]):
            try:
                res = requests.get(entry.link, headers=headers, timeout=10)

                soup = BeautifulSoup(
                    res.content,
                    'html.parser',
                    from_encoding=res.apparent_encoding
                )

                paragraphs = soup.find_all('p')
                content = "".join(f"<p>{p.get_text()}</p>" for p in paragraphs)

                chapter = epub.EpubHtml(
                    title=entry.title,
                    file_name=f'{safe_name}_{i}.xhtml',
                    content=f"<h1>{entry.title}</h1>{content}"
                )

                book.add_item(chapter)
                portal_chapters.append(chapter)
                all_chapters.append(chapter)

            except Exception as e:
                print(f"Błąd przy {entry.link}: {e}")
                continue

        toc.append((epub.Section(portal_name), portal_chapters))

    # 📚 EPUB struktura
    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + all_chapters

    epub.write_epub(epub_name, book)

    # 📩 TELEGRAM
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendDocument"

        with open(epub_name, "rb") as f:
            requests.post(
                url,
                data={"chat_id": chat_id},
                files={"document": f}
            )

    return {
        "statusCode": 200,
        "body": f"Wysłano EPUB: {epub_name}"
    }