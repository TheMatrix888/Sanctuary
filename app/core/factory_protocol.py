from typing import Protocol, Type

from .state_context import StateContext
from .state import State


class FactoryProtocol(Protocol):
    context_type: Type[StateContext]

    def __call__(self, context: StateContext) -> State:
        ...
