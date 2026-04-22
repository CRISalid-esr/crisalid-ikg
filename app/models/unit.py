from app.models.group_or_organisation_unit import MissionType
from app.models.organisation_unit import OrganisationUnit


class Unit(OrganisationUnit):
    """
    Unit model
    """
    main_mission: MissionType
