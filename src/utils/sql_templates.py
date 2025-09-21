# src/utils/sql_templates.py
class SQLTemplateEngine:
    def __init__(self):
        self.templates = {
            'current_reading': """
                SELECT {columns}
                FROM aq.current_readings_{source}
                WHERE {conditions}
                ORDER BY timestamp DESC
                LIMIT 1
            """,
            'time_series': """
                SELECT 
                    date_trunc('{interval}', timestamp) as period,
                    AVG({metric}) as avg_{metric},
                    MAX({metric}) as max_{metric},
                    MIN({metric}) as min_{metric},
                    COUNT(*) as reading_count
                FROM aq.readings_{source}
                WHERE timestamp >= NOW() - INTERVAL '{duration}'
                GROUP BY period
                ORDER BY period DESC
            """,
            'hotspot': """
                SELECT 
                    latitude, longitude,
                    pm25_value,
                    severity,
                    cluster_size,
                    locality_name
                FROM aq.hotspots_hotspot_xgb
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    {location_filter}
                ORDER BY pm25_value DESC
                LIMIT 20
            """
        }
