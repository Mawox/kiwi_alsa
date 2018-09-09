import psycopg2
from psycopg2.extras import RealDictCursor
from http_reqs import get_stations, find_connection, safe_to_int
from datetime import date
from pprint import pprint

# from itertools import iteritems

pg_config = {
    "host": "35.234.120.106",
    "database": "pythonweekend",
    "user": "shareduser",
    "password": "NeverEverSharePasswordsInProductionEnvironement",
}

conn = psycopg2.connect(**pg_config)


stations = get_stations()
# pprint(stations)


def insert_data(connection):
    sql_insert = """
        INSERT INTO Jon_connections (src_id, dst_id, dep, arr, price, type)
        VALUES (%(src_id)s,
                %(dst_id)s,
    		    %(dep)s,
                %(arr)s,
                %(price)s,
                %(type)s);
    """
    values = connection
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(sql_insert, values)  # psycopg2 prepared statement syntax
        conn.commit()  # important, otherwise your data won’t be inserted!

    # departure_time & arrival_time should be datetime object, psycopg2 will format them for you


def check_if_exists(src, dst, dep_date, pax):
    sql_select = "SELECT * FROM Jon_connections WHERE src_id = %(src_id)s and dst_id = %(dst_id)s and dep = %(dep)s"

    values = {"src_id": src, "dst_id": dst, "dep": dep_date}
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(sql_select, values)
        results_dict = cursor.fetchall()
        return results_dict != []


def scrape_to_database(source, destination):

    if src == 0 or dst == 0:
        connection = None
    elif check_if_exists(src, dst, dep_date, pax):
        return
    else:

        connection = find_connection(trip)
    journey_string = f"journey_{src}_{dst}_{dep_date}_{pax}"
    data[journey_string] = connection
    add_to_databse(connection)


def add_to_databse(connection):
    if connection == None:
        connection = {
            "dep": trip["dates"].isoformat(),
            "arr": None,
            "src": source["name"],
            "dst": destination["name"],
            "type": "train",  # optional (bus/train)
            "price": None,
            "src_id": src,
            "dst_id": dst,
        }
    insert_data(connection)


if __name__ == "__main__":
    data = {}
    for i, source in enumerate(stations):

        for n, destination in enumerate(stations):
            if n % 100 == 0:
                perc = round(i / (len(stations) ** 2), 3)
                print("Progress:", perc, "%", "-" * 80)

            trip = {
                "src_name": source["name"],
                "dst_name": destination["name"],
                "dates": date(2018, 9, 20),
                "passengers": 1,
            }
            src, dst, dep_date, pax = (
                safe_to_int(source["id"]),
                safe_to_int(destination["id"]),
                trip["dates"].isoformat(),
                trip["passengers"],
            )
            scrape_to_database(source, destination)

    conn.close()
    pprint(data)
