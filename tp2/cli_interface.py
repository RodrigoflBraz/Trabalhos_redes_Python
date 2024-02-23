import socket

ip_servidor= "127.0.0.1"
porto_servidor= 20001
bufferSize= 2048

msgServer= "Conectado"
bytesToSend= str.encode(msgServer)

#criar o datagrama de socket
UdpSocketServidor = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

UdpSocketServidor.bind((ip_servidor, porto_servidor))

while(True):

    bytesAddressPair = UdpSocketServidor.recvfrom(bufferSize)
    message = bytesAddressPair[0]
    address = bytesAddressPair[1]

    clientMsg = "Messagem para roteador:{}".format(message)
    clientIP  = "Ip do roteador:{}".format(address)
    
    print(clientMsg)
    print(clientIP)

    UdpSocketServidor.sendto(bytesToSend, address)
