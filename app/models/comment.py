from app.models.article import Article


class Comment(Article):
    """
    Comment Article model
    """
    type: str = "Comment"
