from driver import Driver
from bs4 import BeautifulSoup
import csv, time
from rich import print
import random
import re
import datetime
import time
import os
import sys

category = "tiktok"
country = "Italy"
dateType = "Daily"

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
WAIT_TIME_LIMIT = int(os.getenv('WAIT_TIME_LIMIT'))

def loginProcess(random_id):
    while True:
        try:
            for driver in DriversPool:
                if driver.is_available() and not driver.has_response():
                    driver.do_login()
                    break
            else:
                time.sleep(1)
                print(f'[{random_id}] Waiting for a driver to be available...')
                continue
            break
        except Exception as err:
            print(err)

    wait_time = 0
    while True:
        try:
            if driver.has_response():
                break
            time.sleep(1)
            print(f'[{random_id}] Waiting for a response...')
            wait_time += 1
            if wait_time == WAIT_TIME_LIMIT: 
                driver.release()
                return
        except Exception as err:
            print(err)
            return False
        
    driver.release()
           
    return True

def getCharts(country_id, charts_date, date_type, random_id):

    while True:
        try:
            for driver in DriversPool:
                if driver.is_available() and not driver.has_response():
                    driver.get_charts_tiktok(country_id, charts_date, date_type)
                    break
            else:
                time.sleep(1)
                print(f'[{random_id}] Waiting for a driver to be available...')
                continue
            break
        except Exception as err:
            print(err)

    wait_time = 0
    while True:
        try:
            if driver.has_response():
                break
            time.sleep(1)
            print(f'[{random_id}] Waiting for a response...')
            wait_time += 1
            if wait_time == WAIT_TIME_LIMIT: 
                driver.release()
                return
        except Exception as err:
            print(err)
            return None
        
    soup = BeautifulSoup(driver.get_response(), 'html.parser')

    chart_date_input = soup.find('input', {'id': 'datepicker-chart'})
    chart_date = chart_date_input['value']
    
    data_table = soup.find('table')

    rows = []

    if data_table is not None:

        for tr in data_table.find('tbody').find_all('tr'):
            position = tr.find('td', {'class': 'position'}).contents[0]
            title = tr.find('td', {'class': 'title'}).find('span', {'class': 'title'}).find('a').text.replace('\n', '').strip()
            artists = tr.find('td', {'class': 'title'}).find('span', {'class': 'artists'}).text.replace('\n', '').strip()

            tds = tr.find_all('td')
            regex_pattern = r"[^\w\s]" 
            newVideos = re.sub(regex_pattern, "", tds[3].text).replace('\n', '').strip()
            totalVideos = re.sub(regex_pattern, "", tds[4].text).replace('\n', '').strip()
            rows.append({
                'position': position,
                'title': title,
                'artists': artists,
                'newVideos': newVideos,
                'totalVideos': totalVideos,
            })

    driver.release()
        
    return {
        'date': chart_date,
        'rows': rows
    }

def writeCharts(country_id, charts_date, date_type):

    charts = getCharts(country_id, charts_date, date_type, random.randint(10000, 99999))

    chart_date = charts['date']
    rows = charts['rows']

    if len(rows) == 0:
        print("Whoops! no data for the chart you are looking for")
        return
    
    chart_date_obj = datetime.datetime.strptime(chart_date, '%Y-%m-%d')
    chart_month = chart_date_obj.strftime('%Y-%m')
    output_dir = f'{os.path.dirname(os.path.abspath(__file__))}/output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_dir = f'{output_dir}/{chart_month}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_dir = f'{output_dir}/{category}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = f'{output_dir}/output_{category}_{date_type}_{chart_date}.csv'
    if os.path.exists(output_path):
        return

    output_file = open(output_path, 'w+', newline='', encoding='utf8')
    writer = csv.writer(output_file)

    writer.writerow(["position", "title", "artists", "new videos", "total videos"])
    output_file.flush()

    for row in rows:
        if (row is None):
            continue
        writer.writerow([row['position'], row['title'], row['artists'], row['newVideos'], row['totalVideos']])
        output_file.flush()
        print(row)

