import typer

app = typer.Typer()


@app.command()
def clean(ctx: typer.Context):
    print("clean handler")
    print(ctx)
