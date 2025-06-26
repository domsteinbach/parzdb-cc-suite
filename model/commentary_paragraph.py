
class CommentaryParagraph:
    def __init__(self, paragraph, parentId):
        #if paragraph.is_title:
            #raise ValueError(f"CommentParagraph {paragraph.idx} is a title.")
        self.idx = paragraph.idx
        self.id = f"{parentId}_C_{str(self.idx).zfill(5)}"
        self.text = paragraph.text
        self.fassung = paragraph.fassung
        self.elements = paragraph.comment_elements
        self.is_list_item = paragraph.is_list_item
