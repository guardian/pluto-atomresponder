from django.db import models


class CachedCommission(models.Model):
    """
    Represents the data that we need to know about a commission.
    This is saved into the database
    """
    id = models.IntegerField(primary_key=True,null=False)
    title = models.TextField(max_length=32768)


class LinkedProject(models.Model):
    """
    This is used to relate the project ID that comes from the atomtool to a commission id, which is required by
    deliverables to create a new deliverable bundle.
    """
    project_id = models.IntegerField(primary_key=True, null=False)
    commission = models.ForeignKey(to=CachedCommission, on_delete=models.CASCADE)


class ProjectModel(models.Model):
    """
    Represents the data that we get sent about a project.
    This is NOT saved to the database but treated purely transiently
    """
    id = models.IntegerField(primary_key=True,null=False)
    projectTypeId = models.IntegerField()
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
        return "{0} by {1} at {2}".format(self.title, self.user, self.id)