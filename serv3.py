from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, emit
import time
import serial
import random
import asyncio
import RPi.GPIO as GPIO
from smbus2 import SMBus
import threading
import psycopg2
from datetime import datetime,date
import os
from form import MyForm, csrf

#global c 
data=''

app = Flask(__name__)
app.config['SECRET_KEY'] = '@11tahe89'
socketio = SocketIO(app)
 
 
@app.route('/')
def index(name=None):
    return render_template('index.html', name=name)



@app.route('/readdb', methods=('GET', 'POST'))
def data_form_bd():
    potsoma=0
    print('entrou readbd')
    form = MyForm()
    if form.validate_on_submit():
        print('entrou no if do form')
        data_inicio=form.data_inicio.data
        data_fim=form.data_fim.data
        hora_inicio=form.hora_inicio
        hora_final=form.hora_final
        dias=abs((data_fim-data_inicio).days)
        tempo= int(dias)*(60*12*24)
        print('SUBMIT')
        print(data_inicio)
        print(data_fim)
        print(dias)
        try:
            conn = psycopg2.connectcon = psycopg2.connect(host='localhost', database='teste',user='pi', password='root')
            cur = conn.cursor()
            print('BANCO CONECTADO!')
        except (Exception, psycopg2.Error) as error :
            print ("Error while connecting to PostgreSQL", error)
        finally:
            conn = psycopg2.connect(host='localhost', database='teste',user='pi', password='root')
            cur = conn.cursor()
            cur.execute("select potencia FROM consumo WHERE (data_event BETWEEN %s AND %s)",(data_inicio, data_fim))
            data_dif=cur.fetchall()
            #print(data_dif)
            cur.close()
            conn.close()
            vet=[]
            for i in data_dif:
                a= str(i).strip("('").strip("')',")
                b=float(a)
                vet.append(b)
                potsoma=sum(vet)
                potsoma=round(potsoma,3)
                potsoma=potsoma/tempo
                print('potsoma= ', potsoma)
                
                @socketio.on('potsoma2')
                def enviapotbd(pot2):
                    print('entrei na funcao envia')
                    print(pot2)
                    emit('potsoma2',potsoma)
    else:
        print('FALHA NA VALIDACAO DO FORMULARIO!')
    
    return render_template('grafico.html', form=form)


@socketio.on('menssagem')
def potencia(data):    
    # Open i2c bus 1 and read one byte from address 80, offset 0
    bus = SMBus(1)   
    tensaoStr=''
    correnteStr= ''
    tensaoArray=[]
    correntArray=[]
    print(data)
    try:
	    con = psycopg2.connect(host='localhost',database='teste',user='pi',password='root')
    except:
        print('Falha ao conectar com o banco!')
    while True:
               
        try:
            tensaoArray = bus.read_i2c_block_data(0x18,0,6)
            correnteArray = bus.read_i2c_block_data(0x17,0,6)
            print("i2c corrente-array:", correntArray)
            print("i2c tensão-array:", tensaoArray)
            time.sleep(0.5)
        except:
            print('I2C tentativa 2 ...')
            tensaoArray = bus.read_i2c_block_data(0x18,0,6)
            correnteArray = bus.read_i2c_block_data(0x17,0,6)
            print("i2c corrente-array:", correntArray)
            print("i2c tensão-array:", tensaoArray)
            time.sleep(0.5)
        finally:
            for i in range(6):
                tensaoStr += chr(tensaoArray[i])
                correnteStr += chr(correnteArray[i])
                

            tensao=float(tensaoStr)
            tensao=round(tensao,3)
            tensaoStr=str(tensao)
            corrente=float(correnteStr)
            corrente=round(corrente,3)
            correnteStr=str(corrente)
            potenciafloat = tensao*corrente        
            potencia=round(potenciafloat,3)
            potenciaStr=str(potencia)
            print('V:',tensao)
            print('A:',corrente)
            tensaoStr = ''
            correnteStr =''
            time.sleep(1)
            print('W: ',potenciaStr)
            emit('menssagem2', potenciaStr)
            
                    

'''def insere_bd():	
    bus = SMBus(1)
    tensaoStr=''
    correnteStr=''
    erro=1
    try: 
        con = psycopg2.connect(host='localhost', database='teste', user='pi', password='root')
    except:
        print('Falha ao conectar com o banco!')     
    
    while True:
        time.sleep(5)
        try:
            tensaoArray = bus.read_i2c_block_data(0x18,0,6)
            #print("i2c tensão-array")
            time.sleep(0.5)
        except:
            tensaoArray = bus.read_i2c_block_data(0x18,0,6)
        try:
            correnteArray = bus.read_i2c_block_data(0x17,0,6)
            #print("i2c corrente-array")
            time.sleep(0.5)
        except:
            correnteArray = bus.read_i2c_block_data(0x17,0,6)
        for i in range(6):
            tensaoStr += chr(tensaoArray[i])
            correnteStr += chr(correnteArray[i]
        
        tensao = float(tensaoStr)
        tensao=round(tensao,3)
        tensaoStr=str(tensao)
        corrente=float(correnteStr)
        corrente=round(corrente,3)
        correnteStr=str(corrente)
        potenciafloat = tensao*corrente
        potencia=round(potenciafloat,3)
        potenciaStr=str(potencia)
	if potencia > 0:
        now = datetime.now()
	    hora = now.strftime("%H:%M")
	    date = now.strftime("%Y-%m-")
	    cur = con.cursor()
	    cur.execute("INSERT INTO consumo (potencia, tensao, corrente, data_event, hora)VALUES(%s,%s,%s,%s,%s)",(potenciaStr,tensaoStr,correnteStr,date, hora))
	    con.commit()
	    tensaoStr = ''
	    correnteStr =''
	else:
	    print("ERROR: POTENCIA MENOR QUE ZERO")
	    continue   '''                
	
    
tpotencia = threading.Thread(target=potencia)
#tinsere_bd = threading.Thread(target=insere_bd)


tpotencia.start()
#tinsere_bd.start()
         
if __name__ == '__main__':
    socketio.run(app, debug = True, host='0.0.0.0')
