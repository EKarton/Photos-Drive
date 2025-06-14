import logging
from types import TracebackType

from photos_drive.shared.metadata.clients_repository import (
    ClientsRepository,
)

logger = logging.getLogger(__name__)


class TransactionsContext:
    def __init__(self, repo: ClientsRepository):
        self.__repo = repo

    def __enter__(self):
        self.__repo.start_transactions()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        if exc_type:
            logger.error(f"Aborting transaction due to error: {exc_value}")
            self.__repo.abort_and_end_transactions()
            logger.error("Transaction aborted")
        else:
            self.__repo.commit_and_end_transactions()
            logger.debug("Commited transactions")
