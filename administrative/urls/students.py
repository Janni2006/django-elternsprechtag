from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from ..views.students import *

urlpatterns = [
    ## Students ##
    path("", StudentListView.as_view(), name="student_list_view"),
    path("<pk>/view", StudentDetailView.as_view(), name="student_details_view"),
    path("<pk>/edit", StudentEdit.as_view(), name="student_edit_view"),
    path(
        "<pk>/reset_relationship",
        ResetStudentParentRelationshipView.as_view(),
        name="student_reset_relationship_view",
    ),
    path(
        "<pk>/send_registration_mail",
        UpcommingUserSendRegistrationMail.as_view(),
        name="administrative_student_send_registration_mail",
    ),
    path(
        "import/upload/",
        StudentImportStart.as_view(),
        name="student_import_filepload",
    ),
    path(
        "import/cancel/",
        StudentImportCancel.as_view(),
        name="student_import_cancel",
    ),
    path(
        "import/view/",
        StudentImportListChanges.as_view(),
        name="student_import_listchanges",
    ),
    path(
        "import/apply/all/",
        StudentImportApproveAndApplyAll.as_view(),
        name="student_import_apply_all_changes",
    ),
    path(
        "import/apply/<pk>/",
        StudentImportApproveAndApply.as_view(),
        name="student_import_apply_change",
    ),
    path(
        "import/apply/operation/<int:operation>/",
        StudentImportApproveAndApplyWithOperation.as_view(),
        name="student_import_apply_with_operation",
    ),
    ## Users ##
    # path(
    #     "users/",
    #     RedirectView.as_view(pattern_name="parents_table"),
    #     name="administrative_users_view",
    # ),
    # path(
    #     "users/parents/",
    #     ParentTableView.as_view(),
    #     name="parents_table",
    # ),
    # path(
    #     "users/parents/<parent_id>/edit",
    #     ParentEditView.as_view(),
    #     name="parent_edit_view",
    # ),
    # path(
    #     "users/teachers/",
    #     TeacherTableView.as_view(),
    #     name="teachers_table",
    # ),
    # path(
    #     "users/teachers/import/",
    #     TeacherImportView.as_view(),
    #     name="teachers_import",
    # ),
    # path(
    #     "users/teachers/<pk>/edit",
    #     TeacherEditView.as_view(),
    #     name="teachers_edit_view",
    # ),
    ## Events ##
    # path(
    #     "events/",
    #     EventsListView.as_view(),
    #     name="administrative_event_list_view",
    # ),
    # path(
    #     "events/<event_id>/block",
    #     EventBlockView.as_view(),
    #     name="administrative_event_block_view",
    # ),
    # path(
    #     "events/formulars/",
    #     AdministrativeFormulaApprovalView.as_view(),
    #     name="administrative_event_formular_view",
    # ),
    # path(
    #     "events/formulars/add/new_date",
    #     EventAddNewDateAndFormularsView.as_view(),
    #     name="administrative_event_formular_new_date_add_view",
    # ),
    # path(
    #     "events/formulars/add/<event_group_id>",
    #     EventChangeFormularAddView.as_view(),
    #     name="administrative_event_formular_add_view",
    # ),
    # path(
    #     "events/formulars/<pk>/edit/",
    #     EditTimeSlotView.as_view(),
    #     name="administrative_event_formular_edit_view",
    # ),
    # path(
    #     "events/formulars/<int:formular_id>/approve/",
    #     EventChangeFormularApproveView.as_view(),
    #     name="administrative_event_formular_approve_view",
    # ),
    # path(
    #     "events/formulars/<int:formular_id>/disapprove/",
    #     EventChangeFormularDisapproveView.as_view(),
    #     name="administrative_event_formular_disapprove_view",
    # ),
    # path("settings/", SettingsView.as_view(), name="administrative_settings"),
]