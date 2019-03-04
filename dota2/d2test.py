import d2db
import os
import d2parser
import time
import requests
import json
# Для парсинга динамически подгружаемых страниц используем модуль selenium + chromedriver.exe
from selenium import webdriver 
#db = d2db.connectDB()
#db.close()

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
url = 'https://opendota.com/request#4145911655'

#driver = webdriver.Chrome('D:\\programFiles\\chromedriver.exe') 
#driver.implicitly_wait(10) # time.sleep(10) 10 секунд а щагрузку страницы
#driver.get(url);
#textHtml = driver.page_source
#driver.quit()
#print(textHtml)



#driver = webdriver.Chrome('D:\\programFiles\\chromedriver.exe')
#count = 0
#for id in matchesID:
#  count += 1
#  #if count == 100:
#  #  count = 0
#  #  time.sleep(300)
#  #if os.path.getsize('./assets/opendota/{}.txt'.format(id)) < 200:
#  if os.path.isfile('./assets/opendota/26/{}.txt'.format(id)):
#    driver.get('https://opendota.com/request#{}'.format(id));
#    time.sleep(3)
#driver.quit()

def GoldInfo(matchID):
  with open('./assets/opendota/{}.txt'.format(matchID), mode='r', encoding='utf-8') as file:
    parsed_string = json.loads(file.read())
  players = parsed_string['players'] 
  gold1 = players[0]['gold_per_min'] + players[1]['gold_per_min'] + players[2]['gold_per_min'] + players[3]['gold_per_min'] + players[4]['gold_per_min']
  gold2 = players[5]['gold_per_min'] + players[6]['gold_per_min'] + players[7]['gold_per_min'] + players[8]['gold_per_min'] + players[9]['gold_per_min']
  print(gold1, gold1/5.0, gold2, gold2/5.0)
  return 

#GoldInfo(2531259945)


