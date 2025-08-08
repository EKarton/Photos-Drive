from datetime import datetime
from typing import List, Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field

from photos_drive.cli.commands.llms.tools.media_item import (
    MediaItemModel,
    dataclass_to_pydantic_media_item,
)
from photos_drive.shared.llm.models.image_embeddings import ImageEmbeddings
from photos_drive.shared.llm.vector_stores.base_vector_store import (
    BaseVectorStore,
    QueryMediaItemEmbeddingRequest,
)
from photos_drive.shared.metadata.media_item_id import parse_string_to_media_item_id
from photos_drive.shared.metadata.media_items_repository import MediaItemsRepository

DEFAULT_PROMPT = '''
Use this tool to search for photos based on a natural language description.

This tool is ideal when the user describes what they want to see in photos —
for example, "sunsets on the beach", "photos with dogs", or "Christmas morning".

The tool embeds the user's text query and retrieves visually similar media items
from the photo library based on semantic similarity.
'''


class SearchPhotosByTextToolInput(BaseModel):
    query: str = Field(..., description="A text string describing what to find")
    earliest_date_taken: str = Field(
        '',
        description="Earliest photo date (YYYY-MM-DD) to include in search. "
        + "If empty (''), no lower bound for when the photo should be taken "
        + "will be applied. Can be used alone or with latest_date_taken.",
    )
    latest_date_taken: str = Field(
        '',
        description="Latest photo date (YYYY-MM-DD) to include in search. "
        + "If empty (''), no upper bound for when the photo should be taken "
        + "will be applied. Can be used alone or with earliest_date_taken.",
    )
    within_media_item_ids: str = Field(
        '',
        description="A list of media item IDs to include in the search, delimited "
        + "with commas (','). If empty (''), we will consider all photos.",
    )
    top_k: Optional[int] = Field(
        5, description="Maximum number of similar photos to retrieve."
    )


class SearchPhotosByTextToolOutput(BaseModel):
    media_items: List[MediaItemModel] = Field(..., description="List of similar photos")


class SearchPhotosByTextTool(BaseTool):
    name: str = "SearchPhotosByText"
    description: str = DEFAULT_PROMPT
    args_schema: Optional[ArgsSchema] = SearchPhotosByTextToolInput
    return_direct: bool = False

    image_embedder: ImageEmbeddings = Field(..., exclude=True)
    vector_store: BaseVectorStore = Field(..., exclude=True)
    media_items_repo: MediaItemsRepository = Field(..., exclude=True)

    def __init__(
        self,
        image_embedder: ImageEmbeddings,
        vector_store: BaseVectorStore,
        media_items_repo: MediaItemsRepository,
    ):
        super().__init__(
            image_embedder=image_embedder,
            vector_store=vector_store,
            media_items_repo=media_items_repo,
        )

    def _run(
        self,
        query: str,
        earliest_date_taken: str = '',
        latest_date_taken: str = '',
        within_media_item_ids: str = '',
        top_k: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> SearchPhotosByTextToolOutput:
        query_embedding = self.image_embedder.embed_texts([query])[0]

        earliest_date_obj = None
        if earliest_date_taken != '':
            earliest_date_obj = datetime.strptime(earliest_date_taken, "%Y-%m-%d")

        latest_date_obj = None
        if latest_date_taken != '':
            latest_date_obj = datetime.strptime(latest_date_taken, "%Y-%m-%d")

        within_media_item_id_objs = None
        if within_media_item_ids != '':
            within_media_item_id_objs = [
                parse_string_to_media_item_id(raw_media_item_id)
                for raw_media_item_id in within_media_item_ids.split(',')
            ]

        embeddings = self.vector_store.get_relevent_media_item_embeddings(
            QueryMediaItemEmbeddingRequest(
                embedding=query_embedding,
                start_date_taken=earliest_date_obj,
                end_date_taken=latest_date_obj,
                within_media_item_ids=within_media_item_id_objs,
                top_k=top_k,
            )
        )

        return SearchPhotosByTextToolOutput(
            media_items=[
                dataclass_to_pydantic_media_item(
                    self.media_items_repo.get_media_item_by_id(embedding.media_item_id)
                )
                for embedding in embeddings
            ]
        )

    async def _arun(
        self,
        query: str,
        earliest_date_taken: str = '',
        latest_date_taken: str = '',
        within_media_item_ids: str = '',
        top_k: int = 5,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> SearchPhotosByTextToolOutput:
        """Use the tool asynchronously."""
        return self._run(
            query,
            earliest_date_taken,
            latest_date_taken,
            within_media_item_ids,
            top_k,
            run_manager=run_manager.get_sync() if run_manager else None,
        )
