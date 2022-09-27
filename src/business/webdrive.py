from selenium import webdriver
from json import loads
import time
from datetime import datetime
from datetime import timedelta

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from src.config.config import Config
from src.libs.log import logger


class WebBrowser:
    def __init__(self):
        self._config = Config()
        self._logger = logger(__name__)
        self._navigator = ''
        self.last_option = False
        self._gym = 1
        self._group =1
        self._time_reserve = self._config.env.time_reserve_default
        self._date_reserve = ''

    def webextension(self):
        chrome_options = Options()
        #executar em segundo plano
        #chrome_options.add_argument("--headless")
        extension = './extension/0.0.0.2_0.crx'
        chrome_options.add_extension(extension)
        self._navigator = webdriver.Chrome(chrome_options=chrome_options)
        self._navigator.implicitly_wait(10)

    def weblogin(self):
        self.webextension()
        self._navigator.get(self._config.env.url)
        self._logger.info("Página carregada!")
        # Preenchendo campos login
        c_username = self._navigator.find_element(By.NAME, "email")
        c_password = self._navigator.find_element(By.NAME, "senha")
        b_login = self._navigator.find_element(By.NAME, "salvar")
        self._logger.info("Logando")
        c_username.send_keys(self._config.env.user_login, Keys.ARROW_DOWN)
        b_login.click()
        c_password.send_keys(self._config.env.password_login, Keys.ARROW_DOWN)
        b_login.click()
        self._logger.info(f"Reservar dia {self._date_reserve } das {self._time_reserve}")


    def selectgym(self):
        self._logger.info(f"Selecionou academia {self._gym}")
        self._navigator.find_element(By.XPATH,
                                     ".ng-scope:nth-child(25) > .menu-list-item .ng-scope:nth-child(1) .md-caption") \
            .click()
        self._navigator.find_element(By.XPATH, f"//div/div/figure/figcaption/div/a/p[text()='Academia {self._gym}']") \
            .click()
        WebBrowser.checkreserve(self)

    def checkreserve(self):
        self._logger.info(f"Selecionou academia {self._gym}")
        x = range(1, 5)
        free = False
        for group in x:
            try:
                free = self._navigator.find_element(By.XPATH,
                                                    f'//*[@id="Clients_Areadocondomino_Grids_Reservas0"]/tbody[{group}]'
                                                    f'//tr[.//td[1]/span/span/h5/text()=" {self._time_reserve} "][{self._gym}]'
                                                    f'//td[4][.//div/span/text()="Livre"]')

            except Exception:
                continue

            if free:
                self._group = group
                break
        self._logger.info(f'Selecionou grupo: {self._group}')


        if not free:
            if self._gym > 1:
                self._logger.info(f"NÃO DISPONIVEL, RESERVA NÃO EFETUADA :(")
                self._navigator.quit()
            else:
                self._logger.info(f"Horário não disponível na ACADEMIA {self._gym}")
                self._gym = 2
                WebBrowser.checkreserve(self)
        else:
            self._logger.info(f"Horário disponível na ACADEMIA {self._gym}")
            WebBrowser.reserve(self)

    def calculate_day_reserve(self):
        date_reserve = datetime.now() + timedelta(days=2)
        self._date_reserve = date_reserve.strftime('%Y-%m-%d')
        dia_s = date_reserve.isoweekday()
        print(dia_s)
        if dia_s in (6, 7):
            dia_s = self._config.days[dia_s]
            self._logger.warning(f"{dia_s} não é dia de reservar")
            return False
        if dia_s == 8:
            self._time_reserve = self._config.env.time_reserve_custom
        return True

    def reserve(self):
        prereserve = self._navigator.find_element(By.XPATH, f'//*[@id="Clients_Areadocondomino_Grids_Reservas0"]'
                                               f'/tbody[{self._group}]'
                                               f'//tr[.//td[1]/span/span/h5/'
                                               f'text()=" {self._time_reserve} "][{self._gym}]'
                                               f'//td[4][.//div/span/text()="Livre"]//a[./text()="Pré-reservar"]')
        self._navigator.execute_script("arguments[0].click();", prereserve)
        self._logger.info("Finalizando reserva...")

        fprereserve = self._navigator.find_element(By.XPATH, '//*[@id="myModal"]'
                                                             '//button[@id="salvar"][.//text()="Pré-reservar "]')
        self._navigator.execute_script("arguments[0].click();", fprereserve)
        time.sleep(4)
        self._logger.info(f"Reserva efetuada {self._date_reserve} das {self._time_reserve}!")
        self._navigator.quit()
