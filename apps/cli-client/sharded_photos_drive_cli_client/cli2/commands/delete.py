import typer

app = typer.Typer()


@app.command()
def delete(ctx: typer.Context):
    print("delete handler")
    print(ctx)
