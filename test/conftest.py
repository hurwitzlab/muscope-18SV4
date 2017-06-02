# content of conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption("--uchime-ref-db-fp", action="store",  help="path to PR2 database")

@pytest.fixture
def uchime_ref_db_fp(request):
    return request.config.getoption("--uchime-ref-db-fp")
