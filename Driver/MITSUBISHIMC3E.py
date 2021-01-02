"""
驱动类默认仅提供驱动方法，不包含网络类，需在上层提供接口
"""
import io


class ProtocolModel():
    """
    添加各个类型的字段信息
    """
    M = b'\x90'
    SM = b'\x91'
    SD = b'\xA9'
    X = b'\x9C'
    Y = b'\x9D'
    L = b'\x92'
    F = b'\x93'
    V = b'\x94'
    B = b'\xA0'
    D = b'\xA8'
    W = b'\xB4'
    TS = b'\xC1'
    TN = b'\xC0'
    TC = b'\xC2'
    SS = b'\xC7'
    SC = b'\xC6'
    SN = b'\xC8'
    CS = b'\xC4'
    CC = b'\xC3'
    CN = b'\xC5'
    SB = b'\xA1'
    SW = b'\xB5'
    S = b'\x98'
    DX = b'\xA2'
    DY = b'\xA3'
    Z = b'\xCC'
    R = b'\xAF'
    ZR = b'\xB0'
    SoftModel = {'M': M, 'SM': SM, 'SD': SD, 'X': X, 'Y': Y, 'L': L, 'F': F, 'V': V,
                 'B': B, 'D': D, 'W': W, 'TS': TS, 'TN': TN, 'TC': TC, 'SS': SS, 'SC': SC,
                 'SN': SN, 'CS': CS, 'CC': CC, 'CN': CN, 'SB': SB, 'SW': SW, 'S': S, 'DX': DX,
                 'DY': DY, 'Z': Z, 'R': R, 'ZR': ZR}


class MainCommand(object):
    BATCHREAD = b'\x04\x01'  # 反转了字符，表示批量读取
    BATCHWRITE = b'\x14\x01'  # 反转了字符，表示批量写入
    RANDOMREAD = b'\x01\x03'  # 反转了字符，表示批量随机读取，不计划使用
    RANDOMWRITE = b'\x14\x02'  # 反转了字符 ，表示批量随机写入，不计划使用


class SlaveCommand(object):
    WORD = b'\x00\x00'  # 按照字为一个宽度读取
    BIT = b'\x00\x01'  # 按照位进行读取（反应在返回的数据上）


class Result(object):

    def __init__(self, msg=False, res=None):
        if res is None:
            res = dict()
        self.IsSucess = msg
        self.Content = res


class McProtocolBase(object):
    def __init__(self):
        self.head = b'\x50\x00'  # 副报文头
        self.networkID = b'\x00'  # 网络ID
        self.plcID = b'\xFF'  # PLC 编号
        self.ioNum = b'\xFF\x03'  # IO编号
        self.modelNum = b'\x00'  # 模块编号
        self.dataLenth = b'\x0C\x00'  # 数据长度-- TODO:自动计算后面的数据长度，后面需要单独通过函数计算（此部分支持读取固定16位）
        self.timeout = b'\x01\x00'  # 等待PLC反馈的时间，单位250ms
        self.mainCommand = b'\x01\x04'  # 主控制指令--批量读取  # TODO：后面提供不同的读写方案，基本 转换成Read16 及批量读取两类
        self.slaveCommand = b'\x00\x00'  # 子控制指令--按字读取 TODO： 指定读取宽度，一般字读取，后面根据需求开发
        self.startAddress = b'\xE8\x03\x00'  # 地址起始位置   TODO：指定地址位置，16进制表示，字符需要反转如1000，后期根据用户输入获取
        self.softModel = b'\xA8'  # 软原件标识，表示读取D区域  TODO： 后期通过用户输入获取
        self.readLenth = b'\x01'  # 读取的长度  1   TODO：指定读取的长度，后期通过用户输入获取
        self.endMark = b'\x00'  # 结束标识符

    def CreatePacket(self):
        return self.head + self.networkID + self.plcID + \
               self.ioNum + self.modelNum + self.dataLenth + \
               self.timeout + self.mainCommand + self.slaveCommand + \
               self.startAddress + self.softModel + self.readLenth + self.endMark


