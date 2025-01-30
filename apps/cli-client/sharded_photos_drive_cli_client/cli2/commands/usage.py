import typer

app = typer.Typer()


@app.command()
def usage(ctx: typer.Context):
    print("usage handler")
    print(ctx)
