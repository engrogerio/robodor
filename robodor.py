from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import BytesIO
import requests
import datetime
from datetime import datetime as dt
import time
import numpy as np
import smtplib, ssl
import logging
import json
import os


BASE_DIR = os. getcwd() 

with open(os.path.join(BASE_DIR, 'config.json'), 'r') as f:
    config = json.load(f)

logging.basicConfig(filename=os.path.join(BASE_DIR, 'robo.log'), format='%(asctime)s %(message)s', level=logging.INFO)

def send_mail(email, message):
    # https://realpython.com/python-send-email/
    sent = True
    port = 465  # For SSL
    smtp_server = config['smtp_server']
    sender_email = config['sender_email']  
    password = config['password']
    receiver_email = email

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
    except Exception as ex:
        logger.error(ex)
        print(ex)
        sent = False
    return sent

def days_between(d1, d2):
    return np.busday_count(d1, d2)

def get_nu_diario():
    #return dt.now().strftime("%Y%m%d")
    return '20240314'

def pdf_to_text(path):
    manager = PDFResourceManager()
    retstr = BytesIO()
    layout = LAParams(all_texts=True)
    device = TextConverter(manager, retstr, laparams=layout)
    filepath = open(path, 'rb')
    interpreter = PDFPageInterpreter(manager, device)

    for page in PDFPage.get_pages(filepath, check_extractable=True):
       interpreter.process_page(page)

    text = retstr.getvalue()
    filepath.close()
    device.close()
    retstr.close()
    return text


def get_pdf_file(url, tmp_file_path):
    response = requests.get(url)
    exists = False
    if len(response.text)>0:
        with open(tmp_file_path, 'wb') as f:
            f.write(response.content)
        exists = True
    return exists

def start():
    logging.info("***** ROBODOR STARTING @ %s - DO number %s ******" % (datetime.datetime.now(), get_nu_diario()))
    start_total = time.time()
    nu_diario = get_nu_diario()
    print("********", nu_diario)

    with open(os.path.join(BASE_DIR, 'tasks.json'), 'r') as f:
        tasks = json.load(f)
    
    url = f'https://www.imprensaoficial.com.br/downloads/pdf/edicao/{nu_diario}LG.pdf'
    # url='https://dje.tjsp.jus.br/cdje/getPaginaDoDiario.do?cdVolume=13&nuDiario=%s&cdCaderno=10&nuSeqpagina=%s' %(nu_diario, page) 
    path = os.path.join(BASE_DIR, f'do_{nu_diario}.pdf')
    start_download = time.time()
    logging.info(f'Downloading document from {url}')
    has_content = get_pdf_file(url, path)
    logging.info('Document took %s seconds' %(time.time()-start_download))

    if has_content:
        text = str(pdf_to_text(path), encoding = 'utf-8')
        print(text)
        for task in tasks['buscas']: 
            print(task)
            search_string = task['name']
            email = task['email']
            start_search = time.time()
            logging.info(f'Searching {task["name"]} on document {nu_diario}')
            if search_string in text:
                logging.info("Search took %s seconds" % (time.time() - start_search))
                logging.info("######## STRING FOUND #########")
                logging.info("### Sending email ###")
                s = send_mail(email, f'Nome: {search_string} foi encontrado no DO: {url}' )
                if s:
                    logging.info("Email Sent !")
                    logging.info("### Robodor mission complete ###")
                else:
                    logging.warning("Oops...For some reason, the email was not sent... sorry :-(")
            else:
                logging.info(f'String not found on document from {nu_diario}. Search took {time.time() - start_search} seconds.')
    else:
        logging.warning("It looks like there is no DO issue today. Try tomorrow")

if __name__ == '__main__':
    start()

