from django.db import models


class CachedCommission(models.Model):
    """
    Represents the data that we need to know about a commission.
    This is saved into the database
    """
    commission_id = models.IntegerField(primary_key=True,null=False)
    title = models.TextField(max_length=32768)


class ProjectModel(models.Model):
    """
    Represents the data that we get sent about a project.
    This is NOT saved to the database but treated purely transiently
    """
    project_id = models.IntegerField(primary_key=True,null=False)
    project_type_id = models.IntegerField()
    title = models.TextField(max_length=32768)
    created = models.DateTimeField()
    user = models.TextField(max_length=1024)
    workingGroupId = models.IntegerField()
    commissionId = models.IntegerField()
    deletable = models.BooleanField()
    sensitive = models.BooleanField()
    status = models.TextField(max_length=32)
    productionOffice = models.TextField(max_length=8)

    def __str__(self):
        return "{0} by {1} at {2}".format(self.title, self.user, self.project_id)