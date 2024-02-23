import socket
import select
import queue as Queue
import struct
import sys
import argparse

#Função que monta o cabeçalho
def pack_cabecalho(tipo_msgm, origem_msg, destino_msg, num_seq):
    
    CABECALHO_FORMATO = 'HHHH'
    cabecalho = b''
    tamanho = 0
    
    t = tipo_msgm
    o = origem_msg
    d = destino_msg
    n = num_seq
   
    cabecalho = struct.pack(CABECALHO_FORMATO, t , o, d, n)
    return cabecalho

#Função que monta a Mensagem
def pack_mensagem(cabecalho, mensagem):
    mensagem = str(mensagem)
    tam_msg = 0
    tam_coded = b''
    msg = mensagem
    msg_coded = b''
    cabecalho_msg = cabecalho
    msg = mensagem.encode(encoding = 'ascii')
    tam_msg = len(msg)
    tam_coded = struct.pack('i', tam_msg)
    msg_coded = cabecalho_msg + tam_coded + msg
    
    return msg_coded

    #separar o cabeçalho
def get_cabecalho(dados):
    dados_decripted = b''
    cabecalho_formato = 'HHHH'
    dados_encripted = dados[0:8]
    cabecalho_decripted = struct.unpack(cabecalho_formato, dados_encripted)
    return cabecalho_decripted


#separar a mensagem
def get_mensagem(dados_msg):
    dados_encodados = dados_msg[12:]
    dados_desencodados = b''
    dados_desencodados = dados_encodados.decode(encoding = 'ascii')
    return dados_desencodados

#Tamanho mensagem
def get_size(dados_recebidos):
    tam_msg = dados_recebidos[8:12]
    tam_msg_decoded = struct.unpack('i', tam_msg)
    return tam_msg_decoded


def main(id:int, ip:str, porto: int):
    
    SERVER_ID = 65535
    num_sequencia = 0
    mensagem_envio = ''

    OK = 1
    ERRO = 2
    OI = 3
    FLW = 4
    MSG = 5

    cliente_id = id

    #Verificando se o CLIENT_ID esta dentro do padrão
    if cliente_id < 1 or cliente_id > 65534:
        print('Cliente ID inválido!!!!!!, escolher valor entre 1 a 65534')
        sys.exit()

    #fazendo conexão
    HOST = ip
    PORTO = porto
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORTO))

    #montando mensagem OI
    cabecalho = pack_cabecalho(OI, cliente_id, SERVER_ID, num_sequencia)
    s.send(cabecalho)

    #Verificando se a conexão foi estabelecida(''hand shake'')
    resposta = s.recv(8)
    tipo_resposta = struct.unpack('HHHH', resposta)

    if tipo_resposta[0] != 1:
        print('Não foi possível estabelecer conexão, use um userID diferente')
        sys.exit()
    else:
        print('OK')

    #HAND SHAKE feito corretamente, agora começar a aplicação
    while True:
        mensagem = input()
        if mensagem:
            #se for uma mensagem para sair do sistema, envie o FLW, espere o OK e saia.
            if mensagem == 'S' or mensagem == 's':
                mensagem_flw = pack_cabecalho(4, cliente_id, SERVER_ID, num_sequencia)
                s.send(mensagem_flw)
                resposta_flw = s.recv(8)
                resposta_decod = struct.unpack('HHHH', resposta_flw)
                if resposta_decod[0] == 1:
                    print('OK')
                    s.close()
                    sys.exit()
                else:
                    print('Erro na desconexao')
                    s.close()
                    sys.exit()
            
            elif mensagem[0] == 'm' or mensagem[0] == 'M':
                parametros = mensagem.split(' ', 2)
                
                #broadcast 1 pra todos
                if int(parametros[1]) == 0:
                    cabecalho_broad = pack_cabecalho(5, cliente_id, 0, num_sequencia)
                    mensagem_broad = pack_mensagem(cabecalho_broad, parametros[2])
                    s.send(mensagem_broad)
                    resposta_broad = s.recv(8)
                    resposta_broad_decode = struct.unpack('HHHH', resposta_broad)
                    
                    if resposta_broad_decode[0] == 1:
                        print('OK')
                        num_sequencia +=1
                        continue
                    else:
                        print('Erro ao enviar broadcast')
                        continue
                #anycast 1 pra 1
                else:
                    cabecalho_any = pack_cabecalho(5, cliente_id, int(parametros[1]), num_sequencia)
                    mensagem_any = pack_mensagem(cabecalho_any, parametros[2])
                    s.send(mensagem_any)
                    resposta_any = s.recv(8)
                    resposta_any_decode = struct.unpack('HHHH', resposta_any)
                    
                    if resposta_any_decode[0] == 1:
                        print('OK')
                        num_sequencia +=1
                        continue
                    else:
                        print('Erro ao enviar anycast')
                        continue
        try:
            while True:
                mensagem_recebida = s.recv()
                cabecalho_recebido = get_cabecalho(mensagem_recebida)
                mensagem_decode = get_mensagem(mensagem_recebida)
                print('Mensagem de {}: {}'.format(cabecalho_recebido[1], mensagem_decode))
                continue

        
        
        except:
            continue


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description= 'Cliente')
    parser.add_argument('ID', type= int)
    parser.add_argument('IP', type= str)
    parser.add_argument('PORTO', type= int)
    args = parser.parse_args()
    main(args.ID, args.IP, args.PORTO)