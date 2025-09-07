# CETI Institute Sensor Tech Workshop Notes

This repo contains the slides for two workshops I recently held at [CETI Institute](http://ceti.institute) in Portland, Oregon. It also includes code for a demo.

The first workshop - [SensorTech](presentations/Sensortech.pdf) - covers broad concepts in sensors - kinds of sensors, things you need to think about, how to prioritize. And ends with a discussions of a sensor I dislike (eCO2 - "equivalent CO2", which guesses how  much CO2 there might be in a space) and a sensor I do like ("Nuclear Event Detector").

The second workshop - [Assisted Assisted Living](presentations/Assisted%20Assisted%20Living.pdf) covers a project for monitoring an asissted living space using Home Assistant and Zigbee-based sensors.

## Code

The [demo](demo/) is written in [CircuitPython](https://circuitpython.org). Run it by  copying the files to a CircuitPython device and restarting it (or use [circremote](https://github.com/romkey/circremote). 

You'll want to connect a true CO2 sensor - the SCD40 or SCD41 - and an "equivalent CO2" sensor - CCS811 or ENS160. The code will show live graph of both sensors. Try exposing them to various gasses - especially actual pure CO2 (a SodaStream CO2 cartridge is useful for this) or alcohol - and you'll see how wildly the eCO2 sensor can vary from a true CO2 sensor.

## License

Presentations are licensed [CC BY-NC 4.0](CC-BY-NC-4.0.txt), [Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/) by John Romkey, 2025.

The code is licensed under the [MIT License](MIT-LICENSE.txt).

Datasheets are owned and licensed by the companies that published them.
