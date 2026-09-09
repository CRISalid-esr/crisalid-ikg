from app.amqp.amqp_change_event_message_factory import AMQPChangeEventMessageFactory


class AMQPChangeFailedEventMessageFactory(AMQPChangeEventMessageFactory):
    """Factory for AMQP messages reporting a failed change."""

    def _build_routing_key(self) -> str:
        return self.settings.amqp_graph_change_event_failed_routing_key

    def _event_name(self) -> str:
        return "failed"
