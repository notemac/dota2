
# Вспомогательный модуль для подсчета промежуточной статистики
import time
import d2db
import d2parser
import os
import json
import statistics
from random import randint
# date = "2018-11-09 06:40:23"
def dateToTimestamp(date):
  if date is None:
    return date
  parts = date.partition('-')
  year = int(parts[0])*360*24*3600
  parts = parts[2].partition('-')
  month = int(parts[0])*30*24*3600
  parts = parts[2].partition(' ')
  day = int(parts[0])*24*3600
  parts = parts[2].partition(':')
  hour = int(parts[0])*3600
  parts = parts[2].partition(':')
  minute = int(parts[0])*60
  second = int(parts[2])
  return year + month + day + hour + minute + second

# duration = "01:22:49"
def durationToTimestamp(duration):
  parts = duration.partition(':')
  hour = int(parts[0])*60*60
  parts = parts[2].partition(':')
  minute = int(parts[0])*60
  second = int(parts[2])
  return hour + minute + second

# Сколько каждая команда сыграла всего матчей на текущий момент
def getTeamsRecord():
  db = d2db.connectDB()
  cursor = d2db.selectTeamsIDName(db, bufferedCursor=True)
  teams = []
  for (id, name,) in cursor:
    print(id)
    record = int(d2parser.parseTeamRecord(id))
    time.sleep(0.5)
    lastMatchDate = d2parser.parseTeamLastMatchDate(id)
    time.sleep(0.5)
    teams.append([lastMatchDate, record, name, id, dateToTimestamp(lastMatchDate)])
  from operator import itemgetter
  # Cортируем по элементу с индексом N: itemgetter(N)
  teams = sorted(teams, key=itemgetter(4), reverse=False)
  with open('./assets/teams_record2.txt', mode='w', encoding='utf-8') as file:
    for team in teams:
      file.write('{} {} {} {}\n'.format(team[0], team[1], team[2], team[3]))
  cursor.close()
  db.close()

def getDataForUpdateTop500SoloMMR(inputFile):
  data = []
  with open(inputFile, mode='r', encoding='utf-8') as file:
    for line in file:
      #Если line = "154715080 Fnatic.Abed", то parts[0] = 154715080 и parts[2] = "Fnatic.Abed"
      parts = line.strip().partition(' ');
      data.append((int(parts[0]), parts[2]))
  return data

# Обновляем таблицу top500_solo_mmr
def updateTop500SoloMMR(inOutFile):
  #d2parser.parseTop500SoloMMR(inOutFile)
  playersInfo = getDataForUpdateTop500SoloMMR(inOutFile)
  #***УДАЛЕНИЕ ИГРОКОВ, КОТОРЫЕ УЖЕ НЕ В ХОДЯТ В ТОП-500***
  ## список addID содержит только ID игроков
  #addID, deleteID = [info[0] for info in playersInfo], []
  db = d2db.connectDB()
  ## Находим игроков, которые уже не входят в топ-500
  #cursor = d2db.selectTop500SoloMMR(db)
  #for (playerID,) in cursor: 
  #  if playerID not in addID: # type(playerID) == Integer
  #    deleteID.append((playerID,))
  #cursor.close()
  ## Удаляем этих игроков
  #if (len(deleteID) > 0):
  #  d2db.deleteTop500SoloMMRPlayers(db, deleteID)
  #Обновляем таблицу top500_solo_mmr
  d2db.insertTop500SoloMMR(db, playersInfo)
  db.close()


