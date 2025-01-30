import typer


app = typer.Typer()


@app.command()
def init(ctx: typer.Context):
    print('config init')
    print(ctx)
