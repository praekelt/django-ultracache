from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models import Model
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType

import ultracache.monkey


@receiver(post_save)
def on_post_save(sender, **kwargs):
    """Expire ultracache cache keys affected by this object"""
    if issubclass(sender, Model):
        obj = kwargs['instance']
        if isinstance(obj, Model):
            # get_for_model itself is cached
            ct = ContentType.objects.get_for_model(sender)
            key = 'ultracache-%s-%s' % (ct.id, obj.pk)
            to_delete = cache.get(key, [])
            if to_delete:
                try:
                    cache.delete_many(to_delete)
                except NotImplementedError:
                    for k in to_delete:
                        cache.delete(k)
