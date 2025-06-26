from bs4 import BeautifulSoup
from model.commentary_paragraph import CommentaryParagraph
from shared.html import get_as_element, get_as_a

IGNORED_LITERATURE_KEYS = ['2007', '2009', '2008', '1989', '2022', '2018', '.', 'GR', 'GR.', '1992', '1982', '1929', '1993', '1833', '2000', '2019', 'Online', '1968']

class Literature:
    def __init__(self, idx, paragraph):
        self.idx = idx
        self.id = f"L_{str(idx).zfill(3)}"
        self.fassungen = [paragraph.fassung]
        self._paragraph = CommentaryParagraph(paragraph, self.id)
        self.key = self.getKey()

    def getKey(self):
        if not 'MHD' in self._paragraph.elements[0].text.upper():
            return self._paragraph.elements[0].text
        else: # Super special case MHD
            year = ''
            if '2007' in self._paragraph.text[:20]:
                year = '2007'
            elif '2009' in self._paragraph.text[:20]:
                year = '2009'
            elif '2018' in self._paragraph.text[:20]:
                year = '2018'
            else:
                print("MHD")
                print('WARNING, NO YEAR FOR MHD FOUND', self._paragraph.text[:20])
            return f"MHD{year}"




    def as_html(self):
        soup = BeautifulSoup(features="html.parser")
        main_div = soup.new_tag("div", id=self.id, **{"class": "fk-literatur"})
        main_div.append(BeautifulSoup(self.get_content_as_html(), "html.parser"))

        return main_div

    def get_content_as_html(self):
        soup = BeautifulSoup(features="html.parser")
        content_div = soup.new_tag("div", **{"class": "fk-content"})
        paragraph = soup.new_tag("p", **{"class": "fk-commentary"})
        for e in self._paragraph.elements:
            if e.h_ref:
                paragraph.append(BeautifulSoup(get_as_a(e), "html.parser"))
            else:
                paragraph.append(BeautifulSoup(get_as_element(e), "html.parser"))
        content_div.append(paragraph)
        return str(content_div)


class CommentaryIsCiting:
    def __init__(self, idx, commentary, literature):
        self.idx = idx
        self.id = f"C_{str(idx).zfill(5)}"
        self.commentary = commentary
        self.literature = literature
