import gzip
import os
import base64
import tempfile
from django.conf import settings

"""
f = tempfile.NamedTemporaryFile(delete=False)
f.close()
f.name
"""

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")


class Encrypter:

    def __init__(self, key=settings.ENCRYPT_KEY):

        super(Encrypter, self).__init__()

        self.path = None
        self.key = key

    def encrypt(self, filepath):
        self.path = filepath
        filename = os.path.basename(self.path)
        FILE_ENC = os.path.join(settings.ENCRYPTED_FILE_PATH, filename + '.enc')
        file = self.ReadFile(self.path)
        enc_file = self.encode(self.key, file)
        with open(FILE_ENC, 'wb') as f:
            f.write(enc_file)
        self.compress_file = self.compress_all(FILE_ENC)
        return self.compress_file

    def compress_all(self, filepath):
        file = filepath + '.gz'
        with open(filepath, 'rb') as f:
            data = f.read()
        with gzip.open(file, 'wb') as gz:
            gz.write(data)
            os.remove(filepath)
        print('Arquivo compactado com sucesso!!!')
        return file

    def decrypt(self, filepath):
        self.path = filepath
        file_extract = self.extract_all(self.path)
        FILE_JSON = os.path.join(settings.DECRYPTED_FILE_PATH, file_extract).replace('.enc', '')
        file = self.ReadFile(file_extract)
        dec_file = self.decode(self.key, file)
        with open(FILE_JSON, 'w') as f:
            f.write(dec_file)
            os.remove(file_extract)
        return [dec_file, FILE_JSON]

    def extract_all(self, filepath):
        self.path = filepath
        filename = os.path.basename(self.path).replace('.gz', '')
        local_file = os.path.join(settings.DECRYPTED_FILE_PATH, filename)
        with gzip.open(self.path, 'rb') as gz:
            data = gz.read()
        with open(local_file, 'wb') as f:
            f.write(data)
        print('Arquivo extraído com sucesso!!!')
        return local_file

    def encode(self, key, clear):
        enc = []
        for i in range(len(clear)):
            key_c = key[i % len(key)]
            enc_c = (ord(clear[i]) + ord(key_c)) % 256
            enc.append(enc_c)
        return base64.urlsafe_b64encode(bytes(enc))

    def decode(self, key, enc):
        dec = []
        enc = base64.urlsafe_b64decode(enc)
        for i in range(len(enc)):
            key_c = key[i % len(key)]
            dec_c = chr((256 + enc[i] - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)

    def ReadFile(self, fileName):
        with open(fileName, 'r') as f:
            content = f.read()
        return content
