import os
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtTest import *
from config.errorCode import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print("키움증권 클래스 입니다!!")

        ####### event loop를 실행하기 위한 변수모음
        self.login_event_loop = QEventLoop() #로그인 요청용 이벤트루프
        self.detail_account_info_event_loop = QEventLoop() # 예수금 요청용 이벤트루프
        #self.detail_account_info_event_loop2 = QEventLoop()  # 계좌평가잔고내역 요청용 이벤트루프
        self.calculator_event_loop = QEventLoop()
        #########################################

        ### 변수 모음
        self.account_num = None
        ################

        ########### 종목 분석 용
        self.calcul_data = []
        ##########################################

        ####### 계좌 관련된 변수
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        self.portfolio_stock_dict = {}
        self.deposit = 0  # 예수금
        self.use_money = 0  # 실제 투자에 사용할 금액
        self.use_money_percent = 0.5  # 예수금에서 실제 사용할 비율
        self.output_deposit = 0  # 출력가능 금액
        self.total_profit_loss_money = 0  # 총평가손익금액
        self.total_profit_loss_rate = 0.0  # 총수익률(%)
        ########################################

        ####### 요청 스크린 번호
        self.screen_my_info = "2000" #계좌 관련한 스크린 번호
        self.screen_calculation_stock = "4000" #계산용 스크린 번호
        self.screen_real_stock = "5000" #종목별 할당할 스크린 번호
        self.screen_meme_stock = "6000" #종목별 할당할 주문용스크린 번호
        self.screen_start_stop_real = "1000" #장 시작/종료 실시간 스크린번호
        ########################################

        self.get_ocx_instance()
        self.event_slots()

        self.signal_login_commConnect()
        self.get_account_info() ## 계좌 번호 정보
        self.detail_account_info() ## 예수금 정보
        self.detail_account_mystock() ## 계좌평가잔고내역 정보
        self.not_concluded_account() ## 미체결 잔고 내역 요청

        self.calculator_fnc()  ## 종목 분석용 // 임시용
        self.read_code()  ## 저장된 종목들 불러오기
        self.screen_number_setting() ## 스크린 번호 할당하기

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")  # 레지스트리에 저장된 api 모듈 불러오기

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot) # 로그인 관련 이벤트
        self.OnReceiveTrData.connect(self.trdata_slot) # 트랜잭션 요청 관련 이벤트
        #self.OnReceiveMsg.connect(self.msg_slot)


    def login_slot(self, errCode):
        print("login 에러코드 발생 부분")
        print(errors(errCode))

        # 로그인 처리가 완료됐으면 이벤트 루프를 종료한다.
        self.login_event_loop.exit()


    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()") # 로그인 요청 시그널

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_() # 이벤트루프 실행

    def get_account_info(self):
        account_list = self.dynamicCall("GetLogininfo(String)", "ACCNO") # 계좌번호 반환
        self.account_num = account_list.split(';')[0]
        print("나의 보유 계좌번호 : %s " % self.account_num)

    def detail_account_info(self):
        print("예수금 정보 요청")

        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000") ### 모의 투자 계좌 패스워드 0000
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "1")
        ### 내가지은 요청 이름 : 예수금상세현황요청 // TR번호 : opw00001 // preNext : 0 // 화면번호 : 2000 ###
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청", "opw00001", "0", self.screen_my_info)

        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        print("계좌평가 잔고내역 요청")
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "opw00018", sPrevNext,self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def not_concluded_account(self, sPrevNext="0"):
        print("실시간미체결 잔고내역 요청")
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()


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
            ###print("예수금 : %s" % self.deposit)

            output_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,"출금가능금액")
            self.output_deposit = int(output_deposit)
            ###print("출금가능금액 : %s" % self.output_deposit)


            use_money = float(self.deposit) * self.use_money_percent
            self.use_money = int(use_money)
            self.use_money = self.use_money / 4

            self.detail_account_info_event_loop.exit()

        elif sRQName == "계좌평가잔고내역요청":
            total_buy_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,"총매입금액")
            self.total_buy_money = int(total_buy_money)

            total_profit_loss_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,0, "총평가손익금액")
            self.total_profit_loss_money = int(total_profit_loss_money)

            total_profit_loss_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,0, "총수익률(%)")
            self.total_profit_loss_rate = float(total_profit_loss_rate)

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,"종목번호")  # 출력 : A039423 // 알파벳 A는 장내주식, J는 ELW종목, Q는 ETN종목
                code = code.strip()[1:]

                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")  # 출럭 : 한국기업평가
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")  # 보유수량 : 000000000000010
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")  # 매입가 : 000000000054100
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")  # 수익률 : -000000001.94
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")  # 현재가 : 000000003450
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")

                if code in self.account_stock_dict:  # dictionary 에 해당 종목이 있나 확인
                    pass
                else:
                    self.account_stock_dict[code] = {}

                # 좌우 공백 제거
                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())

                # dictionary 에 종목 정보 update
                asd = self.account_stock_dict[code]
                asd.update({"종목명": code_nm})
                asd.update({"보유수량": stock_quantity})
                asd.update({"매입가": buy_price})
                asd.update({"수익률(%)": learn_rate})
                asd.update({"현재가": current_price})
                asd.update({"매입금액": total_chegual_price})
                asd.update({'매매가능수량' : possible_quantity})

            print("계좌에 가지고 있는 종목은 %s " % self.account_stock_dict)
            print("계좌에 가지고 있는 종목은 %s " % rows)

            #계좌평가 잔고내역 요청은 1페이지에 최대 20개 // 20개 이상 보유할 경우 동작
            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit()


        elif sRQName == "실시간미체결요청":
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드")
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,"주문상태")  # 접수,확인,체결
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,"주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,"주문가격")
                order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,"주문구분")  # -매도, +매수, -매도정정, +매수정정
                not_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,"미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,"체결량")

                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}

                nasd = self.not_account_stock_dict[order_no]
                nasd.update({'종목코드': code})
                nasd.update({'종목명': code_nm})
                nasd.update({'주문번호': order_no})
                nasd.update({'주문상태': order_status})
                nasd.update({'주문수량': order_quantity})
                nasd.update({'주문가격': order_price})
                nasd.update({'주문구분': order_gubun})
                nasd.update({'미체결수량': not_quantity})
                nasd.update({'체결량': ok_quantity})

                print("미체결 종목은 %s " % nasd)


            self.detail_account_info_event_loop.exit()

        elif sRQName == "주식일봉차트조회":
            #print("일봉 데이터 요청")
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            code = code.strip()

            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            #self.logging.logger.debug("남은 일자 수 %s" % cnt)
            #print("남은 일자 수 %s" % cnt)

            # data = self.dynamicCall("GetCommDataEx(QString, QString)", sTrCode, sRQName)
            # [[‘’, ‘현재가’, ‘거래량’, ‘거래대금’, ‘날짜’, ‘시가’, ‘고가’, ‘저가’. ‘’], [‘’, ‘현재가’, ’거래량’, ‘거래대금’, ‘날짜’, ‘시가’, ‘고가’, ‘저가’, ‘’]. […]]

            for i in range(cnt):
                data = []

                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")  # 출력 : 000070
                value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량")  # 출력 : 000070
                trading_value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금")  # 출력 : 000070
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")  # 출력 : 000070
                start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가")  # 출력 : 000070
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가")  # 출력 : 000070
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가")  # 출력 : 000070

                data.append("")
                data.append(current_price.strip())
                data.append(value.strip())
                data.append(trading_value.strip())
                data.append(date.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append("")

                self.calcul_data.append(data.copy())

            #print(self.calcul_data)

            if sPrevNext == "2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)
            else:
                ##과거 데이터가 더이상 없으면...
                #print("총 일수 %s " % len(self.calcul_data))
                pass_success = False

                # 120일 이평선을 그릴만큼의 데이터가 있는지 체크
                if self.calcul_data == None or len(self.calcul_data) < 120:
                    pass_success = False

                else:
                    # 120일 이평선의 최근 가격 구함
                    total_price = 0
                    for value in self.calcul_data[:120]:
                        total_price += int(value[1])
                    moving_average_price = total_price / 120

                    # 오늘자 주가가 120일 이평선에 걸쳐있는지 확인
                    bottom_stock_price = False
                    check_price = None
                    # data = self.dynamicCall("GetCommDataEx(QString, QString)", sTrCode, sRQName)
                    # [[‘’, ‘현재가’, ‘거래량’, ‘거래대금’, ‘날짜’, ‘시가’, ‘고가’, ‘저가’. ‘’], [‘’, ‘현재가’, ’거래량’, ‘거래대금’, ‘날짜’, ‘시가’, ‘고가’, ‘저가’, ‘’]. […]]
                    if int(self.calcul_data[0][7]) <= moving_average_price and moving_average_price <= int(self.calcul_data[0][6]):
                        #self.logging.logger.debug("오늘 주가 120이평선 아래에 걸쳐있는 것 확인")
                        print("오늘 주가 120이평선 아래에 걸쳐있는 것 확인")
                        bottom_stock_price = True
                        check_price = int(self.calcul_data[0][6])

                    # 과거 일봉 데이터를 조회하면서 120일 이평선보다 주가가 계속 밑에 존재하는지 확인
                    prev_price = None
                    if bottom_stock_price == True:
                        moving_average_price_prev = 0
                        price_top_moving = False
                        idx = 1

                        while True:

                            if len(self.calcul_data[idx:]) < 120:  # 120일치가 있는지 계속 확인
                                print("120일치가 없음")
                                #self.logging.logger.debug("120일치가 없음")
                                break

                            total_price = 0
                            for value in self.calcul_data[idx:120 + idx]:
                                total_price += int(value[1])
                            moving_average_price_prev = total_price / 120

                            if moving_average_price_prev <= int(self.calcul_data[idx][6]) and idx <= 20:
                                print("20일 동안 주가가 120일 이평선과 같거나 위에 있으면 조건 통과 못함")
                                #self.logging.logger.debug("20일 동안 주가가 120일 이평선과 같거나 위에 있으면 조건 통과 못함")
                                price_top_moving = False
                                break

                            elif int(self.calcul_data[idx][7]) > moving_average_price_prev and idx > 20:
                                # 120일 이평선 위에 있는 구간 존재
                                print("120일치 이평선 위에 있는 구간 확인됨")
                                #self.logging.logger.debug("120일치 이평선 위에 있는 구간 확인됨")
                                price_top_moving = True
                                prev_price = int(self.calcul_data[idx][7])
                                break

                            idx += 1

                        # 해당부분 이평선이 가장 최근의 이평선 가격보다 낮은지 확인
                        if price_top_moving == True:
                            if moving_average_price > moving_average_price_prev and check_price > prev_price:
                                #self.logging.logger.debug("포착된 이평선의 가격이 오늘자 이평선 가격보다 낮은 것 확인")
                                #self.logging.logger.debug("포착된 부분의 저가가 오늘자 주가의 고가보다 낮은지 확인")
                                print("포착된 이평선의 가격이 오늘자 이평선 가격보다 낮은 것 확인")
                                print("포착된 부분의 저가가 오늘자 주가의 고가보다 낮은지 확인")
                                pass_success = True

                if pass_success == True:
                    #self.logging.logger.debug("조건부 통과됨")
                    print("조건부 통과됨")

                    code_nm = self.dynamicCall("GetMasterCodeName(QString)", code)

                    f = open("../files/condition_stock.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.calcul_data[0][1])))
                    f.close()

                elif pass_success == False:
                    #self.logging.logger.debug("조건부 통과 못함")
                    print("조건부 통과 못함")

                self.calcul_data.clear()
                self.calculator_event_loop.exit()






    def get_code_list_by_market(self, market_code):
        '''
        종목코드 리스트 받기
        #0:장내, 10:코스닥
        :param market_code: 시장코드 입력
        :return:
        '''
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_code)
        code_list = code_list.split(';')[:-1]
        return code_list

    def calculator_fnc(self):
        '''
        종목 분석관련 함수 모음
        :return:
        '''

        code_list = self.get_code_list_by_market("10") ###0:장내, 10:코스닥
        #self.logging.logger.debug("코스닥 갯수 %s " % len(code_list))
        print("코스닥 갯수 %s " % len(code_list))

        for idx, code in enumerate(code_list):
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock)  # 스크린 연결 끊기

            #self.logging.logger.debug("%s / %s :  KOSDAQ Stock Code : %s is updating... " % (idx + 1, len(code_list), code))
            print("%s / %s :  KOSDAQ Stock Code : %s is updating... " % (idx + 1, len(code_list), code))
            self.day_kiwoom_db(code=code)

    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):

        QTest.qWait(3600) #3.6초마다 딜레이를 준다.

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        if date != None: ## 기준일자 데이터 없으면 오늘부터
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", sPrevNext, self.screen_calculation_stock)  # Tr서버로 전송 -Transaction

        self.calculator_event_loop.exec_()

    def read_code(self):
        print("코드 읽는 부분")
        if os.path.exists("../files/condition_stock.txt"): # 해당 경로에 파일이 있는지 체크한다.
            f = open("../files/condition_stock.txt", "r", encoding="utf8") # "r"을 인자로 던져주면 파일 내용을 읽어 오겠다는 뜻이다.

            lines = f.readlines() #파일에 있는 내용들이 모두 읽어와 진다.
            for line in lines: #줄바꿈된 내용들이 한줄 씩 읽어와진다.
                if line != "":
                    ls = line.split("\t")

                    stock_code = ls[0]  # 종목 코드
                    stock_name = ls[1]  # 종목 명
                    stock_price = int(ls[2].split("\n")[0]) # 현재가
                    stock_price = abs(stock_price)
                    
                    self.portfolio_stock_dict.update({stock_code:{"종목명":stock_name, "현재가":stock_price}})
            f.close()

    def screen_number_setting(self):
        screen_overwrite = []

        #계좌평가잔고내역에 있는 종목들
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        #미체결에 있는 종목들
        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]['종목코드']
            if code not in screen_overwrite:
                screen_overwrite.append(code)


        #포트폴리로에 담겨있는 종목들
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 스크린번호 할당
        cnt = 0
        for code in screen_overwrite:

            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)

            if (cnt % 50) == 0:
                temp_screen += 1
                self.screen_real_stock = str(temp_screen)

            if (cnt % 50) == 0:
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)

            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({"스크린번호": str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호": str(self.screen_meme_stock)})

            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code: {"스크린번호": str(self.screen_real_stock), "주문용스크린번호": str(self.screen_meme_stock)}})

            cnt += 1
