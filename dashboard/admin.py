from django.contrib import admin

from .models import Event, TeacherStudentInquiry

# Register your models here.


@admin.action(description='Mark selected events as occupied')
def make_occupied(modeladmin, request, queryset):
    queryset.update(occupied=True)


@admin.action(description='Mark selected events as unoccupied')
def make_empty(modeladmin, request, queryset):
    queryset.update(occupied=False, parent=None)


class EventAdmin(admin.ModelAdmin):
    list_display = ("teacher", "occupied", "start", "end")
    list_filter = ("occupied",)

    # fieldsets = (("Time", {'fields': ('start', 'end')}),)

    # fieldsets = ((None, {'fields': ('teacher', 'start', 'end')}),)

    actions = [make_occupied, make_empty]


admin.site.register(Event, EventAdmin)
admin.site.register(TeacherStudentInquiry)
