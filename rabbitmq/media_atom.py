import logging
from .models import ProjectModel, CachedCommission

logger = logging.getLogger(__name__)

MSG_PROJECT_CREATED = 'project-created'
MSG_PROJECT_UPDATED = 'project-updated'


def update_kinesis(project_instance: ProjectModel, commission_instance: CachedCommission, message_type):
    """
    notifies media atom of a project update or create by pushing a message onto its kinesis stream.
    the kinesis stream is indicated in settings.
    :param project_instance: model instance describing the project that has been created/updated
    :param commission_instance: model instance describing the commission that it belongs to
    :param message_type: either `media_atom.MSG_PROJECT_CREATED` or `media_atom.MSG_PROJECT_UPDATED`
    :return:
    """
    from boto import sts, kinesis
    from django.conf import settings
    import json

    SESSION_NAME = 'pluto-media-atom-integration'

    project_id = str(project_instance.id)
    logger.info("{0}: Project updated, notifying {1} via role {2}".format(project_id,
                                                                          settings.MEDIA_ATOM_STREAM_NAME,
                                                                          settings.MEDIA_ATOM_ROLE_ARN
                                                                          )
                )

    sts_connection = sts.STSConnection(
        aws_access_key_id=settings.MEDIA_ATOM_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.MEDIA_ATOM_AWS_SECRET_ACCESS_KEY)

    assume_role_result = sts_connection.assume_role(
        role_arn=settings.MEDIA_ATOM_ROLE_ARN,
        role_session_name=SESSION_NAME)

    credentials = assume_role_result.credentials

    logger.debug("{0}: Got kinesis credentials".format(project_id))
    kinesis_connection = kinesis.connect_to_region(
        region_name='eu-west-1',
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        security_token=credentials.session_token)

    message_content = {
        'type': message_type,
        'id': project_id,
        'title': project_instance.title,
        'status': project_instance.status,
        'commissionId': project_instance.commissionId,
        'commissionTitle': commission_instance.title,
        'productionOffice': project_instance.productionOffice,
        'created': project_instance.created.isoformat()
    }
    logger.debug("{0}: Message is {1}".format(project_id, message_content))

    kinesis_connection.put_record(
        stream_name=settings.MEDIA_ATOM_STREAM_NAME,
        data=json.dumps(message_content),
        partition_key=project_id)
    logger.info("{0}: Project update sent".format(project_id))