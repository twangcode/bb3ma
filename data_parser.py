import pandas as pd 
# import matplotlib.pyplot as plt 
# from datetime import datetime


# def read_data(filename, start_dt, end_dt):
# 	start = pd.to_datetime(start_dt)
# 	end = pd.to_datetime(end_dt)
# 	df = pd.read_csv(filename, sep=' ', header=None, parse_dates=[[0,1]], usecols=[0,1,5,19,23], index_col='0_1')
# 	df.columns = ['price', '2D_MA', '2D_STD']
# 	df.index.names = ['Date']
# 	return df[start_dt:end_dt]

def data_reader(filename):
	df = pd.read_csv(filename, sep=' ', header=None, parse_dates=[[0,1]], \
		usecols=[0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29], index_col='0_1')
	df.columns = ['N_points', 'Price', \
					'6H_EMA', '6H_SMA', '6H_STDDEV', \
					'12H_EMA', '12H_SMA', '12H_STDDEV', \
					'2D_EMA', '2D_SMA', '2D_STDDEV', \
					'5D_EMA', '5D_SMA', '5D_STDDEV']
	df.index.names = ['Date']
	return df

class spread():
	def __init__(self, filename):
		self.name = filename[2:-5]
		self.data = data_reader(filename)
	

	def print_name(self):
		print self.name
	def get_name(self):
		return self.name
	def print_data(self):
		print self.data
	def get_data(self, start_dt, end_dt):
		start = pd.to_datetime(start_dt)
		end = pd.to_datetime(end_dt)
		return self.data[start_dt:end_dt]
	
	def plot(self, columns):
		self.data.plot(y=columns)

def main():
	filename = 'S_BB3_TEN_GBL-ZN+XE6.data'
	dp = spread(filename).get_data('20181001', '20181005')
	print dp

if __name__ == '__main__':
	main()