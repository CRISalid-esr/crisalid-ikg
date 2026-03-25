"""
Managed institution model
"""
from app.models.institution import Institution

class ManagedInstitution(Institution):
    """
    Managed institution API model
    """
    external = False
