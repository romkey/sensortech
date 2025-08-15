# SPDX-FileCopyrightText: 2025 John Romkey
#
# SPDX-License-Identifier: CC0-1.0

import time
import board
import busio
import adafruit_scd4x
import adafruit_ccs811
import adafruit_ens160
import adafruit_ahtx0
import json
import gc
import wifi
import socketpool
from adafruit_httpserver import Request, Response, Server

i2c = busio.I2C(board.IO36, board.IO35)

# Initialize SCD40
scd4x = None
try:
    scd4x = adafruit_scd4x.SCD4X(i2c)
except Exception as e:
    print(f"Error initializing SCD40: {e}")

# Initialize CCS811
ccs = None
try:
    ccs = adafruit_ccs811.CCS811(i2c)
except Exception as e:
    print(f"Error initializing CCS811: {e}")

# Initialize ENS160
ens = None
try:
    ens = adafruit_ens160.ENS160(i2c)
except Exception as e:
    print(f"Error initializing ENS160: {e}")

# Initialize AHT21
aht21 = None
try:
    aht21 = adafruit_ahtx0.AHTx0(i2c)
except Exception as e:
    print(f"Error initializing AHT21: {e}")

# Store latest sensor data
sensor_data = {
    'co2': None,
    'temperature': None,
    'humidity': None,
    'eco2': None,
    'tvoc': None,
    'aqi': None,
    'ens_aqi': None,
    'ens_tvoc': None,
    'ens_eco2': None,
    'aht21_temperature': None,
    'aht21_humidity': None
}

