from app.models.article import Article


class ConferenceAbstract(Article):
    """
    Conference Abstract Article model
    """
    type: str = "ConferenceAbstract"