# Добавление новой команды
def opendota():
  matchesID = []
  with open('./assets/opendota/matches.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      matchesID.append(line.strip())
      
  for i in range(4721, len(matchesID)):
    print(matchesID[i])
    time.sleep(1) #разрешено 60 вызовов в минуту и 50000 в месяц
    with open('./assets/opendota/{}.txt'.format(matchesID[i]), mode='w', encoding='utf-8') as file:
      file.write(d2parser.parseMatchDetailsOpendota(matchesID[i]))
  return

# Добавление новой команды
def addTeam(id):
  name, founded = d2parser.parseTeamNameAndFounded(id)
  d2db.insertTeam(id, name, founded, False)

# Обновляем таблицу matches для конкретной команды
def updateTeamMatches(teamID, startPage, headers, lastMatchDate=None):
  bad_proxies = []
  from itertools import cycle
  from random import shuffle
  shuffle(headers)
  HEADER_POOL = cycle(headers)
  START_TIMESTAMP = dateToTimestamp('2016-05-01 00:00:00') # 2017-03-09 00:00:00 Начало киевского мейджора
  isStop = False
  isNextProxy = True
  print('teamID: ', teamID)
  record = d2parser.parseTeamMatchesRecord(teamID)
  # кол-во страниц с матчами
  if (record % 20) == 0:
    pagesCount = int(record/20)
  else:
    pagesCount = int(record/20) + 1
  db = d2db.connectDB()
  for page in range(startPage, pagesCount+1):
    print('page: ', page)
    print('parse proxies')
    d2parser.parseProxies()
    proxies = []
    with open('./assets/proxies.txt', mode='r', encoding='utf-8') as file:
      for line in file:
        proxy = line.strip().partition(' ')
        proxies.append({proxy[0]: proxy[2]})
    shuffle(proxies)
    PROXY_POOL = cycle(proxies)
    time.sleep(3) # PAUSE
    # список матчей на странице
    tableRows = d2parser.parseMatchesOnPage(teamID, page)
    for tr in tableRows:
      if isNextProxy:
        proxy = next(PROXY_POOL)
        while proxy in bad_proxies:
          proxy = next(PROXY_POOL)
        header = next(HEADER_POOL)
      print(proxy)
      print(header)
      # пропускаем незасчитанные игры
      if tr.has_attr('class'): #<tr class="inactive">
        print('Inactive game')
        isNextProxy = False
        continue
      matchID, date, duration, winner, loser = d2parser.parseMatchOverview(teamID, tr)
      print('matchID: ', matchID)
      if d2db.isMatchExist(db, matchID):
        print('match exist')
        if (dateToTimestamp(date) < START_TIMESTAMP) or (lastMatchDate == date):
          print('Stopped:' + date)
          isStop = True
          break
        isNextProxy = False
        continue
      else:
        isNextProxy = True
      if (dateToTimestamp(date) < START_TIMESTAMP) or (lastMatchDate == date):
        print('Stopped:' + date)
        isStop = True
        break
      time.sleep(1.5) # PAUSE
      wplayers, lplayers, wheroes, lheroes, wgpm, lgpm = [], [], [], [], 0, 0
      while True:
        try:
          wplayers, lplayers, wheroes, lheroes, wgpm, lgpm = d2parser.parseMatchDetails(matchID, proxy, header)
          break
        except AssertionError as exc: # некорректный матч: https://www.dotabuff.com/matches/2962623862
          print(exc.args)
          break
        except:
          print('BAD PROXY')
          bad_proxies.append(proxy)
          while proxy in bad_proxies:
            proxy = next(PROXY_POOL)
          print('NEXT PROXY {}'.format(proxy))
      # Пропускаем некорректные игры. Пример: https://www.dotabuff.com/matches/3012665523
      if (len(wplayers) < 5) or (len(lplayers) < 5):
        print('Incorrect game')
        continue
      matchDetails = (matchID, winner, *tuple(wplayers), *tuple(wheroes), 
                      loser, *tuple(lplayers), *tuple(lheroes), wgpm, lgpm, date, duration)
      d2db.insertMatch(db, matchDetails)
    if isStop:
      break
  db.close()

# Обновляем таблицу matches
def updateMatches():
  # Обновление матчей
  teamsID = []
  with open('./assets/teams2.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      teamsID.append(line.strip())

  ua = []
  with open('./assets/ua.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      ua.append({'User-Agent': line.strip()})

  #3573107497 до этого матча все убрать
  #3438821932
  teamNumber = 176 #порядковый номер команды в file.txt (отсчет с 0)
  startPage = 1
  for i in range(teamNumber, len(teamsID)):
    #teamID = teams[i].partition(' ')[0]
    #if  teams[i].partition(' ')[1] == '19':
    #  print('break 19')
    #  break
    db = d2db.connectDB()
    date = d2db.selectTeamLastMatchDate(db, teamsID[i]) #парсим матчи только до этой даты
    db.close()
    updateTeamMatches(teamsID[i], startPage, headers=ua, lastMatchDate=date)
    print('TEAM {} UPDATED'.format(teamsID[i]))
    startPage = 1

#updateMatches()

def addCounters():
  db = d2db.connectDB()
  cursor = d2db.selectHeroes(db, isBufferedCursor=True)
  for (hero,) in cursor:
    print(hero)
    counters = d2parser.parseHeroCounters(hero)
    print(counters)
    d2db.insertHeroCounters(db, hero, counters)
    time.sleep(0.5)
  cursor.close()
  db.close()
 

#Выгрузка данных для Deductor
def DEDUCTOR():

  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  (hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()
  # контрпики (пример: counters[zeus][lina] = 10.0)
  for h in hero:
    counters[h] = dict()
  for h, c, d in zip(hero, counter, disadvantage):
    counters[h][c] = d

  factors = [] # входные переменные логистической регрессии  
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\n')
    for i in range(0, len(matches)):
      match = matches[i]
      #matchID = int(match[0])
      winner = match[1]
      loser = match[12]
      # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
      if (int(winner) not in teamsID) or (int(loser) not in teamsID):
        continue
      wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
      wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
      lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
      lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
      date, duration = int(match[25]), int(match[26])
      wkills, lkills = int(match[27]), int(match[27])
      # 1) Разница в количестве топ500 игроков в матче между командами
      wtop500_count = len([1 for wp in [wp1,wp2,wp3,wp4,wp5] if wp in playersID])
      ltop500_count = len([1 for lp in [lp1,lp2,lp3,lp4,lp5] if lp in playersID])
      F_TOP500D, F_TOP500R  = wtop500_count - ltop500_count, wtop500_count/5
      F2_TOP500D, F2_TOP500R = ltop500_count - wtop500_count, ltop500_count/5
      # 2) Доля матчей, в которых команда проиграла и которые длились больше 35, 40 мин
      # Были вычислены statistics.median = 34:33, statistics.mean = 35:59
      # Должно быть проиграно 5 матчей, иначе значения по умолчанию
      wduration, lduration, = [], []
      w_winrate, l_winrate = [1, 1], [1, 1] # [кол-во побед, кол-во поражений]
      for j in range(0, i): #просматриваем все матчи до текущего матча
        if matches[j][12] == winner: #если текущий winner проиграл в матче
          wduration.append(int(matches[j][26]))
          w_winrate[1] += 1
        elif matches[j][12] == loser: #если текущий loser проиграл в матче
          lduration.append(int(matches[j][26]))
          l_winrate[1] += 1
        if matches[j][1] == winner: #если текущий winner выиграл в матче
          w_winrate[0] += 1
        elif matches[j][1] == loser: #если текущий loser выиграл в матче
          l_winrate[0] += 1

      _35min, _40min = 2100, 2400
      if len(wduration) >= 5: #должно быть проиграно 5 матчей
        wr35 = len([1 for dur in wduration if dur >= _35min])/len(wduration)
        wr40 = len([1 for dur in wduration if dur >= _40min])/len(wduration)
      else:
        wr35 = 0.4
        wr40 = 0.3
      if len(lduration) >= 5: #должно быть проиграно 5 матчей
        lr35 = len([1 for dur in lduration if dur >= _35min])/len(lduration)
        lr40 = len([1 for dur in lduration if dur >= _40min])/len(lduration)
      else:
        lr35 = 0.4
        lr40 = 0.3
      F_LMG35, F_LMG40 = round(wr35-lr35, 4), round(wr40-lr40, 4)
      F2_LMG35, F2_LMG40 = round(lr35-wr35, 4), round(lr40-wr40, 4)
      # 3) Средняя длина матчей, в которых команда проиграла
      if len(wduration) > 0:
        if len(wduration) == 1:
          w_avg = round((wduration[0] + 1800)/2) # 1800 == 30 min
        else:
          wduration.append(1800)
          w_avg = round(statistics.mean(wduration))
      else:
        w_avg = 1800
      if len(lduration) > 0:
        if len(lduration) == 1:
          l_avg = round((lduration[0] + 1800)/2) # 1800 == 30 min
        else:
          lduration.append(1800)
          l_avg = round(statistics.mean(lduration))
      else:
        l_avg = 1800
      F_LMAVG = w_avg - l_avg
      F2_LMAVG = l_avg-w_avg 
      # 4) Общий винрейт команд за все время
      F_WINRATE = round(w_winrate[0]/sum(w_winrate)*100) - round(l_winrate[0]/sum(l_winrate)*100)
      F2_WINRATE = round(l_winrate[0]/sum(l_winrate)*100) - round(w_winrate[0]/sum(w_winrate)*100)
      # 5) Количество сыгранных матчей за все время
      F_NMATCHES = sum(w_winrate) - sum(l_winrate)
      F2_NMATCHES = sum(l_winrate) - sum(w_winrate)
      # 6) Контрпики (сумма, медиана, +-1)
      # Отрицательный disadvantage означает, что первый герой "контрит" второго
      F_w_dis, F_l_dis, F_w_dis2, F_l_dis2 = 0, 0, 0, 0
      for wh in [wh1,wh2,wh3,wh4,wh5]:
        for lh in [lh1,lh2,lh3,lh4,lh5]:
          F_w_dis += counters[wh][lh]
          F_l_dis += counters[lh][wh]
          if counters[wh][lh] < -1.0:
            F_w_dis2 -= 1
          elif counters[wh][lh] > 1.0:
            F_w_dis2 += 1
          if counters[lh][wh] < -1.0:
            F_l_dis2 -= 1
          elif counters[lh][wh] > 1.0:
            F_l_dis2 += 1
      F_w_dis, F_l_dis = round(F_w_dis, 4), round(F_l_dis, 4)
      factors.append([[F_TOP500D, F_TOP500R, F_LMG35, F_LMG40, F_LMAVG, F_WINRATE, F_NMATCHES, F_w_dis, F_w_dis2],
                [F2_TOP500D, F2_TOP500R, F2_LMG35, F2_LMG40, F2_LMAVG, F2_WINRATE, F2_NMATCHES, F_l_dis, F_l_dis2]])
      #factors.append([ str(count), str(founded[teamsID.index(winner)]), str(-count), str(founded[teamsID.index(loser)]) ])
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\twin\n'.format(factor[0][0], factor[0][1], factor[0][2], factor[0][3], factor[0][4], factor[0][5], factor[0][6], factor[0][7], factor[0][8]))
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\tlose\n'.format(factor[1][0], factor[1][1], factor[1][2], factor[1][3], factor[1][4], factor[1][5], factor[1][6], factor[1][7], factor[1][8]))
      #file.write('{}\t{}\twin\n'.format(factor[0],factor[1]))
      #file.write('{}\t{}\tlose\n'.format(factor[2],factor[3]))
  return

#DEDUCTOR()

#Доля матчей, в которых команда проиграла и которые длились больше 30 min
def DEDUCTOR2():
  matches = []
  # matches3.txt - вся таблица matches
  with open('./assets/matches3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  (hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()
  for h in hero:
    counters[h] = dict()
  for h, c, d in zip(hero, counter, disadvantage):
    counters[h][c] = d
  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    loser = match[12]
    lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    # 2) Доля матчей, в которых команда проиграла и которые длились больше 30 min
    wduration, lduration, = [], []
    w_winrate, l_winrate = [1, 1], [1, 1] # [кол-во побед, кол-во поражений]
    for j in range(0, i): #просматриваем все матчи до текущего матча
      if matches[j][12] == winner: #если текущий winner проиграл в матче
        wduration.append(int(matches[j][26]))
        w_winrate[1] += 1
      elif matches[j][12] == loser: #если текущий loser проиграл в матче
        lduration.append(int(matches[j][26]))
        l_winrate[1] += 1
      if matches[j][1] == winner: #если текущий winner выиграл в матче
        w_winrate[0] += 1
      elif matches[j][1] == loser: #если текущий loser выиграл в матче
        l_winrate[0] += 1

    _30min = 1800
    if len(wduration) >= 5: #должно быть проиграно 5 матчей
      wr30 = len([1 for dur in wduration if dur >= _30min])/len(wduration)
    else:
      wr30 = 0.4
    if len(lduration) >= 5: #должно быть проиграно 5 матчей
      lr30 = len([1 for dur in lduration if dur >= _30min])/len(lduration)
    else:
      lr30 = 0.4
    F_LMG30 = round(wr30-lr30, 4)
    F2_LMG30 = round(lr30-wr30, 4)
    factors[IDX].append(F_LMG30)
    factors[IDX+1].append(F2_LMG30)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10]))
  return

#2) Винрейт между текущими командами
def DEDUCTOR3():
  matches = []
  # matches3.txt - вся таблица matches
  with open('./assets/matches3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  (hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()
  for h in hero:
    counters[h] = dict()
  for h, c, d in zip(hero, counter, disadvantage):
    counters[h][c] = d
  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    loser = match[12]
    lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    # 2) Винрейт между текущими командами
    winrate_p = [1, 1] # [кол-во побед виннера, кол-во побед лузера]
    for j in range(0, i): #просматриваем все матчи до текущего матча
      if matches[j][12] == loser and matches[j][1] == winner:
        winrate_p[0] += 1
      elif matches[j][12] == winner and matches[j][1] == loser:
        winrate_p[1] += 1
    F_WINRATE = round(winrate_p[0]/sum(winrate_p)*100)
    F2_WINRATE = round(winrate_p[1]/sum(winrate_p)*100)
    factors[IDX].append(F_WINRATE)
    factors[IDX+1].append(F2_WINRATE)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11]))
  return

