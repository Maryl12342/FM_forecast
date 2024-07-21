from utils import fetch_train_data, connect_to_postgres, insert_data_to_postgres, calculate_dates_history
TRAIN_NUMBER = 27

# Fetch data for the last year
start_date, end_date = calculate_dates_history()
train_data = fetch_train_data(start_date, end_date, TRAIN_NUMBER)
conn = connect_to_postgres()
insert_data_to_postgres(conn, train_data)
