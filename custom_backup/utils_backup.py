from dashboard.models import *
from authentication.models import *
from django.contrib.auth.models import Group, Permission
import logging
from pathlib import Path
from django.conf import settings
import os
from .apps import CustomBackupConfig
import json
from json import JSONEncoder
import tarfile
from .exceptions import MigrationNotFound, CreateException
import socket
from .models import Backup
from .helpers import *
from django.core.signing import Signer

signer = Signer()


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


class CustomBackup:
    def __init__(self, manual=False) -> None:
        self.logger = logging.getLogger(__name__)
        self.manual = manual
        self.json_path = Path(
            os.path.join(settings.BACKUP_ROOT, CustomBackupConfig.JSON_FILENAME)
        )
        self.dumpinfo_path = Path(
            os.path.join(settings.BACKUP_ROOT, CustomBackupConfig.DUMPINFO)
        )
        self.created_at = timezone.now()

    def backup_upcomming_users(self):
        upcomming_user_dict = []
        for up_user in Upcomming_User.objects.all():
            if up_user.email_send:
                upcomming_user_dict.append(
                    {
                        "access_key": up_user.access_key,
                        "otp": up_user.otp,
                        "created": up_user.created,
                        "student_shield_id": up_user.student.shield_id,
                        "email_send": True,
                        "parent_email": up_user.parent_email,
                        "parent_registration_email_send": up_user.parent_registration_email_send,
                    }
                )
            else:
                upcomming_user_dict.append(
                    {
                        "student_shield_id": up_user.student.shield_id,
                        "email_send": False,
                    }
                )
        return upcomming_user_dict

    def backup_students(self):
        student_dict = []
        for student in Student.objects.all():
            student_dict.append(
                {
                    "shield_id": student.shield_id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "student_email": student.child_email,
                    "class_name": student.class_name,
                    "parent_registered": student.registered,
                }
            )
        return student_dict

    def backup_tags(self):
        tag_dict = []
        for tag in Tag.objects.all():
            tag_dict.append(
                {"name": tag.name, "synonyms": tag.synonyms, "color": tag.color}
            )
        return tag_dict

    def backup_custom_user(self):
        user_dict = []
        for user in CustomUser.objects.all():
            # signed_password = signer.sign(user.password)
            signed_password = user.password
            user_groups = [group.name for group in user.groups.all()]
            user_permissions = [
                permission.pk for permission in user.user_permissions.all()
            ]

            match user.role:
                case 0:
                    user_dict.append(
                        {
                            "email": user.email,
                            "role": 0,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "students": [
                                student.shield_id for student in user.students.all()
                            ],
                            "is_active": user.is_active,
                            "permissions": user_permissions,
                            "is_staff": False,
                            "is_superuser": user.is_superuser,
                            "password": signed_password,
                            "groups": user_groups,
                        }
                    )
                case 1:
                    try:
                        extra_data = user.teacherextradata.first()
                    except:
                        user_dict.append(
                            {
                                "email": user.email,
                                "role": 1,
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "is_active": user.is_active,
                                "permissions": user_permissions,
                                "is_staff": True,
                                "is_superuser": user.is_superuser,
                                "password": signed_password,
                                "groups": user_groups,
                            }
                        )
                    else:
                        user_dict.append(
                            {
                                "email": user.email,
                                "role": 1,
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "acronym": extra_data.acronym,
                                "tags": [tag.name for tag in extra_data.tags.all()],
                                "is_active": user.is_active,
                                "permissions": user_permissions,
                                "is_staff": True,
                                "is_superuser": user.is_superuser,
                                "password": signed_password,
                                "groups": user_groups,
                            }
                        )
                case 2:
                    user_dict.append(
                        {
                            "email": user.email,
                            "role": 2,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "is_active": user.is_active,
                            "permissions": user_permissions,
                            "is_staff": user.is_staff,
                            "is_superuser": user.is_superuser,
                            "password": signed_password,
                            "groups": user_groups,
                        }
                    )
        return user_dict

    def backup_groups(self):
        group_dict = []
        for group in Group.objects.all():
            group_dict.append(
                {
                    "group_name": group.name,
                    "group_permissions": [
                        permission.pk for permission in group.permissions.all()
                    ],
                }
            )
        return group_dict

    def backup_settings(self):
        settings = SiteSettings.objects.first()
        settings_dict = {
            "event_duration": settings.event_duration.total_seconds(),
            "impressum": settings.impressum,
            "keep_events_for": settings.keep_events.total_seconds(),
            "delete_events": settings.delete_events,
            "keep_student_changes_for": settings.keep_student_changes.total_seconds(),
            "delete_student_changes": settings.delete_student_changes,
            "keep_announcements_for": settings.keep_announcements.total_seconds(),
            "delete_announcements": settings.delete_announcements,
            "keep_formulars_for": settings.keep_event_change_formulas.total_seconds(),
            "delete_formulars": settings.delete_event_change_formulas,
            "inquiry_behaviour": settings.iquiry_bahvior,
        }
        return settings_dict

    def backup_individual_event(self, event: Event):
        event_dict = {
            "start": event.start,
            "end": event.end,
            "occupied": event.occupied,
            "status": event.status,
            "lead_status": event.lead_status,
            "lead_status_last_change": event.lead_status_last_change,
            "lead_manual_override": event.lead_manual_override,
            "disable_automatic_changes": event.disable_automatic_changes,
            "students": list(event.student.all().values_list("shield_id", flat=True)),
        }
        return event_dict

    def backup_individual_event_change_formular(self, formular: EventChangeFormula):
        if formular.no_events:
            formular_dict = {
                "type": formular.type,
                "child_fomular": [
                    self.backup_individual_event_change_formular(child_formular)
                    for child_formular in formular.childformular.all()
                ],
                "start_time": None,
                "end_time": None,
                "no_events": True,
                "status": formular.status,
                "created_at": formular.created_at,
            }
        else:
            try:
                formular_dict = {
                    "type": formular.type,
                    "child_fomular": [
                        self.backup_individual_event_change_formular(child_formular)
                        for child_formular in formular.childformular.all()
                    ],
                    "start_time": formular.start_time.isoformat(),
                    "end_time": formular.end_time.isoformat(),
                    "no_events": False,
                    "status": formular.status,
                    "created_at": formular.created_at,
                }
            except:
                self.logger.log(
                    "An incorrectly configured event change formular was detected. It will be ignored in the backup."
                )
        return formular_dict

    def backup_teacher_group(self, teacher_group: TeacherEventGroup, backup_old=False):
        events = Event.objects.filter(Q(teacher_event_group=teacher_group))
        if not backup_old:
            events = events.exclude(Q(start__lte=timezone.now()))

        teacher_group_dict = {
            "teacher": teacher_group.teacher.email,
            "lead_start": teacher_group.lead_start,
            "lead_inquiry_start": teacher_group.lead_inquiry_start,
            "lead_end_timedelta": teacher_group.lead_end_timedelta.total_seconds(),
            "lead_allow_same_day": teacher_group.lead_allow_same_day,
            "room": teacher_group.room,
            "lead_manual_override": teacher_group.lead_manual_override,
            "lead_status": teacher_group.lead_status,
            "lead_status_last_change": teacher_group.lead_status_last_change,
            "disable_automatic_changes": teacher_group.disable_automatic_changes,
            "events": [self.backup_individual_event(event) for event in events],
            "formulars": [
                self.backup_individual_event_change_formular(formular)
                for formular in EventChangeFormula.objects.filter(
                    Q(teacher_event_group=teacher_group), Q(parent_formular=None)
                )
            ],
        }  # Force und manual apply werden hier nicht mit gesichert, da diese Felder im regulären Betrieb immer auf False stehen sollten. Falls sie in einem anderen Status stehen geblieben sind, soll der Fehler nicht übernommen werden.

        return teacher_group_dict

    def backup_day_event_group(self, day_group: DayEventGroup):
        day_event_group_dict = {
            "date": day_group.date,
            "lead_start": day_group.lead_start,
            "lead_inquiry_start": day_group.lead_inquiry_start,
            "created": day_group.created,
            "lead_manual_override": day_group.lead_manual_override,
            "lead_status": day_group.lead_status,
            "lead_status_last_change": day_group.lead_status_last_change,
            "disable_automatic_changes": day_group.disable_automatic_changes,
            "teacher_event_groups": [
                self.backup_teacher_group(teacher_group)
                for teacher_group in TeacherEventGroup.objects.filter(
                    day_group=day_group
                )
            ],
        }  # Force und manual apply werden hier nicht mit gesichert, da diese Felder im regulären Betrieb immer auf False stehen sollten. Falls sie in einem anderen Status stehen geblieben sind, soll der Fehler nicht übernommen werden.

        return day_event_group_dict

    def backup_individual_inquries(self, inquiry: Inquiry):
        inquiry_dict = {
            "type": inquiry.type,
            "requester": inquiry.requester.email,
            "students": [student.shield_id for student in inquiry.students.all()],
            "respondent": inquiry.respondent.email,
            "reason": inquiry.reason,
            "processed": inquiry.processed,
            "respondent_reaction": inquiry.respondent_reaction,
            "notified": inquiry.notified,
            "created": inquiry.created,
            "event_start": inquiry.event.start if inquiry.event else None,
            "event_teacher": inquiry.event.teacher if inquiry.event else None,
        }
        return inquiry_dict

    def backup_individual_base_events(self, base_event: BaseEventGroup):
        base_event_dict = {
            "lead_start": base_event.lead_start,
            "lead_inquiry_start": base_event.lead_inquiry_start,
            "lead_status": base_event.lead_status,
            "lead_status_last_change": base_event.lead_status_last_change,
            "disable_automatic_changes": base_event.disable_automatic_changes,
            "day_groups": [
                self.backup_day_event_group(day_group)
                for day_group in DayEventGroup.objects.filter(base_event=base_event)
            ],
            "inquries": [
                self.backup_individual_inquries(inquiry)
                for inquiry in Inquiry.objects.filter(base_event=base_event)
            ],
        }  # Force und manual apply werden hier nicht mit gesichert, da diese Felder im regulären Betrieb immer auf False stehen sollten. Falls sie in einem anderen Status stehen geblieben sind, soll der Fehler nicht übernommen werden.

        return base_event_dict

    def backup_all_events(self, backup_old=False):
        if backup_old:
            base_events = BaseEventGroup.objects.all()
        else:
            base_events = BaseEventGroup.objects.filter(valid_until__gte=timezone.now())

        base_list = [
            self.backup_individual_base_events(base_event) for base_event in base_events
        ]

        return base_list

    def get_backup_data(self):
        backup = {
            "upcomming_users": {
                "version": 1,
                "data": self.backup_upcomming_users(),
            },
            "students": {
                "version": 1,
                "data": self.backup_students(),
            },
            "tags": {
                "version": 1,
                "data": self.backup_tags(),
            },
            "groups": {
                "version": 1,
                "data": self.backup_groups(),
            },
            "custom_user": {
                "version": 1,
                "data": self.backup_custom_user(),
            },
            "settings": {
                "version": 1,
                "data": self.backup_settings(),
            },
            "events": {
                "version": 1,
                "data": self.backup_all_events(),
            },
        }

        return backup

    def create_backup_json_file(self):
        self.logger.debug(f"creating database dump: {self.json_path}")

        self.json_data = json.dumps(self.get_backup_data(), cls=DateTimeEncoder)

        with open(self.json_path, "w") as f:
            f.write(self.json_data)

        with open(self.dumpinfo_path, "w") as f:
            f.write(f"created_at;{self.created_at}\n")
            f.write(f"backup_directories;{CustomBackupConfig.BACKUP_DIRS}\n")
            f.write(
                f"backup_validation_hash;{get_validation_hash(json_data=self.json_data, created_at=self.created_at)}"
            )

        if Path(self.json_path).is_file() and Path(self.dumpinfo_path).is_file():
            return Path(self.json_path), Path(self.dumpinfo_path)
        else:
            raise Exception("Error could not create database dump")

    def create_tar_file(
        self,
        output_path: Path,
        compress: bool,
        source_dirs: list,
        source_files: list,
        **kwargs,
    ):
        if compress:
            mode = "w:gz"
            suffix = ".tar.gz"
        else:
            mode = "w"
            suffix = ".tar"
        output_path = str(output_path) + suffix
        with tarfile.open(output_path, mode) as tar:
            for source_dir in source_dirs:
                if not Path(source_dir).is_absolute():
                    self.logger.debug(
                        f"add directory {source_dir} to tar: {output_path}"
                    )
                    tar.add(source_dir, arcname=Path(os.path.basename(source_dir)))
                else:
                    tar.add(source_dir, arcname=source_dir)
            for source_file in source_files:
                self.logger.debug(f"add file {source_file} to tar: {output_path}")
                tar.add(source_file, arcname=os.path.basename(source_file))
            # for migration in migrations:
            #     if Path(migration).exists():
            #         self.logger.debug(f"add file {migration} to tar: {output_path}")
            #         arcname = (
            #             f"_migration_backup/{migration.relative_to(settings.BASE_DIR)}"
            #         )
            #         tar.add(migration, arcname=arcname)
            #         self.dump_migration_files += 1
        if not Path(output_path).is_file():
            raise Exception("tarfile has not been created")

        return output_path

    def create_backup_file(self, compress=False, silent=False, *args, **options):
        OUTPUT_DIR = Path(settings.BACKUP_ROOT)

        if not silent:
            print(f"create new backup in {settings.BACKUP_ROOT}, compress = {compress}")
        if not OUTPUT_DIR.is_dir():
            self.logger.debug(f"creating output_dir {OUTPUT_DIR}")
            os.makedirs(OUTPUT_DIR, exist_ok=True)

        for path in CustomBackupConfig.BACKUP_DIRS:
            posix = os.path.join(settings.BASE_DIR, path)
            posix = Path(posix)
            if not posix.is_dir():
                self.context["backup"] = "failed to create"
                raise CreateException(
                    f"directory does not exist", output=str(posix), **self.context
                )

        if self.json_path.exists():
            self.logger.debug(f"clean up remaining {self.json_path}")
            os.remove(self.json_path)

        if self.dumpinfo_path.exists():
            self.logger.debug(f"clean up remaining {self.dumpinfo_path}")
            os.remove(self.dumpinfo_path)

        JSON_FILE, DUMPINFO_FILE = self.create_backup_json_file()
        TAR_PREFIX = (
            str(socket.gethostname())
            + "_"
            + CustomBackupConfig.PROJECT_NAME
            + "_"
            + str(self.created_at.strftime("%Y-%m-%d_%H-%M-%S"))
        )
        OUTPUT_TAR = Path(f"{OUTPUT_DIR}/{TAR_PREFIX}")
        OUTPUT_TAR = self.create_tar_file(
            output_path=OUTPUT_TAR,
            source_dirs=CustomBackupConfig.BACKUP_DIRS,
            source_files=[JSON_FILE, DUMPINFO_FILE],
            compress=compress,
        )

        Backup.objects.create(
            backup_file=Path(OUTPUT_TAR),
            backup_type=(
                Backup.BackupTypeChoices.MANUAL
                if self.manual
                else Backup.BackupTypeChoices.AUTOMATIC
            ),
            size_bytes=Path(OUTPUT_TAR).stat().st_size,
            backup_directories=CustomBackupConfig.BACKUP_DIRS,
            keep_backup=self.manual,
            validation_hash=get_validation_hash(
                json_data=self.json_data, created_at=self.created_at
            ),
            external=False,
        )

        os.remove(Path(JSON_FILE).absolute())
        os.remove(Path(DUMPINFO_FILE).absolute())
