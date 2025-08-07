from typing import List, Optional
from photos_drive.cli.commands.llms.tools.media_item import (
    MediaItemModel,
    dataclass_to_pydantic_media_item,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from pydantic import BaseModel, Field
from photos_drive.shared.llm.models.image_embeddings import ImageEmbeddings
from photos_drive.shared.llm.vector_stores.base_vector_store import BaseVectorStore
from photos_drive.shared.metadata.media_item_id import (
    parse_string_to_media_item_id,
)
from photos_drive.shared.metadata.media_items_repository import MediaItemsRepository

DEFAULT_PROMPT = '''
Searches your photo library using a natural language query.
Use this tool when the user describes a photo, scene, or moment in words
(e.g., "photos of sunsets at the beach" or "pictures with dogs").
Returns the most visually relevant media items based on semantic similarity.
'''


class FindSimilarPhotosInput(BaseModel):
    media_item_id: str = Field(
        ..., description="Media item ID to find similar photos for"
    )
    top_k: Optional[int] = Field(5, description="Number of media items to retrieve")


class FindSimilarPhotosOutput(BaseModel):
    media_items: List[MediaItemModel] = Field(
        ..., description="List of similar media items"
    )


class FindSimilarPhotosTool(BaseTool):
    name: str = "FindSimilarPhotos"
    description: str = DEFAULT_PROMPT
    args_schema: Optional[ArgsSchema] = FindSimilarPhotosInput
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
        media_item_id: str,
        top_k: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> FindSimilarPhotosOutput:
        print('find_similar_photos:', media_item_id)

        media_item = self.media_items_repo.get_media_item_by_id(
            parse_string_to_media_item_id(media_item_id)
        )
        if not media_item.embedding_id:
            return FindSimilarPhotosOutput(media_items=[])

        embedding = self.vector_store.get_embedding_by_id(media_item.embedding_id)
        rel_embeddings = self.vector_store.get_relevent_media_item_embeddings(
            embedding.embedding, k=top_k
        )

        return FindSimilarPhotosOutput(
            media_items=[
                dataclass_to_pydantic_media_item(
                    self.media_items_repo.get_media_item_by_id(
                        rel_embedding.media_item_id
                    )
                )
                for rel_embedding in rel_embeddings
            ]
        )

    async def _arun(
        self,
        media_item_id: str,
        top_k: int = 5,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> FindSimilarPhotosOutput:
        """Use the tool asynchronously."""
        return self._run(
            media_item_id,
            top_k,
            run_manager=run_manager.get_sync() if run_manager else None,
        )
