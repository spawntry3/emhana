import json
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_datetime

from emhana.models import Appointment, Doctor, Patient


class Command(BaseCommand):
    help = 'Импортирует тестовые данные (пациенты, врачи, приемы) из JSON файла.'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Путь к JSON файлу')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f'Файл {json_file} не найден!'))
            return

        with open(json_file, 'r', encoding='utf-8') as fp:
            data = json.load(fp)

        # 1. Пациенты
        created_patients = 0
        for p in data.get('patients', []):
            _, created = Patient.objects.get_or_create(
                iin=p['iin'],
                defaults={'full_name': p['full_name'], 'phone': p['phone']},
            )
            if created:
                created_patients += 1
        self.stdout.write(self.style.SUCCESS(f'Пациентов добавлено: {created_patients}'))

        # 2. Врачи (User + Doctor)
        created_doctors = 0
        for d in data.get('doctors', []):
            user, user_created = User.objects.get_or_create(
                username=d['username'],
                defaults={
                    'first_name': d.get('first_name', ''),
                    'last_name': d.get('last_name', ''),
                },
            )
            if user_created:
                user.set_password(d['password'])
                user.save()
            Doctor.objects.get_or_create(
                user=user,
                defaults={'specialty': d['specialty']},
            )
            if user_created:
                created_doctors += 1
        self.stdout.write(self.style.SUCCESS(f'Врачей добавлено: {created_doctors}'))

        # 3. Приёмы
        created_appts = 0
        for a in data.get('appointments', []):
            try:
                patient = Patient.objects.get(iin=a['patient_iin'])
                doctor = Doctor.objects.get(user__username=a['doctor_username'])
            except (Patient.DoesNotExist, Doctor.DoesNotExist) as e:
                self.stdout.write(self.style.WARNING(
                    f"Пропуск приёма {a.get('patient_iin')} → {a.get('doctor_username')}: {e}"
                ))
                continue

            _, created = Appointment.objects.get_or_create(
                patient=patient,
                doctor=doctor,
                date_time=parse_datetime(a['date_time']),
                defaults={
                    'status': a.get('status', 'pending'),
                    'notes': a.get('notes', ''),
                },
            )
            if created:
                created_appts += 1
        self.stdout.write(self.style.SUCCESS(f'Приёмов добавлено: {created_appts}'))

        self.stdout.write(self.style.SUCCESS('Импорт успешно завершён.'))
