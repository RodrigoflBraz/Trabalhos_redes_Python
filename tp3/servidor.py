#Desenvolvido por: Rodrigo Felipe Lima Braz e Diego Santos Tomaz, as referências usadas estão num txt na pasta do projeto, denominado "ref"

import socket
import select
import sys
import queue
import struct
import argparse



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

#função que vai fazer o hand shake do SV (mensagem oi)
def hand_shake(client_socket):
    try:
        cabecalho = client_socket.recv(8)
        cabecalho_decoded = struct.unpack('HHHH', cabecalho)
        #se for uma mensagem diferente de 3 (oi), retorna falso.
        if cabecalho_decoded[0] != 3:
            return False
        else:
            return cabecalho_decoded

    except:
        return False

def enviar_ok(client_socket, id_destino, seq_numero = 0):
    ok_msg = struct.pack('HHHH', 1, id_destino, 65535, seq_numero)
    client_socket.send(ok_msg)

def enviar_erro(client_socket, id_destino, seq_numero = 0):
    erro_msg = struct.pack('HHHH', 2, id_destino, id_destino, seq_numero)
    client_socket.send(erro_msg)

def receber_mensagem(client_socket):
    receber_cabecalho = client_socket.recv(8)
    cabecalho_unpacked = struct.unpack('HHHH', receber_cabecalho)
    
    if cabecalho_unpacked[0] == 5:
        tamanho = client_socket.recv(4)
        tamanho_msg = struct.unpack('I', tamanho)
        mensagem_encodada = client_socket.recv(tamanho_msg[0])
        mensagem_final = mensagem_encodada.decode(encoding = 'ascii')
        #retorna um dicionário, com valor de cabeçalho = tupla de 4 elementos, e mensagem em data
        print('mensagem de {}: {}'.format(cabecalho_unpacked[1], mensagem_final))
        return {'header': cabecalho_unpacked, 'data': mensagem_final}
    
    elif cabecalho_unpacked[0] == 4:
        enviar_ok(client_socket, cabecalho_unpacked[1], cabecalho_unpacked[3])
        return False
    
    else:
        return False
    

    

def main(porto: int):

    OK = 1
    ERRO = 2
    OI = 3
    FLW = 4
    MSG = 5

    IP = '127.0.0.1'
    PORTO = porto
    SERVER_ID = 65535


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((IP, PORTO))
    s.listen()

    s_list = [s]
    clients = {}
    print(f'Esperando conexoes em {IP}:{PORTO}...')
    id_list = []


    while True:
        read_sockets, _, exception_sockets = select.select(s_list, [], s_list) 
        
        for s_ready in read_sockets:
            #se for uma nova conexão, aceite.
            if s_ready == s:
                client_socket, client_address = s.accept()
                #logo após o cliente vai mandar o oi, receba
                user = hand_shake(client_socket)
                
                #verifica se deu certo a conexão
                if user is False:
                    continue
                
                #verifica se o id já está sendo usado
                if user[1] in id_list:
                    enviar_erro(client_socket, user[1], user[3])
                    continue

                
                #colocar o socket do cliente na lista de sockets
                s_list.append(client_socket)
                clients[client_socket] = user[1]
                print(f'Nova conexao aceita de: {client_address}, id_client: {user[1]} .')
                id_list.append(user[1])

                enviar_ok(client_socket, user[1], SERVER_ID)
                continue
            
            #se for uma mensagem de uma conexão ativa, receba
            elif s_ready != s:
                menssagem = receber_mensagem(s_ready)
                if menssagem == False:
                    print(f'Desconectando id_client {user}')
                    s_list.remove(client_socket)
                    del clients[client_socket]
                    id_list.remove(user)
                    continue
                user = clients[s_ready]

                #se o destino for 0, faça broadcast;
                if menssagem['header'][2] == 0:
                    #remontando a mensagem
                    header_send = struct.pack('HHHH', menssagem['header'][0], menssagem['header'][1], menssagem['header'][2], menssagem['header'][3])
                    envio = pack_mensagem(header_send, menssagem['data'])
                    for client_socket in clients:
                        #verifica se não é o proprio cliente que enviou a mensagem
                        if client_socket != s_ready:
                            client_socket.send(envio)
                    enviar_ok(client_socket, menssagem['header'][1], menssagem['header'][3])      
                else:
                    if menssagem['header'][2] not in id_list:
                        enviar_erro(client_socket,menssagem['header'][1], menssagem['header'][3])
                        continue
                    else:
                        #remontando a mensagem
                        header_send = struct.pack('HHHH', menssagem['header'][0], menssagem['header'][1], menssagem['header'][2], menssagem['header'][3])
                        envio = pack_mensagem(header_send, menssagem['data'])
                        #procura o Cliente do ID requisitado e transmite a mensagem
                        for client_socket in clients:
                            if int(clients[client_socket]) == int(menssagem['header'][2]):
                                try:
                                    client_socket.send(envio)
                                    enviar_ok(client_socket, menssagem['header'][1], menssagem['header'][3])

                                
                                except:
                                    enviar_erro(client_socket,menssagem['header'][1], menssagem['header'][3])



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description= 'Servidor')
    parser.add_argument('PORTO', type= int)
    args = parser.parse_args()
    main(args.PORTO)