"""
Internal institution model
"""
from app.models.institution import Institution

class InternalInstitution(Institution):
    """
    Internal institution API model
    """
    external = False
