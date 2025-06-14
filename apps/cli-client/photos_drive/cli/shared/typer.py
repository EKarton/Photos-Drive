import typer


def createMutuallyExclusiveGroup(size=2):
    group = set()

    def callback(ctx: typer.Context, param: typer.CallbackParam, value: str):
        if value is not None and param.name not in group:
            group.add(param.name)
            if len(group) > size - 1:
                remaining_group = set(group)
                remaining_group.remove(param.name)
                raise typer.BadParameter(
                    f"{param.name} is mutually exclusive with {remaining_group}"
                )
        return value

    return callback
