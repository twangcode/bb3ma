from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from datetime import datetime
from pandas.tseries.offsets import BDay 

FILEPATH = 'data' #'/var/opt/lufgroup/apps/nova_lufcomp/novaStats_ma/data'

def list_files():
	files = [f for f in listdir(FILEPATH) if isfile(join(FILEPATH, f))]
	return files

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
	data['buy'] = np.where(data['Trade'] > 0,  data['Cost'] / data['Trade'], np.nan)
	data['sell'] = np.where(data['Trade'] < 0,  data['Cost'] / data['Trade'], np.nan)
	# calculate daily pnl:
	daily_PnL = data.groupby(data.index.date).last()[['Position', 'cumPnL']].fillna(method='ffill').fillna(0)
	daily_PnL['PnL'] = daily_PnL['cumPnL'] - daily_PnL['cumPnL'].shift(1)
	# Calculate Sharpe Ratio:
	temp = daily_PnL['PnL'].copy()
	sharpeRatio = temp.mean() / temp.std() * np.sqrt(len(temp))
	return sharpeRatio

def optimize_sr(filename, start_dt, end_dt, entry_list=[1.5,2], exit_list=[0.5,1], threshold=10):
	max_sr = 0
	opt_entry = 0
	opt_exit = 0
	for entry in entry_list:
		for exit in exit_list:
			sr = calc_sr(filename, start_dt, end_dt, entry, exit, threshold)
			if sr > max_sr:
				max_sr = sr
				opt_entry = entry
				opt_exit = exit
	return [max_sr, opt_entry, opt_exit]



def main():
	end_dt = datetime.now()
	start_dt = end_dt - BDay(10)
	files = list_files()
	for file in files:
		print optimize_sr(file, start_dt, end_dt)



	
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
		
		

	

if __name__ == "__main__":
	main()
