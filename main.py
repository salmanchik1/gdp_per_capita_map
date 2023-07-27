import folium
import pandas as pd
import requests
from geopy.geocoders import Nominatim


def fetch_gdp_data(year):
    # URL for World Bank API to get GDP data (using World Development Indicators - WDI)
    api_url = "https://api.worldbank.org/v2/countries/all/indicators/NY.GDP.PCAP.CD"

    # Parameters for the API request
    params = {
        "format": "json",   # Response format (JSON)
        "per_page": 300,    # Number of records per page (max 100)
        "date": year,
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raise an error if the request is not successful
        data = response.json()

        # Extracting the relevant data from the API response
        gdp_data = []
        for entry in data[1][49:]:
            country = entry["country"]["value"]
            gdp_per_capita = entry["value"]
            gdp_data.append({"Country": country, "GDP_Per_Capita": gdp_per_capita})

        return gdp_data

    except requests.exceptions.RequestException as e:
        print("Error fetching GDP data:", e)
        return None


def prepare_data(data):
    gdp_df = pd.DataFrame(data, columns=["Country", "GDP_Per_Capita"])
    return gdp_df


def geocode_countries(df):
    geolocator = Nominatim(user_agent="gdp_per_capita_app")
    latitudes = []
    longitudes = []

    for country in df["Country"]:
        print("Country:", country)
        location = geolocator.geocode(country)
        if location:
            latitudes.append(location.latitude)
            longitudes.append(location.longitude)
        else:
            latitudes.append(None)
            longitudes.append(None)

    df["Latitude"] = latitudes
    df["Longitude"] = longitudes

    return df


def create_map(df):
    # Center the map at the average latitude and longitude
    center_lat = df["Latitude"].mean()
    center_lon = df["Longitude"].mean()

    # Create the map
    gdp_map = folium.Map(location=[center_lat, center_lon], zoom_start=3)

    # Add markers for each country
    for _, row in df.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"{row['Country']} - GDP per Capita: {row['GDP_Per_Capita']}",
        ).add_to(gdp_map)

    return gdp_map


if __name__ == "__main__":
    # Fetch GDP data
    gdp_data = fetch_gdp_data(2022)
    if gdp_data is None:
        exit()

    # Prepare the data
    gdp_df = prepare_data(gdp_data)

    # Geocode the countries
    gdp_df = geocode_countries(gdp_df)
    gdp_df.dropna(subset=["Latitude", "Longitude"], inplace=True) # Remove rows with missing corrdinates

    # Create the map
    gdp_map = create_map(gdp_df)

    # Save the map to an HTML file
    gdp_map.save("gdp_per_capita.html")