#DEDUCTOR3()

#Доля матчей, в которых команда выиграла и которые длились меньше 20 min
def DEDUCTOR4():
  matches = []
  # matches3.txt - вся таблица matches
  with open('./assets/matches3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  (hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()
  for h in hero:
    counters[h] = dict()
  for h, c, d in zip(hero, counter, disadvantage):
    counters[h][c] = d
  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    loser = match[12]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    # 2) Доля матчей, в которых команда выиграла и которые длились меньше 20 min
    wduration, lduration, = [], []
    w_winrate, l_winrate = [1, 1], [1, 1] # [кол-во побед, кол-во поражений]
    for j in range(0, i): #просматриваем все матчи до текущего матча
      if matches[j][12] == winner: #если текущий winner проиграл в матче
        w_winrate[1] += 1
      elif matches[j][12] == loser: #если текущий loser проиграл в матче
        l_winrate[1] += 1
      if matches[j][1] == winner: #если текущий winner выиграл в матче
        wduration.append(int(matches[j][26]))
        w_winrate[0] += 1
      elif matches[j][1] == loser: #если текущий loser выиграл в матче
        lduration.append(int(matches[j][26]))
        l_winrate[0] += 1

    _20min = 1200
    if len(wduration) == 0:
      wr20 = 0
    else:
      wr20 = len([1 for dur in wduration if dur <= _20min])/len(wduration)
    if len(lduration) == 0:
      lr20 = 0
    else:
      lr20 = len([1 for dur in lduration if dur <= _20min])/len(lduration)
    F_WML20 = round(wr20-lr20, 4)
    F2_WML20 = round(lr20-wr20, 4)
    factors[IDX].append(F_WML20)
    factors[IDX+1].append(F2_WML20)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12]))
  return
#DEDUCTOR4()

#Разница между датами основания команд
def DEDUCTOR5():
  matches = []
  # matches3.txt - вся таблица matches
  with open('./assets/matches3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  (hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()
  for h in hero:
    counters[h] = dict()
  for h, c, d in zip(hero, counter, disadvantage):
    counters[h][c] = d
  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    loser = match[12]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    # 2) Разница между датами основания команд
    w_founded = dateToTimestamp(str(founded[teamsID.index(int(winner))]))
    l_founded = dateToTimestamp(str(founded[teamsID.index(int(loser))]))
    factors[IDX].append(w_founded - l_founded)
    factors[IDX+1].append(l_founded - w_founded)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13]))
  return
#DEDUCTOR5()

# Винрейт за героев
def DEDUCTOR6():
  matches = []
  # matches3.txt - вся таблица matches
  with open('./assets/matches3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  (hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()
  for h in hero:
    counters[h] = dict()
  for h, c, d in zip(hero, counter, disadvantage):
    counters[h][c] = d
  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    loser = match[12]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    # 2) Винрейт за героев
    w_winrate_h, l_winrate_h = [1, 1], [1, 1] # [кол-во побед, кол-во поражений]
    for j in range(0, i): #просматриваем все матчи до текущего матча
      w1,w2,w3,w4,w5 = matches[j][7], matches[j][8], matches[j][9], matches[j][10], matches[j][11]
      l1,l2,l3,l4,l5 = matches[j][18], matches[j][19], matches[j][20], matches[j][21], matches[j][22]
      if matches[j][12] == winner: #если текущий winner проиграл в матче
        w_winrate_h[1] += sum([1 for l in [l1,l2,l3,l4,l5] if l in [wh1,wh2,wh3,wh4,wh5]])
      elif matches[j][12] == loser: #если текущий loser проиграл в матче
        l_winrate_h[1] += sum([1 for l in [l1,l2,l3,l4,l5] if l in [lh1,lh2,lh3,lh4,lh5]])
      if matches[j][1] == winner: #если текущий winner выиграл в матче
        w_winrate_h[0] += sum([1 for w in [w1,w2,w3,w4,w5] if w in [wh1,wh2,wh3,wh4,wh5]])
      elif matches[j][1] == loser: #если текущий loser выиграл в матче
        l_winrate_h[0] += sum([1 for w in [w1,w2,w3,w4,w5] if w in [lh1,lh2,lh3,lh4,lh5]])
    F_HWINRATE = round(w_winrate_h[0]/sum(w_winrate_h)*100) - round(l_winrate_h[0]/sum(l_winrate_h)*100)
    F2_HWINRATE = round(l_winrate_h[0]/sum(l_winrate_h)*100) - round(w_winrate_h[0]/sum(w_winrate_h)*100)
    factors[IDX].append(F_HWINRATE)
    factors[IDX+1].append(F2_HWINRATE)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14]))
  return
#DEDUCTOR6()

