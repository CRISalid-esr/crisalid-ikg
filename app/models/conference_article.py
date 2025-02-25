from app.models.article import Article


class ConferenceArticle(Article):
    """
    Conference Article model
    """
    type: str = "ConferenceArticle"
