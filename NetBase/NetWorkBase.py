from socket import socket,AF_INET,SOCK_STREAM
from ErrorMessage import ConnectResult
class NetWork(object):
    """提供一个网络类，需具备：网络建立，返回可操作socket并且能够支持断线重连"""
    def __init__(self, ip, port):
        self.sock = None  # socket实例
        self.IsConnect = False # 连接状态标示
        self.address = (ip,port)  # 网络连接地址

    def Connect(self,connectTimeOut):
        """
        网络连接方法，返回连接后的socket
        :param connectTimeOut:
        :return:
        """
        connectResult = ConnectResult
        conn = socket(AF_INET, SOCK_STREAM)
        conn.settimeout(connectTimeOut)
        result = conn.connect_ex(self.address)  # 这里不在使用connect _ex 不会经过try 性能据说可以提高一倍
        if result == 0:   # 成功返回
            connectResult.msg = ConnectResult.SUCESS
            connectResult.result = conn
            self.IsConnect = True
        else:              # 失败返回
            connectResult.msg = ConnectResult.ERROR
            connectResult.result = None
            self.IsConnect = False
        self.sock = conn   #  返回给公用sock
        return connectResult
    def GetAvailableConnect(self,timeout = 10):
        """
        获取可用的Socket并返回，如果没有则尝试重新连接后返回
        :return: 返回ConnectResult 结构
        """
        result = ConnectResult()
        if self.IsConnect:  # 如果连接可用则返回sock
            result.result = self.sock
            result.msg = ConnectResult.SUCESS
            return result
        return self.Connect(connectTimeOut=timeout)  # 重连并返回结果


def test():
    a = NetWork('127.0.0.1',1023)
    print(a.GetAvailableConnect().msg,a.GetAvailableConnect().result)



if __name__ == '__main__':
    test()
