import datetime
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch, Q
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from chats.models import ChatRoom, Message
from schedule.models import ShiftTime, Shift
from users.models import CustomUser
from .forms import TaskForm, LessonForm, GroupTemplateForm, UserSearchForm, VolunteerChannelForm, GradeForm
from .models import Subject, GroupTemplate, Lesson_crm2, Task, VolunteerChannel, Grade
from .serializers import CustomUserSerializer, VolunteerChannelSerializer


@login_required
def home_view(request):
    user = request.user
    today = timezone.now().date()

    user_lessons = Lesson_crm2.objects.filter(
        group_template__students=user
    ).select_related('teacher', 'subject', 'chat_room')
    print("Debug - User Lessons with Chat Rooms:", [(lesson.group_name, lesson.chat_room) for lesson in user_lessons])

    last_task = Task.objects.filter(
        chat_room__in=[lesson.chat_room for lesson in user_lessons]
    ).select_related('created_by').order_by('-deadline').first()

    print("Debug - Last Task Details:", last_task)

    if last_task:
        task_teacher = last_task.created_by
        creator_profile_pic_url = task_teacher.profile_picture.url if task_teacher.profile_picture else None
        subject_name = last_task.chat_room.lessons.first().subject.name if last_task.chat_room.lessons.exists() else "No Subject"
    else:
        task_teacher = None
        creator_profile_pic_url = None
        subject_name = "No Subject"

    if user.role == 'Mentor':
        template_name = 'subjects/mentor-home.html'
    else:
        template_name = 'subjects/home.html'

    return render(request, template_name, {
        'task_teacher': task_teacher,
        'creator_profile_pic_url': creator_profile_pic_url,
        'subject_name': subject_name,
        'last_task': last_task
    })

@login_required
def tasks_view(request):
    user = request.user
    # Get all tasks related to the lessons where the user is a student
    tasks = Task.objects.filter(chat_room__lessons__group_template__students=user).order_by('-deadline')

    return render(request, 'subjects/tasks.html', {
        'tasks': tasks
    })


