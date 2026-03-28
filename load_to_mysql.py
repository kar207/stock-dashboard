import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Kar@+-2818',
    database='stock_analytics'
)
cursor = conn.cursor()

df = pd.read_csv('stock_data_clean.csv')
df['Date'] = pd.to_datetime(df['Date']).dt.date

rows = [
    (
        row['Date'],
        row['Stock'],
        float(row['Open']) if pd.notna(row['Open']) else None,
        float(row['High']) if pd.notna(row['High']) else None,
        float(row['Low']) if pd.notna(row['Low']) else None,
        float(row['Close']) if pd.notna(row['Close']) else None,
        int(row['Volume']) if pd.notna(row['Volume']) else None,
    )
    for _, row in df.iterrows()
]

cursor.executemany(
    '''
        INSERT INTO stock_prices
        (trade_date, stock_name, open_price, high_price, low_price, close_price, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''',
    rows,
)

conn.commit()
print(f'All data loaded! Inserted rows: {len(rows)}')
cursor.close()
conn.close()