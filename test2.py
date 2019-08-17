#database test
import sqlite3
db_filename = 'test.db'

db = sqlite3.connect(db_filename, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
cursor = db.cursor()
#cursor.execute('''CREATE TABLE IF NOT EXISTS coin_premium(date timestamp, KRW2USD FLOAT, USD2KRW FLOAT, KRW_ASK FLOAT, KRW_BID FLOAT, USD_ASK FLOAT, USD_BID FLOAT, EXCHANGE_RATE FLOAT, KRW2USD_weight FLOAT, USD2KRW_weight FLOAT, balance_krw FLOAT, balance_usd FLOAT, balance_btc FLOAT)''')
cursor.execute('''DELETE FROM coin_premium WHERE KRW_ASK == 0.0''')
db.commit()
        