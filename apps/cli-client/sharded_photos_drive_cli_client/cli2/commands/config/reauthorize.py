import typer

app = typer.Typer()


@app.command()
def gphotos(ctx: typer.Context):
    print('config reauthorize gphotos')
    print(ctx)


@app.command()
def mongodb(ctx: typer.Context):
    print("config reauthorize mongodb")
    print(ctx)
