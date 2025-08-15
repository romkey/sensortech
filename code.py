# SPDX-FileCopyrightText: 2025 John Romkey
#
# SPDX-License-Identifier: CC0-1.0

import time
import board
import busio
import busio
import adafruit_scd4x
import adafruit_ccs811
import adafruit_ens160


# Initialize I2C with fallback
try:
    i2c = busio.I2C({{ scl }}, {{ sda }})
except:
    i2c = board.I2C()

# Initialize SCD40
scd4x = None
try:
    scd4x = adafruit_scd4x.SCD4X(i2c)
except Exception as e:
    print(f"Error initializing SCD40: {e}")

# Initialize CCS811
ccs = None
try:
#    ccs = adafruit_ccs811.CCS811(i2c, address={ address }})
    ccs = adafruit_ccs811.CCS811(i2c)
except Exception as e:
    print(f"Error initializing CCS811: {e}")

# Initialize ENS160
ens = None
try:
#    ens = adafruit_ens160.ENS160(i2c, address={ address }})
    ens = adafruit_ens160.ENS160(i2c)
except Exception as e:
    print(f"Error initializing ENS160: {e}")


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

# Main reading loop
while True:
    # poll roughly once per second
    time.sleep(1)
    
    if scd4x and scd4x.data_ready:
        try:
            # Read sensor data
            co2 = scd4x.CO2
            temperature = scd4x.temperature
            humidity = scd4x.relative_humidity
            
            # Display readings
            print(f"CO2: {co2} ppm")
            print(f"Temperature: {temperature:.1f}°C")
            print(f"Humidity: {humidity:.1f}%")
            print("-" * 30)
            
        except Exception as e:
            print(f"Error reading sensor data: {e}")
            print("-" * 30)
    else:
        print("Waiting for data...")
        print("-" * 30)

    if ccs and ccs.data_ready:
        eco2 = ccs.eco2
        tvoc = ccs.tvoc
            
        print(f"eCO2: {eco2} ppm")
        print(f"TVOC: {tvoc} ppb")
        print("-" * 30)

    if ens:
        aqi = ens.AQI
        tvoc = ens.TVOC
        eco2 = ens.eCO2
        
        print(f"Air Quality Index: {aqi}")
        print(f"TVOC: {tvoc:.1f} ppb")
        print(f"eCO2: {eco2:.1f} ppm")
        print("-" * 30)
