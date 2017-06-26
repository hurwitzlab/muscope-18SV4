# content of conftest.py
import pytest

import qc18SV4


def pytest_addoption(parser):
    parser.addoption("--uchime-ref-db-fp", action="store", required=True, help="path to PR2 database")


@pytest.fixture
def pipeline():
    return qc18SV4.pipeline.Pipeline(
        forward_reads_fp='',
        forward_primer='', reverse_primer='',
        min_overlap=0,
        uchime_ref_db_fp='',
        work_dp='', core_count=1
    )


@pytest.fixture
def uchime_ref_db_fp(request):
    return request.config.getoption("--uchime-ref-db-fp")
