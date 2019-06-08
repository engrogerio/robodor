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

with open('passwd.json', 'r') as f:
    config = json.load(f)

logging.basicConfig(filename='/home/ubuntu/invent/robodor/robo.log', format='%(asctime)s %(message)s', level=logging.WARNING)


def send_mail(email, link):
    # https://realpython.com/python-send-email/
    sent = True
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "eng.rogerio@gmail.com"  # Enter your address
    receiver_email = email  # Enter receiver address
    password = config["password"]
    message = """\
Subject: Voce foi nomeado para o cargo de Escrevente 
        
Leo, consulte a sua nomeacao no link do Diario Oficial abaixo: \n %s \n 
\n P A R A B E N S !!! \n \n Mensagem enviada pelo Robodor.""" % link

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
    except:
        sent = False
    return sent

def days_between(d1, d2):
    return np.busday_count(d1, d2)

def get_nu_diario():
    today = dt.today().strftime("%Y-%m-%d") 
    # nuDiario = 2820 is from 2019-05-31 (Friday)
    # It increments Mon through Fri.
    nu_diario = days_between('2019-05-31', today)  + 2820 - 1
    return nu_diario

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
    logging.warning("***** ROBODOR STARTING @ %s - DO number %s ******" % (datetime.datetime.now(), get_nu_diario()))
    print("***** ROBODOR STARTING @ %s - DO number %s ******" % (datetime.datetime.now(), get_nu_diario()))
    start_total = time.time()
    nu_diario = get_nu_diario()
    page = 0
    while True:
        page = page + 1
        url='https://dje.tjsp.jus.br/cdje/getPaginaDoDiario.do?cdVolume=13&nuDiario=%s&cdCaderno=10&nuSeqpagina=%s' %(nu_diario, page) 
        path ='/home/ubuntu/invent/robodor/temp_pdf/do_%s.pdf'% (nu_diario)
        email = 'lglopesp@gmail.com.br'
        start_download = time.time()
        logging.warning("Downloading page %s" % page)
        print("Downloading page %s..." %page)
        has_content = get_pdf_file(url, path)
        logging.warning("page %s takes %s seconds" %(page, time.time()-start_download))

        if has_content:
            text = str(pdf_to_text(path), encoding = 'utf-8')
            search_string = 'Leonardo Gurgel Lopes Pereira'
            start_search = time.time()
            logging.warning('Searching page %s' % page)
            print("Searching page...")
            if search_string in text:

                logging.warning("Search takes %s seconds" % (time.time() - start_search))
                logging.warning("######## STRING FOUND #########")
                logging.warning("### Sending email ###")
                s = send_mail(email, url)
                if s:
                    logging.warning("Email Sent !")
                    logging.warning("### Robodor mission complete ###")
                else:
                    logging.warning("Oops...For some reason, the email was not sent... sorry :-(")
                # Turn off crontab
                break

            else:
                logging.warning("String not found :-( Search takes %s seconds." %(time.time() - start_search))
                print("String not found.")
        else:
            if page > 1:
                logging.warning("Last page was scrapped: %s" % page)
                logging.warning("Job finished in %s seconds. See you tomorrow !" % (time.time() - start_total))
                print("Job finished in %s seconds" % (time.time() - start_total))
            else:
                logging.warning("It looks like there is no DO issue today. Try tomorrow")
            break

start()