# Винрейт против гереов соперника
def DEDUCTOR7():
  matches = []
  # matches3.txt - вся таблица matches
  with open('./assets/matches3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  (hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()
  for h in hero:
    counters[h] = dict()
  for h, c, d in zip(hero, counter, disadvantage):
    counters[h][c] = d
  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    loser = match[12]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    # 2) Винрейт против героев соперника
    w_winrate_h, l_winrate_h = [1, 1], [1, 1] # [кол-во побед, кол-во поражений]
    for j in range(0, i): #просматриваем все матчи до текущего матча
      w1,w2,w3,w4,w5 = matches[j][7], matches[j][8], matches[j][9], matches[j][10], matches[j][11]
      l1,l2,l3,l4,l5 = matches[j][18], matches[j][19], matches[j][20], matches[j][21], matches[j][22]
      if matches[j][12] == winner: #если текущий winner проиграл в матче
        w_winrate_h[1] += sum([1 for l in [lh1,lh2,lh3,lh4,lh5] if l in [w1,w2,w3,w4,w5]])
      elif matches[j][12] == loser: #если текущий loser проиграл в матче
        l_winrate_h[1] += sum([1 for w in [wh1,wh2,wh3,wh4,wh5] if w in [w1,w2,w3,w4,w5]])
      if matches[j][1] == winner: #если текущий winner выиграл в матче
        w_winrate_h[0] += sum([1 for l in [lh1,lh2,lh3,lh4,lh5] if l in [l1,l2,l3,l4,l5]])
      elif matches[j][1] == loser: #если текущий loser выиграл в матче
        l_winrate_h[0] += sum([1 for w in [wh1,wh2,wh3,wh4,wh5] if w in [l1,l2,l3,l4,l5]])
    F_HWINRATE = round(w_winrate_h[0]/sum(w_winrate_h)*100) - round(l_winrate_h[0]/sum(l_winrate_h)*100)
    F2_HWINRATE = round(l_winrate_h[0]/sum(l_winrate_h)*100) - round(w_winrate_h[0]/sum(w_winrate_h)*100)
    factors[IDX].append(F_HWINRATE)
    factors[IDX+1].append(F2_HWINRATE)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15]))
  return
#DEDUCTOR7()

# MATCHID
def DEDUCTOR8():
  matches = []
  # matches3.txt - вся таблица matches
  with open('./assets/matches3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  (hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()
  for h in hero:
    counters[h] = dict()
  for h, c, d in zip(hero, counter, disadvantage):
    counters[h][c] = d
  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    loser = match[12]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    factors[IDX].append(match[0])
    factors[IDX+1].append(match[0])
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16]))
  return
#DEDUCTOR8()


#Общий винрейт команд за 6 месяцев
def DEDUCTOR9():
  matches = []
  # matches3.txt - вся таблица matches
  with open('./assets/matches3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #counters = dict()
  db = d2db.connectDB()
  #(playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    loser = match[12]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    # 2) Общий винрейт команд за 6 месяцев
    month6x = 15552000
    w_winrate6, l_winrate6 = [1, 1], [1,1] # [кол-во побед виннера, кол-во побед лузера]
    for j in range(0, i): #просматриваем все матчи до текущего матча
      if abs(date - int(matches[j][25])) <= month6x:
        if matches[j][12] == winner: #если текущий winner проиграл в матче
          w_winrate6[1] += 1
        elif matches[j][12] == loser: #если текущий loser проиграл в матче
          l_winrate6[1] += 1
        if matches[j][1] == winner: #если текущий winner выиграл в матче
          w_winrate6[0] += 1
        elif matches[j][1] == loser: #если текущий loser выиграл в матче
          l_winrate6[0] += 1
    F_WINRATE6 = round(w_winrate6[0]/sum(w_winrate6)*100) - round(l_winrate6[0]/sum(l_winrate6)*100)
    F2_WINRATE6 = round(l_winrate6[0]/sum(l_winrate6)*100) - round(w_winrate6[0]/sum(w_winrate6)*100)
    factors[IDX].append(F_WINRATE6)
    factors[IDX+1].append(F2_WINRATE6)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17]))
  return

#DEDUCTOR9()

# Количество смертей
def DEDUCTOR10():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)
  # СРЕДНЕЕ ЧИСЛО УБИЙСТВ И СМЕРТЕЙ РАВНО 25
  #kills = []
  #for match in matches:
  #   kills.append(int(match[27]))
  #   kills.append(int(match[28])) 
  #print(statistics.mean(kills))
  #print(statistics.median(kills))

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    loser = match[12]
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    #date, duration = int(match[25]), int(match[26])
    wkills, lkills = int(match[27]), int(match[28])

    # 1) Среднее число смертей команды
    w_death_avg, l_death_avg = [25], [25] #по умолчанию 25
    wdl25_count, ldl25_count = 0, 0 #число матчей, в которых <= 25 смертей
    #w_winrate6, l_winrate6 = [1, 1], [1,1] # [кол-во побед виннера, кол-во побед лузера]
    for j in range(0, i): #просматриваем все матчи до текущего матча
      if matches[j][12] == winner: #если текущий winner проиграл в матче
        d = int(matches[j][27])
        w_death_avg.append(d)
        if d <= 25:
          wdl25_count += 1
      elif matches[j][12] == loser: #если текущий loser проиграл в матче
        d = int(matches[j][27])
        l_death_avg.append(d)
        if d <= 25:
          ldl25_count += 1
      if matches[j][1] == winner: #если текущий winner выиграл в матче
        d = int(matches[j][28])
        w_death_avg.append(d)
        if d <= 25:
          wdl25_count += 1
      elif matches[j][1] == loser: #если текущий loser выиграл в матче
        d = int(matches[j][28])
        l_death_avg.append(d)
        if d <= 25:
          ldl25_count += 1
    # 1) Среднее число смертей в матчах
    F_DEATH_AVG = round(statistics.mean(w_death_avg) - statistics.mean(l_death_avg)) #округляем до целого
    F2_DEATH_AVG = round(statistics.mean(l_death_avg) - statistics.mean(w_death_avg))
    # 2) Доля матчей, в которых число смертей <= 25
    F_DEATH_L25 = round((wdl25_count/len(w_death_avg) - ldl25_count/len(l_death_avg))*100) #в процентах от 0 до 100
    F2_DEATH_L25 = round((ldl25_count/len(l_death_avg) - wdl25_count/len(w_death_avg))*100) #в процентах от 0 до 100
    factors[IDX].append(F_DEATH_AVG)
    factors[IDX].append(F_DEATH_L25)
    factors[IDX+1].append(F2_DEATH_AVG)
    factors[IDX+1].append(F2_DEATH_L25)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19]))
  return

#DEDUCTOR10()

# Количество убийств
def DEDUCTOR11():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)
  # СРЕДНЕЕ ЧИСЛО УБИЙСТВ И СМЕРТЕЙ РАВНО 25
  #kills = []
  #for match in matches:
  #   kills.append(int(match[27]))
  #   kills.append(int(match[28])) 
  #print(statistics.mean(kills))
  #print(statistics.median(kills))

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #counters = dict()
  db = d2db.connectDB()
  #(playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    loser = match[12]
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    #date, duration = int(match[25]), int(match[26])
    wkills, lkills = int(match[27]), int(match[28])

    # 1) Среднее число убийств команды
    w_kill_avg, l_kill_avg = [25], [25] #по умолчанию 25
    for j in range(0, i): #просматриваем все матчи до текущего матча
      if matches[j][12] == winner: #если текущий winner проиграл в матче
        w_kill_avg.append(int(matches[j][28]))
      elif matches[j][12] == loser: #если текущий loser проиграл в матче
        l_kill_avg.append(int(matches[j][28]))
      if matches[j][1] == winner: #если текущий winner выиграл в матче
        w_kill_avg.append(int(matches[j][27]))
      elif matches[j][1] == loser: #если текущий loser выиграл в матче
        l_kill_avg.append(int(matches[j][27]))
    # 1) Среднее число убийств в матче
    F_KILL_AVG = round(statistics.mean(w_kill_avg) - statistics.mean(l_kill_avg)) #округляем до целого
    F2_KILL_AVG = round(statistics.mean(l_kill_avg) - statistics.mean(w_kill_avg))
    factors[IDX].append(F_KILL_AVG)
    factors[IDX+1].append(F2_KILL_AVG)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\tKILL_AVG\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20]))
  return

