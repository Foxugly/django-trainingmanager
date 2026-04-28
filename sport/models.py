from django.db import models


class Sport(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    energy_systems = models.ManyToManyField(
        "exercise.EnergySystem",
        related_name="sports",
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
