from app.models.organization_types import GenericOrganizationType, NationalOrganizationType
from app.models.organization_unit import Institution, nonUnitAdapter, unitAdapter


def test_create_valid_institution(institution_a_json_data):
    org = nonUnitAdapter.validate_python(institution_a_json_data)
    assert isinstance(org, Institution)
    assert org.generic_type == GenericOrganizationType.INSTITUTION
    assert org.national_type == NationalOrganizationType.UNIV
    assert len(org.short_labels) == 2
    assert len(org.long_labels) == 2


def test_create_valid_research_unit(research_unit_center_json_data):
    org = unitAdapter.validate_python(research_unit_center_json_data)
    assert org.generic_type == GenericOrganizationType.UNIT
    assert org.national_type == NationalOrganizationType.UMR
    assert len(org.long_labels) == 2
    assert len(org.descriptions) == 2
