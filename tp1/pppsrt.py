#################################################################
# pppsrt.py - protocolo ponto-a-ponto simples com retransmissão
#           - entrega interface semelhante a um socket
#################################################################
# fornece a classe PPPSRT, que tem os métodos:
#
# contrutor: pode receber um ou dois parâmetros, para criar um
#            canal que implementa o protocolo PPPSRT;
#            - o servidor cria o objeto apenas com o porto;
#            - o cliente cria o objeto com host e porto.
# close: encerra o enlace
# send(m): envia o array de bytes m pelo canal, calculando o 
#           checksum, fazendo o enquadramento e controlando a
#           retransmissão, se necessário.
# recv(): recebe um quadro e retorna-o como um array de bytes,
#         conferindo o enquadramento, conferindo o checksum e
#         enviando uma mensagem de confirmação, se for o caso.
# OBS: o tamanho da mensagem enviada/recebida pode variar, 
#      mas não deve ser maior que 1500 bytes.
################################################################
# PPPSRT utiliza o módulo dcc023_tp1 como API para envio e recepção
#        pelo enlace; o qual não deve ser alterado.
# PPPSRT não pode utilizar a interface de sockets diretamente.
################################################################

import dcc023_tp1
import time

frame_num = 0
tam_send = 0
ack_atual = bytes('', encoding = 'utf-8')


#def get_ack(quadro_numberack):
    #quadro = 0
    #quadro = str(quadro_numberack)
    #quadro_ack = bytes(quadro, encoding = 'utf-8')
    #FLAG = bytes('126', encoding = 'utf-8')
    #ADDRESS = bytes('255', encoding = 'utf-8')
    #CONTROL_ACK = bytes('7', encoding = 'utf-8')
    #ack_quadro = FLAG + ADDRESS + CONTROL_ACK + quadro_ack + FLAG
    #return ack_quadro

def encapsular(arquivo, quadro_num, checksum_number ,data = 1):
    
    quadro_num = str(quadro_num)
    checksum_num = str(checksum_number)
    
    protocol = bytes(quadro_num, encoding = 'utf-8')
    checksum_byte = bytes(checksum_num, encoding = 'utf-8')
    FLAG = bytes('126', encoding = 'utf-8')
    ADDRESS = bytes('255', encoding = 'utf-8')
    CONTROL_DATA = bytes('3', encoding = 'utf-8')
    CONTROL_ACK = bytes('7', encoding = 'utf-8')
    
    
    if data:
        retorno = FLAG + ADDRESS + CONTROL_DATA + protocol +  arquivo + checksum_byte + FLAG
        return retorno
    else:
        retorno = FLAG + ADDRESS + CONTROL_ACK + protocol + arquivo + checksum_byte + FLAG
        return retorno

def desencapsular(arquivo,  quadro_num, data = 1):
    
    quadro_num = str(quadro_num)
    flag = '@'
    
    flag_checksum = bytes(flag, encoding = 'utf-8')
    protocol = bytes(quadro_num, encoding = 'utf-8')
    FLAG = bytes('126', encoding = 'utf-8')
    ADDRESS = bytes('255', encoding = 'utf-8')
    CONTROL_DATA = bytes('3', encoding = 'utf-8')
    CONTROL_ACK = bytes('7', encoding = 'utf-8')
    
    len_protocol = len(protocol)
    len_flag= len(FLAG)
    len_address= len(ADDRESS) 
    len_data= len(CONTROL_DATA) 
    len_ack= len(CONTROL_ACK)
    
    if data:
        #remove o byte de flag
        flag_position = arquivo.find(FLAG)
        arquivo = arquivo[flag_position+len_flag:]
        
        #remove o byte de address
        address_position = arquivo.find(ADDRESS)
        arquivo = arquivo[address_position + len_address:]
        
        #remove o byte controle
        data_position = arquivo.find(CONTROL_DATA)
        arquivo = arquivo[data_position +len_data:]

        #remove os bytes de protocolo
        protocol_position = arquivo.find(protocol)
        arquivo = arquivo[protocol_position +len_protocol:]

        #remove o byte flag do final
        arquivo = arquivo[:len(arquivo) - len_flag]

        #remove a primeira flag do checksum
        arquivo = arquivo[:len(arquivo) - 1]
        
        #remove a segunda flag do checksum, e pega o checksum
        flagc_position = arquivo.find(flag_checksum, len(arquivo) - 4)
        eval_check = arquivo[flagc_position+1:]
        arquivo = arquivo[0:flagc_position - 1]
        return arquivo
    
    else:
        flag_position = arquivo.find(FLAG)
        arquivo = arquivo[flag_position+len_flag:]
        
        address_position = arquivo.find(ADDRESS)
        arquivo = arquivo[address_position +len_address:]
        
        ack_position = arquivo.find(CONTROL_ACK)
        arquivo = arquivo[ack_position +len_ack:]

        protocol_position = arquivo.find(protocol)
        arquivo = arquivo[protocol_position +len_protocol:]

        arquivo = arquivo[:len(arquivo) - len_flag]
        
        return arquivo
    


