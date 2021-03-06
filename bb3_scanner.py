from os import listdir
from os.path import isfile, join
import csv
import pandas as pd
import numpy as np
from datetime import datetime
from pandas.tseries.offsets import BDay 

FILEPATH = '/var/opt/lufgroup/apps/nova_lufcomp/novaStats_ma/data'

def list_files():
	files = [f for f in listdir(FILEPATH) if isfile(join(FILEPATH, f))]
	return files
	
def list_files_sub():
	BB3_files = [f for f in listdir(FILEPATH) if 'BB3:' in f]
	BB3_TEN_files = [f for f in listdir(FILEPATH) if 'BB3_TEN' in f]
	BB3_FIX_files = [f for f in listdir(FILEPATH) if 'BB3_FIX' in f]
	BB3_FLY_files = [f for f in listdir(FILEPATH) if 'BB3_FLY' in f]	
	return [BB3_files, BB3_TEN_files, BB3_FIX_files, BB3_FLY_files]
	
def read_data(filename, start_dt, end_dt):
	start = pd.to_datetime(start_dt)
	end = pd.to_datetime(end_dt)
	df = pd.read_csv(join(FILEPATH, filename), sep=' ', header=None, parse_dates=[[0,1]], usecols=[0,1,5,19,23], index_col='0_1')
	df.columns = ['price', '2D_MA', '2D_STD']
	df.index.names = ['Date']
	return df[start_dt:end_dt]
	
def calc_sr(filename, start_dt, end_dt, entry, exit, threshold=10):
	# read data from file
	data = read_data(filename, start_dt, end_dt)
	# calculate upper and lower band
	data['UpperBand'] = data['2D_MA'] + data['2D_STD'] * entry
	data['LowerBand'] = data['2D_MA'] - data['2D_STD'] * entry
	data['LongExit'] = data['LowerBand'] + data['2D_STD'] * entry * exit
	data['ShortExit'] = data['UpperBand'] - data['2D_STD'] * entry * exit
	# generate trades according to bands
	data['Position'] = None
	data['Position'] = np.where(data['price'] > (data['UpperBand'] + threshold), -1, None)
	data['Position'] = np.where(data['price'] < (data['LowerBand'] - threshold), 1, data['Position'])
	data['Position'] = np.where((data['price'] > (data['LongExit'] + threshold)) & (data['price'] < (data['ShortExit'] - threshold)), 0, data['Position'])
	data['Position'] = data['Position'].fillna(method='ffill')
	data['Position'] = data['Position'].fillna(0)
	data['Trade'] = data['Position'] - data['Position'].shift(1)
	data['Trade'] = np.where(data['Trade'].isnull(), data['Position'], data['Trade'])
	# calculate cumulated pnl:
	data['Cost'] = data['Trade'] * data['price']
	data['MarketValue'] = data['price'] * data['Position']
	data['cumPnL'] = data['MarketValue'] - data['Cost'].cumsum()
	total_profit = data['cumPnL'].tail(1).values[0]
	# calculate pnl and sharpe ratio
	data['PnL'] = data['cumPnL'] - data['cumPnL'].shift(1)
	sharpeRatio = data['PnL'].mean() / data['PnL'].std() * np.sqrt(len(data))
	# data['buy'] = np.where(data['Trade'] > 0,  data['Cost'] / data['Trade'], np.nan)
	# data['sell'] = np.where(data['Trade'] < 0,  data['Cost'] / data['Trade'], np.nan)
	# calculate daily pnl:
	# daily_PnL = data.groupby(data.index.date).last()[['Position', 'cumPnL']].fillna(method='ffill').fillna(0)
	# daily_PnL['PnL'] = daily_PnL['cumPnL'] - daily_PnL['cumPnL'].shift(1)
	# Calculate Sharpe Ratio:
	# temp = daily_PnL['PnL'].copy()
	# sharpeRatio = temp.mean() / temp.std() * np.sqrt(len(temp))
	return [sharpeRatio, total_profit]

def optimize_sr(filename, start_dt, end_dt, entry_list=[1.5, 2], exit_list=[0.5, 1], threshold=10):
	max_sr = -100
	opt_entry = 0
	opt_exit = 0
	for entry in entry_list:
		for exit in exit_list:
			[sr,pnl] = calc_sr(filename, start_dt, end_dt, entry, exit, threshold)
			if sr > max_sr:
				max_sr = sr
				max_pnl = pnl
				opt_entry = entry
				opt_exit = exit
	return [filename[:-5], max_pnl, max_sr,  opt_entry, opt_entry * opt_exit]
	
