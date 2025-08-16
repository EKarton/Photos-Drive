import logging
import numpy as np

from langchain.globals import set_debug
from photos_drive.shared.llm.models.open_clip_image_embeddings import (
    OpenCLIPImageEmbeddings,
)
import typer
from typing_extensions import Annotated

from photos_drive.cli.shared.logging import setup_logging
from photos_drive.cli.shared.typer import (
    createMutuallyExclusiveGroup,
)
from photos_drive.cli.commands.llms.embeddings_from_web import (
    men,
    women,
    people_playing_soccer,
    girls,
)

logger = logging.getLogger(__name__)

app = typer.Typer()
config_exclusivity_callback = createMutuallyExclusiveGroup(2)


@app.command()
def compare_embeddings(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Whether to show all logging debug statements or not",
        ),
    ] = False,
):
    setup_logging(verbose)
    if verbose:
        set_debug(True)

    logger.debug(
        "Called compare-embeddings handler with args:\n" + f" verbose={verbose}"
    )

    image_embedder = OpenCLIPImageEmbeddings()

    texts = ['men', 'women', 'people playing soccer', 'girls']
    web_embeddings = [men, women, people_playing_soccer, girls]

    for i in range(len(texts)):
        cli_embedding: np.ndarray = image_embedder.embed_texts([texts[i]])[0]
        web_embedding = web_embeddings[i]
        print(f"For {texts[i]}:", np.dot(cli_embedding, web_embedding))
