from .ProjectMessageProcessor import ProjectMessageProcessor
from .CommissionMessageProcessor import CommissionMessageProcessor
from .VidispineMessageProcessor import VidispineMessageProcessor

##This structure is imported by name in the run_rabbitmq_responder
EXCHANGE_MAPPINGS = [
    {
        "exchange": 'pluto-core',
        "handler":  ProjectMessageProcessor(),
    },
    {
        "exchange": "pluto-core",
        "handler": CommissionMessageProcessor(),
    },
    {
        "exchange": "vidispine-events",
        "handler": VidispineMessageProcessor(),
    }
]
