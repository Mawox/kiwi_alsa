from requests_html import HTMLSession
import re
from bs4 import BeautifulSoup
from datetime import datetime, date
from pprint import pprint
from redis import StrictRedis
from slugify import slugify
import difflib
import json

redis_config = {"host": "35.198.72.72", "port": 3389}

redis = StrictRedis(socket_connect_timeout=3, **redis_config)
session = HTMLSession()


def get_stations() -> dict:

    stations = redis.get("stations_names_leave_me_alone121")
    if stations is not None:
        return json.loads(stations)

    data = session.get(
        "https://www.alsa.com/en/c/portal/layout?p_l_id=70167&p_p_cacheability=cacheLevelPage&p_p_id=JourneySearchPortlet_WAR_Alsaportlet&p_p_lifecycle=2&p_p_resource_id=JsonGetOrigins&locationMode=1&_=1536485710879"
    )
    stations = data.json()

    redis.set("stations_names_leave_me_alone121", json.dumps(stations))
    print(f"Set stations_names_leave_me_alone to {stations}")
    return stations


# noinspection PyPep8Naming
def find_ID_in_json(name: str, json_data: dict) -> int:
    name = str(name)

    for i in json_data:
        if name in slugify(i["name"], separator="_"):
            return i["id"]


def find_journeys(trip: dict) -> dict:

    payload = {
        "p_auth": auth,
        "p_p_id": "PurchasePortlet_WAR_Alsaportlet",
        "p_p_lifecycle": "1",
        "p_p_state": "normal",
        "p_p_mode": "view",
        "p_p_col_id": "column-1",
        "p_p_col_count": "3",
        "_PurchasePortlet_WAR_Alsaportlet_javax.portlet.action": "searchJourneysAction",
        "code": "",
        "serviceType": "",
        "accessible": "0",
        "originStationNameId": trip["src_name"],
        "destinationStationNameId": trip["dst_name"],
        "originStationId": trip["src_id"],
        "destinationStationId": trip["dst_id"],
        "departureDate": trip["dates"].strftime("%m/%d/%Y"),
        "_departureDate": trip["dates"].strftime("%m/%d/%Y"),
        "returnDate": "",
        "_returnDate": "",
        "locationMode": "1",
        "passengerType-1": trip["passengers"],
        "passengerType-4": "0",
        "passengerType-5": "0",
        "passengerType-2": "0",
        "passengerType-3": "0",
        "numPassengers": trip["passengers"],
        "regionalZone": "",
        "travelType": "OUTWARD",
        "LIFERAY_SHARED_isTrainTrip": "false",
        "promoCode": "",
        "jsonAlsaPassPassenger": "",
        "jsonVoucherPassenger": "",
    }
    # pprint(payload)
    a = session.get("https://www.alsa.com/en/web/bus/checkout", params=payload)

    soup = BeautifulSoup(a.text, features="lxml")
    journey_data_url = soup.find("data-sag-journeys-component")[
        "sag-journeys-table-body-url"
    ]
    journey_data = session.get(journey_data_url).json()
    if journey_data.get("errorMessage") is not None:
        # print("", journey_data.get("errorMessage"))
        return None
    return journey_data


# noinspection PyPep8Naming
def time_UTC_to_ISO(time: int) -> str:
    # print(time)
    d = date.fromtimestamp(time // 1000).isoformat()
    # print(d)
    return d


def parse_journey(journey: dict) -> dict:
    # pprint(journey)
    output_data = {
        "dep": time_UTC_to_ISO(journey.get("departureDate")),
        "arr": time_UTC_to_ISO(journey.get("arrivalDate")),
        "src": journey.get("originName"),
        "dst": journey.get("destinationName"),
        "type": "bus"
        if "busCharacteristic" in journey
        else "train",  # optional (bus/train)
        "price": min(journey["fares"], key=lambda x: x.get("price"))["price"],
        "src_id": journey.get("originId"),  # optional (alsa id)
        "dst_id": journey.get("destinationId"),  # optional (alsa id)
    }
    return output_data


def add_cheapest_fare(journeys: dict):
    for journey in journeys["journeys"]:
        journey["lowest_fare"] = min(journey["fares"], key=lambda x: x.get("price"))[
            "price"
        ]
    return


def get_city_id(name: str) -> int:
    city_id = redis.get(name)
    try:
        return int(city_id)
    except (TypeError, ValueError) as e:
        # print("name is", e)
        stations = get_stations()
        city_id = find_ID_in_json(name, stations)
        redis.set(name, city_id)
        print(f"Set {name} to {city_id}")
        return safe_to_int(city_id)


def safe_to_int(inp):
    try:
        return int(inp)
    except ValueError:
        return 0


def find_journey(trip):
    results = {}

    src, dst, dep_date, pax = (
        trip["src_id"],
        trip["dst_id"],
        trip["dates"],
        trip["passengers"],
    )
    journey_string = f"journey_{src}_{dst}_{dep_date}_{pax}"

    journey = redis.get(journey_string)
    if journey is not None:
        return json.loads(journey)

    journeys = find_journeys(trip)
    # add_cheapest_fare(journeys)
    if journeys is None:
        return None
    try:
        cheapest_journey_loc = journeys["journeys"][
            0
        ]  # min(journeys["journeys"], key=lambda x: x.get("lowest_fare"))
    except IndexError as e:
        # print("IndexError", e)
        return None

    journey = parse_journey(cheapest_journey_loc)

    redis.set(journey_string, json.dumps(journey))
    print(f"Set {journey_string} to {journey}")

    return journey


def auth_start():
    global session, auth

    a = session.get("https://www.alsa.com/en/web/bus/home")

    auth = re.search("Liferay.authToken = '[\s\S]*?';", a.text)
    auth = auth.group(0)[21:-2]


def find_connection(trip: dict) -> dict:
    if "auth" not in globals():
        auth_start()
    origin = slugify(trip["src_name"], separator="_")
    destination = slugify(trip["dst_name"], separator="_")

    trip["src_id"] = get_city_id(origin)
    trip["dst_id"] = get_city_id(destination)

    cheapest_journey = find_journey(trip)

    return cheapest_journey


def find_station_name(partial_name: str) -> str:
    stations = get_stations()

    for i in stations:
        if slugify(partial_name) in slugify(i["name"], separator="_"):
            return i["name"]

    best_match = difflib.get_close_matches(
        partial_name, [i["name"] for i in stations], n=1
    )
    # print(best_match)
    return best_match[0]


if __name__ == "__main__":
    trip = {
        "src_name": "Barcelona (All stops)",
        "dst_name": "Madrid (All stops)",
        "dates": date(2018, 10, 10),
        "passengers": 1,
    }

    print(find_connection(trip))
