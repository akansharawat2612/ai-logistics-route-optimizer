import requests


# Dehradun locations
locations = {
    "Warehouse": (78.0322, 30.3165),
    "ISBT Dehradun": (78.0080, 30.2850),
    "Clock Tower": (78.0437, 30.3256),
    "Prem Nagar": (77.9630, 30.3510),
    "Rajpur Road": (78.0800, 30.3600)
}


start = locations["Warehouse"]
end = locations["Clock Tower"]


url = (
    f"https://router.project-osrm.org/route/v1/driving/"
    f"{start[0]},{start[1]};"
    f"{end[0]},{end[1]}"
    f"?overview=false"
)


response = requests.get(url)

data = response.json()


if data["code"] == "Ok":

    distance_km = data["routes"][0]["distance"] / 1000

    duration_minutes = data["routes"][0]["duration"] / 60

    print("Road distance:", round(distance_km, 2), "km")

    print(
        "Estimated driving time:",
        round(duration_minutes, 1),
        "minutes"
    )

else:

    print("Could not calculate route.")