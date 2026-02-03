from datetime import date


def test_ai_search_public(client):
    payload = {
        "origin_iata": "LOS",
        "destination_iata": "ABV",
        "date": date.today().isoformat(),
    }
    resp = client.post("/api/v1/flights/search", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "internal_flights" in data
    assert "external_flights" in data
    assert isinstance(data["external_flights"], list)
