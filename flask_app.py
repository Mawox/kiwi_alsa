from flask import Flask, jsonify, request, render_template
from http_reqs import find_connection, find_station_name
from datetime import date, timedelta
from time import time
from pprint import pprint


app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True


@app.route("/")
def template_test():
    print("A")
    return render_template("results.html", welcome="Hello world")


@app.route("/search", methods=["GET", "POST"])
def search():
    t0 = time()
    date_from = date.fromisoformat(request.args.get("date_from"))
    date_to = date.fromisoformat(request.args.get("date_to", date_from.isoformat()))
    t_d = date_to - date_from
    dates = [date_from + timedelta(days=x) for x in range(t_d.days + 1)]
    print(dates)
    trip = {
        "src_name": find_station_name(request.args.get("src")),
        "dst_name": find_station_name(request.args.get("dst")),
        # "dep_date": dates,
        "passengers": int(request.args.get("passengers", 1)),
        "dates": dates,
    }
    search_results = find_connection(trip)
    pprint(search_results)
    return render_template(
        "results.html",
        search=trip,
        results=search_results.values(),
        t=round(time() - t0, 1),
    )


if __name__ == "__main__":
    app.run()
