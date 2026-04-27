from django.contrib import admin

from .models import Appointment, Doctor, Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('iin', 'full_name', 'phone', 'created_at')
    search_fields = ('iin', 'full_name', 'phone')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty')
    search_fields = ('user__username', 'user__last_name', 'specialty')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date_time', 'status')
    list_filter = ('status', 'doctor')
    search_fields = ('patient__iin', 'patient__full_name')
    date_hierarchy = 'date_time'