#DEDUCTOR11()


# Топ500 игроки (баллы)
def DEDUCTOR12():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  players = []
  with open('./assets/top500.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      player = line.strip()
      players.append(int(player))

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #counters = dict()
  db = d2db.connectDB()
  #(playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    loser = match[12]
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    #date, duration = int(match[25]), int(match[26])
    #wkills, lkills = int(match[27]), int(match[28])

    # 1) ТОП500 (баллы)
    wtop500, ltop500 = 0, 0
    for wp in [wp1,wp2,wp3,wp4,wp5]:
      try:
        idx = players.index(wp)
        if idx < 500:
          wtop500 += 3
        elif idx < 1000:
          wtop500 += 2
        else:
          wtop500 += 1
      except ValueError:
        foo = None
    for lp in [lp1,lp2,lp3,lp4,lp5]:
      try:
        idx = players.index(lp)
        if idx < 500:
          ltop500 += 3
        elif idx < 1000:
          ltop500 += 2
        else:
          ltop500 += 1
      except ValueError:
        foo = None
    F_TOP500B = wtop500 - ltop500
    F2_TOP500B = ltop500 - wtop500

    factors[IDX].append(F_TOP500B)
    factors[IDX+1].append(F2_TOP500B)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\tKILL_AVG\tTOP500B\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21]))
  return

#DEDUCTOR12()

# LMG35V2 и LMAVGV2
def DEDUCTOR13():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #counters = dict()
  db = d2db.connectDB()
  #(playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    loser = match[12]
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    #wkills, lkills = int(match[27]), int(match[28])

    # 1) Доля проигранных матчей <= 35 min LMG35V2
    _35min = 35*60
    wduration, lduration = [_35min], [_35min] #по умолчанию програно по одному матчу по 35 мин
    wlmg35_count, llmg35_count = 0, 0 #реальное количество проигранных матчей >= 35 min 

    for j in range(0, i): #просматриваем все матчи до текущего матча
      if matches[j][12] == winner: #если текущий winner проиграл в матче
        dur = int(matches[j][26])
        wduration.append(dur)
        if dur >= _35min: 
          wlmg35_count += 1
      elif matches[j][12] == loser: #если текущий loser проиграл в матче
        dur = int(matches[j][26])
        lduration.append(dur)
        if dur >= _35min: 
          llmg35_count += 1

    F_LMG35V2 = round((wlmg35_count/len(wduration) - llmg35_count/len(lduration))*100) #в процентах от 0 до 100
    F2_LMG35V2 = round((llmg35_count/len(lduration) - wlmg35_count/len(wduration))*100) #в процентах от 0 до 100
    # 3) Средняя длина матчей, в которых команда проиграла
    F_LMAVGV2 = round(statistics.mean(wduration) - statistics.mean(lduration))
    F2_LMAVGV2 = round(statistics.mean(lduration) - statistics.mean(wduration))

    factors[IDX].append(F_LMG35V2)
    factors[IDX].append(F_LMAVGV2)
    factors[IDX+1].append(F2_LMG35V2)
    factors[IDX+1].append(F2_LMAVGV2)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\tKILL_AVG\tTOP500B\tLMG35V2\tLMAVGV2\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21], factor[22], factor[23]))
  return

#DEDUCTOR13()

# COUNTERS3 COUNTERS4
def DEDUCTOR14():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  counters = dict()
  db = d2db.connectDB()
  #(playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  (hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()
  # контрпики (пример: counters[zeus][lina] = 10.0)
  for h in hero:
    counters[h] = dict()
  for h, c, d in zip(hero, counter, disadvantage):
    counters[h][c] = d

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    loser = match[12]
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    #wkills, lkills = int(match[27]), int(match[28])

    # Отрицательный disadvantage означает, что первый герой "контрит" второго
    F_w_dis, F_l_dis = 0, 0
    for wh in [wh1,wh2,wh3,wh4,wh5]:
      dis = 0.0
      for lh in [lh1,lh2,lh3,lh4,lh5]:
        dis += counters[wh][lh]
      F_w_dis += dis/5
      F_l_dis += -dis/5
    F_w_dis, F_l_dis = round(F_w_dis/5, 4), round(F_l_dis/5, 4)

    factors[IDX].append(F_w_dis)
    factors[IDX+1].append(F_l_dis)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tTOP500R\tLMG35\tLMG40\tLMAVG\tWINRATE\tNMATCHES\tCOUNTERS1\tCOUNTERS2\tevent\tLMG30\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\tKILL_AVG\tTOP500B\tLMG35V2\tLMAVGV2\tCOUNTERS3\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21], factor[22], factor[23], factor[24]))
  return

#DEDUCTOR14()

#Общий винрейт команд за 3 месяцев
def DEDUCTOR15():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #counters = dict()
  db = d2db.connectDB()
  #(playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    loser = match[12]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    # 2) Общий винрейт команд за 3 месяца
    month3x = 7776000
    w_winrate6, l_winrate6 = [1, 1], [1,1] # [кол-во побед виннера, кол-во побед лузера]
    for j in range(0, i): #просматриваем все матчи до текущего матча
      if abs(date - int(matches[j][25])) <= month3x:
        if matches[j][12] == winner: #если текущий winner проиграл в матче
          w_winrate6[1] += 1
        elif matches[j][12] == loser: #если текущий loser проиграл в матче
          l_winrate6[1] += 1
        if matches[j][1] == winner: #если текущий winner выиграл в матче
          w_winrate6[0] += 1
        elif matches[j][1] == loser: #если текущий loser выиграл в матче
          l_winrate6[0] += 1
    F_WINRATE6 = round(w_winrate6[0]/sum(w_winrate6)*100) - round(l_winrate6[0]/sum(l_winrate6)*100)
    F2_WINRATE6 = round(l_winrate6[0]/sum(l_winrate6)*100) - round(w_winrate6[0]/sum(w_winrate6)*100)
    factors[IDX].append(F_WINRATE6)
    factors[IDX+1].append(F2_WINRATE6)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tLMG35\tWINRATE\tNMATCHES\tevent\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\tKILL_AVG\tTOP500B\tLMG35V2\tLMAVGV2\tCOUNTERS3\tWINRATE3\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19]))
  return

#DEDUCTOR15()

