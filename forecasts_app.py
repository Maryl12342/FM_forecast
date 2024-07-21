from datetime import datetime, timedelta
from utils import connect_to_postgres, fetch_train_data, calculate_dates_history, get_historical_data,\
    get_delays_and_dates, calculate_average_delay, get_scheduled_time, generate_line_chart, forecast_train_time
from flask import Flask, request, render_template

# Initialize Flask application
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    forecasted_time = None
    line_chart_data = None
    scheduled_time = None
    error_message = None

    if request.method == 'POST':
        # Getting user input
        day_of_ride = request.form.get('day_of_ride', '')
        train_number = request.form.get('train_number', '')
        station_short_code = request.form.get('station_short_code', '')
        timetable_type = request.form.get('timetable_type', '')
        try:
            future_date = datetime.strptime(day_of_ride, '%Y-%m-%d')
            day_of_week = future_date.weekday()
        except ValueError:
            error_message = 'Invalid date format. Please use YYYY-MM-DD.'
            return render_template('index.html', error_message=error_message)

        # Calculate date range for historical data (yesterday, yesterday -1 year)
        start_date, end_date = calculate_dates_history()

        conn = connect_to_postgres()

        # Get historical data
        data = get_historical_data(conn, train_number, station_short_code, timetable_type, start_date, end_date, day_of_week)

        train_delays, train_dates = get_delays_and_dates(data)
        average_delay = calculate_average_delay(train_delays)

        # Get scheduled arrival time for forecast calculation
        scheduled_info = fetch_train_data(day_of_ride, day_of_ride, train_number)
        scheduled_time = get_scheduled_time(scheduled_info, station_short_code)

        line_chart_data = generate_line_chart(train_delays, train_dates)
        if scheduled_time:
            forecasted_time = forecast_train_time(scheduled_time, average_delay)
        else:
            error_message = 'No scheduled arrival time available for the previous week.'

        conn.close()

    return render_template('index.html', forecasted_time=forecasted_time, scheduled_time=scheduled_time,
                           line_chart_data=line_chart_data, error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)
