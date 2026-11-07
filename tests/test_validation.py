import pytest
from fastapi import HTTPException

from app.main import validate_repo_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("fastapi/fastapi", ("fastapi", "fastapi")),
        (" pallets/flask/ ", ("pallets", "flask")),
    ],
)
def test_validate_repo_name_accepts_valid_input(raw, expected):
    assert validate_repo_name(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "fastapi",
        "a/b/c",
        "/x",
        "../etc",
        "foo/bar baz",
    ],
)
def test_validate_repo_name_rejects_invalid_input(raw):
    with pytest.raises(HTTPException) as exc_info:
        validate_repo_name(raw)
    assert exc_info.value.status_code == 400
