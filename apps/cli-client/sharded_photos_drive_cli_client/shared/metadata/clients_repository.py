from bson.objectid import ObjectId
from abc import ABC, abstractmethod


class ClientsRepository(ABC):
    @abstractmethod
    def find_id_of_client_with_most_space(self) -> ObjectId:
        """
        Returns the client ID with the most amount of space.

        Returns:
            ObjectId: the client ID with the most amount of space.
        """
        pass

    @abstractmethod
    def start_transactions(self):
        '''
        Starts a transaction.

        Database transactions are only saved if commit_and_end_transactions() is called.

        A call to abort_and_end_transactions() will abort and roll back all
        transactions.
        '''
        pass

    @abstractmethod
    def abort_and_end_transactions(self):
        '''
        Aborts the transactions and ends the session.
        Note: it must call start_transactions() first before calling this method.
        '''
        pass

    @abstractmethod
    def commit_and_end_transactions(self):
        '''
        Commits the transactions and ends the session.
        Note: it must call start_transactions() first before calling this method.
        '''
        pass
