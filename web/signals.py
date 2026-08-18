
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver


def update_archives_for_year(year):
    from .models import WiehrArchiveModel
    
    if not year:
        return
    
    try:
        archives = WiehrArchiveModel.objects.filter(year=year)
        for archive in archives:
            archive.refresh_counts()
            archive.save()
    except Exception:
        pass


def get_year_from_instance(instance):
    if hasattr(instance, 'year'):
        return instance.year
    if hasattr(instance, 'start_year'):
        return instance.start_year
    if hasattr(instance, 'date') and instance.date:
        return instance.date.year
    return None


@receiver(post_save)
def auto_update_archive_on_save(sender, instance, **kwargs):
    from .models import (
        WiehrGlobeModel, WiehrAtlasModel, WiehrLabModel,
        WiehrStorageModel
    )
    
    tracked_models = (
        WiehrGlobeModel, WiehrAtlasModel, WiehrLabModel,
        WiehrStorageModel
    )
    
    if isinstance(instance, tracked_models):
        year = get_year_from_instance(instance)
        if year:
            update_archives_for_year(year)


@receiver(m2m_changed)
def auto_update_archive_on_extra_archives_change(sender, instance, action, pk_set, **kwargs):
    """Refresh counts when a Lab item is pinned to / unpinned from an archive."""
    from .models import WiehrArchiveModel, WiehrLabModel

    if sender is not WiehrLabModel.extra_archives.through:
        return
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return

    if isinstance(instance, WiehrArchiveModel):
        archives = [instance]
    else:
        archives = list(WiehrArchiveModel.objects.filter(pk__in=pk_set or []))

    for archive in archives:
        try:
            archive.refresh_counts()
        except Exception:
            pass


@receiver(post_delete)
def auto_update_archive_on_delete(sender, instance, **kwargs):
    from .models import (
        WiehrGlobeModel, WiehrAtlasModel, WiehrLabModel,
        WiehrStorageModel
    )
    
    tracked_models = (
        WiehrGlobeModel, WiehrAtlasModel, WiehrLabModel,
        WiehrStorageModel
    )
    
    if isinstance(instance, tracked_models):
        year = get_year_from_instance(instance)
        if year:
            update_archives_for_year(year)
