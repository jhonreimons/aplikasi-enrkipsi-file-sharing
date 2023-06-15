from django.shortcuts import render, redirect
from django.urls import reverse
from minio import Minio
from .models import User
from django.conf import settings
# from django.http import HttpResponse
from Crypto.PublicKey import RSA
from Crypto.PublicKey import ECC
from django.core.files.base import ContentFile
import time
import os
from django.http import FileResponse,HttpResponseRedirect, HttpResponse
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from Crypto.Cipher import PKCS1_OAEP, PKCS1_v1_5
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm

def example(request):
    return render(request, 'ftrans_app/example.html')
    
# User = get_user_model()

minio_client = Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_HTTPS,
    )

bucket_name=settings.MINIO_STORAGE_BUCKET_NAME

def file_list(request):

        objects = minio_client.list_objects(
        bucket_name=settings.MINIO_STORAGE_BUCKET_NAME,
        recursive=True,
        )

        files = []

        for obj in objects:
            size = obj.size
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            index = 0

            while size >= 1024 and index < len(units):
                size /= 1024
                index += 1

            if index >= len(units):
                index = len(units) - 1

            file_size_formatted = f'{size:.2f} {units[index]}'

            file_size = f"{file_size_formatted}"

            file_info = {
                'name': obj.object_name,
                'size' : file_size,
                'url': minio_client.get_presigned_url(
                    'GET',
                    settings.MINIO_STORAGE_BUCKET_NAME,
                    obj.object_name,
                ),
            }
            files.append(file_info)
        return render(request, 'ftrans_app/index.html', {'files': files})

def form_generate(request):
    if request.user.is_authenticated:
        return render(request, 'ftrans_app/generate_key.html')
    else:
        return redirect(reverse('ftrans_app:login'))


def generate_keys(passphrase):
    key = RSA.generate(2048)

    encrypted_key = key.exportKey(passphrase=passphrase)

    private_key = encrypted_key.decode('utf-')
    public_key = key.publickey().exportKey().decode('utf-8')

    return [public_key,private_key]

def generate_key_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        passphrase = request.POST.get('passphrase')
        # Panggil fungsi generate_keys untuk membuat kunci
        key = generate_keys(passphrase)
        user = User(username=username,email=email,public_key=key[0],private_key=key[1],passphrase=passphrase)
        user.save()
        # return HttpResponse(f"Private key: {key[0]} <br>Public key: {key[1]}")
    
    users = User.objects.order_by('-id')
    return render(request, 'ftrans_app/nama_template.html', { 'users' : users})

def encrypt_chunk(cipher, chunk):
    return cipher.encrypt(chunk)

def encrypt_file(request):
    if request.method == 'POST':
        chunk_size = 200 
        username = request.POST.get('username')
        name = request.POST.get('name')
        file_name = name
        data = minio_client.get_object(bucket_name, file_name)
        content = data.read()
        # content = content.encode()
        user = User.objects.get(username=username)
        public_key = user.public_key
        start_time = time.time()
        cipher = PKCS1_OAEP.new(RSA.import_key(public_key))
        encrypted_chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            encrypted_chunks.append(encrypt_chunk(cipher, chunk))

        encrypted_data = b''.join(encrypted_chunks)
        end_time = time.time()
        elapsed_time = end_time - start_time
        elapsed_time = round(elapsed_time, 2)
        data_size = len(encrypted_data)
        # Mendapatkan path file yang ingin Anda buka
        file_name = file_name + ".enc"
        file_path = f"files/{file_name}"
        with open(file_path, 'wb') as file:
            file.write(encrypted_data)
        
        file_size = os.path.getsize(file_path)
        user = User.objects.get(username=username)
        public_key = user.public_key
        info = {
            'elapsed_time': elapsed_time,
            'data_size': file_size,
            'file_name': file_name,
            'public_key': public_key
        }
    
        return render(request, 'ftrans_app/waktu_enkripsi.html',{'info': info})


def download_file(request):
    if request.method == 'POST':
        data = request.POST.get('file')
        file_name = request.POST.get('file_name')
        file_path = f"files/{file_name}"

        with open(file_path, 'rb') as file:
            encrypted_data = file.read()

        response = HttpResponse(encrypted_data , content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    else:
        return HttpResponse('Invalid request method', status=400)


def decrypt_file(request):
    if request.method == 'POST':
        chunk_size = 200 # Ubah ukuran chunk sesuai dengan ukuran yang digunakan pada fungsi encrypt_file
        private = request.POST.get('private')
        file = request.FILES.get('file')
        passphrase = request.POST.get('passphrase')
        file_name = ''
        if file is not None:
            file_name = file.name[:-4]# Menghilangkan ekstensi .enc pada nama file terenkripsi
            content = file.read()
            # content = base64.b64decode(content)
            username='ce320041'
            user = User.objects.get(username=username)
            private_key = user.private_key # Mengambil kunci privat pengguna
            # private_key = private
            # cipher = PKCS1_OAEP.new(RSA.import_key(private_key))
            cipher = PKCS1_OAEP.new(RSA.import_key(private_key, passphrase=passphrase))

            decrypted_data = b''
            # decrypted_data = cipher.decrypt(content)
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                padded_chunk = cipher.decrypt(chunk) # Menggunakan fungsi decrypt() untuk mendekripsi data
                decrypted_data += padded_chunk
                # Menyimpan file terdekripsi ke sistem file
                # decrypted_data = cipher.decrypt(content)
                with open(f"{file_name}", 'wb') as f:
                    f.write(decrypted_data)
                
            response = HttpResponse(content=decrypted_data, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            data = { 'success': True }
            response_data = json.dumps(data)
            response.content = response_data.encode()
            return response

    return render(request, 'ftrans_app/nama_template.html')

def dekripsi(request):
    return render(request,'ftrans_app/dekripsi.html')

def enkripsi(request):
    return render(request,'ftrans_app/enkripsi.html')

# def login_view(request):
#     return render(request,'ftrans_app/login.html')

def signup(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'ftrans_app/register.html', {'form': form})
    else:
        form = UserCreationForm()
        return render(request, 'ftrans_app/register.html', {'form': form})


def signin(request):
    if request.user.is_authenticated:
        return render(request, 'index.html')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/') #profile
        else:
            msg = 'Error Login'
            form = AuthenticationForm(request.POST)
            return render(request, 'ftrans_app/login.html', {'form': form, 'msg': msg})
    else:
        form = AuthenticationForm()
        return render(request, 'ftrans_app/login.html', {'form': form})


def signout(request):
    logout(request)
    return redirect('/')