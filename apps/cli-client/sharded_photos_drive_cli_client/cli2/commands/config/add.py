import typer

app = typer.Typer()


@app.command()
def gphotos(ctx: typer.Context):
    print('config add gphotos')
    print(ctx)


@app.command()
def mongodb(ctx: typer.Context):
    print("config add mongodb")
    print(ctx)
