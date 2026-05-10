"""Backfill Event.refer_program from the soon-to-be-dropped Program.events M2M.

Historically, Program had both an FK-reverse (Event.refer_program) and a
redundant M2M (Program.events). The FK was canonical but optional, while
the M2M could host extra links that drifted from the FK.

Before dropping the M2M (migration 0008), this data migration walks every
M2M row and, for each Event whose refer_program is still NULL, sets it to
the Program found in the M2M. Conflicts (Event already FK-linked to a
DIFFERENT Program than the M2M row) are logged and ignored — the FK wins,
per the documented data-model contract.

Idempotent and reverse-noop (we cannot reconstruct the M2M from the FK
alone since the M2M never had a uniqueness invariant tying it to the FK).
"""

from django.db import migrations


def backfill_refer_program(apps, schema_editor):
    Program = apps.get_model("program", "Program")
    # We use the M2M through model via Program.events.through to inspect rows
    # without depending on table naming conventions.
    through = Program.events.through
    Event = apps.get_model("event", "Event")

    updated = 0
    skipped_conflict = 0
    for link in through.objects.all().iterator():
        event = Event.objects.filter(pk=link.event_id).first()
        if event is None:
            continue
        if event.refer_program_id is None:
            event.refer_program_id = link.program_id
            event.save(update_fields=["refer_program_id"])
            updated += 1
        elif event.refer_program_id != link.program_id:
            # FK already points elsewhere; FK is canonical, M2M is being dropped.
            skipped_conflict += 1

    if updated or skipped_conflict:
        print(
            f"Backfilled {updated} Event.refer_program from Program.events M2M; "
            f"{skipped_conflict} conflicts ignored (FK wins)."
        )


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("program", "0006_alter_program_options"),
        ("event", "0004_event_created_at_event_updated_at"),
    ]
    operations = [
        migrations.RunPython(backfill_refer_program, reverse_noop),
    ]
