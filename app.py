from flask import Flask, request, jsonify, render_template, redirect
import time
import threading
import pymysql
from datetime import datetime

app = Flask(__name__)

# Initialize data variables
received_data = None
received_data2 = None
latest_data = {}
last_post_time = time.time()
is_device_connected = False
data_expiry_time = 3  # Time in seconds after which data expires

MYSQL_HOST = "db-mysql-blr1-66074-do-user-14248157-0.b.db.ondigitalocean.com"
MYSQL_USER = "doadmin"
MYSQL_PASSWORD = "AVNS_LmiUK2PelZn9rejYQa7"
MYSQL_DB = "defaultdb"
MYSQL_PORT = 25060
sslmode = "REQUIRED"

# MySQL configuration
# MYSQL_HOST = '127.0.0.1'
# MYSQL_USER = 'root'
# MYSQL_PASSWORD = 'aapl@123'
# MYSQL_DB = 'elogari'

def create_connection():
    return pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, port=MYSQL_PORT)

def get_filtered_data(start_datetime, end_datetime):
    connection = create_connection()  # Call the function to obtain the connection object
    cursor = connection.cursor()

    query = "SELECT id, timestamp, channel, value FROM logging_data WHERE timestamp BETWEEN %s AND %s"

    cursor.execute(query, (start_datetime, end_datetime))

    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return data

def execute_query(query, values):
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, values)
        connection.commit()
    except pymysql.Error as e:
        print(f"Error executing query: {e}")
        connection.rollback()  # Rollback the transaction in case of error
    finally:
        connection.close()

@app.route('/dodata', methods=['GET', 'POST'])
def handle_requests():
    global received_data
    if request.method == 'POST':
        try:
            received_data = request.get_json()
            return jsonify({'Digital_Output_Value': 'Data received successfully'})
        except Exception as e:
            return jsonify({'status': 'Error: {}'.format(str(e))}), 400
    elif request.method == 'GET':
        if received_data:
            return jsonify(received_data)
        else:
            return jsonify({'status': 'No data received'})

@app.route('/aodata', methods=['GET', 'POST'])
def handle_aodata():
    global received_data2
    if request.method == 'POST':
        received_data2 = request.get_json()
        return jsonify({'status': 'Data received successfully'})
    elif request.method == 'GET':
        if received_data2:
            return jsonify(received_data2)
        else:
            return jsonify({'status': 'No data received'})

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'Admin' and password == 'aapl123':
            # Successful login, redirect to /home route
            return redirect('/home')
        else:
            # Invalid login, pass error message to the template
            error_message = 'Invalid username or password.'
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('index.html')

# @app.route('/DataFilter', methods=['GET', 'POST'])
# def filter_data():
#     if request.method == 'POST':
#         start_datetime_str = request.form.get('start_datetime')
#         end_datetime_str = request.form.get('end_datetime')

#         if start_datetime_str and end_datetime_str:
#             start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')
#             end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M')

#             channel_data = [[] for _ in range(12)]
#             filtered_data = get_filtered_data(start_datetime, end_datetime)
#             for row in filtered_data:
#                 channel = int(row[2])
#                 value = row[3]
#                 timestamp = row[1]
#                 if 4 <= channel <= 7:
#                     if float(value) > 3:
#                         channel_data[channel].append((timestamp, "ON"))
#                     else:
#                         channel_data[channel].append((timestamp, "OFF"))
#                 else:
#                     channel_data[channel].append((timestamp, value))
#         else:
#             channel_data = None
#             start_datetime_str = ''
#             end_datetime_str = ''
#     else:
#         channel_data = None
#         start_datetime_str = ''
#         end_datetime_str = ''

#     return render_template('DataFilter.html', channel_data=channel_data, start_datetime=start_datetime_str, end_datetime=end_datetime_str, max=max)


@app.route('/DataFilter', methods=['GET', 'POST'])
def filter_data():
    if request.method == 'POST':
        start_datetime_str = request.form.get('start_datetime')
        end_datetime_str = request.form.get('end_datetime')

        if start_datetime_str and end_datetime_str:
            start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')
            end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M')

            channel_data = [[] for _ in range(12)]
            filtered_data = get_filtered_data(start_datetime, end_datetime)
            for row in filtered_data:
                channel = int(row[2])
                value = row[3]
                timestamp = row[1]
                if 4 <= channel <= 7:
                    if float(value) > 3:
                        # Formatting value to 4 decimal places
                        value = "{:.4f}".format(float(value))
                        channel_data[channel].append((timestamp, "ON"))
                    else:
                        # Formatting value to 4 decimal places
                        value = "{:.4f}".format(float(value))
                        channel_data[channel].append((timestamp, "OFF"))
                else:
                    # Formatting value to 4 decimal places
                    value = "{:.4f}".format(float(value))
                    channel_data[channel].append((timestamp, value))
        else:
            channel_data = None
            start_datetime_str = ''
            end_datetime_str = ''
    else:
        channel_data = None
        start_datetime_str = ''
        end_datetime_str = ''

    return render_template('DataFilter.html', channel_data=channel_data, start_datetime=start_datetime_str, end_datetime=end_datetime_str, max=max)
@app.route('/insert_data', methods=['POST'])
def handle_insert_data():
    json_data = request.get_json()
    if isinstance(json_data, list):
        for item in json_data:
            if 'CHANNEL' in item and 'VALUE' in item:
                channel = str(item['CHANNEL'])
                value = str(item['VALUE'])
                latest_data[channel] = {'CHANNEL': channel, 'VALUE': value}
                insert_data_to_mysql(channel, value)
    else:
        channel = str(json_data['CHANNEL'])
        value = str(json_data['VALUE'])
        latest_data[channel] = {'CHANNEL': channel, 'VALUE': value}
        insert_data_to_mysql(channel, value)
    return 'Success'



def insert_data_to_mysql(channel, value):
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    query = "INSERT INTO logging_data (timestamp, channel, value) VALUES (%s, %s, %s)"
    values = (current_time, channel, value)
    execute_query(query, values)

@app.route('/data/', methods=['POST', 'GET'])
def data():
    global latest_data, is_device_connected, last_post_time

    # Check if no new data has been received for 5 seconds
    current_time = time.time()
    if current_time - last_post_time > 5:
        latest_data = {}  # Delete all data

        # Update device connection status
        is_device_connected = False

    if request.method == 'GET':
        sorted_data = [latest_data[str(i)] for i in sorted(latest_data, key=int)]
        return jsonify(sorted_data)
    else:
        try:
            json_data = request.get_json()

            # Validate the received data structure
            if isinstance(json_data, dict):
                channel = str(json_data.get('CHANNEL', ''))
                value = str(json_data.get('VALUE', ''))
                if channel and value:
                    latest_data[channel] = {'CHANNEL': channel, 'VALUE': value}
            elif isinstance(json_data, list):
                for item in json_data:
                    channel = str(item.get('CHANNEL', ''))
                    value = str(item.get('VALUE', ''))
                    if channel and value:
                        latest_data[channel] = {'CHANNEL': channel, 'VALUE': value}
            else:
                return jsonify({'status': 'Invalid data format'})

            # Update device connection status and last post time
            is_device_connected = True
            last_post_time = current_time

            return 'Success'
        except Exception as e:
            return jsonify({'status': 'Error', 'message': str(e)})
   
# Function to periodically check device connection status
def check_connection():
    global is_device_connected, last_post_time
    while True:
        current_time = time.time()
        if current_time - last_post_time > 5:
            # No new data received, update device connection status
            is_device_connected = False
        time.sleep(1)  # Check connection status every 1 second


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
