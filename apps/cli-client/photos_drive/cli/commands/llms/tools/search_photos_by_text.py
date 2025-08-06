from typing import List, Optional
from photos_drive.cli.commands.llms.tools.media_item import (
    MediaItemModel,
    dataclass_to_pydantic_media_item,
)
from pydantic import BaseModel, Field

from photos_drive.shared.llm.models.image_embeddings import ImageEmbeddings
from photos_drive.shared.llm.vector_stores.base_vector_store import BaseVectorStore
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
    top_k: Optional[int] = Field(5, description="Number of photos to retrieve")


class SearchPhotosByTextToolOutput(BaseModel):
    media_items: List[MediaItemModel] = Field(..., description="List of similar photos")


class SearchPhotosByTextTool:
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

    def search_photos_by_text(
        self, request: SearchPhotosByTextToolInput
    ) -> SearchPhotosByTextToolOutput:
        print('search_photos_by_text:', request.query)

        embedding = self.image_embedder.embed_texts([request.query])[0]
        embeddings = self.vector_store.get_relevent_media_item_embeddings(
            embedding, k=request.top_k
        )

        return SearchPhotosByTextToolOutput(
            media_items=[
                dataclass_to_pydantic_media_item(
                    self.media_items_repo.get_media_item_by_id(embedding.media_item_id)
                )
                for embedding in embeddings
            ]
        )
