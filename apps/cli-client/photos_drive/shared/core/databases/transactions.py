from abc import ABC, abstractmethod
import logging
from types import TracebackType

logger = logging.getLogger(__name__)


class TransactionsRepository(ABC):
    @abstractmethod
    def start_transactions(self):
        '''
        Starts a transaction.

        Database transactions are only saved if commit_and_end_transactions() is called.

        A call to abort_and_end_transactions() will abort and roll back all
        transactions.
        '''

    @abstractmethod
    def abort_and_end_transactions(self):
        '''
        Aborts the transactions and ends the session.
        Note: it must call start_transactions() first before calling this method.
        '''

    @abstractmethod
    def commit_and_end_transactions(self):
        '''
        Commits the transactions and ends the session.
        Note: it must call start_transactions() first before calling this method.
        '''


class TransactionsContext:
    def __init__(self, repo: TransactionsRepository):
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