class McProtocol(McProtocolBase):

    def __init__(self):
        super().__init__()

    def GetCommand(self, address='M100'):  # 此方法将输入的地址字母与数字分开
        firstCommand = ''
        secondCommand = ''

        if address[0].isalpha() is False:
            return Result(msg=False, res=None)
        for item in address:
            if item.isalpha():   # 如果是字母 就付给地址单元标识
                firstCommand += item
            else:  # 如果是数字的话就赋值给 地址序列标识
                secondCommand += item
        if firstCommand != '' and secondCommand != '':  # 判断如果单元标识与地址标识都不是空，那就认为这个地址是合法的
            return Result(msg=True, res={'firstCommand': firstCommand, 'secondCommand': secondCommand})
        return Result(msg=False, res=None)   # 如果校验失败 则返回解析失败

    def OrToX16(self, num,reverse=True):
        X16Num = hex(num)
        addressList = []
        res = b''
        addressStr = str(X16Num).replace('0x', '')
        if len(addressStr) % 2 != 0:
            addressStr = '0' + addressStr
        for n, value in enumerate(addressStr):
            if n % 2 == 0 and n < len(addressStr) - 1:
                addressList.append(addressStr[n] + addressStr[n + 1])
        if reverse:
            addressList.reverse()
        for item in addressList:
            temp = bytes().fromhex(item)
            res += temp
        return Result(msg=True, res={'result': res})

    def CreateReadInt16(self, address,readLen=1):
        """
        创建读16位地址的基类函数，后续如需读取更多字符，提供读取的地址长度，默认FF长度是OK的，修改self.readlenth即可，响应的接受解析也是要对应的
        :param address:  地址，如M100，Y100，X100等 特殊的后期进行特殊处理
        :return:
        """
        self.readLenth = self.OrToX16(readLen).Content['result']
        addressConvert = self.GetCommand(address)
        ReadCommand = Result()
        if addressConvert.IsSucess:  # 只有输入的软原件在控制器包含的带进行后面计算
            if addressConvert.Content['firstCommand'].upper() in ProtocolModel.SoftModel.keys():
                self.softModel = ProtocolModel.SoftModel[addressConvert.Content['firstCommand'].upper()]
                self.startAddress = self.OrToX16(int(addressConvert.Content['secondCommand'])).Content['result']
                if len(self.startAddress) == 2:
                    self.startAddress += b'\x00'
                elif len(self.startAddress) == 1:
                    self.startAddress += b'\x00\x00'
                ReadCommand.Content['result'] = self.CreatePacket()
                self.dataLenth =  self.OrToX16(len(ReadCommand.Content['result']) - 9).Content['result']
                if len(self.dataLenth) != 2:
                    self.dataLenth = self.dataLenth + b'\x00'
                ReadCommand.Content['result'] = self.CreatePacket()
                ReadCommand.IsSucess = True
            else:
                ReadCommand.Content['result'] = None
                ReadCommand.IsSucess = False
        return ReadCommand

    def CreateReadBool(self, address):
        pass

    def CreateReadFolat(self, address):
        pass

    def CreateWriteBool(self, address):
        pass

    def CreateWriteInt16(self, address):
        pass

    def CreateWriteFloat(self, address):
        pass

    def CreateWriteBool(self, address):
        pass

if __name__ == '__main__':
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

    a = McProtocol()
    print("MB100:",a.GetCommand('MB100').Content)  # 测试地址解析
    print(a.OrToX16(2).Content['result'])  # 测试十进制转16进制 反转函数
    print('读取16位INT测试：',a.CreateReadInt16('M1000',200).IsSucess,'\r\n',a.CreateReadInt16('M1000').Content) # 正常测试
    print('读取16位INT测试：',a.CreateReadInt16('MMM100').IsSucess,'\r\n',a.CreateReadInt16('MMM100').Content) # 异常测试
    input()


