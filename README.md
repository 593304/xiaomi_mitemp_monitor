# Xiaomi Mi Temperature and Humidity Monitor

Simple python script for saving the sensor data to database for future use

Database schema for the script:
```SQL
CREATE TABLE monitoring.sensor_data (  
    id BIGSERIAL PRIMARY KEY,  
    name VARCHAR(128),  
    mac_address VARCHAR(32),  
    room_temp_celsius NUMERIC(5, 2),  
    room_humdity_percent NUMERIC(5, 2),  
    battery_percent NUMERIC(5, 2),  
    timestamp TIMESTAMP  
)
```

## Update 1

View for hourly average room temperature
```SQL
CREATE VIEW monitoring.sensor_data_room_hourly AS  
    SELECT  
        name,  
        ROUND(AVG(room_temp_celsius), 2) AS room_temp_celsius,  
        ROUND(AVG(room_humdity_percent), 2) AS room_humdity_percent,  
        DATE_TRUNC('hour', timestamp) AS hour  
    FROM  
        monitoring.sensor_data  
    GROUP BY  
        name,  
        hour  
    ORDER BY  
    hour ASC;
```

View for daily average room temperature
```SQL
CREATE VIEW monitoring.sensor_data_room_daily AS  
    SELECT  
        name,  
        ROUND(AVG(room_temp_celsius), 2) AS room_temp_celsius,  
        ROUND(AVG(room_humdity_percent), 2) AS room_humdity_percent,  
        DATE_TRUNC('day', timestamp) AS day  
    FROM  
        monitoring.sensor_data  
    GROUP BY  
        name,  
        day  
    ORDER BY  
    day ASC;
```

View for calculating the battery life difference minute by minute
```SQL
CREATE VIEW monitoring.sensor_data_battery_diff_by_minutes AS  
    SELECT  
        next.name,  
        (next.battery_percent - base.battery_percent) AS battery_diff_percent,  
        next.minute  
    FROM  
        (SELECT name, battery_percent, DATE_TRUNC('minute', timestamp) AS minute FROM monitoring.sensor_data WHERE id < (SELECT MAX(id) FROM monitoring.sensor_data) ORDER BY minute) AS base,  
        (SELECT name, battery_percent, DATE_TRUNC('minute', timestamp) AS minute FROM monitoring.sensor_data WHERE id > (SELECT MIN(id) FROM monitoring.sensor_data) ORDER BY minute) AS next  
    WHERE  
        (base.minute + (interval '1 minute')) = next.minute  
    ORDER BY  
        next.minute ASC;
```

View for battery life differences by hours
```SQL
CREATE VIEW monitoring.sensor_data_battery_diff_by_hours AS  
    SELECT  
        name,  
        SUM(battery_diff_percent) AS battery_diff_percent,  
        DATE_TRUNC('hour', minute) AS hour  
    FROM  
        monitoring.sensor_data_battery_diff_by_minutes  
    GROUP BY  
        name,  
        hour  
    ORDER BY  
        hour ASC;
```

View for battery life differences by days
```SQL
CREATE VIEW monitoring.sensor_data_battery_diff_by_days AS  
    SELECT  
        name,  
        SUM(battery_diff_percent) AS battery_diff_percent,  
        DATE_TRUNC('day', minute) AS day  
    FROM  
        monitoring.sensor_data_battery_diff_by_minutes  
    GROUP BY  
        name,  
        day  
    ORDER BY  
        day ASC;
```

## Update 2

Checking the temporary file and saving its content to the database  
Code and readme optimization 

#
Based on: https://github.com/ratcashdev/mitemp