# HTML page with Chart.js graphing
HTML_PAGE = '''<!DOCTYPE html>
<html>
<head>
    <title>Sensor Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .sensor-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .sensor-value {
            font-size: 2em;
            font-weight: bold;
            color: #2196F3;
        }
        .sensor-label {
            color: #666;
            margin-bottom: 10px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        .temp-humidity-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-top: 20px;
        }
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        .sensor-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .value-display {
            min-width: 120px;
        }
        .bottom-sensors {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>Sensor Dashboard <span id="connectionStatus">❌</span></h1>
    
    <div class="grid">
        <div class="sensor-card" id="co2Card" style="display: none;">
            <div class="sensor-info">
                <div class="value-display">
                    <div class="sensor-label">CO2 (SCD40)</div>
                    <div class="sensor-value" id="co2">--</div>
                    <div>ppm</div>
                </div>
                <div class="chart-container">
                    <canvas id="co2Chart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="sensor-card" id="eco2Card" style="display: none;">
            <div class="sensor-info">
                <div class="value-display">
                    <div class="sensor-label">eCO2 (CCS811)</div>
                    <div class="sensor-value" id="eco2">--</div>
                    <div>ppm</div>
                </div>
                <div class="chart-container">
                    <canvas id="eco2Chart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="sensor-card" id="tvocCard" style="display: none;">
            <div class="sensor-info">
                <div class="value-display">
                    <div class="sensor-label">TVOC (CCS811)</div>
                    <div class="sensor-value" id="tvoc">--</div>
                    <div>ppb</div>
                </div>
                <div class="chart-container">
                    <canvas id="tvocChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="sensor-card" id="ensEco2Card" style="display: none;">
            <div class="sensor-info">
                <div class="value-display">
                    <div class="sensor-label">eCO2 (ENS160)</div>
                    <div class="sensor-value" id="ens_eco2">--</div>
                    <div>ppm</div>
                </div>
                <div class="chart-container">
                    <canvas id="ensEco2Chart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <div class="temp-humidity-row">
        <div class="sensor-card" id="tempCard" style="display: none;">
            <div class="sensor-info">
                <div class="value-display">
                    <div class="sensor-label">Temperature</div>
                    <div class="sensor-value" id="temperature">--</div>
                    <div>°C (SCD40)</div>
                    <div class="sensor-value" id="aht21_temperature">--</div>
                    <div>°C (AHT21)</div>
                </div>
                <div class="chart-container">
                    <canvas id="tempChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="sensor-card" id="humidityCard" style="display: none;">
            <div class="sensor-info">
                <div class="value-display">
                    <div class="sensor-label">Humidity</div>
                    <div class="sensor-value" id="humidity">--</div>
                    <div>% (SCD40)</div>
                    <div class="sensor-value" id="aht21_humidity">--</div>
                    <div>% (AHT21)</div>
                </div>
                <div class="chart-container">
                    <canvas id="humidityChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    </div>
    
    <div class="bottom-sensors">
        <div class="sensor-card">
            <div class="sensor-label">Air Quality Index (ENS160)</div>
            <div class="sensor-value" id="ens_aqi">--</div>
            <div>index</div>
        </div>
    </div>
    
    <div class="timestamp" id="timestamp">Last update: --</div>

    <script>
        // Initialize charts
        const maxDataPoints = 120;
        const timeLabels = [];
        const co2Data = [];
        const eco2Data = [];
        const tvocData = [];
        const ensTvocData = [];
        const ensEco2Data = [];
        const tempData = [];
        const humidityData = [];
        const aht21TempData = [];
        const aht21HumidityData = [];
        
        // Chart instances
        let co2Chart = null;
        let eco2Chart = null;
        let tvocChart = null;
        let ensEco2Chart = null;
        let tempChart = null;
        let humidityChart = null;
        
        function createCo2Chart() {
            if (!co2Chart) {
                co2Chart = new Chart(document.getElementById('co2Chart'), {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [{
                    label: 'CO2 (ppm)',
                    data: co2Data,
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        display: false
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
                });
            }
        }
        
        function createEco2Chart() {
            if (!eco2Chart) {
                eco2Chart = new Chart(document.getElementById('eco2Chart'), {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [{
                    label: 'eCO2 (ppm)',
                    data: eco2Data,
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        display: false
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
                });
            }
        }
        
        function createTvocChart() {
            if (!tvocChart) {
                tvocChart = new Chart(document.getElementById('tvocChart'), {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [{
                    label: 'TVOC (CCS811)',
                    data: tvocData,
                    borderColor: '#FF9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    tension: 0.4,
                    fill: false
                }, {
                    label: 'TVOC (ENS160)',
                    data: ensTvocData,
                    borderColor: '#9C27B0',
                    backgroundColor: 'rgba(156, 39, 176, 0.1)',
                    tension: 0.4,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        display: false
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
                });
            }
        }
        
                function createEnsEco2Chart() {
            if (!ensEco2Chart) {
                ensEco2Chart = new Chart(document.getElementById('ensEco2Chart'), {
                    type: 'line',
                    data: {
                        labels: timeLabels,
                        datasets: [{
                            label: 'eCO2 (ENS160)',
                            data: ensEco2Data,
                            borderColor: '#E91E63',
                            backgroundColor: 'rgba(233, 30, 99, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: false,
                                grid: {
                                    color: 'rgba(0,0,0,0.1)'
                                }
                            },
                            x: {
                                display: false
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            }
                        }
                    }
                });
            }
        }
        
        function createTempChart() {
            if (!tempChart) {
                tempChart = new Chart(document.getElementById('tempChart'), {
                    type: 'line',
                    data: {
                        labels: timeLabels,
                        datasets: [{
                            label: 'Temperature (SCD40)',
                            data: tempData,
                            borderColor: '#FF5722',
                            backgroundColor: 'rgba(255, 87, 34, 0.1)',
                            tension: 0.4,
                            fill: false
                        }, {
                            label: 'Temperature (AHT21)',
                            data: aht21TempData,
                            borderColor: '#795548',
                            backgroundColor: 'rgba(121, 85, 72, 0.1)',
                            tension: 0.4,
                            fill: false
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: false,
                                grid: {
                                    color: 'rgba(0,0,0,0.1)'
                                }
                            },
                            x: {
                                display: false
                            }
                        },
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top'
                            }
                        }
                    }
                });
            }
        }
        
        function createHumidityChart() {
            if (!humidityChart) {
                humidityChart = new Chart(document.getElementById('humidityChart'), {
                    type: 'line',
                    data: {
                        labels: timeLabels,
                        datasets: [{
                            label: 'Humidity (SCD40)',
                            data: humidityData,
                            borderColor: '#00BCD4',
                            backgroundColor: 'rgba(0, 188, 212, 0.1)',
                            tension: 0.4,
                            fill: false
                        }, {
                            label: 'Humidity (AHT21)',
                            data: aht21HumidityData,
                            borderColor: '#607D8B',
                            backgroundColor: 'rgba(96, 125, 139, 0.1)',
                            tension: 0.4,
                            fill: false
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: false,
                                grid: {
                                    color: 'rgba(0,0,0,0.1)'
                                }
                            },
                            x: {
                                display: false
                            }
                        },
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top'
                            }
                        }
                    }
                });
            }
        }
        
        function addDataPoint(chart, dataArray, value, timeLabel, datasetIndex = 0) {
            if (!chart) return;
            
            dataArray.push(value);
            if (dataArray.length > maxDataPoints) {
                dataArray.shift();
            }
            
            chart.data.labels = timeLabels;
            chart.data.datasets[datasetIndex].data = dataArray;
            chart.update('none');
        }
        
        function updateSensorValues() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    // Update connection status to green checkmark
                    document.getElementById('connectionStatus').textContent = '✅';
                    
                    const now = new Date();
                    const timeLabel = now.toLocaleTimeString();
                    
                    if (data.co2 !== null) {
                        document.getElementById('co2').textContent = data.co2;
                        if (!co2Chart) {
                            document.getElementById('co2Card').style.display = 'block';
                            setTimeout(() => createCo2Chart(), 100);
                        }
                        addDataPoint(co2Chart, co2Data, data.co2, timeLabel);
                    }
                    if (data.eco2 !== null) {
                        document.getElementById('eco2').textContent = data.eco2;
                        if (!eco2Chart) {
                            document.getElementById('eco2Card').style.display = 'block';
                            setTimeout(() => createEco2Chart(), 100);
                        }
                        addDataPoint(eco2Chart, eco2Data, data.eco2, timeLabel);
                    }
                    if (data.tvoc !== null || data.ens_tvoc !== null) {
                        if (data.tvoc !== null) {
                            document.getElementById('tvoc').textContent = data.tvoc;
                            addDataPoint(tvocChart, tvocData, data.tvoc, timeLabel);
                        }
                        if (data.ens_tvoc !== null) {
                            addDataPoint(tvocChart, ensTvocData, data.ens_tvoc, timeLabel);
                        }
                        if (!tvocChart) {
                            document.getElementById('tvocCard').style.display = 'block';
                            setTimeout(() => createTvocChart(), 100);
                        }
                    }
                    if (data.ens_eco2 !== null) {
                        document.getElementById('ens_eco2').textContent = data.ens_eco2.toFixed(1);
                        if (!ensEco2Chart) {
                            document.getElementById('ensEco2Card').style.display = 'block';
                            setTimeout(() => createEnsEco2Chart(), 100);
                        }
                        addDataPoint(ensEco2Chart, ensEco2Data, data.ens_eco2, timeLabel);
                    }
                    if (data.temperature !== null || data.aht21_temperature !== null) {
                        if (data.temperature !== null) {
                            document.getElementById('temperature').textContent = data.temperature.toFixed(1);
                            addDataPoint(tempChart, tempData, data.temperature, timeLabel, 0);
                        }
                        if (data.aht21_temperature !== null) {
                            document.getElementById('aht21_temperature').textContent = data.aht21_temperature.toFixed(1);
                            addDataPoint(tempChart, aht21TempData, data.aht21_temperature, timeLabel, 1);
                        }
                        if (!tempChart) {
                            document.getElementById('tempCard').style.display = 'block';
                            setTimeout(() => createTempChart(), 100);
                        }
                    }
                    if (data.humidity !== null || data.aht21_humidity !== null) {
                        if (data.humidity !== null) {
                            document.getElementById('humidity').textContent = data.humidity.toFixed(1);
                            addDataPoint(humidityChart, humidityData, data.humidity, timeLabel, 0);
                        }
                        if (data.aht21_humidity !== null) {
                            document.getElementById('aht21_humidity').textContent = data.aht21_humidity.toFixed(1);
                            addDataPoint(humidityChart, aht21HumidityData, data.aht21_humidity, timeLabel, 1);
                        }
                        if (!humidityChart) {
                            document.getElementById('humidityCard').style.display = 'block';
                            setTimeout(() => createHumidityChart(), 100);
                        }
                    }
                    if (data.ens_aqi !== null) {
                        document.getElementById('ens_aqi').textContent = data.ens_aqi;
                    }
                    
                    // Update timestamp
                    document.getElementById('timestamp').textContent = 'Last update: ' + timeLabel;
                    
                    // Update time labels for all charts
                    if (!timeLabels.includes(timeLabel)) {
                        timeLabels.push(timeLabel);
                        if (timeLabels.length > maxDataPoints) {
                            timeLabels.shift();
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    document.getElementById('connectionStatus').textContent = '❌';
                });
        }
        
        // Update every second
        setInterval(updateSensorValues, 1000);
        
        // Initial update
        updateSensorValues();
    </script>
</body>
</html>'''

