from app.models.article import Article


class Preface(Article):
    """
    Preface Article model
    """
    type: str = "Preface"
