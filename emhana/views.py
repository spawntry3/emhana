import json
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Appointment, Doctor, Patient


def login_view(request):
    if request.user.is_authenticated:
        return redirect('emhana:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('emhana:dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('emhana:login')


_RU_MONTHS_SHORT = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                    'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']


def _aggregate_dynamics(period: str):
    now = timezone.now()

    if period == '30d':
        start = now - timedelta(days=30)
        trunc = TruncDate('date_time')
        fmt = lambda d: d.strftime('%d.%m')
        title = 'Динамика приёмов (30 дней)'
    elif period == '6m':
        start = now - timedelta(days=183)
        trunc = TruncWeek('date_time')
        fmt = lambda d: d.strftime('%d.%m')
        title = 'Динамика приёмов по неделям (полгода)'
    elif period == '1y':
        start = now - timedelta(days=365)
        trunc = TruncMonth('date_time')
        fmt = lambda d: f'{_RU_MONTHS_SHORT[d.month - 1]} {d.year}'
        title = 'Динамика приёмов по месяцам (год)'
    else:
        period = '7d'
        start = now - timedelta(days=7)
        trunc = TruncDate('date_time')
        fmt = lambda d: d.strftime('%d.%m.%Y')
        title = 'Динамика приёмов (последние 7 дней)'

    qs = (
        Appointment.objects
        .filter(date_time__gte=start)
        .annotate(bucket=trunc)
        .values('bucket')
        .annotate(count=Count('id'))
        .order_by('bucket')
    )

    labels = [fmt(row['bucket']) for row in qs]
    counts = [row['count'] for row in qs]
    return labels, counts, title


@login_required
def dashboard_chart_data(request):
    period = request.GET.get('period', '7d')
    labels, counts, title = _aggregate_dynamics(period)
    return JsonResponse({
        'period': period,
        'labels': labels,
        'counts': counts,
        'title': title,
    })


@login_required
def dashboard_view(request):
    period = request.GET.get('period', '7d')
    dates, counts, dynamics_title = _aggregate_dynamics(period)

    status_qs = (
        Appointment.objects
        .values('status')
        .annotate(count=Count('id'))
    )
    status_map = {row['status']: row['count'] for row in status_qs}
    status_labels = [label for _, label in Appointment.STATUS_CHOICES]
    status_data = [status_map.get(value, 0) for value, _ in Appointment.STATUS_CHOICES]

    total_patients = Patient.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()

    context = {
        'dates_json': json.dumps(dates),
        'counts_json': json.dumps(counts),
        'dynamics_title': dynamics_title,
        'period': period,
        'status_labels_json': json.dumps(status_labels),
        'status_data_json': json.dumps(status_data),
        'total_patients': total_patients,
        'pending_appointments': pending_appointments,
    }
    return render(request, 'dashboard.html', context)


@login_required
def appointment_list_view(request):
    appointments = Appointment.objects.select_related('patient', 'doctor__user').all()

    status_filter = request.GET.get('status', '').strip()
    doctor_filter = request.GET.get('doctor_id', '').strip()
    search_query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)

    if status_filter:
        appointments = appointments.filter(status=status_filter)
    if doctor_filter:
        appointments = appointments.filter(doctor_id=doctor_filter)
    if search_query:
        appointments = appointments.filter(
            Q(patient__iin__startswith=search_query) |
            Q(patient__full_name__icontains=search_query)
        )

    paginator = Paginator(appointments, 25)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        rows_html = render_to_string(
            'partials/appointment_rows.html',
            {'appointments': page_obj.object_list},
            request=request,
        )
        pagination_html = render_to_string(
            'partials/appointment_pagination.html',
            {'page_obj': page_obj},
            request=request,
        )
        return JsonResponse({
            'rows_html': rows_html,
            'pagination_html': pagination_html,
            'total': paginator.count,
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
        })

    context = {
        'page_obj': page_obj,
        'appointments': page_obj.object_list,
        'doctors': Doctor.objects.select_related('user').all(),
        'status_choices': Appointment.STATUS_CHOICES,
        'selected_status': status_filter,
        'selected_doctor': doctor_filter,
        'search_query': search_query,
        'total_count': paginator.count,
    }
    return render(request, 'appointment_list.html', context)


@login_required
def appointment_create_view(request):
    if request.method == 'POST':
        iin = request.POST.get('iin', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        doctor_id = request.POST.get('doctor_id')
        date_time = request.POST.get('date_time')
        notes = request.POST.get('notes', '').strip()

        patient, _created = Patient.objects.get_or_create(
            iin=iin,
            defaults={'full_name': full_name, 'phone': phone},
        )

        Appointment.objects.create(
            patient=patient,
            doctor_id=doctor_id,
            date_time=date_time,
            notes=notes,
        )
        return redirect('emhana:appointment_list')

    context = {
        'doctors': Doctor.objects.select_related('user').all(),
    }
    return render(request, 'appointment_create.html', context)
