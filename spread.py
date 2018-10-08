from os.path import join
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
from datetime import datetime

FILEPATH = ''

class Spread():
	def __init__(self, name, data):
		self.name = name
		self.data = data
	

	def between(self, start_dt=datetime.now().date().replace(month=1, day=1),\
				end_dt=datetime.today()):
		return self.data.loc[start_dt, end_dt]

	def print_spread_name(self):
		print self.name
	def get_spread_name(self):
		return self.name
	def print_spread_data(self):
		print self.data
	def get_spread_data(self):
		return self.data
	def plot(self):
		self.data.plot(title=self.name)
		plt.show()



def main():
	filename = 'S_BB3_TEN_GBL-ZN+XE6.data'
	df = read_data(filename, '20181001', '20181005')
	print df

if __name__ == '__main__':
	main()