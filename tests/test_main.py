import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app, get_from_coinbase
from httpx import AsyncClient
from httpx import MockTransport, Response

client = TestClient(app)

MOCK_FX_RATES = {
    "USD/EUR": 1.19,
    "EUR/USD": 0.84,
    "USD/GBP": 1.32,
    "GBP/USD": 0.76,
    "EUR/GBP": 1.11,
    "GBP/EUR": 0.90,
}


@pytest.fixture
def mock_fx_rates():
    with patch("main.get_from_coinbase", return_value=MOCK_FX_RATES):
        yield


@pytest.mark.asyncio
async def test_convert_currency_valid(mock_fx_rates):
    await client.app.cache.reset()
    response = client.get("/v1/convert?ccy_from=USD&ccy_to=GBP&quantity=1000")
    assert response.status_code == 200
    assert response.json() == {"quantity": 1320.0, "ccy": "GBP"}


@pytest.mark.asyncio
async def test_convert_currency_invalid_quantity(mock_fx_rates):
    await client.app.cache.reset()
    response = client.get("/v1/convert?ccy_from=USD&ccy_to=GBP&quantity=0")
    assert response.status_code == 400
    assert response.json().get('detail') == 'Quantity must be positive value, but given value is: 0.0'

    response = client.get("/v1/convert?ccy_from=USD&ccy_to=GBP&quantity=-1.0")
    assert response.status_code == 400
    assert response.json().get('detail') == 'Quantity must be positive value, but given value is: -1.0'


@pytest.mark.asyncio
async def test_convert_currency_same_currency(mock_fx_rates):
    await client.app.cache.reset()
    response = client.get("/v1/convert?ccy_from=USD&ccy_to=USD&quantity=1000")
    assert response.status_code == 200
    assert response.json() == {"quantity": 1000.0, "ccy": "USD"}


@pytest.mark.asyncio
async def test_convert_currency_lowercase_same_currency(mock_fx_rates):
    await client.app.cache.reset()
    response = client.get("/v1/convert?ccy_from=GBP&ccy_to=Gbp&quantity=1000")
    assert response.status_code == 200
    assert response.json() == {"quantity": 1000.0, "ccy": "GBP"}


@pytest.mark.asyncio
async def test_convert_currency_invalid_currency_pair(mock_fx_rates):
    await client.app.cache.reset()
    response = client.get("/v1/convert?ccy_from=USD&ccy_to=JPY&quantity=1000")
    assert response.status_code == 400
    assert response.json().get('detail') == 'Either ccy_from USD or ccy_to JPY is not supported or invalid'


@pytest.mark.asyncio
async def test_get_from_coinbase_success():
    mock_response_data = {
        "bpi": {
            "USD": {"rate_float": 1.0},
            "EUR": {"rate_float": 0.85},
        }
    }
    mock_pricing_url = "http://mock.coinbase.pricing.url"

    mock_handler = lambda req: Response(200, json=mock_response_data)

    transport = MockTransport(mock_handler)

    with patch("main.httpx.AsyncClient", lambda: AsyncClient(transport=transport)), \
            patch("main.Settings.coinbase.pricing_url", mock_pricing_url):
        rates = await get_from_coinbase()

        assert rates == {
            "USD/EUR": 0.85 / 1.0,
            "EUR/USD": 1.0 / 0.85,
        }


@pytest.mark.asyncio
async def test_get_from_coinbase_failure():
    mock_response_data = {
        "bpi": {
            "USD": {"rate_float": 1.0},
            "JPY": {"rate_float": 100.00},
        }
    }
    mock_pricing_url = "http://mock.coinbase.pricing.url"

    mock_handler = lambda req: Response(200, json=mock_response_data)

    transport = MockTransport(mock_handler)

    with patch("main.httpx.AsyncClient", lambda: AsyncClient(transport=transport)), \
            patch("main.Settings.coinbase.pricing_url", mock_pricing_url):
        await client.app.cache.reset()
        response = client.get("/v1/convert?ccy_from=USD&ccy_to=GBP&quantity=1000")
        assert response.status_code == 404
        assert response.json()['detail'] == 'Unable to find fx rate for USD/GBP'

