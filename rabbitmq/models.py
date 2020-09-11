from django.db import models


class CachedCommission(models.Model):
    """
    Represents the data that we need to know about a commission.
    This is saved into the database
    """
    commission_id = models.IntegerField(primary_key=True,null=False)
    title = models.TextField(max_length=32768)

# ## see https://pynative.com/python-json-validation/
# PROJECT_SCHEMA = {
#     "type": "object",
#     "properties": {
#         "id": {"type": "number"},
#         "projectTypeId": {"type": "number"},
#         "title": {"type": "string"},
#         "created": {"type": "string"},
#         "user": {"type": "string"},
#         "workingGroupId": {"type": "string"},
#         "commissionId": {"type": "string"},
#         "deletable": {"type": "boolean"},
#         "sensitive": {"type": "boolean"},
#         "status": {"type": "string"},
#         "productionOffice": {"type": "string"},
#     }
# }

class ProjectModel(models.Model):
    """
    Represents the data that we get sent about a project.
    This is NOT saved to the database but treated purely transiently
    """
    project_id = models.IntegerField(primary_key=True,null=False)
    project_type_id = models.IntegerField()
    title = models.TextField(max_length=32768)
