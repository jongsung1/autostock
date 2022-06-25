from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print("키움증권 클래스 입니다!!")

        ### eventloop 모음
        self.login_event_loop = None
        ################

        ### 변수 모음
        self.account_num = None
        ################
        self.get_ocx_instance()
        self.event_slots()

        self.signal_login_commConnect()
        self.get_account_info() ## 계좌 번호 정보
        self.detail_account_info() ## 예수금 정보

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)

    def login_slot(self, errCode):
        print(errors(errCode))

        self.login_event_loop.exit()

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_info(self):
        account_list = self.dynamicCall("GetLogininfo(String)", "ACCNO")
        self.account_num = account_list.split(':')[0]
        print("나의 보유 계좌번호 : %s " % self.account_num)

    def detail_account_info(self):
        print("예수금 정보 요청")

        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000") ### 모의 투자 계좌 패스워드 0000
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        ### 내가지은 요청 이름 : 예수금상세현황요청 // TR번호 : opw00001 // preNext : 0 // 화면번호 : 2000 ###
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청", "opw00001", "0", "2000")

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''
        :param sScrNo: 스크린 번호
        :param sRQName: 사용자가 요청했을 때 지은 이름
        :param sTrCode: 요청 id, TR코드
        :param sRecordName: 사용안함
        :param sPrevNext: 다음 페이지 있는지
        :return:
        '''

        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "예수금")
            self.deposit = int(deposit)

            output_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,"출금가능금액")
            self.output_deposit = int(output_deposit)