def checksum(arquivo, checksum = 0):
    checksum = 0
    tam_arquivo = len(arquivo)
    for byte in range(tam_arquivo):
        checksum = checksum + arquivo[byte]
    checksum = checksum % 256
    
    #adicionando uma flag ao checksum, para facilitar encontrar (como no desecncapsulamento o checksum fica no final após a remoção da flag, só terá ocorrencia dessa string no final do pacote quando realmente for o checksum, logo não é necessário se fazer byte stuffing)
    checksum = str(checksum)
    checksum = "@" + checksum + "@"
    return checksum

def eval_checksum(arquivocheck, number_check):
    number_check = int.from_bytes(number_check, "big")
    dechecksum = 0
    tam_arquivocheck = len(arquivocheck)
    for byte in range(tam_arquivocheck):
        dechecksum = dechecksum + arquivocheck[byte]
    dechecksum = dechecksum - number_check
    return dechecksum
    

class PPPSRT:
  
    def __init__(self, port, host='' ):
        self.link = dcc023_tp1.Link(port,host)

    def close(self):
        self.link.close()
        
####################################################################
# A princípio, só é preciso alterar as duas funções a seguir.
  
    def send(self,message):
        # Aqui, PPSRT deve fazer:
        #   - fazer o encapsulamento de cada mensagem em um quadro PPP,
        #   - calcular o Checksum do quadro e incluído,
        #   - fazer o byte stuffing durante o envio da mensagem,
        #   - aguardar pela mensagem de confirmação,
        #   - retransmitir a mensagem se a confirmação não chegar.
        len_payload = 1500
        num_payload = 0
        len_arquivo = len(message)
        
        global tam_send
        global ack_atual

        if len_arquivo<=len_payload:
            num_payload = 1
        else:
            if len_arquivo % len_payload != 0 :
                num_payload = (len_arquivo // len_payload) + 1
            else: 
                num_payload = len_arquivo // len_payload

        for pacote in range (num_payload):
            payload = message[pacote * len_payload : (pacote * len_payload) + len_payload]
            checksum_num = checksum(payload)
            send_pacote = encapsular(payload, pacote, checksum_num)
            tam_send = len(send_pacote)
            self.link.send(send_pacote)
            time.sleep(5)
            ack_str = str(pacote)
            ack_verify = bytes(ack_str, encoding = 'utf-8')
            
            if(ack_verify not in ack_atual and pacote == 52525525):
                print('erro na transmissao, recomecar')
                self.link.send(message)
                break

            
    def recv(self):
        # Aqui, PPSRT deve fazer:
        #   - identificar começo de um quadro,
        #   - receber a mensagem byte-a-byte, para retirar o stuffing,
        #   - detectar o fim do quadro,
        #   - calcular o checksum do quadro recebido,
        #   - descartar silenciosamente quadros com erro,
        #   - enviar uma confirmação para quadros recebidos corretamente,
        #   - conferir a ordem dos quadros e descartar quadros repetidos.
        global frame_num
        global tam_send
        global ack_atual
        
        
        FLAG_ack = bytes('126', encoding = 'utf-8')
        ADDRESS_ack = bytes('255', encoding = 'utf-8')
        CONTROL_ACK_ack = bytes('7', encoding = 'utf-8')


        try:            
            frame = self.link.recv(15000)
            #identifica se é um bloco verificando a flag no inicio e fim e desencapsula a mensagem e manda o ACK
            if (len(frame)!= 0) and frame.startswith(FLAG_ack) and frame.endswith(FLAG_ack):
                frame = desencapsular(frame, frame_num)
                frame_num+=1
                quadro_ack = str(frame_num)
                quadro_ack_ack = bytes(quadro_ack, encoding = 'utf-8')
                ack_z_ack = FLAG_ack + ADDRESS_ack + CONTROL_ACK_ack + quadro_ack_ack + FLAG_ack
                ack_atual = ack_z_ack

            
        except TimeoutError: # use para tratar temporizações
            print("Timeout")
        return frame
