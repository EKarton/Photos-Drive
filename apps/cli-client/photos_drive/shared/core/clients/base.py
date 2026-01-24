from abc import ABC, abstractmethod


class TransactionRepository(ABC):
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
