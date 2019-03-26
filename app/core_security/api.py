import os
import datetime
from django.contrib.auth.decorators import login_required, user_passes_test
from libs.default.decorators import request_ajax_required
from django.db.models import Case, When
from django.http import Http404
from django.utils.decorators import method_decorator
from apps.core.backup.dropboxbackup import BackupManager
from apps.core.backup.gdrivebackup import GDriveClient
#from libs.pygit import check_update, update, install
from apps.core.controller import BaseController
from apps.core.models import Backup
from otma.apps.core.authentication.models import User
from project_ivis import settings
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
# from selenium import webdriver
from django.db import models


class BackupController(BaseController):

    # method_decorator(login_required)
    # user_passes_test(lambda u: u.permissions.can_view_entity(), login_url='/error/access_denied', redirect_field_name=None)
    @request_ajax_required
    @method_decorator(login_required)
    def load_backups(self, request, company_repository, project_name):
        x = BaseController().filter(request, model=Backup)
        # print("VEJA O QUE TENHO QUE ENVIAR: ",x)
        return BaseController().filter(request, model=Backup, limit=12)

    @request_ajax_required
    @method_decorator(login_required)
    def create_backup_local(self, request, company_repository, project_name):
        self.start_process(request)
        #backup_paramters = BackupManager().create_backup_local()
        backup_paramters = GDriveClient().create_backup_local()
        # print('BACKUP REALIZADO COM SUCESSO.')
        response_dict = {}
        response_dict['result'] = True
        response_dict['message'] = ""
        response_dict['object'] = True
        return self.response(response_dict)

    """ backup = Backup()
        backup.backup_file_name = backup_paramters['file_name']
        backup.backup_link = 'Null'
        backup.backup_size = backup_paramters['size']
        self.get_exceptions(backup, None)
        if self.full_exceptions == {}:
            response_dict = self.execute(backup, backup.save)
        else:
            response_dict = self.notify.error(self.full_exceptions)
        return self.response(response_dict)
        """

    @request_ajax_required
    @method_decorator(login_required)
    def create_backup(self, request, company_repository, project_name):
        self.start_process(request)
        folder_id = GDriveClient().verify_folder()

        backup_paramters = GDriveClient().create_backup(folder_id, compressed=True)
        print(backup_paramters['size'])
        backup = Backup()
        backup.backup_file_name = backup_paramters['file_name']
        backup.backup_link = backup_paramters['link']
        backup.backup_size = backup_paramters['size']
        self.get_exceptions(backup, None)
        if self.full_exceptions == {}:
            response_dict = self.execute(backup, backup.save)
        else:
            response_dict = self.notify_error(self.full_exceptions)
        return self.response(response_dict)

    @request_ajax_required
    @method_decorator(login_required)
    def restore_backup(self, request, company_repository, project_name, specific_file):
        self.start_process(request)
        if specific_file:
            backup_paramters = GDriveClient().restore_backup(int(specific_file))
        else:
            backup_paramters = GDriveClient().restore_backup()
        response_dict = {}
        response_dict['result'] = True
        response_dict['message'] = ""
        response_dict['object'] = backup_paramters
        if backup_paramters is True:
            pass
        else:
            pass
        return self.response(response_dict)

    #@request_ajax_required
    @method_decorator(login_required)
    def list_backups(self, request, company_repository, project_name):
        self.start_process(request)
        folder_id = GDriveClient().verify_folder()
        backup_list = GDriveClient().list_backup(folder_id)
        new_list = []
        for item in reversed(backup_list):
            if len(new_list) == 10:
                break
            else:
                new_list.append(item)

        backup_list = new_list
        response_dict = {}
        response_dict['result'] = True
        response_dict['message'] = ""
        response_dict['object'] = backup_list
        # print("VEJA A LISTA:", backup_list)
        # for item in backup_list:
        #    response_data = {}
        #    response_data['object'] = {}
        #    response_dict['object']['file_name'] = item['file_name']
        #    response_dict['object']['link'] = item['link']
        #    response_dict['object']['size'] = item['size']
        #    response_dict['object']['date'] = item['client_modified']
        #    print('SOU RESPONSE',response_dict)
        return self.response(response_dict)

    @request_ajax_required
    @method_decorator(login_required)
    def check_available_space(self, request, company_repository, project_name):
        self.start_process(request)
        backup_list = Backup.objects.all()
        response_dict = {}
        response_dict['result'] = True
        response_dict['message'] = ""
        response_dict['object'] = {}
        response_dict['object']['total_files'] = len(backup_list)
        response_dict['object']['total_space'] = 2000000000
        response_dict['object']['used_space'] = 0

        for item in backup_list:
            response_dict['object']['used_space'] = response_dict['object']['used_space'] + item.backup_size
        response_dict['object']['used_percent_space'] = round(
            (response_dict['object']['used_space'] / response_dict['object']['total_space']) * 100, 2)

        # print("ESPACO DE ARMAZENAMENTO: ",response_dict)
        return self.response(response_dict)

    @request_ajax_required
    @method_decorator(login_required)
    def check_available_system_space(self, request, company_repository, project_name):
        self.start_process(request)
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(settings.BACKUP_STORAGE_OPTIONS['location']):
            for f in filenames:
                filepath = os.path.join(dirpath, f)
                total_size += os.path.getsize(filepath) / 1024
                file_count = len(filenames)

        if total_size < 1024:
            total_size = '{0:.2f}'.format(total_size)
            suffix = ' Kb'
        elif total_size >= 1024:
            total_size = '{0:.1f}'.format(total_size / 1024)
            suffix = ' Mb'
        elif total_size >= 1024 * 1024:
            total_size = '{0:.1f}'.format(total_size / 1024)
            suffix = ' Gb'

        response_dict = {}
        response_dict['result'] = True
        response_dict['message'] = ""
        response_dict['object'] = {}
        try:
            response_dict['object']['total_files'] = file_count
        except:
            response_dict['object']['total_files'] = 0
        response_dict['object']['folder_size'] = total_size + suffix

        return self.response(response_dict)

    @request_ajax_required
    @method_decorator(login_required)
    def check_available_space1(self, request, company_repository, project_name):
        self.start_process(request)
        # backup_list = BackupManager().list_backup()
        backup_list = Backup.objects.all()

        response_dict = {}
        response_dict['result'] = True
        response_dict['message'] = ""
        response_dict['object'] = {}
        response_dict['object']['total_files'] = len(backup_list)
        response_dict['object']['total_space'] = 2000000000
        response_dict['object']['used_space'] = 0
        response_dict['object']['last_update'] = None
        for item in backup_list:
            response_dict['object']['used_space'] = response_dict['object']['used_space'] + float(item['size'])
        response_dict['object']['used_space'] = '{0:.2f}'.format(response_dict['object']['used_space'])
        # print('RESPONSE:',(response_dict['object']['used_space']))
        response_dict['object']['used_percent_space'] = round(
            (float(response_dict['object']['used_space']) / response_dict['object']['total_space']) * 100, 2)
        # print("PERCENTUAL: ",float(response_dict['object']['used_space']) / response_dict['object']['total_space'])
        # print("ESPACO DE ARMAZENAMENTO: ",response_dict)
        return self.response(response_dict)

    @request_ajax_required
    @method_decorator(login_required)
    def last_backup(self, request, company_repository, project_name):
        x = BaseController().filter(request, model=Backup)
        # print("VEJA O QUE TENHO QUE ENVIAR: ",x)
        return BaseController().filter(request, model=Backup, limit=1)