# Initialize WiFi access point
try:
    wifi.radio.start_ap("SensorWorkshop", "password123")
    print("WiFi AP started: SensorWorkshop")
    print("Password: password123")
    print(f"IP Address: {wifi.radio.ipv4_address}")
except Exception as e:
    print(f"Error starting WiFi: {e}")

# Create socket pool and HTTP server
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, debug=True)

@server.route("/")
def base(request: Request):
    """Serve the main HTML page"""
    return Response(request, HTML_PAGE, content_type="text/html")

@server.route("/data")
def data(request: Request):
    """Serve sensor data as JSON"""
    return Response(request, json.dumps(sensor_data), content_type="application/json")

# Display sensor information
if scd4x:
    print(f"Serial Number: {scd4x.serial_number}")
    print(f"Temperature Offset: {scd4x.temperature_offset}°C")
    print(f"Altitude: {scd4x.altitude} m")
    print(f"Automatic Self-Calibration: {scd4x.self_calibration_enabled}")
    print()

    # Start periodic measurements
    scd4x.start_periodic_measurement()
    print("Started periodic SCD4x measurements...")

print("Starting web server...")
print("Connect to http://<device-ip> to view sensor dashboard")

# Start the server
server.start(str(wifi.radio.ipv4_address))

# Main reading loop
while True:
    # Handle web server requests
    try:
        server.poll()
    except Exception as e:
        print(f"Web server error: {e}")
    
    # Read SCD40 data
    if scd4x and scd4x.data_ready:
        try:
            sensor_data['co2'] = scd4x.CO2
            sensor_data['temperature'] = scd4x.temperature
            sensor_data['humidity'] = scd4x.relative_humidity
            
        except Exception as e:
            print(f"Error reading SCD40 data: {e}")

    # Read CCS811 data
    if ccs and ccs.data_ready:
        try:
            sensor_data['eco2'] = ccs.eco2
            sensor_data['tvoc'] = ccs.tvoc
            
        except Exception as e:
            print(f"Error reading CCS811 data: {e}")

    # Read ENS160 data
    if ens:
        try:
            sensor_data['ens_aqi'] = ens.AQI
            sensor_data['ens_tvoc'] = ens.TVOC
            sensor_data['ens_eco2'] = ens.eCO2
            
        except Exception as e:
            print(f"Error reading ENS160 data: {e}")

    # Read AHT21 data
    if aht21:
        try:
            sensor_data['aht21_temperature'] = aht21.temperature
            sensor_data['aht21_humidity'] = aht21.relative_humidity
            
        except Exception as e:
            print(f"Error reading AHT21 data: {e}")

    # Small delay to prevent overwhelming the system
    time.sleep(0.1)
    
    # Garbage collection to prevent memory issues
    gc.collect()
