from .PlutoCoreMessageProcessor import PlutoCoreMessageProcessor

##This structure is imported by name in the run_rabbitmq_responder
EXCHANGE_MAPPINGS = {
    'pluto-core': PlutoCoreMessageProcessor(),
}
