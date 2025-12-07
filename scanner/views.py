import os
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')

from pyzbar.pyzbar import decode


from django.shortcuts import render
from .models import QRCode
import qrcode
from django.core.files.storage import FileSystemStorage
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
from PIL import Image


def generate_qr(request):
    qr_image_url = None
    if request.method == 'POST':
        mobile_number = request.POST.get('mobile_number')
        data = request.POST.get('qr_data')
        
        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            return render(request, 'scanner/generate.html', {'error': 'Please enter a valid 10-digit mobile number.'})  
        
        #generate qr code img with data and mobile number
        qr_content = f"{data}|{mobile_number}"
        qr = qrcode.make(qr_content)
        qr_img_io = BytesIO() #create a BytesIO object to save the image
        #save the qr code image to the BytesIO object
        qr.save(qr_img_io, format='PNG')
        qr_img_io.seek(0) #move the cursor to the beginning of the BytesIO object
        
        #save the qr code image to the media folder
        qr_storage_path = Path(settings.MEDIA_ROOT) / 'qr_codes' 
        fs = FileSystemStorage(location=qr_storage_path, base_url='/media/qr_codes/')
        
        filename = f"{data}_{mobile_number}.png"
        qr_image_content = ContentFile(qr_img_io.read(), name=filename)
        file_path = fs.save(filename, qr_image_content)
        qr_image_url = fs.url(filename)
        
        #save the qr code details to the database
        QRCode.objects.create(mobile_number=mobile_number, data=data, qr_image=file_path)
    return render(request, 'scanner/generate.html', {'qr_image_url': qr_image_url})

def scan_qr(request):
    results = None
    if request.method == 'POST' and request.FILES.get('qr_image'):
        mobile_number = request.POST.get('mobile_number')
        qr_image = request.FILES['qr_image']

        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            return render(request, 'scanner/scan.html', {'error': 'Please enter a valid 10-digit mobile number.'})

        fs = FileSystemStorage()
        filename = fs.save(qr_image.name, qr_image)
        image_path = Path(fs.location) / filename

        try:
            image = Image.open(image_path)
            decoded_objects = decode(image)

            if not decoded_objects:
                results = "No QR code found in the image."
                return render(request, 'scanner/scan.html', {'results': results})

            # extract QR contents
            qr_content = decoded_objects[0].data.decode('utf-8').strip()
            qr_data, qr_mobile_number = qr_content.split('|')

            # check DB
            qr_entry = QRCode.objects.filter(data=qr_data, mobile_number=mobile_number).first()

            if qr_entry:
                results = f"QR Code is valid. Data: {qr_data}, Mobile Number: {qr_mobile_number}"

                # delete DB entry
                qr_entry.delete()

                # delete QR image file
                qr_image_path = Path(settings.MEDIA_ROOT) / 'qr_codes' / f'{qr_data}_{qr_mobile_number}.png'
                if qr_image_path.exists():
                    qr_image_path.unlink()

            else:
                results = "QR Code is invalid or does not match the provided mobile number."

        except Exception as e:
            results = f"Error processing image: {str(e)}"

        finally:
            # always delete the uploaded scan image
            if image_path.exists():
                image_path.unlink()

    return render(request, 'scanner/scan.html', {'results': results})