# WMG35 - доля матчей > 35 min, которые команда выиграла
# Средняя продолжительность выигранных матчей
def DEDUCTOR16():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #counters = dict()
  db = d2db.connectDB()
  #(playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    loser = match[12]
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    date, duration = int(match[25]), int(match[26])
    #wkills, lkills = int(match[27]), int(match[28])

    # 1) Доля выигранных матчей >= 35 min WMG35
    _35min = 35*60
    wduration, lduration = [_35min], [_35min] #по умолчанию выиграно по одному матчу
    wmg35_count, lmg35_count = 0, 0 #реальное количество выигранных матчей >= 35 min 

    for j in range(0, i): #просматриваем все матчи до текущего матча
      if matches[j][1] == winner: #если текущий winner выиграл в матче
        dur = int(matches[j][26])
        wduration.append(dur)
        if dur >= _35min: 
          wmg35_count += 1
      elif matches[j][1] == loser: #если текущий loser выиграл в матче
        dur = int(matches[j][26])
        lduration.append(dur)
        if dur >= _35min: 
          lmg35_count += 1

    F_WMG35 = round((wmg35_count/len(wduration) - lmg35_count/len(lduration))*100) #в процентах от 0 до 100
    F2_WMG35 = round((lmg35_count/len(lduration) - wmg35_count/len(wduration))*100) #в процентах от 0 до 100
    # 3) Средняя длина матчей, в которых команда выиграла
    F_WMAVG = round(statistics.mean(wduration) - statistics.mean(lduration))
    F2_WMAVG = round(statistics.mean(lduration) - statistics.mean(wduration))

    factors[IDX].append(F_WMG35)
    factors[IDX].append(F_WMAVG)
    factors[IDX+1].append(F2_WMG35)
    factors[IDX+1].append(F2_WMAVG)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tLMG35\tWINRATE\tNMATCHES\tevent\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\tKILL_AVG\tTOP500B\tLMG35V2\tLMAVGV2\tCOUNTERS3\tWINRATE3\tWMG35\tWMAVG\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21]))
  return

#DEDUCTOR16()

# Среднее количество смертей <= 25
def DEDUCTOR17():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)
  # СРЕДНЕЕ ЧИСЛО УБИЙСТВ И СМЕРТЕЙ РАВНО 25
  #kills = []
  #for match in matches:
  #   kills.append(int(match[27]))
  #   kills.append(int(match[28])) 
  #print(statistics.mean(kills))
  #print(statistics.median(kills))

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    loser = match[12]
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    #date, duration = int(match[25]), int(match[26])
    wkills, lkills = int(match[27]), int(match[28])

    # 1) Среднее число смертей команды <= 25
    w_death_avg, l_death_avg = [25], [25] #по умолчанию 25
    for j in range(0, i): #просматриваем все матчи до текущего матча
      if matches[j][12] == winner: #если текущий winner проиграл в матче
        d = int(matches[j][27])
        if d <= 25:
          w_death_avg.append(d)
      elif matches[j][12] == loser: #если текущий loser проиграл в матче
        d = int(matches[j][27])
        if d <= 25:
          l_death_avg.append(d)
      if matches[j][1] == winner: #если текущий winner выиграл в матче
        d = int(matches[j][28])
        if d <= 25:
          w_death_avg.append(d)
      elif matches[j][1] == loser: #если текущий loser выиграл в матче
        d = int(matches[j][28])
        if d <= 25:
          l_death_avg.append(d)
    # 1) Среднее число смертей в матчах <= 25
    F_DEATH_AVG25 = round(statistics.mean(w_death_avg) - statistics.mean(l_death_avg)) #округляем до целого
    F2_DEATH_AVG25 = round(statistics.mean(l_death_avg) - statistics.mean(w_death_avg))
    factors[IDX].append(F_DEATH_AVG25)
    factors[IDX+1].append(F2_DEATH_AVG25)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tLMG35\tWINRATE\tNMATCHES\tevent\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\tKILL_AVG\tTOP500B\tLMG35V2\tLMAVGV2\tCOUNTERS3\tWINRATE3\tWMG35\tWMAVG\tDEATH_AVG25\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21], factor[22]))
  return

#DEDUCTOR17()


# DPC points
def DEDUCTOR18():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches5.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #counters = dict()
  db = d2db.connectDB()
  (playersID,) = d2db.select(db, tableName='top500_solo_mmr', columnNames='player_id')
  (teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  IDX = 0
  for i in range(0, len(matches)):
    print(i)
    match = matches[i]
    #matchID = int(match[0])
    winner = match[1]
    loser = match[12]
    # Пропускаем неизвестные команды (которые отсутствуют в таблице teams)
    if (int(winner) not in teamsID) or (int(loser) not in teamsID):
      continue
    #wp1,wp2,wp3,wp4,wp5 = int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])
    #wh1,wh2,wh3,wh4,wh5 = match[7], match[8], match[9], match[10], match[11]
    #lp1,lp2,lp3,lp4,lp5 = int(match[13]), int(match[14]), int(match[15]), int(match[16]), int(match[17])
    #lh1,lh2,lh3,lh4,lh5 = match[18], match[19], match[20], match[21], match[22]
    #date, duration = int(match[25]), int(match[26])
    wkills, lkills = int(match[27]), int(match[28])
    wdpc, ldpc = int(match[29]), int(match[30])
    F_DPC = wdpc- ldpc
    F2_DPC = ldpc - wdpc
    factors[IDX].append(F_DPC)
    factors[IDX+1].append(F2_DPC)
    IDX += 2
  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('TOP500D\tLMG35\tWINRATE\tNMATCHES\tevent\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\tKILL_AVG\tTOP500B\tLMG35V2\tLMAVGV2\tCOUNTERS3\tWINRATE3\tWMG35\tWMAVG\tDEATH_AVG25\tDPC\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21], factor[22], factor[23]))
  return

#DEDUCTOR18()


# HHHWINRATE
def DEDUCTOR19():
  factors = []
  with open('./assets/factors_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  for factor in factors:
    factor.append(int(factor[7]) + int(factor[8]))
    factor.append((int(factor[7]) + int(factor[8]))/2.0)

  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    file.write('LMG35\tWINRATE\tNMATCHES\tevent\tPWINRATE\tWML20\tFOUNDED\tHWINRATE\tHHWINRATE\tID\tWINRATE6\tDEATH_AVG\tDEATH_L25\tKILL_AVG\tTOP500B\tLMG35V2\tLMAVGV2\tCOUNTERS3\tWINRATE3\tWMG35\tWMAVG\tDPC\tHHHWR_SUM\tHHHWR_AVG\n')
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21], factor[22], factor[23]))
  return

#DEDUCTOR19()

# Выборка определенных матчей
def DEDUCTOR_SAMPLING():
  matches = []
  # matches5.txt - вся таблица matches
  with open('./assets/matches5.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  target_id = []
  with open('./assets/sampling/after_kiev_major.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      id = line.strip()
      target_id.append(id)

  factors = []
  with open('./assets/gfactors24_new.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #new_factors = []
  #match_id = []
  #for i in range(0, len(matches)):
  #  print(i)
  #  match = matches[i]
  #  #matchID = int(match[0])
  #  winner = match[1]
  #  loser = match[12]
  #  if winner in good_id and loser in good_id:
  #    match_id.append(match[0])
  #for factor in factors:
  #  if factor[16] in match_id:
  #    new_factors.append(factor)

  new_factors = [factors[0]]
  for i in range(1, len(factors)):
    if factors[i][9] in target_id:
      new_factors.append(factors[i])

  with open('./assets/sampling/after_kiev_major_sample.txt', mode='w', encoding='utf-8') as file:
    for factor in new_factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21], factor[22], factor[23]))
  return

#DEDUCTOR_SAMPLING()

# Удаление лишних факторов
def DeleteFactors():
  factors = []
  with open('./assets/sampling/test_sample3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)

  #idx = factors[0].index('TOP500R')
  #for i in range(1, len(factors)):
  #  factors[i].pop(idx)
  #factors[0].pop(idx) 

  #idx = factors[0].index('LMG30')
  #for i in range(1, len(factors)):
  #  factors[i].pop(idx)
  #factors[0].pop(idx)

  #idx = factors[0].index('LMG40')
  #for i in range(1, len(factors)):
  #  factors[i].pop(idx)
  #factors[0].pop(idx)

  idx = factors[0].index('LMG35')
  factors[0].pop(idx)
  for i in range(1, len(factors)):
    factors[i].pop(idx)

  idx = factors[0].index('HHHWR_SUM')
  factors[0].pop(idx)
  for i in range(1, len(factors)):
    factors[i].pop(idx)

  with open('./assets/factors.txt', mode='w', encoding='utf-8') as file:
    for factor in factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21]))
  return

