REPLY_REQUESTS = "convox.assitant.reply-requests.v1"
REPLY_RESULTS = "convox.ai.reply-results.v1"
INGEST_REQUESTS = "convox.knowledge.ingest-requests.v1"
INGEST_STATUS = "convox.ai.ingest-status.v1"

REPLY_GROUP = "convox-ai-reply"
INGEST_GROUP = "convox-ai-ingest"

HEADER_ORGANIZATION = "convox-organization-id"
HEADER_MESSAGE_TYPE = "convox-message-type"
HEADER_TRACEPARENT = "traceparent"

def dead_letter(topic: str) -> str:
    """Each consumed topic has a dead-letter topic with the same partitions."""
    return f"{topic}.dlt"
