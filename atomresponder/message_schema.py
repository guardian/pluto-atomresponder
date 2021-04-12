import jsonschema

# This file contains useful constants and interface definitions from
# https://github.com/guardian/media-atom-maker/blob/main/common/src/main/scala/com/gu/media/model/PlutoIntegrationData.scala

MESSAGE_TYPE_ASSIGNED_PROJECT = "project-assigned"
MESSAGE_TYPE_PAC_FILE = "pac-file-upload"
MESSAGE_TYPE_VIDEO_UPLOAD = "video-upload"
MESSAGE_TYPE_RESYNC = "video-upload-resync"

AtomAssignedProjectMessageSchema = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "atomId": {"type": "string"},
        "commissionId": {"type": "string"},
        "projectId": {"type": "string"},
        "title": {"type": "string"},
        "user": {"type": ["string", "null"]}
    },
    "required": [
        "type","atomId","projectId"
    ]
}

PacFileMessageSchema = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "atomId": {"type": "string"},
        "s3Bucket": {"type": "string"},
        "s3Path": {"type": "string"},
    },
    "required": ["type", "atomId", "s3Bucket", "s3Path"]
}

VideoUploadMessageSchema = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "projectId": {"type": ["string","null"]},
        "s3Key": {"type": "string"},
        "atomId": {"type": "string"},
        "title": {"type": "string"},
        "user": {"type": "string"},
        "posterImageUrl": {"type": ["string", "null"]}
    },
    "required": ["type", "s3Key", "atomId"]
}

VideoUploadResyncMessageSchema = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "projectId": {"type": ["string","null"]},
        "s3Key": {"type": "string"},
        "atomId": {"type": "string"},
        "title": {"type": "string"},
        "posterImageUrl": {"type": ["string", "null"]}
    },
    "required": ["type", "s3Key", "atomId"]
}


def validate_message(raw_message: dict) -> dict:
    """
    validates parsed data as a Media Atom message.
    :param raw_message: the parsed data to check, as a dictionary
    :return: a dictionary of validated data. If the data does not validate, then either a jsonschema.ValidationError or
    a ValueError is raised with a descriptive string.
    """
    if "type" not in raw_message:
        raise ValueError("Message was missing the \"type\" field")

    schema = None

    if raw_message["type"]==MESSAGE_TYPE_ASSIGNED_PROJECT:
        schema = AtomAssignedProjectMessageSchema
    elif raw_message["type"]==MESSAGE_TYPE_PAC_FILE:
        schema = PacFileMessageSchema
    elif raw_message["type"]==MESSAGE_TYPE_VIDEO_UPLOAD:
        schema = VideoUploadMessageSchema
    elif raw_message["type"]==MESSAGE_TYPE_RESYNC:
        schema = VideoUploadResyncMessageSchema
    else:
        raise ValueError("Message had an invalid \"type\" field: \"{}\".".format(raw_message["type"]))

    jsonschema.validate(raw_message, schema)    #raises ValidationError if it fails
    return raw_message
