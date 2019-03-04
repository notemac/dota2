import os
import logging
import mysql.connector
from mysql.connector import errorcode
import d2parser

#logging.basicConfig(format='%(asctime)s %(levelname)s: file db.py: %(message)s', 
#                    datefmt='%m/%d/%Y %I:%M:%S %p',
#                    filename='logs.txt', level=logging.DEBUG)



# Подключение к БД
def connectDB():
  config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'dota2scoring',
    'raise_on_warnings': False 
  }
  db = mysql.connector.connect(**config)
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


# Получаем все player_id из таблицы top500_solo_mmr
def selectTop500SoloMMR(db):
  query = ('SELECT player_id FROM top500_solo_mmr')
  cursor = db.cursor()
  cursor.execute(query)
  playersID = []
  for (id,) in cursor:
    playersID.append(id)
  cursor.close()
  return playersID

# Получаем всех героев из таблицы heroes
def selectHeroes(db, isBufferedCursor):
  query = ('SELECT name FROM heroes')
  cursor = db.cursor(isBufferedCursor)
  cursor.execute(query)
  return cursor

def deleteTop500SoloMMRPlayers(db, playersID):
  cursor = db.cursor()
  query = ('DELETE FROM top500_solo_mmr WHERE player_id = %s')
  cursor.executemany(query, playersID)
  db.commit()
  cursor.close()

# Обновляем таблицу top500_solo_mmr
def insertTop500SoloMMR(db, playersInfo):
  cursor = db.cursor()
  query = ('INSERT IGNORE INTO top500_solo_mmr (player_id, player_name) VALUES(%s, %s)')
  cursor.executemany(query, playersInfo)
  db.commit()
  cursor.close()

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
def selectTeamsIDName(db, isBufferedCursor=False):
  query = ('SELECT id, name FROM teams')
  cursor = db.cursor(buffered=isBufferedCursor)
  cursor.execute(query)
  return cursor

def select(db, tableName, columnNames):
  query = ('SELECT {} FROM {}'.format(columnNames, tableName))
  cursor = db.cursor()
  cursor.execute(query)
  result = tuple([[] for name in cursor.column_names])
  for row in cursor:
    for i in range(0, len(row)):
      result[i].append(row[i])
  cursor.close()
  return result

def isMatchExist(db, matchID):
  query = ('SELECT COUNT(*) FROM matches WHERE id = {}'.format(matchID))
  cursor = db.cursor(buffered=True)
  cursor.execute(query)
  ((count,),) = cursor
  cursor.close()
  return count == 1

def selectTeamLastMatchDate(db, id, isBufferedCursor=True):
  query = ('SELECT date FROM matches WHERE loser = {} or winner = {} ORDER BY date DESC LIMIT 1'.format(id, id))
  cursor = db.cursor(buffered=isBufferedCursor)
  cursor.execute(query)
  ((date,),) = cursor
  cursor.close()
  return str(date)

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

def insertHeroCounters(db, hero, counters):
  cursor = db.cursor()
  query = ('INSERT INTO counters (hero, counters, disadvantage) VALUES(%s, %s, %s)')
  for (counter, disadvantage) in counters:
    cursor.execute(query, (hero, counter, disadvantage))
  db.commit()
  cursor.close()

# Добавление новой команды
def insertTeam(id, name, founded, popular):
  db = connectDB()
  cursor = db.cursor()
  query = ('INSERT IGNORE INTO teams (id, name, founded, popular) VALUES(%s, %s, %s, %s)')
  cursor.execute(query, (id, name, founded, 0))
  db.commit()
  cursor.close()
  db.close()



#insertTeams('./assets/teams9.txt')
#updateTop500SoloMMR('./assets/top500solommr.txt')
#insertHeroes(db, './assets/heroes.txt')
#insertTop500SoloMMR(db, './assets/top500solommr.txt')