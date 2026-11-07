import pytest
from app.main import validate_repo_name
from fastapi import HTTPException


@pytest.mark.parametrize(
    "rep_name",
    [
        "owner/name",
        "owner/name ",
        " owner/name ",
        "owner/name/",
        "/owner/name/",
        "/owner/name/ ",
        " /owner/name/ ",
    ],
)
def test_validate_repo_name(rep_name: str):
    owner, name = validate_repo_name(rep_name)
    assert 'owner' == owner
    assert 'name' == name

@pytest.mark.parametrize(
    "rep_name",
    [
        "owner/name/etc",
        "owner /name",
        "own er/name",
        "owner/ name",
        "owner/na me",
        "/name",
        "name",
        "./name",
        "../name",
        "owner",
        "owner/",
        "owner/.",
        "owner/..",
    ]
)
def test_validate_repo_name_invalid(rep_name: str):
    with pytest.raises(HTTPException) as exc_info:
        validate_repo_name(rep_name)
    assert exc_info.value.status_code == 400