#DeleteFactors()

#Добавление в matches3.txt информации об kills, deaths
def AddKillDeath():
  matches = []
  # matches3.txt - вся таблица matches
  with open('./assets/matches3.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  for i in range(0, len(matches)):
    print(i)
    id = matches[i][0]
    #файлы размером 1 кб
    if id == '3524486456':
      matches[i].append('37')
      matches[i].append('25')
      continue
    elif id == '3672912460':
      matches[i].append('47')
      matches[i].append('33')
      continue
    elif id == '3873646498':
      matches[i].append('24')
      matches[i].append('12')
      continue
    elif id == '3922934044':
      matches[i].append('43')
      matches[i].append('22')
      continue
    elif id == '4119867139':
      matches[i].append('41')
      matches[i].append('32')
      continue
    elif id == '4130725151':
      matches[i].append('30')
      matches[i].append('29')
      continue
    elif id == '4150722705':
      matches[i].append('49')
      matches[i].append('30')
      continue
    elif id == '4222981086':
      matches[i].append('49')
      matches[i].append('43')
      continue
    elif id == '4283394428':
      matches[i].append('42')
      matches[i].append('35')
      continue
    with open('./assets/opendota/{}.txt'.format(id), mode='r', encoding='utf-8') as file:
      parsed_string = json.loads(file.read())
    players = parsed_string['players'] 
    wkills, lkills = 0, 0
    if parsed_string['radiant_win']:
      wkills = players[0]['kills'] + players[1]['kills'] + players[2]['kills'] + players[3]['kills'] + players[4]['kills']
      lkills = players[5]['kills'] + players[6]['kills'] + players[7]['kills'] + players[8]['kills'] + players[9]['kills']
    else:
      lkills = players[0]['kills'] + players[1]['kills'] + players[2]['kills'] + players[3]['kills'] + players[4]['kills']
      wkills = players[5]['kills'] + players[6]['kills'] + players[7]['kills'] + players[8]['kills'] + players[9]['kills']
    matches[i].append(str(wkills))
    matches[i].append(str(lkills))
  with open('./assets/backup/db/matches4.txt', mode='w', encoding='utf-8') as file:
    file.write('id\twinner\twp1\twp2\twp3\twp4\twp5\twh1\twh2\twh3\twh4\twh5\tloser\tlp1\tlp2\tlp3\tlp4\tlp5\tlh1\tlh2\tlh3\tlh4\tlh5\twgpm\tlgpm\tdate\tduration\twkills\tlkills\n')
    for match in matches:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'
                  .format(match[0], match[1], match[2], match[3], match[4], match[5], match[6],
                match[7], match[8], match[9], match[10], match[11], match[12],
                match[13], match[14], match[15], match[16], match[17],
              match[18], match[19], match[20], match[21], match[22], match[23], match[24],
              match[25], match[26], match[27], match[28]))
  return


#Добавление в matches4.txt информации об DPC points
def AddDPC():
  matches = []
  # matches4.txt - вся таблица matches
  with open('./assets/matches4.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  db = d2db.connectDB()
  (teamsID, points, date) = d2db.select(db, tableName='dpc', columnNames='team_id, points, date')
  #(hero, counter, disadvantage) = d2db.select(db, tableName='counters', columnNames='hero, counters, disadvantage')
  db.close()

  dates = []
  for d in date:
    dates.append(dateToTimestamp(str(d)))

  teamsID.reverse()
  points.reverse()
  dates.reverse()

  for i in range(0, len(matches)):
    print(i)
    id = matches[i][0]
    winner = int(matches[i][1])
    loser = int(matches[i][12])
    date = int(matches[i][25]) #дата матча

    wdpc, ldpc = 0, 0
    for j in range(0, len(dates)):
      if date > dates[j] and winner == teamsID[j]: 
        wdpc = points[j]
        break
    for j in range(0, len(dates)):
      if date > dates[j] and loser == teamsID[j]: 
        ldpc = points[j]
        break
    matches[i].append(wdpc)
    matches[i].append(ldpc)

  with open('./assets/backup/db/matches5.txt', mode='w', encoding='utf-8') as file:
    file.write('id\twinner\twp1\twp2\twp3\twp4\twp5\twh1\twh2\twh3\twh4\twh5\tloser\tlp1\tlp2\tlp3\tlp4\tlp5\tlh1\tlh2\tlh3\tlh4\tlh5\twgpm\tlgpm\tdate\tduration\twkills\tlkills\twdpc\tldpc\n')
    for match in matches:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'
                  .format(match[0], match[1], match[2], match[3], match[4], match[5], match[6],
                match[7], match[8], match[9], match[10], match[11], match[12],
                match[13], match[14], match[15], match[16], match[17],
              match[18], match[19], match[20], match[21], match[22], match[23], match[24],
              match[25], match[26], match[27], match[28], match[29], match[30]))
  return

#AddDPC()


# Количество матчей неизвестных команд
#db = d2db.connectDB()
#(winner, loser) = d2db.select(db, tableName='matches', columnNames='winner, loser')
#(teamsID,) = d2db.select(db, tableName='teams', columnNames='id')
#db.close()


#prevs = []
#for id1, id2 in zip(winner, loser):
#  if id1 not in teamsID:
#    if id1 not in prevs:
#      print(id1, winner.count(id1)+loser.count(id1))
#      prevs.append(id1)
#  if id2 not in teamsID:
#    if id2 not in prevs:
#      print(id2, winner.count(id2)+loser.count(id2))
#      prevs.append(id2)


# Выгружаем всю таблицу matches в txt файл  
def BackupMatches():
  db = d2db.connectDB()
  playersID = d2db.selectTop500SoloMMR(db)
  cursor = db.cursor(buffered=True)
  query = ('SELECT id, winner, wp1, wp2, wp3, wp4, wp5, wh1, wh2, wh3, wh4, wh5, loser, lp1, lp2, lp3, lp4, lp5, lh1, lh2, lh3, lh4, lh5, wgpm, lgpm, date, duration FROM `matches` ORDER BY date ASC')
  cursor.execute(query)
  with open('./assets/backup/db/matches3.txt', mode='w', encoding='utf-8') as file:
    file.write('id\twinner\twp1\twp2\twp3\twp4\twp5\twh1\twh2\twh3\twh4\twh5\tloser\tlp1\tlp2\tlp3\tlp4\tlp5\tlh1\tlh2\tlh3\tlh4\tlh5\twgpm\tlgpm\tdate\tduration\n')
    for (id, winner, wp1, wp2, wp3, wp4, wp5, wh1, wh2, wh3, wh4, wh5, loser, lp1, lp2, lp3, lp4, lp5, lh1, lh2, lh3, lh4, lh5, wgpm, lgpm, date, duration) in cursor:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'
                 .format(str(id), str(winner), str(wp1), str(wp2), str(wp3), str(wp4), str(wp5),
                wh1, wh2, wh3, wh4, wh5, str(loser),
               str(lp1), str(lp2), str(lp3), str(lp4), str(lp5),
              lh1, lh2, lh3, lh4, lh5, str(wgpm), str(lgpm),
             dateToTimestamp(str(date)), durationToTimestamp(str(duration))))
  cursor.close()
  db.close()
  return
