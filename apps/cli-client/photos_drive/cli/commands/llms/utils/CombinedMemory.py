import logging

from langchain_core.memory import BaseMemory

logger = logging.getLogger(__name__)


class CombinedMemory(BaseMemory):
    def __init__(self, summary_memory, kg_memory, memory_key="chat_history"):
        self._summary_memory = summary_memory
        self._kg_memory = kg_memory
        self._memory_key = memory_key

    @property
    def memory_variables(self):
        return [self._memory_key]

    def load_memory_variables(self, inputs):
        summary_key = self._summary_memory.memory_key
        kg_key = self._kg_memory.memory_key

        summary = self._summary_memory.load_memory_variables(inputs).get(
            summary_key, ""
        )
        kg = self._kg_memory.load_memory_variables(inputs).get(kg_key, "")

        print('summary:', summary)
        print('kg:', kg)

        return {self._memory_key: summary + kg}

    def save_context(self, inputs, outputs):
        self._summary_memory.save_context(inputs, outputs)
        self._kg_memory.save_context(inputs, outputs)

    def clear(self):
        self._summary_memory.clear()
        self._kg_memory.clear()
