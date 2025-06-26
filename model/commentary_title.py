
class CommentaryTitle:
    def __init__(self, paragraph, parentId):
        if not paragraph.is_title:
            raise ValueError(f"CommentParagraph {paragraph.idx} is not a title.")
        self.idx = paragraph.idx
        self.id = f"{parentId}_T"
        self.text = paragraph.text
        self.fassung = paragraph.fassung
        self.elements = paragraph.comment_elements

