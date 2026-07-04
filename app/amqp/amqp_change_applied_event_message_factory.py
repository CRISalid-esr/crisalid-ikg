from app.amqp.amqp_change_event_message_factory import AMQPChangeEventMessageFactory


class AMQPChangeAppliedEventMessageFactory(AMQPChangeEventMessageFactory):
    """Factory for AMQP messages reporting a successfully applied change."""

    def _build_routing_key(self) -> str:
        return self.settings.amqp_graph_change_event_applied_routing_key

    def _event_name(self) -> str:
        return "applied"
