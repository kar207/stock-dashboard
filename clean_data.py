import pandas as pd

df = pd.read_csv('stock_data.csv')
print('Shape before cleaning:', df.shape)
print('Null values:', df.isnull().sum())

# Keep only columns needed for MySQL load.
required_cols = ['Date', 'Stock', 'Open', 'High', 'Low', 'Close', 'Volume']
df = df[required_cols]

# Remove rows with missing values
df = df.dropna()

# Make sure Date column is in date format
df['Date'] = pd.to_datetime(df['Date'])

# Ensure numeric fields are valid numbers.
for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
	df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna()
df['Volume'] = df['Volume'].astype('int64')

# Sort by stock and date
df = df.sort_values(['Stock', 'Date']).reset_index(drop=True)
print('Shape after cleaning:', df.shape)
df.to_csv('stock_data_clean.csv', index=False)
print('Clean data saved!')