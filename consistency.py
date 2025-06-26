import requests
from bs4 import BeautifulSoup

from export import Exporter


class ConsistencyChecker:
    def __init__(self):
        self.comments_w_failed_hyperlinks = []

    def test_complete_comment_title_pairs(self, docxExtractor):
        for doc in docxExtractor.documents:
            if len(doc.comments) % 2 == 0:
                raise ValueError(f"Number of comments in {doc.file_name} is even, expected an uneven number.")

            for comment in doc.comments:
                if comment.idx % 2 != 0 and comment.is_title:
                    raise ValueError(f"Comment {comment.id} in {doc.file_name} is a title but should not be.")
                if comment.idx % 2 == 0 and not comment.is_title:
                    raise ValueError(f"Comment {comment.id} in {doc.file_name} is not a title but should be.")


    def check_hyperlinks(self, assembler):
        e = Exporter(assembler)
        for idx, c in enumerate(assembler.commentaries):
            html = e.export_commentary_as_html(c, True, True)
            # Parse the HTML string to find all <a> tags
            soup = BeautifulSoup(html, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True)]
            for link in links:
                try:
                    # Try HEAD request first
                    response = requests.head(link, timeout=5)
                    if response.status_code == 404:
                        print(f"fuu: {link} returned 404 with HEAD")
                        self.comments_w_failed_hyperlinks.append(c)
                        continue
                except requests.RequestException:
                    # Handle HEAD request failure, try GET request
                    try:
                        response = requests.get(link, timeout=5)
                        if response.status_code == 404:
                            print(f"fuu: {link} returned 404 with GET")
                            self.comments_w_failed_hyperlinks.append(c)
                    except requests.RequestException:
                        # Handle GET request failure
                        print(f"fuu: {link} failed with error.")
                        self.comments_w_failed_hyperlinks.append(c)