def company_id(client, name="Acme"):
    """Id of the company with this name, creating it if needed."""
    for company in client.get("/companies").json():
        if company["name"].lower() == name.lower():
            return company["id"]
    return client.post("/companies", json={"name": name, "location": "Berlin"}).json()["id"]
