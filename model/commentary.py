from bs4 import BeautifulSoup
from shared.html import get_as_element, get_as_a, get_as_dynamic_hyperlink, clean_up_html
from model.commentary_title import CommentaryTitle
from model.commentary_paragraph import CommentaryParagraph
from extract_docx import PararaphHyperlinkElement
from model.literature import IGNORED_LITERATURE_KEYS
from config import VERSION_HASH


class Commentary:
    def __init__(self, paragraph, idx):
        self.id = f"C_{paragraph.fassung.upper()}_{str(idx).zfill(5)}"
        self.fassung = paragraph.fassung
        self.text_orig = paragraph.text
        self.vers, self.end_vers = self.get_verses(paragraph)
        self.fassung_targets = self._get_fassung_targets(paragraph.text)

        self.title = CommentaryTitle(paragraph, self.id)
        self._content = []  # List of CommentaryParagraphs

    def get_verses(self, paragraph):
        v_pot = paragraph.text.split(' ')[0].replace(':', '')
        verse = None
        end_verse = None
        if '–' in v_pot:
            verse = v_pot.split('–')[0]
            end_verse = v_pot.split('–')[1]
            if not '.' in end_verse:  # then the whole verse is of format 113.2-8; we need then to create 113.2 as verse and 113.8 as end_verse
                end_verse = verse.split('.')[0] + '.' + end_verse
        else:
            verse = v_pot
        return [verse, end_verse]

    def add_content(self, paragraph):
        p = CommentaryParagraph(paragraph, self.id)
        self._content.append(p)

    def _get_fassung_targets(self, title_text):
        if self.fassung != 'a':
            return [self.fassung]

        if '(' not in title_text:
            return ['D', 'G', 'm', 'T']

        parts = title_text.split('(')[1].split(')')[0].split('*')
        return [part for part in parts if part]


    ### pass literature as parameter if there should be literature entries in the commentary
    def get_as_html(self, literature):
        soup = BeautifulSoup(features="html.parser")

        html = soup.new_tag("html", lang="en")
        soup.append(html)
        head = soup.new_tag("head")
        head.append(soup.new_tag("meta", charset="UTF-8"))
        html.append(head)
        head.append(soup.new_tag("title"))
        head.title.string = "Fassungskommentar"

        #css_link = soup.new_tag("link", rel="stylesheet", href=f"commentary.css?v={VERSION_HASH}")
        #head.append(css_link)

        body = soup.new_tag("body")
        html.append(body)

        body.append(self._get_html_main(soup))

        for l in literature:
            body.append(l.as_html())

        # Clean up HTML to merge single-space spans
        return clean_up_html(str(soup))

    def get_as_html_element_str(self, literature=None):
        soup = BeautifulSoup(features="html.parser")
        html = self._get_html_main(soup)
        if literature is not None:
            for l in literature:
                html.append(l.as_html())
        return clean_up_html(str(html))

    def _get_html_main(self, soup):
        main_div = soup.new_tag("div", id=self.id, **{"class": "fassungs-kommentar"})
        title_div = BeautifulSoup(self.get_title_as_html(), "html.parser").find("div", {"class": "fk-title"})
        if self.fassung != 'a':
            title_div = self.append_fassung_to_title(title_div)

        main_div.append(title_div)
        main_div.append(BeautifulSoup(self.get_content_as_html(), "html.parser"))
        return main_div


    # Append the "fassung" in brackets to the title's text for the fassungs specific commentaries
    # example: Fro "2.5: noch" in Fassung G we append the Fassung "2.5: noch (*G)"
    def append_fassung_to_title(self, title_div):
        # Add the "fassung" in brackets to the title's text
        v = self.end_vers if self.end_vers else self.vers
        if title_div.text.endswith(v):
            # There is no ":" or citings like "2.5: noch" in the title, so we can just append the fassung in brackets
            # without overriding the structure
            title_div.append(f" (*{self.fassung})")
        else:
            for tag in title_div.contents:
                if ':' in tag.text:
                    # Remove spaces and get the clean position of the ":"
                    clean_text = tag.text.replace(' ', '')  # Remove spaces for comparison
                    colon_position = clean_text.find(':')

                    if colon_position != -1:
                        # Replace the ":" in the original text
                        original_text = tag.text
                        updated_text = (
                                original_text[:colon_position]
                                + f" (*{self.fassung}):"
                                + original_text[colon_position + 1:]
                        )
                        tag.string = updated_text  # Update the tag's text
                        break  # Stop after modifying the first occurence of ":"
        return title_div

    def get_title_as_html(self):
        soup = BeautifulSoup(features="html.parser")
        title_div = soup.new_tag("div", **{"class": "fk-title"})
        for e in self.title.elements:
            if e.h_ref:
                title_div.append(BeautifulSoup(get_as_a(e), "html.parser"))
            else:
                title_div.append(BeautifulSoup(get_as_element(e), "html.parser"))
        return str(title_div)

    def get_content_as_html(self):
        soup = BeautifulSoup(features="html.parser")
        content_div = soup.new_tag("div", **{"class": "fk-content"})
        for c in self._content:
            paragraph = soup.new_tag("p", **{"class": "fk-commentary"})
            for e in c.elements:
                if e.h_ref:
                    paragraph.append(BeautifulSoup(get_as_a(e), "html.parser"))
                else:
                    #if e.has_versnumber_for_citing:
                        #paragraph.append(BeautifulSoup(get_as_dynamic_hyperlink(e), "html.parser"))
                        #print("DYNAMIC HYPERLINK", self.vers)

                    paragraph.append(BeautifulSoup(get_as_element(e), "html.parser"))
            content_div.append(paragraph)
        return str(content_div)

    def get_cited_literature_keys(self):
        keys = []
        for c in self._content:
            for index, e in enumerate(c.elements):
                if not isinstance(e, PararaphHyperlinkElement):
                    if not e.style.small_caps or len(e.text) <= 2:
                        continue
                    # if e is not instance of HyperlinkElement, it is a normal element
                    fuu = e.text.strip().replace(' ', '')
                    if fuu in IGNORED_LITERATURE_KEYS:
                        continue

                    if e.text not in keys:
                        if 'MHD' in e.text.upper():
                            k = self.get_mhd_key(c, e, index)
                            if k:
                                keys.append(k)
                        else:
                            keys.append(e.text)
                else:
                    for h_e in e.elements:
                        if not h_e.style.small_caps or len(h_e.text) <= 2:
                            continue
                        # if e is not instance of HyperlinkElement, it is a normal element
                        fuu = h_e.text.strip().replace(' ', '')
                        if fuu in IGNORED_LITERATURE_KEYS:
                            continue
                        if h_e.text not in keys:
                            keys.append(h_e.text)

        return keys

    def get_mhd_key(self, c, e, e_index):
        search_str = ''
        if 'MHD.GR.20' in e.text.upper().replace(' ', ''):
            # it seems complete
            search_str = e.text.upper()
        else:
            # look at the next five elements if there is one containing 2007, 2009 or 2018
            search_str = ''
            for i in range(1, 6):
                if e_index + i < len(c.elements):
                    search_str = search_str + c.elements[e_index + i].text

        if '2007' in search_str:
            return 'MHD2007'
        if '2009' in search_str:
            return 'MHD2009'
        if '2018' in search_str:
            return 'MHD2018'
        return None


