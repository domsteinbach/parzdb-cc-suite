from model.commentary import Commentary
from model.literature import Literature, CommentaryIsCiting, IGNORED_LITERATURE_KEYS

class DataAssembler:
    def __init__(self, documents):
        self.not_found_literature = []
        self._documents = documents
        self.literature = self._get_literature(documents)
        self.commentaries = self._get_commentaries(documents)
        self.commentary_citings = self._get_commentary_is_citing()

    def _get_commentaries(self, documents):
        commentaries = []
        current_commentary = None
        for doc in documents:
            c_idx = 1
            for p in doc.paragraphs:
                if p.is_title:
                    # If there's a new title, append the current_commentary to the list and create a new Commentary
                    # with the title paragraph
                    if current_commentary and current_commentary.id not in [c.id for c in commentaries]:
                        commentaries.append(current_commentary)
                        c_idx += 1
                    # Start a new commentary with the title paragraph
                    current_commentary = Commentary(p, c_idx)
                else:
                    # Add the paragraph as content to the current commentary if it exists
                    if current_commentary and current_commentary.fassung == p.fassung:
                        current_commentary.add_content(p)
                    else:
                        print(f"Comment {p.idx} in {doc.file_name} is not preceded by a title.")
                        # If a paragraph appears before any title, raise an error
                        # raise ValueError(f"Comment {c.id} in {doc.file_name} is not preceded by a title.")

            # After iterated all paragraphs, append also the last commentary if it exists
            if current_commentary:
                commentaries.append(current_commentary)

        return commentaries

    def _get_literature(self, documents):
        literature = {}
        l_idx = 1
        for doc in documents:
            for l in doc.literature_paragraphs:
                literature_pot = Literature(l_idx, l)
                if 'Schöller' in literature_pot.key:
                    print('debug')
                if literature_pot.key not in literature and literature_pot.key.strip() not in IGNORED_LITERATURE_KEYS:
                    literature[literature_pot.key] = literature_pot
                    l_idx += 1
                else:
                    literature.get(literature_pot.key).fassungen.append(literature_pot.fassungen[0])
                    #print(f"WARNING: Literature {literature_pot.key} already in literature.")
        return literature

    def _get_commentary_is_citing(self):
        commentary_citings = []
        c_idx = 1
        for c in self.commentaries:
            lit = c.get_cited_literature_keys()
            for key in lit:
                if key not in self.literature:
                    found_key = self.deep_search_lit_key(key)
                    if not found_key:
                        clean_key = self.deep_search_lit_key(key.replace(' ', '').replace('.', ''))
                        if clean_key and len(clean_key) > 2:
                            found_key = self.deep_search_lit_key(clean_key)

                    if found_key:
                        key = found_key
                    else:
                        print(f"WARNING: Literature {key} not found in assembler.")
                        self.not_found_literature.append([key, c.fassung, c.vers])
                        continue
                cc = CommentaryIsCiting(c_idx, c.id, self.literature[key].id)
                commentary_citings.append(cc)
                c_idx += 1

        return commentary_citings

    def deep_search_lit_key(self, key):

        # iterate over self.literature and check if the key is contained in the literature key
        found_keys = []

        for k, v in self.literature.items():
            if key in v.key or key in v.key.replace(' ', '').replace('.', '') or v.key in key:
                found_keys.append(k)
        if len(found_keys) == 1:
            return found_keys[0]
        elif len(found_keys) > 1:
            print(f"WARNING: Literature key {key} found multiple times in literature.")

        elif len(found_keys) == 0:
            for k, v in self.literature.items():
                if ' ' in v.key and len(v.key.split(' ')[0]) > 7:
                    if v.key.split(' ')[0] in key or key in v.key.split(' ')[0]:
                        found_keys.append(k)
        if len(found_keys) == 1:
            return found_keys[0]
        elif len(found_keys) > 1:
            print(f"WARNING: Literature key {key} found multiple times in literature.")

