from django.db.models.signals import post_delete
from django.dispatch import receiver


# @receiver(post_delete)
# def on_post_delete(sender, instance, using, **kwargs):
#     """Process deletion of a relation."""
#     if type(instance) is models.Relation:
#         if instance.cascade_deletion:
#             instance.target_entity.delete()