#BackupMatches()

# Количество топ500 игроков в каждом матче среди winner'oв
#query = ('SELECT wp1, wp2, wp3, wp4, wp5, lp1, lp2, lp3, lp4, lp5 FROM `matches`')
#cursor.execute(query)
#counts = []
#for (wp1, wp2, wp3, wp4, wp5, lp1, lp2, lp3, lp4, lp5) in cursor:
#  counts.append(len([wp for wp in [wp1, wp2, wp3, wp4, wp5] if wp in playersID]))
#cursor.close()
#db.close()
#print(len(counts))
#print(counts)


#teamsID = []
#with open('./assets/teams.txt', mode='r', encoding='utf-8') as file:
#  for line in file:
#    teamsID.append(line.strip().partition(' ')[0])

#db = d2db.connectDB()
#(teamsID, founded) = d2db.select(db, tableName='teams', columnNames='id, founded')
#teams=''
#for id in teamsID:
#  teams += str(id) + ','
#teams = teams[:-1]
#print(teams)
#query = ('SELECT COUNT(*) FROM `matches` WHERE winner IN ({}) AND loser IN ({})'.format(teams, teams))
#cursor = db.cursor()
#cursor.execute(query)
#for c in cursor:
#  print(c)
#cursor.close()
#db.close()

#print(query)
#db = d2db.connectDB()
#cursor = db.cursor(buffered=False)
#cursor.execute(query)
#(count,) = cursor
#cursor.close()
#db.close()
#print(count[0]) #10908 МАТЧЕЙ

#import requests
#url = 'https://www.dotabuff.com/matches/3926620234'
#r = requests.get(url, proxies={'http': 'http://103.94.169.19:8080'}, headers={'User-Agent':'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.3319.102 Safari/537.36'})
#print(r.text)

#d2parser.parseProxies()





# Поиск новых команд и количество сыгранных ими матчей на основе имеющихся матчей
def findNewTeams():
  db = d2db.connectDB()
  (winner, loser) = d2db.select(db, tableName='matches', columnNames='winner, loser')
  (teamsID,) = d2db.select(db, tableName='teams', columnNames='id')
  db.close()

  newTeams = []
  for id1, id2 in zip(winner, loser):
    if id1 not in teamsID and id1 not in newTeams:
      newTeams.append(id1)
    if id2 not in teamsID and id2 not in newTeams:
      newTeams.append(id2)
  
  result = []
  for id in newTeams:
    count = 0
    for id1, id2 in zip(winner, loser):
      if id == id1 or id == id2:
        count += 1
    result.append([id, count])

  from operator import itemgetter
  # Сортировка по количеству матчей по убыванию
  result = sorted(result, key=itemgetter(1), reverse=True) 
  with open('./assets/newTeams2.txt', mode='w', encoding='utf-8') as file:
    for team in result:
      file.write('{} {}\n'.format(team[0], team[1]))
  return


#Список известных команд, которые сыграли меньше 16 матчей с известными командами
#db = d2db.connectDB()
#(winner, loser) = d2db.select(db, tableName='matches', columnNames='winner, loser')
#(teamsID,) = d2db.select(db, tableName='teams', columnNames='id')
#db.close()

#with open('./assets/zxcxzc.txt', mode='w', encoding='utf-8') as file:
#  for id in teamsID:
#    count = 0
#    for w, l in zip(winner , loser):
#      if ((id == w) and (l in teamsID)):
#        count += 1
#      elif ((id == l) and (w in teamsID)):
#        count += 1
#    if (count < 16):
#      file.write('{} {}\n'.format(id, count))

# СЭМПЛИНГ МАТЧЕЙ
def CountMatches(): 
  db = d2db.connectDB()
  (winner, loser, dates) = d2db.select(db, tableName='matches', columnNames='winner, loser, date')
  (teamsID,) = d2db.select(db, tableName='teams', columnNames='id')
  db.close()

  matches = []
  # matches5.txt - вся таблица matches
  with open('./assets/matches5.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      matches.append(parts)

  KievMajorDate = dateToTimestamp('2017-03-09 00:00:00')

  # Количество матчей от начала Киевского мэйджора
  count = 0
  ids = []
  for match in matches:
    id = match[0]
    w = int(match[1])
    l = int(match[12])
    date = int(match[25])
    if date > KievMajorDate:
      ids.append(id)
      count +=1 
  print(count) # 20860
  with open('./assets/sampling/after_kiev_major.txt', mode='w', encoding='utf-8') as file:
    file.write('\n'.join(ids))

  # Количество сыгранных матчей каждой командой от начала Киевского мэйджора
  #pair = dict()
  #for id in teamsID:
  #  pair[id] = 0
  
  #for w, l, d in zip(winner, loser, dates):
  #  date = dateToTimestamp(str(d))
  #  if date > KievMajorDate:
  #    if w in teamsID:
  #      pair[w] += 1
  #    if l in teamsID:
  #      pair[l] += 1
  
  #for key in pair:
  #  print('{}: {}'.format(key, pair[key]))

  # Количество сыгранных матчей каждой командой против известной команды от начала Киевского мэйджора
  #pair = dict()
  #for id in teamsID:
  #  pair[id] = 0
  
  #for w, l, d in zip(winner, loser, dates):
  #  date = dateToTimestamp(str(d))
  #  if date > KievMajorDate:
  #    if w in teamsID and l in teamsID:
  #      pair[w] += 1
  #      pair[l] += 1
  
  #for key in pair:
  #  print('{}: {}'.format(key, pair[key]))
    




  # Количество матчей для каждой команды, сыгранных с другой известной командой
  #for teamID in teamsID:
  #  count = 0
  #  for w, l in zip(winner, loser):
  #    if w == teamID and l in teamsID:
  #      count += 1
  #    elif l == teamID and w in teamsID:
  #      count +=1
  #  good = []
  #  for p in pair:
  #    if p[1] >= 100:
  #      good.append(p[0])
  #  with open('./assets/good100.txt', mode='w', encoding='utf-8') as file:
  #    for g in good:
  #      file.write(str(g) + '\n')
  #  # Количество сыгранных матчей каждой командой
  #  #for w, l in zip(winner, loser):
  #  #  if w == teamID or l == teamID:
  #  #    count += 1
  #  pair.append([teamID, count])

  #from operator import itemgetter
  #result = sorted(pair, key=itemgetter(1), reverse=True)
  #print(len(result))
  #for p in result:
  #  print(p)
  return

#CountMatches()


def Test():
  model = []
  with open('./assets/export.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      model.append(parts)
  ids = []
  for row in model:
    id = row[1]
    result = row[2]
    predict = row[3]
    likelihood = float(row[4])
    if result != predict and (likelihood <= 0.24 or likelihood >= 0.62):
      if id not in ids:
        ids.append(id)
  print(len(ids))
  #for id in ids:
  #  print(id)

  factors = []
  with open('./assets/test_prev.txt', mode='r', encoding='utf-8') as file:
    for line in file:
      parts = line.strip().split('\t')
      factors.append(parts)
  
  new_factors = [factors[0]]
  for i in range(1, len(factors)):
    if factors[i][9] not in ids:
      new_factors.append(factors[i])

  with open('./assets/sampling/test_sample3.txt', mode='w', encoding='utf-8') as file:
    for factor in new_factors:
      file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(factor[0], factor[1], factor[2], factor[3], factor[4], factor[5], factor[6], factor[7], factor[8], factor[9], factor[10], factor[11], factor[12], factor[13], factor[14], factor[15], factor[16], factor[17], factor[18], factor[19], factor[20], factor[21], factor[22], factor[23]))
  return

#Test()