def ScoreInfo():
  matchesID = []
  with open('./assets/opendota/matches.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      matchesID.append(line.strip())

  parsed_string = ''
  good_count = 0
  score = 0 
  id_score = []

  for id in matchesID:
    if os.path.isfile('./assets/opendota/{}.txt'.format(id)):
      with open('./assets/opendota/{}.txt'.format(id), mode='r', encoding='utf-8') as file:
        parsed_string = json.loads(file.read())
      players = parsed_string['players'] 
      d1 = players[0]['deaths'] + players[1]['deaths'] + players[2]['deaths'] + players[3]['deaths'] + players[4]['deaths']
      d2 = players[5]['deaths'] + players[6]['deaths'] + players[7]['deaths'] + players[8]['deaths'] + players[9]['deaths']
      k1 = players[0]['kills'] + players[1]['kills'] + players[2]['kills'] + players[3]['kills'] + players[4]['kills']
      k2 = players[5]['kills'] + players[6]['kills'] + players[7]['kills'] + players[8]['kills'] + players[9]['kills']
      g1 = players[0]['gold_per_min'] + players[1]['gold_per_min'] + players[2]['gold_per_min'] + players[3]['gold_per_min'] + players[4]['gold_per_min']
      g2 = players[5]['gold_per_min'] + players[6]['gold_per_min'] + players[7]['gold_per_min'] + players[8]['gold_per_min'] + players[9]['gold_per_min']
      d = abs(d1 - d2)
      k = abs(k1 - k2)
      if abs(g1-g2) >= 1500:
        id_score.append([id, g1, g2, abs(g1-g2)])
      #for player in players:
      #  score += player['deaths']
      #duration = parsed_string['duration']
      #if (k1 + k2 <= 30) and (duration >= 35*60): #or (duration <= 599)
        #id_score.append([id, score, score1, score2, '{}:{}'.format(int(duration/60), duration%60)])
        #id_score.append([id, k1+k2, duration])
      #score = 0

  from operator import itemgetter
  result = sorted(id_score, key=itemgetter(3), reverse=False)
  print(len(result))
  for pair in result:
    print(pair)
  return


#for id in matchesID:
#  #if os.path.getsize('./assets/opendota/{}.txt'.format(id)) < 200:
#  if os.path.isfile('./assets/opendota/27/{}.txt'.format(id)):
#    time.sleep(1)
#    text = d2parser.parseMatchDetailsOpendota(id)
#    if len(text) > os.path.getsize('./assets/opendota/{}.txt'.format(id)):
#      with open('./assets/opendota/{}.txt'.format(id), mode='w', encoding='utf-8') as file:
#        file.write(text)
#    else:
#      print(id)

#for id in matchesID:
#  if os.path.isfile('./assets/opendota/27/{}.txt'.format(id)):
#    with open('./assets/opendota/27/{}.txt'.format(id), mode='r', encoding='utf-8') as file:
#      parsed_string = json.loads(file.read())
#    #if parsed_string['radiant_score'] is None or parsed_string['dire_score'] is None:
#    #  print(id, None)
#    #  continue
#    players = parsed_string['players'] 
#    for player in players:
#      if player is None:
#        score = 0
#        break
#      score += player['deaths']
#    if score > 11:
#      id_score.append([id, score])
#      good_count += 1
#      #driver.implicitly_wait(10) # time.sleep(10) 10 секунд а щагрузку страницы
#      time.sleep(7)
#      driver.get('https://opendota.com/request#{}'.format(id));
#      score = 0
#    else:
#      id_score.append([id, 0])
#print(good_count)
#from operator import itemgetter
## Сортировка по количеству убийств по возрастанию
#result = sorted(id_score, key=itemgetter(1), reverse=False)
#for ii in result:
#  print(ii)
#driver.quit()
    #with open('./assets/opendota/{}.txt'.format(id), mode='w', encoding='utf-8') as file:
    #  file.write(d2parser.parseMatchDetailsOpendota(id))

# Обновление матчей
#teamsID = []
#with open('./assets/teams2.txt', mode='r', encoding='utf-8') as file:
#  for line in file:
#    teamsID.append(int(line.strip()))

#db = d2db.connectDB()
#cursor = db.cursor()
#matchID, winner, loser = d2db.select(db, tableName='matches', columnNames='id, winner, loser')
#for id, w, l in zip(matchID, winner, loser):
#  if w not in teamsID and l not in teamsID:
#    if w == 0 or l == 0:
#      continue
#    print(id, w, l)
#    cursor.execute('DELETE FROM matches WHERE id = {}'.format(id))
#    db.commit()
#    if os.path.isfile('./assets/opendota/{}.txt'.format(id)):
#      os.remove('./assets/opendota/{}.txt'.format(id))
#cursor.close()
#db.close()

def GameMode():
  matchesID = []
  with open('./assets/opendota/game_mode.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      matchesID.append(line.strip())
  
  for id in matchesID:
    with open('./assets/opendota/{}.txt'.format(id), mode='r', encoding='utf-8') as file:
      parsed_string = json.loads(file.read())
      if parsed_string['game_mode'] == 23:
        print(id, 23)
  return

def UpdateGPM():
  matchesID = []
  with open('./assets/opendota/matches.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      matchesID.append(line.strip())

  db = d2db.connectDB()
  cursor = db.cursor()
  query = ('UPDATE matches SET wgpm = {}, lgpm = {} WHERE id = {}')
  for id in matchesID:
    if os.path.isfile('./assets/opendota/{}.txt'.format(id)):
      with open('./assets/opendota/{}.txt'.format(id), mode='r', encoding='utf-8') as file:
        parsed_string = json.loads(file.read())
      players = parsed_string['players'] 
      radiant_score = players[0]['gold_per_min'] + players[1]['gold_per_min'] + players[2]['gold_per_min'] + players[3]['gold_per_min'] + players[4]['gold_per_min']
      dire_score = players[5]['gold_per_min'] + players[6]['gold_per_min'] + players[7]['gold_per_min'] + players[8]['gold_per_min'] + players[9]['gold_per_min']
      if parsed_string['radiant_win']:
        cursor.execute(query.format(radiant_score, dire_score, id))
      else:
        cursor.execute(query.format(dire_score, radiant_score, id))
      db.commit()
  cursor.close()
  db.close()
  return



def DeleteBadMatches():
  matchesID = []
  with open('./assets/opendota/matches.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      matchesID.append(line.strip())

  db = d2db.connectDB()
  cursor = db.cursor()
  query = ('DELETE FROM matches WHERE id = {}')
  for id in matchesID:
    if os.path.isfile('./assets/opendota/bad/{}.txt'.format(id)):
      cursor.execute(query.format(id))
      db.commit()
  cursor.close()
  db.close()
  return

#DeleteBadMatches()