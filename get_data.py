import yfinance as yf
import pandas as pd


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df


# These are the 5 NSE stock symbols
stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'WIPRO.NS']

# Download 2 years of data for all 5 stocks
all_data = []
for stock in stocks:
	df = yf.download(stock, period='2y', interval='1d', progress=False)
	df = normalize_columns(df)
	df = df.reset_index()
	df['Stock'] = stock.replace('.NS', '')
	df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Stock']]
	all_data.append(df)

# Combine all stocks into one table
final_df = pd.concat(all_data, ignore_index=True)
final_df = final_df.sort_values(['Stock', 'Date']).reset_index(drop=True)

# Save to CSV
final_df.to_csv('stock_data.csv', index=False)
print('Done! Rows:', len(final_df))