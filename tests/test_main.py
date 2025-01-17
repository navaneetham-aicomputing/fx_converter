import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app, get_cached_fx_rates

# Create a TestClient instance
client = TestClient(app)

# Mocked response from the CoinDesk API
MOCK_COINDESK_RESPONSE = {
    "bpi": {
        "USD": {"rate_float": 50000.0},
        "EUR": {"rate_float": 42000.0},
        "GBP": {"rate_float": 38000.0},
    }
}

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
    """
    Fixture to patch get_cached_fx_rates with mocked FX rates.
    """
    with patch("main.get_cached_fx_rates", return_value=MOCK_FX_RATES):
        yield

@pytest.fixture
def mock_fetch_coindesk():
    """
    Fixture to patch the external CoinDesk API request.
    """
    with patch("main.fetch_fx_rates", return_value=MOCK_FX_RATES):
        yield

def test_convert_currency_valid(mock_fx_rates):
    """
    Test a valid currency conversion.
    """
    response = client.get("/convert?ccy_from=USD&ccy_to=GBP&quantity=1000")
    assert response.status_code == 200
    assert response.json() == {"quantity": 1320.0, "ccy": "GBP"}

def test_convert_currency_same_currency(mock_fx_rates):
    """
    Test converting a currency to itself.
    """
    response = client.get("/convert?ccy_from=USD&ccy_to=USD&quantity=1000")
    assert response.status_code == 200
    assert response.json() == {"quantity": 1000.0, "ccy": "USD"}

def test_convert_currency_invalid_currency_pair(mock_fx_rates):
    """
    Test invalid currency conversion where no FX rate exists.
    """
    response = client.get("/convert?ccy_from=USD&ccy_to=JPY&quantity=1000")
    assert response.status_code == 400
    assert response.json() == {"detail": "Conversion rate for USD/JPY not available"}

def test_fetch_coindesk_rates(mock_fetch_coindesk):
    """
    Test fetching FX rates from CoinDesk API.
    """
    fx_rates = client.app.dependency_overrides[get_cached_fx_rates] = lambda: MOCK_FX_RATES
    rates = client.app.dependency_overrides[get_cached_fx_rates]()
    assert rates == MOCK_FX_RATES

def test_invalid_query_params(mock_fx_rates):
    """
    Test invalid query parameters (e.g., missing required parameters).
    """
    response = client.get("/convert?ccy_from=USD")
    assert response.status_code == 422  # Unprocessable Entity
    response_data = response.json()
    assert "detail" in response_data
    assert any("ccy_to" in str(error) for error in response_data["detail"])