from enum import Enum


class MessageMode(str, Enum):
    """Traffic class for AMQP messages on the graph exchange."""

    BATCH = "batch"
    INTERACTIVE = "interactive"
