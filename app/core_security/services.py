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
        pass

