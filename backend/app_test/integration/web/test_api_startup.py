from src.api.core import logger


def test_startup_connection(test_client):
    response = test_client.get("/startup")
    body = response.json()
    logger.debug("This is the startup response %s", body)
    assert response.status_code == 200
    assert response.json() == {"message": "The API is LIVE!!"}