def scrape_tiktok(start_date, end_date):
    global DriversPool

    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d %H-%M-%S")

    print("======== Starting the App: Tiktok ==========")

    # Get the command line arguments
    run_mode = "date-range"

    if (run_mode == "date-range"):
        # in case of date-range mode
        print("Please input start date. Default would be the first day of this month.")

        if (start_date == ""):
            first_day = datetime.date(now.year, now.month, 1)
            start_date = first_day.strftime("%Y-%m-%d")

        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        except Exception as err:
            print("Invalid date string. please try again")
            print(err)

        start_date = datetime.date(start_date.year, start_date.month, start_date.day)
        if end_date is None:
            end_date = datetime.date(now.year, now.month, now.day)
        delta = datetime.timedelta(days=1)

        DriversSize = 1
        DriversPool = [Driver() for _ in range(DriversSize)]

        loginProcess(random.randint(10000, 99999))

        while start_date <= end_date:
            print("running for", start_date.strftime("%Y-%m-%d"))
            writeCharts(country, start_date.strftime("%Y-%m-%d"), dateType)
            start_date += delta

    else:
        # in case of one-time mode
        print("Please input date. Default would be Today")

        ch_date = None
        while True:
        
            ch_date = input("date (i.e 2023-01-01): ")
            if (ch_date == ""):
                ch_date = now.strftime("%Y-%m-%d")

            try:
                ch_date = datetime.datetime.strptime(ch_date, '%Y-%m-%d')
            except Exception as err:
                print("Invalid date string. please try again")
                print(err)
                continue
            break

        ch_date = datetime.date(ch_date.year, ch_date.month, ch_date.day)

        DriversSize = 1
        DriversPool = [Driver() for _ in range(DriversSize)]
        # executor = concurrent.futures.ThreadPoolExecutor(max_workers=DriversSize)
        futures = []

        initial_row = {'process': "login", "description": "do login"}

        loginProcess(random.randint(10000, 99999))

        writeCharts(country, ch_date.strftime("%Y-%m-%d"), dateType)


# if __name__ == '__main__s':

#     now = datetime.datetime.now()
#     date_string = now.strftime("%Y-%m-%d %H-%M-%S")

#     print("======== Starting the App ==========")

#     # Get the command line arguments
#     mode_arg = "" if not len(sys.argv) > 1 else sys.argv[1] 

#     run_mode = ""
#     if not mode_arg == '--one-time':
#         print("Please select running mode. There are 'date-ranger' and 'one-time' mode.")
#         while True:
#             res = input("date-range mode? (Y/n): ").lower()
#             if (res == "y" or res == ""):
#                 run_mode = "date-range"
#             elif res == "n":
#                 run_mode = "one-time"
#             else:
#                 print("Invalid input. Please enter 'y' or 'n'.")
#                 continue    
#             break
#     else:
#         run_mode = "one-time"

#     if (run_mode == "date-range"):
#         # in case of date-range mode
#         print("Please input start date. Default would be the first day of this month.")

#         start_date = None
#         while True:
        
#             start_date = input("start from (i.e 2023-01-01): ")
#             if (start_date == ""):
#                 first_day = datetime.date(now.year, now.month, 1)
#                 start_date = first_day.strftime("%Y-%m-%d")

#             try:
#                 start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
#             except Exception as err:
#                 print("Invalid date string. please try again")
#                 print(err)
#                 continue
#             break

#         start_date = datetime.date(start_date.year, start_date.month, start_date.day)
#         end_date = datetime.date(now.year, now.month, now.day)
#         delta = datetime.timedelta(days=1)

#         DriversSize = 1
#         DriversPool = [Driver() for _ in range(DriversSize)]

#         loginProcess(random.randint(10000, 99999))

#         while start_date <= end_date:
#             print("running for", start_date.strftime("%Y-%m-%d"))
#             writeCharts(country, start_date.strftime("%Y-%m-%d"), dateType)
#             start_date += delta

#     else:
#         # in case of one-time mode
#         print("Please input date. Default would be Today")

#         ch_date = None
#         while True:
        
#             ch_date = input("date (i.e 2023-01-01): ")
#             if (ch_date == ""):
#                 ch_date = now.strftime("%Y-%m-%d")

#             try:
#                 ch_date = datetime.datetime.strptime(ch_date, '%Y-%m-%d')
#             except Exception as err:
#                 print("Invalid date string. please try again")
#                 print(err)
#                 continue
#             break

#         ch_date = datetime.date(ch_date.year, ch_date.month, ch_date.day)

#         DriversSize = 1
#         DriversPool = [Driver() for _ in range(DriversSize)]
#         # executor = concurrent.futures.ThreadPoolExecutor(max_workers=DriversSize)
#         futures = []

#         initial_row = {'process': "login", "description": "do login"}

#         loginProcess(random.randint(10000, 99999))

#         writeCharts(country, ch_date.strftime("%Y-%m-%d"), dateType)
