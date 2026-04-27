import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from emhana.models import Appointment, Doctor, Patient


class Command(BaseCommand):
    help = 'Генерирует случайных пациентов, врачей и приёмы (Faker).'

    def add_arguments(self, parser):
        parser.add_argument('--patients', type=int, default=300, help='Сколько пациентов создать')
        parser.add_argument('--doctors', type=int, default=10, help='Сколько врачей создать')
        parser.add_argument('--appointments', type=int, default=1000, help='Сколько приёмов создать')
        parser.add_argument('--days', type=int, default=30, help='Разброс дат в прошлое (дней)')

    @transaction.atomic
    def handle(self, *args, **opts):
        fake = Faker('ru_RU')
        Faker.seed(42)
        random.seed(42)

        n_patients = opts['patients']
        n_doctors = opts['doctors']
        n_appts = opts['appointments']
        days_back = opts['days']

        # 1. Пациенты — bulk_create
        self.stdout.write(f'Создаю {n_patients} пациентов...')
        existing_iins = set(Patient.objects.values_list('iin', flat=True))
        patients_to_create = []
        while len(patients_to_create) < n_patients:
            iin = ''.join(random.choices('0123456789', k=12))
            if iin in existing_iins:
                continue
            existing_iins.add(iin)
            patients_to_create.append(Patient(
                iin=iin,
                full_name=fake.name(),
                phone=fake.phone_number()[:20],
            ))
        Patient.objects.bulk_create(patients_to_create, batch_size=500)

        # 2. Врачи (User + Doctor)
        self.stdout.write(f'Создаю {n_doctors} врачей...')
        specialties = ['Терапевт', 'Кардиолог', 'Педиатр', 'Невролог', 'Хирург',
                       'Офтальмолог', 'ЛОР', 'Дерматолог', 'Эндокринолог', 'Уролог']
        existing_usernames = set(User.objects.values_list('username', flat=True))
        for i in range(n_doctors):
            username = f'fake_doc_{i:03d}'
            if username in existing_usernames:
                continue
            user = User.objects.create_user(
                username=username,
                password='fakepass123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            Doctor.objects.create(
                user=user,
                specialty=random.choice(specialties),
            )

        # 3. Приёмы — bulk_create самое быстрое
        self.stdout.write(f'Создаю {n_appts} приёмов...')
        all_patients = list(Patient.objects.values_list('id', flat=True))
        all_doctors = list(Doctor.objects.values_list('id', flat=True))
        if not all_patients or not all_doctors:
            self.stdout.write(self.style.ERROR('Нет пациентов или врачей — приёмы создать нельзя.'))
            return

        statuses = ['pending', 'completed', 'cancelled']
        weights = [3, 5, 2]  # больше completed, меньше cancelled
        now = timezone.now()

        appts = []
        for _ in range(n_appts):
            offset_minutes = random.randint(0, days_back * 24 * 60)
            appts.append(Appointment(
                patient_id=random.choice(all_patients),
                doctor_id=random.choice(all_doctors),
                date_time=now - timedelta(minutes=offset_minutes),
                status=random.choices(statuses, weights=weights, k=1)[0],
                notes=fake.sentence(nb_words=10),
            ))
        Appointment.objects.bulk_create(appts, batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Итого в БД: '
            f'пациентов={Patient.objects.count()}, '
            f'врачей={Doctor.objects.count()}, '
            f'приёмов={Appointment.objects.count()}'
        ))
