from django.core.management.base import BaseCommand
from django.db import transaction

from gallery.models import PortfolioImage


PHASE_SEQUENCE = ['pre_wedding', 'wedding_day', 'post_wedding']


def resolve_phase_for_position(index, total):
    if total <= len(PHASE_SEQUENCE):
        return PHASE_SEQUENCE[min(index, len(PHASE_SEQUENCE) - 1)]

    first_cut = total // 3
    second_cut = (total * 2) // 3

    if index < first_cut:
        return PHASE_SEQUENCE[0]
    if index < second_cut:
        return PHASE_SEQUENCE[1]
    return PHASE_SEQUENCE[2]


class Command(BaseCommand):
    help = 'Backfill missing shoot_phase values for existing wedding gallery images.'

    def handle(self, *args, **options):
        queryset = (
            PortfolioImage.objects
            .select_related('parent')
            .filter(parent__isnull=False, category__slug='wedding', shoot_phase='')
            .order_by('parent_id', 'order', 'created_at', 'id')
        )

        if not queryset.exists():
            self.stdout.write(self.style.SUCCESS('No blank wedding gallery phases found.'))
            return

        updated_count = 0
        parent_count = 0

        with transaction.atomic():
            parent_ids = list(queryset.values_list('parent_id', flat=True).distinct())
            for parent_id in parent_ids:
                images = list(
                    queryset.filter(parent_id=parent_id).order_by('order', 'created_at', 'id')
                )
                if not images:
                    continue

                parent_count += 1
                total = len(images)
                for index, image in enumerate(images):
                    phase = resolve_phase_for_position(index, total)
                    if image.shoot_phase == phase:
                        continue
                    image.shoot_phase = phase
                    image.save(update_fields=['shoot_phase'])
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {updated_count} wedding gallery images across {parent_count} parent stories.'
            )
        )
