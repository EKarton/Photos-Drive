import typer

app = typer.Typer()


@app.command()
def sync(ctx: typer.Context):
    print("sync handler")
    print(ctx)