def generate_bb3_list(entry=2, exit=0.5, threshold=10):
	end_dt = datetime.now()
	start_dt = end_dt - BDay(20)
	start_dt_2 = end_dt - BDay(10)
	time = datetime.now()
	BB3_files = [f for f in listdir(FILEPATH) if 'BB3:' in f]
	total_files = float(len(BB3_files))
	counter = 0
	with open('data/bb3_list.csv','wb') as fout:
		writer = csv.writer(fout)
		for filename in BB3_files:
			counter = counter + 1
			try:
				[sharpeRatio, total_profit] = calc_sr(filename, start_dt, end_dt, entry, exit, threshold)
				if sharpeRatio > 2.0:
					[sharpeRatio_2, total_profit_2] = calc_sr(filename, start_dt_2, end_dt, entry, exit, threshold)
					if sharpeRatio_2 > 2.0:
						print filename[:-5] + ' , ' + str(sharpeRatio) + ' , ' + str(total_profit) + ' , ' + 'finished:' + str(counter/total_files*100) + '%'
						print filename[:-5] + ' , ' + str(sharpeRatio_2) + ' , ' + str(total_profit_2) + ' , ' + 'finished:' + str(counter/total_files*100) + '%'
						writer.writerow([filename[:-5], sharpeRatio, sharpeRatio_2, total_profit, total_profit_2])
			except:
				pass
		fout.close()
		print datetime.now()-time

def generate_bb3_ten_list(threshold=10):
	end_dt = datetime.now()
	start_dt = end_dt - BDay(10)
	time = datetime.now()
	BB3_TEN_files = [f for f in listdir(FILEPATH) if 'BB3_TEN:' in f]
	total_files = float(len(BB3_TEN_files))
	counter = 0
	with open('data/bb3_ten_list.csv','wb') as fout:
		writer = csv.writer(fout)
		for filename in BB3_TEN_files:
			counter = counter + 1
			try:
				srlist = optimize_sr(filename, start_dt, end_dt, threshold=threshold)
				if srlist[2] > 0:
					print srlist[0]  + ' , ' + str(srlist[1]) + ' , ' + str(srlist[2]) + ' , ' + str(srlist[3]) + ' , ' + str(srlist[4]) + ' , finished: ' + str(counter/total_files*100) + '%' 
					writer.writerow(srlist)
			except:
				pass
		fout.close()
		print datetime.now()-time
	
	

def main():
	generate_bb3_list()
	generate_bb3_ten_list()
	
if __name__ == "__main__":
	main()


	
# def read_spread(file, entry=2, exit=0.5, threshold=10, start_date=date(2018,9,1), end_date=date.today()):
# 	df = pd.read_csv(join(FILEPATH, file), sep=' ', header=None)
	
# 	data = pd.DataFrame(index = pd.to_datetime(df[0] + ' ' + df[1]))
# 	data['price'] = df[5].values
# 	data['6H_MA'] = df[7].values
# 	data['6H_STD'] = df[11].values
# 	data['12H_MA'] = df[13].values
# 	data['12H_STD'] = df[17].values
# 	data['2D_MA'] = df[19].values
# 	data['2D_STD'] = df[23].values
# 	data['5D_MA'] = df[25].values
# 	data['5D_STD'] = df[29].values
# 	data['UpperBand'] = data['2D_MA'] + data['2D_STD'] * entry
# 	data['LowerBand'] = data['2D_MA'] - data['2D_STD'] * entry
# 	data['LongExit'] = data['LowerBand'] + data['2D_STD'] * entry * exit
# 	data['ShortExit'] = data['UpperBand'] - data['2D_STD'] * entry * exit
		
# 	data['Position'] = None
# 	data['Position'] = np.where(data['price'] > (data['UpperBand'] + threshold), -1, None)
# 	data['Position'] = np.where(data['price'] < (data['LowerBand'] - threshold), 1, data['Position'])
# 	data['Position'] = np.where((data['price'] > (data['LongExit'] + threshold)) & (data['price'] < (data['ShortExit'] - threshold)), 0, data['Position'])
# 	data['Position'] = data['Position'].fillna(method='ffill')
# 	data['Position'] = data['Position'].fillna(0)
# 	data['Trade'] = data['Position'] - data['Position'].shift(1)
# 	data['Trade'] = np.where(data['Trade'].isnull(), data['Position'], data['Trade'])
# 	data['Price'] = data['Trade'] * data['price']
# 	data['MarketValue'] = data['price'] * data['Position']
# 	data['cumPnL'] = data['MarketValue'] - data['Price'].cumsum()
# 	data['buy'] = np.where(data['Trade'] > 0,  data['Price'] / data['Trade'], np.nan)
# 	data['sell'] = np.where(data['Trade'] < 0,  data['Price'] / data['Trade'], np.nan)
	
# 	daily_PnL = data.groupby(data.index.date).last()[['Position', 'cumPnL']].fillna(method='ffill').fillna(0)
# 	daily_PnL['PnL'] = daily_PnL['cumPnL'] - daily_PnL['cumPnL'].shift(1)

# 	# Calculate Sharpe Ratio between start and end date:
# 	temp = daily_PnL['PnL'].copy()
# 	sharpeRatio = temp.mean() / temp.std() * np.sqrt(len(temp))

# 	# Calculate drawdown
# 	daily_PnL['MaxProfit'] = daily_PnL['cumPnL'].cummax()
		
# 	return sharpeRatio
		
# 	#df.to_csv(join(base_dir, file))
# 	#print 'print ' + file + ' to: ' + join(base_dir, file)
		
		

	


