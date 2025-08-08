from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.runnables.config import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langmem.short_term import RunningSummary, SummarizationNode
from pydantic import BaseModel, Field

from photos_drive.cli.commands.llms.tools.find_photos import FindPhotosTool
from photos_drive.cli.commands.llms.tools.find_similar_photos import (
    FindSimilarPhotosTool,
)
from photos_drive.cli.commands.llms.tools.search_photos_by_text import (
    SearchPhotosByTextTool,
)
from photos_drive.shared.config.config import Config
from photos_drive.shared.llm.models.open_clip_image_embeddings import (
    OpenCLIPImageEmbeddings,
)
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


class ResponseFormatter(BaseModel):
    """Always use this tool to structure your response to the user."""

    output: str = Field(description="The answer to the user's question")
    file_paths: list[str] = Field(
        description="A list of file paths for each media item to show to the user"
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

    search_by_text_tool = SearchPhotosByTextTool(
        image_embedder, vector_store, media_items_repo
    )
    find_similar_photos_tool = FindSimilarPhotosTool(
        image_embedder, vector_store, media_items_repo
    )
    find_photos_tool = FindPhotosTool(media_items_repo)

    tools = [search_by_text_tool, find_similar_photos_tool, find_photos_tool]

    class State(AgentState):
        # NOTE: we're adding this key to keep track of previous summary information
        # to make sure we're not summarizing on every LLM call
        context: dict[str, RunningSummary]
        structured_response: ResponseFormatter

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
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
        debug=True,
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
        if not user_input:
            continue
        raw_response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}, llm_config
        )

        print('===== Raw response ====')
        print(raw_response)
        print('===== End of raw response ====')
        print(raw_response['structured_response'].output)

        for file_path in raw_response['structured_response'].file_paths:
            print(' - ', file_path)
