#!/usr/bin/python3
from flask import Flask, request, render_template_string
import requests
import time

app = Flask(__name__)

def get_weather(city):
    api = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid=6556957913f658a4a0edb3a1c33cdcdc"

    json_data = requests.get(api).json()

    if json_data.get("cod") != 200:
        return None  # Return None if city not found

    temp = int(((json_data['main']['temp'] - 273.15) * 9/5) + 32)
    min_temp = int(((json_data['main']['temp_min'] - 273.15) * 9/5) + 32)
    max_temp = int(((json_data['main']['temp_max'] - 273.15) * 9/5) + 32)
    pressure = json_data['main']['pressure']
    humidity = json_data['main']['humidity']
    wind = json_data['wind']['speed']
    sunset = time.strftime('%I:%M:%S %p', time.gmtime(json_data['sys']['sunset'] - 18000))
    sunrise = time.strftime('%I:%M:%S %p', time.gmtime(json_data['sys']['sunrise'] - 18000))

    return {
        "temp": temp,
        "min_temp": min_temp,
        "max_temp": max_temp,
        "pressure": pressure,
        "humidity": humidity,
        "wind_speed": wind,
        "sunrise": sunrise,
        "sunset": sunset,
    }

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather App</title>
</head>
<body>
    <h1>Weather App</h1>
    <form action="/weather" method="get">
        <label for="city">Enter City:</label>
        <input type="text" id="city" name="city" required>
        <button type="submit">Get Weather</button>
    </form>
    {% if weather_data %}
        <h2>Weather in {{ city }}:</h2>
        <p>Temperature: {{ weather_data.temp }} °F</p>
        <p>Min Temperature: {{ weather_data.min_temp }} °F</p>
        <p>Max Temperature: {{ weather_data.max_temp }} °F</p>
        <p>Pressure: {{ weather_data.pressure }} hPa</p>
        <p>Humidity: {{ weather_data.humidity }}%</p>
        <p>Wind Speed: {{ weather_data.wind_speed }} m/s</p>
        <p>Sunrise: {{ weather_data.sunrise }}</p>
        <p>Sunset: {{ weather_data.sunset }}</p>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/weather', methods=['GET'])
def weather():
    city = request.args.get('city')
    if not city:
        return {"error": "City is required!"}, 400
    
    weather_data = get_weather(city)
    if weather_data is None:
        return {"error": "City not found!"}, 404

    return render_template_string(HTML_TEMPLATE, weather_data=weather_data, city=city)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
