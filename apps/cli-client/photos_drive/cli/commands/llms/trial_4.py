from photos_drive.shared.config.config import Config
from photos_drive.shared.llm.vector_stores.distributed_vector_store import (
    DistributedVectorStore,
)
from photos_drive.shared.llm.vector_stores.vector_store_builder import (
    config_to_vector_store,
)
from photos_drive.shared.metadata.mongodb.clients_repository_impl import (
    MongoDbClientsRepository,
)
from photos_drive.shared.metadata.mongodb.media_items_repository_impl import (
    MediaItemsRepositoryImpl,
)
import json
from langchain.agents import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages.utils import count_tokens_approximately
from langmem.short_term import SummarizationNode, RunningSummary
from langchain_core.runnables.config import RunnableConfig

from photos_drive.shared.llm.models.open_clip_image_embeddings import (
    OpenCLIPImageEmbeddings,
)


class ResponseFormatter(BaseModel):
    """Always use this tool to structure your response to the user."""

    output: str = Field(description="The answer to the user's question")
    image_paths: list[str] = Field(
        description="A list of file paths of images to display to the user"
    )


def trial_4(config: Config):
    print("Performing trial 4")
    image_embedder = OpenCLIPImageEmbeddings()

    # Set up the repos
    mongodb_clients_repo = MongoDbClientsRepository.build_from_config(config)
    media_items_repo = MediaItemsRepositoryImpl(mongodb_clients_repo)
    vector_store = DistributedVectorStore(
        stores=[
            config_to_vector_store(
                config, embedding_dimensions=image_embedder.get_embedding_dimension()
            )
            for config in config.get_vector_store_configs()
        ]
    )

    def search_photos_by_text_with_reranking(query: str, top_k=5):
        print('search_photos_by_text_with_reranking:', query)
        embedding = image_embedder.embed_texts([query])[0]
        embeddings = vector_store.get_relevent_media_item_embeddings(embedding, k=top_k)
        media_items = [
            str(media_items_repo.get_media_item_by_id(embedding.media_item_id))
            for embedding in embeddings
        ]
        print('results_data:', media_items)

        return json.dumps(media_items)

    def find_path_by_caption_snippet(caption: str) -> str:
        print('find_path_by_caption_snippet:', caption)
        embedding = image_embedder.embed_texts([caption])[0]
        embeddings = vector_store.get_relevent_media_item_embeddings(embedding, k=1)
        media_item = media_items_repo.get_media_item_by_id(embeddings[0].media_item_id)
        print('results_data:', media_item)

        return json.dumps(str(media_item))

    tools = [
        Tool(
            name="SearchPhotosByText",
            func=search_photos_by_text_with_reranking,
            description="Search for photos matching a natural language text query. Input: a text string describing what to find (e.g., 'sunset in Santorini'). Returns a list of matching images with captions and file paths.",
        ),
        Tool(
            name="FindImageFilePathFromCaption",
            func=find_path_by_caption_snippet,
            description="Given a short description or snippet from a photo caption, returns the exact file path of the matching image. Useful for resolving vague references like 'pine tree photo' to a file path.",
        ),
    ]

    class State(AgentState):
        # NOTE: we're adding this key to keep track of previous summary information
        # to make sure we're not summarizing on every LLM call
        context: dict[str, RunningSummary]
        structured_response: ResponseFormatter

    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
    )
    print("Loaded llm")

    summarization_node = SummarizationNode(
        token_counter=count_tokens_approximately,
        model=model,
        max_tokens=384,
        max_summary_tokens=128,
        output_messages_key="content",
    )

    checkpointer = InMemorySaver()
    llm_config: RunnableConfig = {"configurable": {"thread_id": "1"}}
    agent = create_react_agent(
        model=model,
        tools=tools,
        response_format=ResponseFormatter,
        # debug=True,
        pre_model_hook=summarization_node,
        state_schema=State,
        checkpointer=checkpointer,
    )
    with open("graph.png", "wb") as f:
        f.write(agent.get_graph().draw_mermaid_png())

    print("📸 Welcome to your Agentic Photo Assistant!")
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            break
        raw_response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}, llm_config
        )

        print('===== Raw response ====')
        print(raw_response)
        print('===== End of raw response ====')
        print(raw_response['structured_response'].output)

        for image_path in raw_response['structured_response'].image_paths:
            print(' - ', image_path)
