import os
import logging
import mysql.connector
from mysql.connector import errorcode
import d2parser

logging.basicConfig(format='%(asctime)s %(levelname)s: file db.py: %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='logs.txt', level=logging.DEBUG)

DB_CONFIG = {
  'user': 'root',
  'password': '',
  'host': '127.0.0.1',
  'database': 'dota2scoring',
  'raise_on_warnings': False
}

# Подключение к БД
def connectDB(config):
  try:
    db = mysql.connector.connect(**config)
  except mysql.connector.Error as err:
    logging.error(err.msg)
    os._exit(1)
  else:
    return db

# Заполняем таблицу heroes
# Таблиц heroes содержит информацию о героях
def insertHeroes(db, inputFile):
  print('insertHeroes(db, inputFile) starting')
  cursor = db.cursor()
  query = ('INSERT INTO heroes (name, name2) VALUES(%s, %s)')
  data = []
  with open(inputFile, mode='r', encoding='utf-8') as file:
    for line in file:
      #Если name = "Nature's Prophet", то name2 = "natures-prophet"
      name = line.strip();
      name2 = name.lower().replace(' ', '-').replace('\'', '')
      data.append((name, name2)) 
  cursor.executemany(query, data)
  db.commit()
  cursor.close()
  print('insertHeroes(db, inputFile) completed')


def getDataForUpdateTop500SoloMMR(inputFile):
  data = []
  with open(inputFile, mode='r', encoding='utf-8') as file:
    for line in file:
      #Если line = "154715080 Fnatic.Abed", то parts[0] = 154715080 и parts[2] = "Fnatic.Abed"
      parts = line.strip().partition(' ');
      data.append((int(parts[0]), parts[2]))
  return data

# Получаем все player_id из таблицы top500_solo_mmr
def selectTop500SoloMMR(db):
  query = ('SELECT player_id FROM top500_solo_mmr')
  cursor = db.cursor()
  cursor.execute(query)
  return cursor

# Обновляем таблицу top500_solo_mmr
def updateTop500SoloMMR(inOutFile):
  d2parser.parseTop500SoloMMR(inOutFile)
  addData = getDataForUpdateTop500SoloMMR(inOutFile)
  # список addID содержит только ID игроков
  addID, deleteID = [data[0] for data in addData], []
  db = connectDB(DB_CONFIG)
  # Находим игроков, которые уже не входят в топ-500
  cursor = selectTop500SoloMMR(db)
  for (playerID,) in cursor: 
    if playerID not in addID: # type(playerID) == Integer
      deleteID.append((playerID,))
  # Удаляем этих игроков
  if (len(deleteID) > 0):
    query = ('DELETE FROM top500_solo_mmr WHERE player_id = %s')
    cursor.executemany(query, deleteID)
    db.commit()
  #Обновляем таблицу top500_solo_mmr (INSERT IGNORE для пропуска дубликатов)
  query = ('INSERT IGNORE INTO top500_solo_mmr (player_id, player_name) VALUES(%s, %s)')
  cursor.executemany(query, addData)
  db.commit()
  cursor.close()
  db.close()



#updateTop500SoloMMR('./assets/top500solommr.txt')
#insertHeroes(db, './assets/heroes.txt')
#insertTop500SoloMMR(db, './assets/top500solommr.txt')