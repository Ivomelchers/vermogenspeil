from django.db import models


class TaxYearParameter(models.Model):
    """Fiscale parameters per belastingjaar (niet hardcoden in berekening)."""

    year = models.PositiveIntegerField(unique=True)
    heffingsvrij_vermogen = models.DecimalField(max_digits=14, decimal_places=2)
    rendement_banktegoeden = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        help_text="PB, bijv. 0.0128",
    )
    rendement_overige_bezittingen = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        help_text="PO, bijv. 0.06",
    )
    rendement_schulden = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        help_text="PS, bijv. 0.027",
    )
    schuldendrempel = models.DecimalField(max_digits=14, decimal_places=2, help_text="SD")
    tarief_box3 = models.DecimalField(max_digits=8, decimal_places=6, help_text="T, bijv. 0.36")
    banktegoeden_definitief = models.BooleanField(default=False)
    schulden_definitief = models.BooleanField(default=False)
    published_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "belastingjaar-parameter"
        verbose_name_plural = "belastingjaar-parameters"
        ordering = ["-year"]

    def __str__(self):
        return f"Box 3 parameters {self.year}"
