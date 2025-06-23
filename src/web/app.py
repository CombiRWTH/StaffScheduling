from flask import Flask, render_template

class App():
    _app: Flask

    def __init__(self):
        self._app = Flask(__name__)
        self._app.add_url_rule("/", "index", self.index)

    def index(self):
        return render_template("index.html")

    def run(self):
        self._app.run(debug=True, port=5000)