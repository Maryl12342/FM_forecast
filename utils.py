import requests
import pandas as pd
from datetime import datetime, timedelta
import psycopg2
from datetime import date
import matplotlib.pyplot as plt
import io
import base64
from dateutil import parser


def fetch_train_data(start_date, end_date, train_number):
    date_range = pd.date_range(start_date, end_date)
    data = []

    for date in date_range:
        date_str = date.strftime("%Y-%m-%d")
        url = f"https://rata.digitraffic.fi/api/v1/trains/{date_str}/{train_number}"
        response = requests.get(url)
        if response.status_code == 200:
            data.append(response.json())

    return data


def connect_to_postgres():
    conn = psycopg2.connect(
        dbname="trains",
        user="postgres",
        password="password123",
        host="localhost",
        port="5432"
    )

    return conn


# Insert data into PostgreSQL
def insert_data_to_postgres(postgres_conn, train_data):
    cur = postgres_conn.cursor()
    for day_data in train_data:
        for train in day_data:
            train_number = train.get('trainNumber')
            date = train.get('departureDate')
            for timetable in train['timeTableRows']:
                if timetable['stationShortCode'].upper() in ('HKI', 'TPE'):
                    scheduled_arrival = timetable['scheduledTime']
                    actual_arrival = timetable.get('actualTime', None)
                    station_short_code = timetable['stationShortCode']
                    timetable_type = timetable['type'].upper()
                    delay_in_minutes = timetable.get('differenceInMinutes', None)
                    cancelled = timetable.get('cancelled', None)

                    cur.execute('''
                        INSERT INTO public.train_arrivals (train_number, station_short_code, timetable_type, date, scheduled_arrival, actual_arrival,
                         delay_in_minutes, cancelled, inserted_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)    
                        ON CONFLICT (train_number, date, station_short_code) DO NOTHING;
                    ''', (train_number, station_short_code, timetable_type, date, scheduled_arrival, actual_arrival,
                         delay_in_minutes, cancelled, datetime.now()))

    # Commit and close connection
    postgres_conn.commit()
    cur.close()
    postgres_conn.close()


def calculate_dates_history():
    today = date.today()
    end_date = today - timedelta(days=1)
    start_date = end_date - timedelta(days=365)
    return start_date, end_date


def get_historical_data(postgres_conn, train_number, station_short_code, timetable_type, start_date, end_date, day_of_week):
    query = '''
        SELECT timetable_type, scheduled_arrival, actual_arrival, delay_in_minutes, date
        FROM public.train_arrivals
        WHERE train_number = %s
        AND station_short_code = %s
        AND timetable_type = %s
        AND date BETWEEN %s AND %s
        AND EXTRACT(DOW FROM date) = %s
        AND cancelled = false;
    '''

    with postgres_conn.cursor() as cur:
        cur.execute(query, (train_number, station_short_code, timetable_type, start_date, end_date, day_of_week))
        data = cur.fetchall()
    cur.close()

    return data


def get_delays_and_dates(data):
    if data:
        delays_list = [row[3] for row in data if row[3] is not None]
        dates_list = [row[4] for row in data if row[4] is not None]
        return delays_list, dates_list


def calculate_average_delay(delays):
    if not delays:
        return 0
    return sum(delays) / len(delays)


def forecast_train_time(scheduled_arrival, average_delay):
    if average_delay is None:
        return scheduled_arrival
    return scheduled_arrival + timedelta(minutes=average_delay)


def get_most_recent_scheduled_arrival(postgres_conn, train_number, station_short_code, timetable_type, day_of_week, end_date):
    query = '''
        SELECT scheduled_arrival
        FROM train_arrivals
        WHERE train_number = %s
        AND station_short_code = %s
        AND timetable_type = %s
        AND EXTRACT(DOW FROM date) = %s
        AND date <= %s
        ORDER BY date DESC
        LIMIT 1;
    '''

    with postgres_conn.cursor() as cur:
        cur.execute(query, (train_number, station_short_code, timetable_type, day_of_week, end_date))
        data = cur.fetchone()
    cur.close()

    return data[0] if data else None


def get_scheduled_time(scheduled_info, station_short_code):
    if not scheduled_info:
        return None

    for entry in scheduled_info:
        journey = entry[0]
        for timetable in journey['timeTableRows']:
            if timetable['stationShortCode'].upper() == station_short_code and timetable['type'].upper() == 'ARRIVAL':
                scheduled_datetime = timetable['scheduledTime']
                parsed_datetime = parser.parse(scheduled_datetime)
                return parsed_datetime

    return None


def generate_line_chart(delays, times):
    plt.figure(figsize=(10, 6))
    plt.plot(times, delays, marker='o', linestyle='-', color='b', label='Delays')

    # Adding average line
    average_delay = calculate_average_delay(delays)
    plt.axhline(y=average_delay, color='r', linestyle='--', label=f'Average Delay: {average_delay:.2f} minutes')

    # Format x-axis with dates
    plt.xlabel('Time')
    plt.ylabel('Delay (minutes)')
    plt.title('Delays Over Time with Average Line')
    plt.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')
