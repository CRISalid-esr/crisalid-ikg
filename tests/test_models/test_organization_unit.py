from datetime import date

import pytest
from pydantic import ValidationError

from app.models.organization_types import (
    GenericOrganizationType,
    MissionType,
    NationalOrganizationType,
    OrgMembershipPosition,
)
from app.models.organization_unit import (
    Institution,
    InstitutionSubdivision,
    OrgInclusion,
    OrgMembership,
    ResearchUnit,
    nonUnitAdapter,
    unitAdapter,
)


def test_create_institution_from_json(institution_a_json_data):
    org = nonUnitAdapter.validate_python(institution_a_json_data)
    assert isinstance(org, Institution)
    assert org.generic_type == GenericOrganizationType.INSTITUTION
    assert org.national_type == NationalOrganizationType.UNIV
    assert len(org.short_labels) == 2
    assert len(org.long_labels) == 2
    assert org.uid is None
    assert any(sl.value == "ExUni" and sl.language == "en" for sl in org.short_labels)
    assert any(ll.value == "Example University" for ll in org.long_labels)


def test_create_institution_subdivision_from_json(institution_subdivision_a_json_data):
    org = nonUnitAdapter.validate_python(institution_subdivision_a_json_data)
    assert isinstance(org, InstitutionSubdivision)
    assert org.generic_type == GenericOrganizationType.INSTITUTION_SUBDIVISION
    assert org.national_type == NationalOrganizationType.FAC
    assert len(org.parents) == 1
    parent = org.parents[0]
    assert isinstance(parent, OrgInclusion)
    assert parent.target == "local-EXAMPLE-UNIV-001"
    assert parent.start_date == date(2010, 1, 1)
    assert parent.end_date == date(2030, 12, 31)


def test_create_research_unit_from_json(research_unit_center_json_data):
    org = unitAdapter.validate_python(research_unit_center_json_data)
    assert isinstance(org, ResearchUnit)
    assert org.generic_type == GenericOrganizationType.UNIT
    assert org.national_type == NationalOrganizationType.UMR
    assert org.main_mission == MissionType.RESEARCH
    assert len(org.local_types) == 2
    assert any(lt.value == "Center" and lt.language == "en" for lt in org.local_types)
    assert len(org.memberships) == 1
    membership = org.memberships[0]
    assert isinstance(membership, OrgMembership)
    assert membership.target == "local-EXAMPLE-UNIV-001"
    assert membership.position == OrgMembershipPosition.MAIN_SUPERVISION
    assert membership.start_date == date(2000, 1, 1)
    assert membership.end_date is None
    assert len(org.long_labels) == 2
    assert len(org.short_labels) == 1


def test_non_unit_adapter_validates_institution(institution_a_json_data):
    org = nonUnitAdapter.validate_python(institution_a_json_data)
    assert isinstance(org, Institution)


def test_unit_adapter_validates_research_unit(research_unit_center_json_data):
    org = unitAdapter.validate_python(research_unit_center_json_data)
    assert isinstance(org, ResearchUnit)


def test_invalid_national_type_for_generic_type_raises():
    data = {
        "generic_type": "unit",
        "type": "FAC",  # FAC is only for institution_subdivision
        "main_mission": "research",
        "identifiers": [{"type": "local", "value": "CENTER-001"}],
    }
    with pytest.raises(ValidationError):
        unitAdapter.validate_python(data)


def test_organization_requires_national_type_or_local_type_or_long_label():
    data = {
        "generic_type": "institution",
        "identifiers": [{"type": "local", "value": "INST-001"}],
        "local_types": [],
        "long_labels": [],
    }
    with pytest.raises(ValidationError):
        nonUnitAdapter.validate_python(data)


def test_contacts_parsed_to_addresses(research_unit_center_json_data):
    org = unitAdapter.validate_python(research_unit_center_json_data)
    assert len(org.addresses) == 1
    addr = org.addresses[0]
    assert any(c.value == "France" for c in addr.country)
    assert any(c.value == "Example City" for c in addr.city)
    assert len(org.electronical_addresses) == 1
    assert org.electronical_addresses[0].uri == "https://www.example.org/"


def test_relationships_parsed_to_memberships(research_unit_center_json_data):
    org = unitAdapter.validate_python(research_unit_center_json_data)
    assert len(org.memberships) == 1
    m = org.memberships[0]
    assert m.target == "local-EXAMPLE-UNIV-001"
    assert m.position == OrgMembershipPosition.MAIN_SUPERVISION


