import jsonify
import requests
from flask import (Flask, make_response, redirect, render_template, request,
                   url_for)

app = Flask("FlaskApp")

FASTAPI_URL = "http://fastapi-app:8000"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    resp = make_response(redirect(url_for("login")))
    resp.set_cookie("access_token", "", expires=0)
    return resp


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form_data = request.form
        username = form_data.get("username")
        password = form_data.get("password")

        # Payload
        data = {"username": username, "password": password}

        try:
            response = requests.post(FASTAPI_URL + "/token", data=data)

            # Check response
            if response.status_code == 200:
                access_token = response.json().get("access_token")

                # Store cookies
                resp = make_response(redirect(url_for("dashboard")))
                resp.set_cookie("access_token", access_token, httponly=True, secure=True)

                return resp
            else:
                return redirect(url_for("login"))

        except requests.exceptions.RequestException as e:
            return (
                jsonify({"error": "Error communicating with FastAPI", "message": str(e)}),
                500,
            )
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        form_data = request.form
        email = form_data.get("username")
        password = form_data.get("password")

        # Payload
        data = {"username": email, "password": password}

        try:
            response = requests.post(FASTAPI_URL + "/register", data=data)

            if response.status_code == 200:
                return redirect(url_for("login"))
            else:
                return redirect(url_for("login"))
        except requests.exceptions.RequestException as e:
            return (
                jsonify({"error": "Error communicating with FastAPI", "message": str(e)}),
                500,
            )
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    access_token = request.cookies.get("access_token")

    if not access_token:
        return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(FASTAPI_URL + "/portfolio/coin/", headers=headers)

    if response.status_code == 200:
        items = response.json()
    elif response.status_code == 401:
        return redirect(url_for("login"))
    else:
        items = []

    return render_template("dashboard.html", items=items)


@app.route("/search", methods=["GET", "POST"])
def search():

    access_token = request.cookies.get("access_token")
    if not access_token:
        return redirect(url_for("login"))

    if request.method == "POST":
        symbol = request.form["symbol"]
        access_token = request.cookies.get("access_token")

        if not access_token:
            return redirect(url_for("login"))

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(FASTAPI_URL + "/portfolio/coin/search/?coin_cymbol=" + symbol, headers=headers)

        if response.status_code == 200:
            search_results = response.json()
        elif response.status_code == 401:
            return redirect(url_for("login"))
        else:
            search_results = []

        return render_template("dashboard.html", search_results=search_results)

    access_token = request.cookies.get("access_token")

    if not access_token:
        return redirect(url_for("login"))
    return render_template("dashboard.html", search_results=[])


@app.route("/add_coin/<coin_id>", methods=["POST"])
def add_coin(coin_id):
    access_token = request.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.post(
        FASTAPI_URL + "/portfolio/coin/add/?coin_text_id=" + coin_id + "&currency=usd", headers=headers
    )

    if response.status_code == 200:
        return {"message": "Coin added successfully"}, 200
    else:
        return {"message": "Error adding coin"}, 500


@app.route("/delete_coin/<coin_id>", methods=["DELETE"])
def delete_coin(coin_id):
    access_token = request.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.delete(FASTAPI_URL + "/coin/remove/" + coin_id, headers=headers)

    if response.status_code == 200:
        return {"message": "Coin removed successfully"}, 200
    else:
        return {"message": "Error removed coin"}, 500


if __name__ == "__main__":
    app.run(debug=True)
