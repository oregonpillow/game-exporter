import typer

app = typer.Typer()


@app.callback()
def callback():
    """
    Game Exporter CLI
    """
    pass


@app.command()
def steam():
    """
    Run the Steam exporter.
    """
    from game_exporter import steam_exporter

    steam_exporter.main()


@app.command()
def playstation():
    """
    Run the PlayStation exporter.
    """
    from game_exporter import playstation_exporter

    playstation_exporter.main()


if __name__ == "__main__":
    app()
