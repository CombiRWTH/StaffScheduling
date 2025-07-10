from web import App
from loader import Loader


def main(loader: Loader, debug: bool = False):
    app = App(loader=loader)
    app.run(debug=debug)


if __name__ == "__main__":
    main()
