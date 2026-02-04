from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep, time
from datetime import datetime
import os
import pandas as pd
import base64


SAVE_PATH = './img'


def save_image(filename, data):
	img_data = data.replace('data:image/jpeg;base64,', '', 1).encode('ascii')
	with open(filename, "wb") as f:
		f.write(base64.decodebytes(img_data))


def save_temp(data):
	save_image('temp.jpg')


def format_date(timestamp):
	if type(timestamp) == str:
		return timestamp
	res = timestamp.strftime('%d.%m.%Y')
	return timestamp.strftime('%d.%m.%Y')


def is_nan(value):
	return pd.isna(value)


def format_table_row_data(cells):
	return {
		'Должник': cells[0].text,
		'Исполнительное производство': cells[1].text,
		'Реквизиты исполнительного документа ': cells[2].text,
		'Дата, причина окончания или прекращения ИП ': cells[3].text,
		'Предмет исполнения, сумма непогашенной задолженности': cells[5].text,
		'Отдел судебных приставов': cells[6].text,
		'Судебный пристав-исполнитель, телефон для получения информации': cells[7].text,
	}


def format_bad_data(row):
	return {
		'Должник': f'{row["Фамилия"]} {row["Имя"]} {row["Отчество"]}\n{row["Регион"]}\n{row["Дата рождения"]}',
		'Исполнительное производство': 'Не найдено'
	}


# #capchaVisual
# df.iloc[0]['Дата рождения'].strftime('%d.%m.%Y')
class FsspGetter:
	url = 'https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D={}'

	def __init__(self):
		self.data = []
		self.driver = Chrome()

	def goto_menu(self, ip=False):
		url = self.url.format(3 if ip else 1)
		self.driver.get(url)
		# sleep(5)

	def set_data(self, data):
		self.df = data

	def iterate(self):
		for i in self.df.index:
			row = self.df.iloc[i]
			self.process(row)
			# sleep(1)

	def process(self, row):
		if is_nan(row['ИП']):
			data = self.process_pl(row)
		else:
			data = self.process_ip(row)

		self.driver.find_element(By.ID, 'btn-sbm').click()

		WebDriverWait(self.driver, 10).until(
			EC.element_to_be_clickable((By.ID, 'ncapcha-submit'))
		)

		success = False
		while not success:
			self.wait_for_captcha_input()
			success = self.wait_for_captcha_result()

		sleep(4)

		self.save_data(row)

	def save_data(self, row):
		table = None
		try:
			table = self.driver.find_element(By.CSS_SELECTOR, '.results-frame table')
		except:
			not_found = self.driver.find_element(By.CSS_SELECTOR, '.b-search-message')
			self.data.append(format_bad_data(row+2))
			return
		rows = table.find_elements(By.TAG_NAME, 'tr')
		for row in rows[1:]:
			cells = row.find_elements(By.TAG_NAME, 'td')
			if len(cells) <= 1:
				continue
			self.data.append(format_table_row_data(cells))

	def wait_for_captcha_input(self):
		while True:
			sleep(.1)
			value = self.driver.find_element(By.ID, 'capcha-popup').get_attribute('value')
			if self.driver.find_element(By.ID, 'ncapcha-submit').is_displayed():
				continue
			value = self.driver.find_element(By.ID, 'capcha-popup')
			try:
				self.captcha_value = value.get_attribute('value')
			except:
				pass
			self.captcha_data = self.driver.find_element(By.ID, 'capchaVisualImage').get_attribute('src')
			return
	def wait_for_captcha_result(self):
		while True:
			sleep(.25)

			try:
				self.driver.find_element(By.CSS_SELECTOR, '.f-loading.t-capcha')
				continue
			except:
				break
		sleep(.04)
		try:
			self.driver.find_element(By.CLASS_NAME, 'b-form__label--error')
			self.save_captcha(False)
			return False
		except:
			self.save_captcha(True)
			return True

	def save_captcha(self, success):
		save_image(f'{SAVE_PATH}/{int(success)}{self.captcha_value}.jpg', self.captcha_data)
	def process_ip(self, row):
		self.goto_menu(True)
		sleep(1.5)
		input_el = self.driver.find_element(By.ID, 'input04')
		input_el.send_keys(row['ИП'])
		sleep(.5)
	def process_pl(self, row):
		self.goto_menu()
		self.fill_data(row)

	def fill_data(self, row):
		self.choose_region(row['Регион'])
		self.driver.find_element(By.ID, 'input01').send_keys(row['Фамилия'])
		self.driver.find_element(By.ID, 'input02').send_keys(row['Имя'])
		self.driver.find_element(By.ID, 'input05').send_keys(row['Отчество'] or '')
		date_el = WebDriverWait(self.driver, 5).until(
			EC.element_to_be_clickable((By.ID, 'input06'))
		)
		date_el.send_keys(format_date(row['Дата рождения']))

	def choose_region(self, region):
		self.driver.find_element(By.CSS_SELECTOR, '.chosen-search input').send_keys(region)
		self.driver.find_element(By.CSS_SELECTOR, '.chosen-results li').click()


def get_output_path():
	with open('./config.txt') as f:
		return f.readline().strip()


def get_data(filename):
	return pd.read_excel(filename)


if __name__ == '__main__':
	input_filename = input('Файл данные: ')
	getter = FsspGetter()
	# df = get_data('./example.xlsx')
	df = get_data(input_filename)
	getter.set_data(df)
	try:
		getter.iterate()
		print('Всё успех')
	except:
		import traceback
		with open('logs.log', 'a', encoding='utf-8') as logs:
			logs.write(f'[{datetime.today().strftime("%Y-%m-%d %H:%M:%S")}]\n')
			logs.write("\n".join(['  ' + line for line in traceback.format_exc().split('\n')]))
			logs.write(f'\n\n')
			print(traceback.format_exc())
	finally:
		res = pd.DataFrame(getter.data)
		res.to_excel(os.path.join(get_output_path(), f'{datetime.today().strftime("%y%m%d%H%M%S")}.xlsx'), index=False)
		getter.driver.close()
