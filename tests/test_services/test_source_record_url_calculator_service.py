import pytest

from app.services.source_records.source_record_url_service import SourceRecordUrlService


@pytest.mark.parametrize(
    "harvester, source_identifier, expected_url",
    [
        ("openalex", "https://openalex.org/W4292200111", "https://openalex.org/W4292200111"),
        ("idref", "http://www.sudoc.fr/232572542/id", "http://www.sudoc.fr/232572542/id"),
        ("hal", "hal-00717561", "https://hal.science/hal-00717561"),
        ("scanr", "doi10.1016/j.jmateco.2023.102886",
         # pylint: disable=line-too-long
         "https://scanr.enseignementsup-recherche.gouv.fr/publications/doi10.1016%2Fj.jmateco.2023.102886"),
    ]
)
def test_compute_url_valid(harvester, source_identifier, expected_url):
    """
    Test the computation of the URL for a source record
    :param harvester:
    :param source_identifier:
    :param expected_url:
    :return:
    """
    computed_url = SourceRecordUrlService.compute_url(harvester, source_identifier)
    assert str(computed_url) == expected_url


@pytest.mark.parametrize(
    "harvester, source_identifier",
    [
        ("UnknownHarvester", "some_identifier"),
        ("hal", "   "),
        ("scanr", ""),
        ("", "https://valid.url"),
    ]
)
def test_compute_url_invalid(harvester, source_identifier):
    """
    Test the computation of the URL for a source record with invalid parameters
    :param harvester:
    :param source_identifier:
    :return:
    """
    with pytest.raises(ValueError):
        SourceRecordUrlService.compute_url(harvester, source_identifier)
