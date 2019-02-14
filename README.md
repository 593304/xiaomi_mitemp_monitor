# Xiaomi Mi Temperature and Humidity Monitor

Simple python script for saving the sensor data to database for future use

Database schema for the script:

CREATE TABLE monitoring.sensor_data (  
	id BIGSERIAL PRIMARY KEY,  
	name VARCHAR(128),  
	mac_address VARCHAR(32),  
	room_temp_celsius NUMERIC(5, 2),  
	room_humdity_percent NUMERIC(5, 2),  
	battery_percent NUMERIC(5, 2),  
	timestamp TIMESTAMP  
)

Based on: https://github.com/ratcashdev/mitemp
