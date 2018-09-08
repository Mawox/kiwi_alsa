from flask import Flask, jsonify, request
from http_reqs import find_connection, find_station_name
from datetime import date

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True



@app.route('/search', methods=['GET'])
def search():
    print()
    trip = {
        "src_name": find_station_name(request.args.get('src')),
        "dst_name": find_station_name(request.args.get('dst')),
        "dep_date": date.fromisoformat(request.args.get('date_from'))
        "passengers" : int(request.args.get('passengers')),
    }
    results = find_connection(trip)
    return jsonify(results)


if __name__ == '__main__':
    app.run()