@login_required
def weekly_schedule_view(request):
    user = request.user
    # еСЛИ ЮЗЕР СУПЕРАДМИН ИЛИ МЕНТОР ЕГО ПЕРЕНАПРАВЛЯЮТ В SUBJECS/VIEWS.PY
    if user.is_superuser or user.role == 'Mentor':
        shifts = Shift.objects.prefetch_related(
            'times__lessons',
            'times__lessons__teacher'
        ).all()

        if not shifts:
            print("No shifts found.")
        else:
            print(f"Found {len(shifts)} shifts.")

        return render(request, 'schedule/shifts.html', {'shifts': shifts})

    today = timezone.now().date()
    start_week = today - datetime.timedelta(days=today.weekday())
    end_week = start_week + datetime.timedelta(days=6)

    # Calculate days of the week for the range
    days_of_week = [(start_week + datetime.timedelta(days=x)).weekday() for x in range(7)]

    # Match ShiftTimes by weekday
    weekly_lessons = {day: [] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
    base_date = datetime.date(2024, 1, 1)  # Adjust based on your needs
    for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
        if i in days_of_week:
            shift_day = (base_date + datetime.timedelta(days=i)).weekday()
            day_shift_times = ShiftTime.objects.filter(date__week_day=shift_day + 1)  # Django week_day starts from 1 (Sunday)
            lessons_on_this_day = []
            for time_slot in day_shift_times:
                lessons = Lesson_crm2.objects.filter(time_slot=time_slot)
                for lesson in lessons:
                    lessons_on_this_day.append((lesson, time_slot.id))
            weekly_lessons[day] = lessons_on_this_day

    return render(request, 'subjects/weekly_schedule.html', {'weekly_lessons': weekly_lessons})

@login_required
def group_templates_view(request):
    # Fetch all group templates
    group_templates = GroupTemplate.objects.prefetch_related('students').all()

    # Count of all students
    student_count = CustomUser.objects.filter(role='Student').count()

    # Get top 8 students by alphabet when search is empty
    students = CustomUser.objects.filter(role='Student').order_by('full_name')[:8]

    # Handling search
    search_query = request.GET.get('search', '')
    if search_query:
        students = CustomUser.objects.filter(
            Q(full_name__icontains=search_query) | Q(phone_number__icontains=search_query),
            role='Student'
        ).order_by('full_name')[:8]

    context = {
        'group_templates': group_templates,
        'student_count': student_count,
        'students': students,
        'search_query': search_query
    }
    return render(request, 'subjects/group-templates.html', context)

class EditGroupTemplateView(UpdateView):
    model = GroupTemplate
    form_class = GroupTemplateForm
    template_name = 'subjects/edit_group_template.html'
    context_object_name = 'template'

    def get_success_url(self):
        return reverse('group_templates_view')

class SubjectListView(ListView):
    model = Lesson_crm2
    template_name = 'subjects/subject_list.html'
    context_object_name = 'lessons'

    def get_queryset(self):
        # Ensuring only lessons where the user is part of the group template are shown
        return Lesson_crm2.objects.filter(
            group_template__students=self.request.user
        ).select_related('mentor', 'teacher', 'subject')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@login_required
def group_template_list(request):
    form = GroupTemplateForm(request.POST or None)
    search_form = UserSearchForm(request.GET or None)

    # Fetch all group templates
    group_templates = GroupTemplate.objects.all()

    # Default fetch top 8 students alphabetically
    students = CustomUser.objects.filter(role='Student').order_by('full_name')[:8]

    # If there is a valid search query, filter by both full name and phone number
    if 'search' in request.GET and search_form.is_valid():
        search_query = request.GET.get('search', '')
        students = CustomUser.objects.filter(
            Q(full_name__icontains=search_query) | Q(phone_number__icontains=search_query),
            role='Student'
        ).order_by('full_name')[:8]

    # If the form is submitted to create a new group template
    if request.method == 'POST' and 'create_template' in request.POST:
        if form.is_valid():
            group_template = form.save(commit=False)
            selected_students = request.POST.getlist('selected_students')
            group_template.save()
            group_template.students.set(selected_students)
            return redirect('subjects:grouptemplate-list')  # Redirect to avoid double POST on refresh

    return render(request, 'subjects/group_template_list.html', {
        'form': form,
        'search_form': search_form,
        'students': students,
        'group_templates': group_templates
    })

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from .models import Lesson_crm2
from django.utils import timezone

class LessonListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Lesson_crm2
    template_name = 'subjects/lesson_list.html'
    context_object_name = 'lessons'

    def test_func(self):
        # Check if user is a student or a superuser
        return self.request.user.is_superuser or self.request.user.role == 'Student'

    def get_queryset(self):
        # Superusers see all lessons, students see only their lessons
        if self.request.user.is_superuser:
            return Lesson_crm2.objects.all().select_related('teacher', 'time_slot')
        return Lesson_crm2.objects.filter(group_template__students=self.request.user).select_related('teacher', 'time_slot')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()  # if you need the current time
        return context

class LessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Lesson_crm2
    form_class = LessonForm
    template_name = 'subjects/lesson_create.html'

    def test_func(self):
        # Check if the user is authenticated and is a mentor
        return self.request.user.is_authenticated and self.request.user.role == 'Mentor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_id'] = self.kwargs['time_id']
        return context

    def form_valid(self, form):
        try:
            time_slot = ShiftTime.objects.get(pk=self.kwargs['time_id'])
        except ShiftTime.DoesNotExist:
            raise Http404("Time slot does not exist")
        form.instance.time_slot = time_slot

        form.instance.mentor = self.request.user  # Set the mentor as the current user
        form.instance.time_slot_id = self.kwargs['time_id']  # Set the time_slot from the URL parameter

        # Create a chat room for the lesson
        chat_room = ChatRoom.objects.create(title="Temporary Title")
        form.instance.chat_room = chat_room  # Associate the chat room with the lesson

        response = super().form_valid(form)  # Save the lesson and form data

        # Update the chat room title and save it
        chat_room.title = f"Lesson {self.object.id} Chat"
        chat_room.save()

        # Add users to chat room
        for student in self.object.group_template.students.all():
            chat_room.participants.add(student)
        if self.object.teacher:
            chat_room.participants.add(self.object.teacher)

        return response
    def get_success_url(self):
        # Redirects back to the shifts page after successful creation
        return reverse('schedule:shifts')

class LessonDetailView(DetailView):
    model = Lesson_crm2
    template_name = 'subjects/lesson_detail.html'

    def get_object(self):
        lesson = super().get_object()
        # Optionally, check permissions here
        return lesson

from django.utils.timezone import localtime, localdate


