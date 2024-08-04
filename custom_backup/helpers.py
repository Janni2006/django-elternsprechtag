from django.apps import apps


def get_all_models():
    all_models = apps.get_models()
    return all_models


def get_all_app_models(app_label):
    app_config = apps.get_app_config(app_label)
    all_models = app_config.get_models()
    return all_models


def get_all_apps():
    app_list = apps.get_app_configs()
    return app_list
