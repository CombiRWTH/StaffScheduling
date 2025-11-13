from loader import Loader
from web import App


def main(loader: Loader, debug: bool = False):
    app = App(loader=loader)
    app.run(debug=debug)


if __name__ == "__main__":
    main()