def create_task(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.chat_room = room
            task.created_by = request.user
            task.save()

            # After saving the task, also create a message in the chat
            message_content = f"Задание от учителя: {task.name} - {localtime(task.deadline).strftime('%Y-%m-%d %H:%M')}"
            if task.file:
                message_content += f" <a href='{task.file.url}'>Download</a>"

            Message.objects.create(
                chat_room=room,
                user=request.user,  # or a system user if you have one
                message=message_content
            )

            return redirect('chats:chat_room_detail', room_id=room_id)  # Adjust this to your chat detail view
    else:
        form = TaskForm()

    tasks = Task.objects.filter(chat_room=room).order_by('-deadline')
    return render(request, 'subjects/create_task.html', {
        'form': form,
        'room': room,
        'tasks': tasks
    })


def search_students(request):
    search_term = request.GET.get('search', '')
    students = CustomUser.objects.filter(
        role='Student',
        full_name__icontains=search_term
    ).order_by('full_name')[:10]

    student_list = list(students.values('id', 'full_name'))
    return JsonResponse(student_list, safe=False)


@login_required
def create_volunteer_channel(request):
    channels = VolunteerChannel.objects.all()  # Get all channels for listing
    if request.method == 'POST':
        if not (request.user.role == 'Mentor' or request.user.is_superuser):
            messages.error(request, "Only mentors and superusers can create channels.")
            return redirect('home')

        form = VolunteerChannelForm(request.POST, request.FILES)
        if form.is_valid():
            volunteer_channel = form.save(commit=False)
            chat_room = ChatRoom.objects.create(title=f"Chat for {volunteer_channel.name}")
            volunteer_channel.chat_room = chat_room
            volunteer_channel.save()
            form.save_m2m()
            for user in volunteer_channel.users.all():
                chat_room.participants.add(user)
            chat_room.participants.add(request.user)  # Adding the creator as a participant
            return redirect('subjects:volunteer_channel_list')  # Redirect to the same page to see the updated list
    else:
        form = VolunteerChannelForm()

    return render(request, 'subjects/volunteer_channel_list.html', {
        'channels': channels,
        'form': form
    })


@login_required
def volunteer_channel_list(request):
    if request.method == 'POST':
        if not (request.user.role == 'Mentor' or request.user.is_superuser):
            messages.error(request, "Only mentors and superusers can create channels.")
            return redirect('home')

        form = VolunteerChannelForm(request.POST, request.FILES)
        if form.is_valid():
            volunteer_channel = form.save(commit=False)
            chat_room = ChatRoom.objects.create(title=f"Chat for {volunteer_channel.name}")
            volunteer_channel.chat_room = chat_room
            volunteer_channel.save()
            form.save_m2m()
            for user in volunteer_channel.users.all():
                chat_room.participants.add(user)
            chat_room.participants.add(request.user)
            return redirect('subjects:volunteer_channel_list')
    else:
        form = VolunteerChannelForm()

    search_query = request.GET.get('search', '')
    if search_query:
        users = CustomUser.objects.filter(
            Q(full_name__icontains=search_query) |
            Q(phone_number__icontains=search_query),
            role='Student'
        )
    else:
        users = CustomUser.objects.filter(role='Student').order_by('full_name')[:8]

    channels = VolunteerChannel.objects.all()

    return render(request, 'subjects/volunteer_channel_list.html', {
        'channels': channels,
        'form': form,
        'users': users
    })

@login_required
def set_grade(request, lesson_id):
    lesson = get_object_or_404(Lesson_crm2, id=lesson_id)
    students = lesson.group_template.students.all()
    if request.user != lesson.teacher and not request.user.is_superuser:
        return HttpResponseForbidden("You are not authorized to set grades for this lesson.")

    if request.method == 'POST':
        form = GradeForm(request.POST, students=students)
        if form.is_valid():
            form.save_grades(lesson, form.cleaned_data['date_assigned'])
    else:
        form = GradeForm(students=students)

    return render(request, 'subjects/set_grade.html', {
        'form': form,
        'lesson': lesson,
        'students': students
    })


@login_required
def grades_by_day_view(request):
    grades = Grade.objects.filter(student=request.user).order_by('date_assigned')

    # Group grades by date
    grades_by_date = {}
    for grade in grades:
        if grade.date_assigned not in grades_by_date:
            grades_by_date[grade.date_assigned] = []
        grades_by_date[grade.date_assigned].append(grade)

    return render(request, 'subjects/grades_by_day.html', {'grades_by_date': grades_by_date})

@login_required
def psy_appointment_view(request):
    return render(request, 'subjects/psy-appointment.html')



class UserSearchAPIView(APIView):
    def get(self, request):
        query = request.query_params.get('term', '')
        users = CustomUser.objects.filter(
            Q(full_name__icontains=query) | Q(phone_number__icontains=query),
            role='Student'
        )
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)

class VolunteerChannelListAPIView(APIView):
    def get(self, request):
        channels = VolunteerChannel.objects.all()
        serializer = VolunteerChannelSerializer(channels, many=True)
        return Response(serializer.data)