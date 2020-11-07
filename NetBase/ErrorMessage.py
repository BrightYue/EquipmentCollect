
class ConnectResult(object):
    SUCESS = 0
    ERROR = 1046
    def __init__(self):
        self.msg = ''   # 连接结果消息
        self.result = None  # 连接返回的socket