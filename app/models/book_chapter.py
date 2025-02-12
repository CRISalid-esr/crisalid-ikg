from app.models.article import Article


class BookChapter(Article):
    """
    Book Chapter model
    """
    type: str = "BookChapter"
