from otma.apps.core.security.enkoder import Encrypter
from django.core.management import call_command
from django.conf import settings

from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth

from datetime import date
import datetime
import shutil
import django
import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")


class GDriveClient:

    def __init__(self, secrets=settings.GDRIVE_CLIENT_SECRETS_JSON, credentials=settings.GDRIVE_CREDENTIALS_JSON):

        super(GDriveClient, self).__init__()

        self.drive = None
        self.dir = None
        self.service = None

        authenticator = GDriveClient.authenticate(secrets, credentials)

        self.init_drive(authenticator)

    def init_drive(self, authenticator):
        self.drive = GoogleDrive(authenticator)
        self.dir = '/'
        self.service = self.drive.auth.service

    def authenticate(secrets, credentials):
        authenticator = GoogleAuth()
        authenticator.settings = {
            'client_config_backend': 'file',
            'client_config_file':    secrets,
            'save_credentials':      False,
            'oauth_scope':           ['https://www.googleapis.com/auth/drive']
        }

        authenticator.LoadCredentialsFile(credentials)
        if authenticator.credentials is None:
            response = input('No credentials. Authenticate with local web browser? [y]/n > ')
            if response.lower() in ['y', 'yes'] or len(response) == 0:
                authenticator.LocalWebserverAuth()
            else:
                authenticator.CommandLineAuth()
        elif authenticator.access_token_expired:
            authenticator.Refresh()
        else:
            authenticator.Authorize()

        authenticator.SaveCredentialsFile(credentials)
        return authenticator

    def create_backup(self, folder_id, compressed=False):
        start_timing_backup = datetime.datetime.now()
        django.setup()

        with open(settings.BACKUP_FILE, 'w') as f:
            call_command('dumpdata', stdout=f)

        final_name = self.rename_backup() + ".json"
        filepath = settings.BACKUP_FILE

        if compressed:
            gz_filepath = Encrypter().encrypt(filepath)
            new_filename = os.path.basename(gz_filepath).replace('dump.json', final_name)
            file_path = gz_filepath
            shutil.copy(gz_filepath, settings.BACKUP_LOCAL.replace('dump.json', new_filename))
        else:
            new_filename = final_name
            file_path = settings.BACKUP_FILE
        update = self.overwrite_backup(folder_id, new_filename)

        if update:
            update.Delete()
        new_file = self.drive.CreateFile({"title": new_filename, "parents": [{"kind": "drive#fileLink", "id": folder_id}]})
        #new_file = self.drive.CreateFile({"title": final_name, "parents": [{"kind": "drive#fileLink", "id": folder_id}]})
        new_file.SetContentFile(file_path)
        new_file.Upload()
        print('Upload realizado com sucesso!!!')
        permission = new_file.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
        new_file.FetchMetadata(fields='permissions')

        #print('Permissions:', new_file['permissions'])
        #print('title: %s, id: %s, url: %s, link: %s' % (new_file['title'], new_file['id'], url_link + new_file['id'], new_file['alternateLink']))

        data = {}
        data['file_name'] = new_file['title']
        data['link'] = new_file['webContentLink']
        data['client_modified'] = new_file['modifiedDate']
        data['size'] = int(new_file['fileSize']) / 1024 #'{0:.2f}'.format(int(new_file['fileSize']) / 1024)

        backup_duration = datetime.datetime.now() - start_timing_backup
        file = open(settings.BACKUP_FILE, 'w')
        file.close()

        os.rename(settings.BACKUP_FILE, settings.BACKUP_FILE.replace("dump.json", final_name))

        try:
            os.remove(gz_filepath)
            os.remove(settings.BACKUP_FILE.replace("dump.json", final_name))
        except:
            pass
            os.remove(settings.BACKUP_FILE.replace("dump.json", final_name))

        #print("Backup gerado em", backup_duration.total_seconds(), "segundos")
        return data

    def rename_backup(self):
        time = datetime.datetime.now()
        now = time.strftime("%p")
        if now == 'AM':
            now = 'mat'
        elif now == 'PM':
            now = 'vesp'
        dias = ('seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom')
        hj = date.today()
        dia = dias[hj.weekday()]
        final_name = dia+"_"+now
        return final_name

    def create_backup_local(self):
        start_timing_backup = datetime.datetime.now()
        django.setup()

        with open(settings.BACKUP_LOCAL, 'w') as f:
            call_command('dumpdata', stdout=f)

        time = datetime.datetime.now()
        final_name = time.strftime("%Y%m%d%H%M%S") + ".json"

        os.rename(settings.BACKUP_LOCAL, settings.BACKUP_LOCAL.replace("dump.json", final_name))

        metadata = {}
        basename = settings.BACKUP_LOCAL.replace("dump.json", final_name)
        new_filename = os.path.basename(basename)
        size = os.path.getsize(basename)
        print(size)
        metadata['file_name'] = new_filename
        metadata['size'] = size

        backup_duration = datetime.datetime.now() - start_timing_backup

        print("Backup gerado em", backup_duration.total_seconds(), "segundos")

        return metadata

    def create_folder(self, foldername):
        new_folder = self.drive.CreateFile(metadata={'title': foldername,"mimeType": "application/vnd.google-apps.folder"})
        new_folder.Upload()
        print('Pasta criada com sucesso!!!')
        print('folder title: %s, id: %s' % (new_folder['title'], new_folder['id']))
        return new_folder['id']

    def verify_folder(self):
        folder_list = self.drive.ListFile({"q": "'root' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
        if folder_list == []:
            self.create_folder(foldername=settings.GDRIVE_ROOT_PATH)
        for folder in folder_list:
            if folder['title'] == 'backup':
                #print('Pasta já existe no gdrive...')
                #print('folder title: %s, id: %s' % (folder['title'], folder['id']))
                break
            else:
                print('Tenho que criar essa pasta...')
                self.create_folder(foldername=settings.GDRIVE_ROOT_PATH)
                break
        return folder['id']

    def overwrite_backup(self,folder_id, filename):
        file_list = self.drive.ListFile({'q': "'{}' in parents and trashed=false".format(folder_id)}).GetList()
        if not file_list == []:
            try:
                for file in file_list:
                    if file['title'] == filename:
                        #print('Filename:', file['title'])
                        #file.Delete()
                        return file
            except:
                return False
        else:
            return False

    def list_backup(self, folder_id):
        file_list = self.drive.ListFile({'q': "'{}' in parents and trashed=false".format(folder_id)}).GetList()
        foldersize = []
        if not file_list == []:
            cont = 0
            metadata = []
            for file in file_list:# sorted(file_list, key=lambda x: x['title']):
                foldersize.append(int(file['fileSize']))
            folder_size = '{0:.2f}'.format(sum(foldersize) / 1024)
            for file in file_list: # sorted(file_list, key=lambda x: x['title']):
                data = {}
                #print(file)
                cont += 1
                #print('Arquivo: {} from GDrive ({}/{})'.format(file['title'], cont, len(file_list)))
                data['file_name'] = file['title']
                data['link'] = file['webContentLink']
                data['client_modified'] = file['modifiedDate']
                data['size'] = '{0:.2f}'.format(int(file['fileSize'])/1024)
                data['folder_size'] = folder_size
                metadata.append(data)
            return metadata
        else:
            print('Pasta sem arquivos para serem visualizados!!!')
            return False

    def restore_backup(self, specific_file=None):
        django.setup()
        from django.contrib.contenttypes.models import ContentType
        restore_file = settings.BACKUP_STORAGE_OPTIONS['location'] + '/restore.json'
        try:
            os.remove(restore_file)
        except OSError:
            pass

        start_timing_backup = datetime.datetime.now()
        folder_id = self.verify_folder()
        if specific_file is not None:
            most_recent_backup = self.gd_download(folder_id, specific_file)
        else:
            most_recent_backup = self.gd_download(folder_id)
        print("Arquivo Baixado em: ",most_recent_backup)
        call_command('flush', '--no-input')
        ContentType.objects.all().delete()
        call_command('loaddata', restore_file)

        backup_duration = datetime.datetime.now() - start_timing_backup
        print("Backup Restaurado em", backup_duration.total_seconds(), "segundos")
        # self.clear_temp_file()
        return True

    def gd_download(self, folder_id, specific_file=None):
        download_dir = settings.BACKUP_STORAGE_OPTIONS['location']
        files_list = self.drive.ListFile({'q': "'{}' in parents and trashed=false".format(folder_id)}).GetList()
        #print('files_list', files_list)
        if specific_file is not None:
            index_file = specific_file
        else:
            index_file = 0
        # new_files_list = files_list # sorted(files_list, key=lambda x: x['title'])
        # print('NEW_LIST:', files_list)
        file_id = files_list[index_file]['id']
        print('Downloading {} from GDrive id {}'.format(files_list[index_file]['title'], file_id))
        for file in files_list:
            # print(file)
            if file['id'] == file_id:
                if '.gz' in files_list[index_file]['title']:
                    file.GetContentFile(download_dir + files_list[index_file]['title'])
                    gz_filepath = Encrypter().decrypt(download_dir + files_list[index_file]['title'])
                    request = gz_filepath[0]
                    #os.remove(gz_filepath[1])
                    #os.remove(download_dir + files_list[index_file]['title'])
                else:
                    request = file.GetContentString()
                #print('folder title: %s, id: %s' % (files_list[index_file]['title'], download_dir + files_list[index_file]['title']))
                break
        final_path = download_dir + 'restore.json'
        with open(final_path, "w") as f:
            f.write(request)
        return final_path

    def clear_temp_file(self):
        backup_file = settings.BACKUP_STORAGE_OPTIONS['location'] + ''
        if os.path.isfile(backup_file):
            os.remove(backup_file)


if __name__ == '__main__':
    GDrive = GDriveClient
    verify = GDrive().verify_folder()
    # print(verify)
    # auth = GDrive().authenticate() Não está sendo utilizado
    # create_folder = GDrive().create_folder(foldername='Backup') Não está sendo utilizado
    # authenticate = GDrive().init_drive
    # list = GDrive().list_backup(verify) Não está sendo utilizado
    # print(list)

    # ESTES SERÃO MAIS UTILIZADOS
    #list = GDrive().list_backup(verify)
    #print(list)
    #upload = GDrive().create_backup(verify, compressed=True)
    #print(upload)
    #download = GDrive().gd_download(verify)
    #restore = GDrive().restore_backup()
    # local_db = GDrive().create_backup_local()
    # print(local_db)

"""
from django.core.management import call_command
from django.conf import settings
from datetime import date
import datetime
import dropbox
import shutil
import django
import sys
import re
import os


class BackupManager:

    def user_profile(self):
        self.dropbox = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)
        share_folder = self.dropbox.sharing_share_folder(settings.DROPBOX_ROOT_PATH)
        #print(share_folder)

    def create_backup(self):
        self.dropbox = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)
        start_timing_backup = datetime.datetime.now()
        django.setup()
        call_command('dbbackup', '-v', '1', '-z')
        backup = self.upload()
        link = backup['link']
        name = backup['file_name']
        size = backup['size']
        link_folder = backup['folder_link']
        self.clear_temp_file()
        backup_duration = datetime.datetime.now() - start_timing_backup
        print("Backup gerado em",backup_duration.total_seconds(),"segundos")
        #print("Arquivo disponivel em "+link)
        #print("Nome: "+name)
        #print("Tamanho em bytes: "+str(size))
        #print("Pasta compartilhada: "+link_folder)
        return backup

    def create_backup_local(self):
        metadata = {}
        start_timing_backup = datetime.datetime.now()
        django.setup()
        call_command('dbbackup', '-v', '1', '-z')
        temp_file = settings.DBBACKUP_STORAGE_OPTIONS['location'] + '/temp.dump.gz'
        time = datetime.datetime.now()
        basename = shutil.copy(temp_file, 'data/backup/' + time.strftime("%Y%m%d%H%M%S") + '.dump.gz')
        new_filename = os.path.basename(basename)
        #print(new_filename)
        size = os.path.getsize(basename)
        #print(size)
        metadata['file_name'] = new_filename
        metadata['size'] = size
        #print(metadata)
        self.clear_temp_file()
        backup_duration = datetime.datetime.now() - start_timing_backup
        print("Backup gerado em",backup_duration.total_seconds(),"segundos")
        return metadata

    def restore_backup(self):
        from django.contrib.contenttypes.models import ContentType
        restore_file = DBBACKUP_STORAGE_OPTIONS['location'] + '/restore.json'
        try:
            os.remove(restore_file)
        except OSError:
            pass
        self.dropbox = dropbox.Dropbox(DROPBOX_OAUTH2_TOKEN)
        start_timing_backup = datetime.datetime.now()
        list_files = self.dropbox.files_list_folder(DROPBOX_ROOT_PATH)
        #print(list_files.entries[-1].path_display)
        most_recent_backup = self.download(list_files.entries[-1].path_display)
        print("Arquivo mais recente: ",list_files.entries[-1].path_display)
        django.setup()
        call_command('flush', '--no-input')

        ContentType.objects.all().delete()

        #call_command('dbrestore', '-v','0', '-i', 'temp.dump.gz', '-z', '-q','--noinput')
        #call_command('dbrestore', '-v', '0', '-i', 'temp.dump.gz', '-z', '--noinput')
        #self.clear_temp_file()

        call_command('loaddata', restore_file)

        backup_duration = datetime.datetime.now() - start_timing_backup
        print("Backup Restaurado em", backup_duration.total_seconds(), "segundos")
        #self.clear_temp_file()
        return True

    def list_backup(self):
        #print('\n')
        foldersize = []
        self.dropbox = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)
        self.dt = self.dropbox.files_list_folder(settings.DROPBOX_ROOT_PATH)
        for entry in self.dropbox.files_list_folder(settings.DROPBOX_ROOT_PATH).entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                foldersize.append(entry.size)
        foldersize = '{0:.2f}'.format(sum(foldersize)/1024)
        #print(foldersize)
        metadata = []
        for entry in self.dt.entries:
            data = {}
            filename = entry.name
            display = entry.name
            path_name = entry.path_lower
            size = entry.size
            filesize = '{0:.2f}'.format(size/1024)
            #print(filesize)
            #print(int(float(filesize)))
            link = self.dropbox.sharing_create_shared_link(path_name)  # Mesmo estando obsoleto,esse é o único modo de retornar o link de arquivos já compartilhados...
            url = link.url
            #dl_url = re.sub(r"\?dl\=0", "?dl=1", url)
            modified = entry.client_modified
            time = datetime.timedelta(hours=2)
            hora = datetime.datetime.strptime(str(modified), '%Y-%m-%d %H:%M:%S')
            now = hora - time
            #print(display, now , filesize, '\n'+url)
            data['file_name'] = filename
            data['link'] = url
            data['client_modified'] = now#entry.client_modified
            data['size'] = filesize
            data['folder_size'] = foldersize
            metadata.append(data)
        #print(metadata)
        #print(data)
        return metadata

    def download(self, file):
        self.file = (file)
        self.file.replace('/backup/', '')
        try:
            metadata, res = self.dropbox.files_download(self.file)
        except Exception as erro:
            print("Erro! ", erro)

        final_path = settings.DBBACKUP_STORAGE_OPTIONS['location'] + '/temp.dump.gz'
        f = open(final_path, "wb")
        f.write(res.content)
        f.close()
        return final_path

    def download_last_file(self):
        self.dropbox = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)
        list_files = self.dropbox.files_list_folder(settings.DROPBOX_ROOT_PATH)
        most_recent_backup = self.download(list_files.entries[-1].path_display)
        return most_recent_backup

    def shared_folder(self):
        self.data = []
        data = {}
        self.dropbox = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)
        #link = self.dropbox.sharing_create_shared_link_with_settings(DROPBOX_ROOT_PATH)
        link = self.dropbox.sharing_create_shared_link(settings.DROPBOX_ROOT_PATH)  # Mesmo estando obsoleto,esse é o único modo de retornar o link de arquivos já compartilhados...
        shared_link = link.url
        #print('\n',shared_link)
        #return shared_link
        data['folder_link'] = link.url
        return data

    def upload(self):
        root_path = sys.argv[0].replace('manage.py','')
        self.data = []
        data = {}
        temp_file = settings.DBBACKUP_STORAGE_OPTIONS['location']+'/temp.dump.gz'
        time = datetime.datetime.now()
        now = time.strftime("%p")
        if now == 'AM':
            now = 'mat'
        elif now == 'PM':
            now = 'vesp'
        dias = ('seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom')
        hj = date.today()
        dia = dias[hj.weekday()]
        #shutil.copy(temp_file,'data/backup/'+time.strftime("%a"+"_"+"%Y%m%d%I%M%S"+"_"+"%p")+".dump.gz")
        #export_name = DROPBOX_ROOT_PATH+'/'+time.strftime("%a"+"_"+"%Y%m%d%I%M%S"+"_"+"%p")+".dump.gz"
        shutil.copy(temp_file,root_path+'/data/backup/'+time.strftime(dia+"_"+now)+".dump.gz")
        export_name = settings.DROPBOX_ROOT_PATH+'/'+time.strftime(dia+"_"+now)+".dump.gz"
        with open(temp_file, 'rb') as f:
            self.dropbox.files_upload(f.read(), export_name, mode=dropbox.files.WriteMode('overwrite'))
        try:
            link = self.dropbox.sharing_create_shared_link_with_settings(export_name)
        except:
            link = self.dropbox.sharing_create_shared_link(export_name)
        file_metadata = self.dropbox.files_get_metadata(export_name)
        print(file_metadata)
        url = link.url
        dl_url = re.sub(r"\?dl\=0", "?dl=1", url)
        data['file_name'] = file_metadata.name
        data['link'] = dl_url
        data['client_modified'] = file_metadata.client_modified
        data['size'] = int(file_metadata.size)
        data['folder_link'] = self.shared_folder()
        return data

    def delete_file(self,file=''):
        self.dropbox = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)
        path = settings.DROPBOX_ROOT_PATH + "/20171221120127.dump.gz"
        self.dropbox.files_delete_v2(path)

    def clear_temp_file(self):
        backup_file = settings.DBBACKUP_STORAGE_OPTIONS['location'] + '/temp.dump.gz'
        if os.path.isfile(backup_file):
            os.remove(backup_file)

    def schedule_backup(self):
        print('test')





if __name__=='__main__':
    arguments = sys.argv
    backup_manage = BackupManager()
    if "create" in arguments:
        backup_manage.create_backup()
    elif "create_local" in arguments:
        backup_manage.create_backup_local()
    elif "restore" in arguments:
        backup_manage.restore_backup()
    elif "list" in arguments:
        backup_manage.list_backup()
    elif "shared" in arguments:
        backup_manage.shared_folder()
    elif "delete" in arguments:
        backup_manage.delete_file()
    elif "share_folder" in arguments:
        backup_manage.user_profile()
    elif "schedule" in arguments:
        backup_manage.schedule_backup()
    else:
        pass"""
