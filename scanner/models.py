from django.db import models

class QRCode(models.Model):
    data = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=10)
    qr_image = models.ImageField(upload_to='qr_codes/', null=True, blank=True)  # new field

    def __str__(self):
        return f"{self.data} - {self.mobile_number}"
    