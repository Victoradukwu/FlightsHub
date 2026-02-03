

def test_create_user(client):
    data = {
        "first_name": "Kanye",
        "last_name": "West",
        "username": "kanyew",
        "password": "password",
        "confirm_password": "password",
        "email": "kanyew@gmail.com",
        "phone_number": "7654"
}
    response = client.post("/api/v1/auth/register/", data=data)
    assert response.status_code == 201
    assert response.json()["email"] == "kanyew@gmail.com"
    