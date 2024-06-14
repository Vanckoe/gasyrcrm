from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, redirect
from datetime import datetime, timedelta

from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from rest_framework.permissions import IsAuthenticated

from .models import Appointment

def week_view(request):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Ensure Monday is day 0
    dates_of_week = [start_of_week + timedelta(days=i) for i in range(6)]  # Get Monday to Saturday

    context = {
        'dates_of_week': dates_of_week,
    }
    return render(request, 'appointments/week_view.html', context)



def appointments_for_day_api(request, year, month, day):
    date = datetime(year, month, day).date()
    appointments = Appointment.objects.filter(date=date)
    appointment_list = [model_to_dict(appointment) for appointment in appointments]  # Convert queryset to list of dicts
    return JsonResponse({'appointments': appointment_list, 'date': date.strftime("%Y-%m-%d")})

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Appointment
from .serializers import AppointmentSerializer, AppointmentLinkSerializer


class AppointmentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        appointments = Appointment.objects.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()  # Automatically use the logged-in user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentSetLinkAPIView(APIView):
    def patch(self, request, pk):
        appointment = Appointment.objects.get(pk=pk)
        serializer = AppointmentLinkSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentBookAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
            if appointment.is_booked:
                return Response({"error": "This appointment is already booked."}, status=status.HTTP_400_BAD_REQUEST)

            appointment.is_booked = True
            appointment.user = request.user
            appointment.save()
            return redirect('subjects:success-appointment')  # Redirect to success page
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment does not exist."}, status=status.HTTP_404_NOT_FOUND)


@login_required
def success_appointment_view(request):
    # Fetch the latest booked appointment for the current user
    latest_appointment = Appointment.objects.filter(user=request.user, is_booked=True).order_by('-date', '-start_time').first()
    if not latest_appointment:
        # Handle the case where there is no appointment found
        return redirect('subjects:psy-appointment')  # Redirect back to the appointment booking page

    # Format the date to include day and month name
    day_month_format = DateFormat(latest_appointment.date).format('j F')
    time_format = DateFormat(latest_appointment.start_time).format(get_format('TIME_FORMAT'))

    context = {
        'user_full_name': request.user.full_name,
        'user_profile_pic_url': request.user.profile_picture.url if request.user.profile_picture else None,
        'appointment_date': day_month_format,
        'appointment_time': time_format,
        'appointment': latest_appointment
    }

    return render(request, 'subjects/appointment/success-appointment.html', context)