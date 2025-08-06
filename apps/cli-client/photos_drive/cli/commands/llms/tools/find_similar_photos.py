from typing import List, Optional
from photos_drive.cli.commands.llms.tools.media_item import (
    MediaItemModel,
    dataclass_to_pydantic_media_item,
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


class FindSimilarPhotosTool:
    def __init__(
        self,
        image_embedder: ImageEmbeddings,
        vector_store: BaseVectorStore,
        media_items_repo: MediaItemsRepository,
    ):
        self.image_embedder = image_embedder
        self.vector_store = vector_store
        self.media_items_repo = media_items_repo

    def get_prompt(self) -> str:
        return DEFAULT_PROMPT

    def find_similar_photos(
        self, request: FindSimilarPhotosInput
    ) -> FindSimilarPhotosOutput:
        print('find_similar_photos:', request.media_item_id)

        media_item = self.media_items_repo.get_media_item_by_id(
            parse_string_to_media_item_id(request.media_item_id)
        )
        if not media_item.embedding_id:
            return FindSimilarPhotosOutput(media_items=[])

        embedding = self.vector_store.get_embedding_by_id(media_item.embedding_id)
        embeddings = self.vector_store.get_relevent_media_item_embeddings(
            embedding, k=request.top_k
        )

        return FindSimilarPhotosOutput(
            media_items=[
                dataclass_to_pydantic_media_item(
                    self.media_items_repo.get_media_item_by_id(embedding.media_item_id)
                )
                for embedding in embeddings
            ]
        )