def test_part_of_relationships_parsed_to_parents(institution_subdivision_a_json_data):
    org = nonUnitAdapter.validate_python(institution_subdivision_a_json_data)
    assert len(org.parents) == 1
    p = org.parents[0]
    assert p.target == "local-EXAMPLE-UNIV-001"


# ── Complex hierarchy model tests ──────────────────────────────────────────────

def test_create_epe_institution_from_json(epe_paris_sud_ouest_json_data):
    org = nonUnitAdapter.validate_python(epe_paris_sud_ouest_json_data)
    assert isinstance(org, Institution)
    assert org.generic_type == GenericOrganizationType.INSTITUTION
    assert org.national_type == NationalOrganizationType.EPE
    assert org.uid is None
    assert len(org.long_labels) == 1
    assert org.long_labels[0].value == "Université Paris Sud-Ouest"
    assert len(org.identifiers) == 2


def test_create_univ_with_member_of_relationship(univ_etienne_dupond_json_data):
    org = nonUnitAdapter.validate_python(univ_etienne_dupond_json_data)
    assert isinstance(org, Institution)
    assert org.national_type == NationalOrganizationType.UNIV
    assert len(org.memberships) == 1
    m = org.memberships[0]
    assert m.target == "uai-07890"
    assert m.start_date == date(2020, 1, 1)
    assert m.position is None


def test_create_cnrs_epst_institution(cnrs_json_data):
    org = nonUnitAdapter.validate_python(cnrs_json_data)
    assert isinstance(org, Institution)
    assert org.national_type == NationalOrganizationType.EPST
    assert len(org.short_labels) == 1
    assert org.short_labels[0].value == "CNRS"


def test_create_ge_institution(ena_astrophysique_json_data):
    org = nonUnitAdapter.validate_python(ena_astrophysique_json_data)
    assert isinstance(org, Institution)
    assert org.national_type == NationalOrganizationType.GE
    assert any(ll.value == "École nationale d'astrophysique" for ll in org.long_labels)


def test_create_dept_without_national_type(dept_physique_json_data):
    org = nonUnitAdapter.validate_python(dept_physique_json_data)
    assert isinstance(org, InstitutionSubdivision)
    assert org.national_type is None
    assert len(org.local_types) == 2
    assert any(lt.value == "Département" and lt.language == "fr" for lt in org.local_types)
    assert len(org.parents) == 1
    assert org.parents[0].target == "uai-02345"
    assert org.parents[0].start_date == date(1995, 1, 1)


def test_create_fac_with_national_type_fac(fac_sciences_json_data):
    org = nonUnitAdapter.validate_python(fac_sciences_json_data)
    assert isinstance(org, InstitutionSubdivision)
    assert org.national_type == NationalOrganizationType.FAC
    assert len(org.parents) == 1
    assert org.parents[0].target == "uai-02345"


def test_create_lra_with_multiple_memberships(lra_research_unit_json_data):
    org = unitAdapter.validate_python(lra_research_unit_json_data)
    assert isinstance(org, ResearchUnit)
    assert org.national_type == NationalOrganizationType.UMR
    assert org.main_mission == MissionType.RESEARCH
    assert len(org.memberships) == 4
    positions = [m.position for m in org.memberships]
    assert OrgMembershipPosition.MAIN_SUPERVISION in positions
    assert positions.count(OrgMembershipPosition.ASSOCIATED_SUPERVISION) == 2
    assert None in positions
    assert len(org.parents) == 1
    assert org.parents[0].target == "local-FAC-SCI-001"
    assert org.parents[0].start_date == date(2000, 1, 1)


def test_create_team_with_local_types_and_part_of(team_astrophysique_json_data):
    from app.models.organization_unit import Team
    org = nonUnitAdapter.validate_python(team_astrophysique_json_data)
    assert isinstance(org, Team)
    assert org.national_type == NationalOrganizationType.TEAM
    assert len(org.local_types) == 2
    assert any(lt.value == "Groupe" and lt.language == "fr" for lt in org.local_types)
    assert len(org.parents) == 1
    assert org.parents[0].target == "local-123456"
    assert org.parents[0].start_date == date(2010, 1, 1)
    assert len(org.memberships) == 1
    assert org.memberships[0].target == "local-AXIS-OBS-001"


def test_create_unit_subdivision_without_national_type(axis_observationnel_json_data):
    from app.models.organization_unit import UnitSubdivision
    org = nonUnitAdapter.validate_python(axis_observationnel_json_data)
    assert isinstance(org, UnitSubdivision)
    assert org.national_type is None
    assert len(org.local_types) == 2
    assert any(lt.value == "Axe de recherche" and lt.language == "fr" for lt in org.local_types)
    assert len(org.parents) == 1
    assert org.parents[0].target == "local-123456"
