import os
import logging
import mysql.connector
from mysql.connector import errorcode
import d2parser

logging.basicConfig(format='%(asctime)s %(levelname)s: file db.py: %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='logs.txt', level=logging.DEBUG)



# Подключение к БД
def connectDB():
  config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'dota2scoring',
    'raise_on_warnings': False 
  }
  try:
    db = mysql.connector.connect(**config)
  except mysql.connector.Error as err:
    logging.error(err.msg)
    os._exit(1)
  else:
    return db
  return None


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
  db = connectDB()
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

# Заполняем таблицу teams
def insertTeams(inputFile):
  teams = []
  with open(inputFile, mode='r', encoding='utf-8') as file:
    lines = file.readlines()
    for i in range(0, len(lines), 5):
      teams.append(tuple([line.strip() for line in lines[i:i+5]])) 

  db = connectDB()
  cursor = db.cursor()
  query = ('INSERT IGNORE INTO teams (id, name, dcp1819_points, dcp_points, founded) '
            'VALUES(%s, %s, %s, %s, %s)')
  cursor.executemany(query, teams)
  db.commit()
  cursor.close()
  db.close()

# Получаем все id из таблицы teams
def selectTeamsIDName(db, bufferedCursor=False):
  query = ('SELECT id, name FROM teams')
  cursor = db.cursor(buffered=bufferedCursor)
  cursor.execute(query)
  return cursor

# Таблица matches содержит инф-цию о матчах
def insertMatch(db, matchDetails):
  cursor = db.cursor()
  query = ('INSERT IGNORE INTO matches (id, winner, wp1, wp2, wp3, wp4, wp5, wh1, wh2, wh3, wh4, wh5, '
            'loser, lp1, lp2, lp3, lp4, lp5, lh1, lh2, lh3, lh4, lh5, wgpm, lgpm, date, duration) '
            'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '
            '%s, %s, %s, %s, %s, %s, %s)')
  cursor.execute(query, matchDetails)
  db.commit()
  cursor.close()



#insertTeams('./assets/teams9.txt')
#updateTop500SoloMMR('./assets/top500solommr.txt')
#insertHeroes(db, './assets/heroes.txt')
#insertTop500SoloMMR(db, './assets/top500solommr.txt')