from django.db import models
from django.contrib.auth.models import User


class Patient(models.Model):
    iin = models.CharField(max_length=12, unique=True, verbose_name="ИИН")
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"

    def __str__(self):
        return f"{self.full_name} ({self.iin})"


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    specialty = models.CharField(max_length=100, verbose_name="Специальность")

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialty}"


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Пациент")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="Врач")
    date_time = models.DateTimeField(verbose_name="Дата и время приема")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус"
    )
    notes = models.TextField(blank=True, verbose_name="Жалобы/Заметки")

    class Meta:
        verbose_name = "Прием"
        verbose_name_plural = "Приемы"
        ordering = ['-date_time']

    def __str__(self):
        return f"Прием: {self.patient.full_name} к {self.doctor.specialty} ({self.date_time})"
