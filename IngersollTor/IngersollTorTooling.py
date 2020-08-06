import socket
import subprocess
import time
import threading

class Model():
    equipmentlist = [('10.50.147.195',502),('10.50.147.196',502),('10.50.147.197',502),('10.50.147.198',502),]
    messageinfo = '0000,0.0,P,0,P,0.0,0.0,0,0,0,1,'
class CONDIFG():
    SERVERIP = '0.0.0.0'
    PORT = 10089
class collection():
    data = {}

    def __init__(self, address):
        self.address = address
        self.so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.so.settimeout(25)
        self.isconnect = False

    @classmethod
    def setdata(cls, res):
        cls.data.update(res)
    def connectToServer(self):   #  此方法没必要进行调用，系统在Get的时候会自动调用重连接算法
        try:
            self.so.connect(self.address)
            self.isconnect = True
        except:
           self.GetNewSocketAndConnect()


    def getdatax(self):
        errorcheck = 0
        if self.GetNewSocketAndConnect():
            try:
                res = self.so.recv(1024).decode().split(',')
                if len(res) > 1:
                    if res[0] != '' or res[0] != ' ':
                        collection.setdata({self.address[0]: res})
                        errorcheck = 1
                        self.isconnect = True
                        return True , {self.address[0]: res}
            except:
                if errorcheck != 1:
                    self.isconnect = False
        return False, {self.address[0]: []}


    def GetNewSocketAndConnect(self):
        if self.isconnect == False:
            self.so.close()
            newso = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            newso.settimeout(30)
            while not self.getEquipmentStatus(self.address[0]):
                time.sleep(10)
                print('%s:连接已丢失！' % (self.address[0]))
            self.so = newso
            try:
                self.so.connect(self.address)
                self.isconnect = True
                return True
            except:
                print('连接失败，继续重连啊')
                self.isconnect = False
                return False
        else:
            return True

    def getEquipmentStatus(self, ip):
        res = subprocess.call('ping -w 3 {}'.format(ip), stdout=subprocess.PIPE, shell=True)
        if res == 0:
            return True
        else:
            return False

    class UserDefineException():
        class SockException(Exception):
            def __init__(self,address):
                self.address =  address
            def __str__(self):
                print(self.address +': socket异常，网络已经掉线了，每5S尝试重新连接！')

        class PortException(Exception):
            def __init__(self,address):
                self.address =  address
            def __str__(self):
                print(self.address +': 网络通，但可能端口不可用，断开Socket，20S后重新连接')


def getEquipmentStatus(ip):
    res = subprocess.call('ping -w 3 {}'.format(ip), stdout=subprocess.PIPE, shell=True)
    if res == 0:
        return True
    else:
        return False

def startCollectTr(client):
    cl = collection(client)
    while True:
        cl.getdatax()
def formatData():
    temp = ''
    res = ''
    for num in range(len(Model.equipmentlist)):
        if Model.equipmentlist[num][0] not in collection.data.keys():
            temp += Model.messageinfo
        else:
            for i in collection.data[Model.equipmentlist[num][0]]:
                temp += i + ','
        res += temp
        temp = ''
    return res



def sendMessage(client, address):
    while True:
        if getEquipmentStatus(address[0]):
            client.send(formatData().encode())
        else:
            client.close()
            break
        time.sleep(4)
def TcpServer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((CONDIFG.SERVERIP,CONDIFG.PORT))
    server.listen(100)
    while True:
        client, address = server.accept()
        tr = threading.Thread(target= sendMessage, args=(client,address))
        tr.start()
if __name__ == '__main__':

    for client in Model.equipmentlist:
        tr = threading.Thread(target=startCollectTr,args=(client,))
        tr.daemon = True
        tr.start()
    tr = threading.Thread(target=TcpServer, )
    tr.daemon = True
    tr.start()
    while True:
        time.sleep(2)
        print(collection.data)
