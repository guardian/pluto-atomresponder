from .ProjectMessageProcessor import ProjectMessageProcessor
from .CommissionMessageProcessor import CommissionMessageProcessor

##This structure is imported by name in the run_rabbitmq_responder
EXCHANGE_MAPPINGS = [
    {
        "exchange": 'pluto-core',
        "handler":  ProjectMessageProcessor(),
    },
    {
        "exchange": "pluto-core",
        "handler": CommissionMessageProcessor(),
    }
]
