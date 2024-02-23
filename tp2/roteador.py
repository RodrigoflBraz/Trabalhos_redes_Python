import socket

msgRoteador      = "Roteador Conectado"
bytesEnvio        = str.encode(msgRoteador)
serverAddressPort   = ("127.0.0.1", 20001)
bufferSize          = 2048

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

UDPClientSocket.sendto(bytesEnvio, serverAddressPort)

msgFromServer = UDPClientSocket.recvfrom(bufferSize)

 

msg = "Menssagem do roteador {}".format(msgFromServer[0])
print(msg)