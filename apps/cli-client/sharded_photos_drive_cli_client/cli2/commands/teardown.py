import typer

app = typer.Typer()


@app.command()
def teardown(ctx: typer.Context):
    print("teardown handler")
    print(ctx)
