
def test_create_user(client_httpx):
    client_httpx = client_httpx
    response = client_httpx.post("/users", json={
        "email": "test@example.com",
        "name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data




def test_get_users(client_httpx):
    response = client_httpx.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(u["email"] == "test@example.com" for u in data)
