from core.exceptions import LumiscrapeError, ParseError, StorageError


def test_custom_exceptions() -> None:
    err = ParseError("Selector not found")
    assert isinstance(err, LumiscrapeError)
    assert str(err) == "Selector not found"

    storage_err = StorageError("MinIO connection failed")
    assert isinstance(storage_err, LumiscrapeError)
