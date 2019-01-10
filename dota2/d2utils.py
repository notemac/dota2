
# Вспомогательный модуль для подсчета промежуточной статистики
import time
import d2db
import d2parser
# date = "2018-11-09 06:40:23"
def dateToTimestamp(date):
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

def updateMatches(teamID, startPage):
  START_TIMESTAMP = dateToTimestamp('2016-05-01 00:00:00') # 2017-03-09 00:00:00 Начало киевского мейджора
  isStop = False
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
    # список матчей на странице
    tableRows = d2parser.parseMatchesOnPage(teamID, page)
    time.sleep(2.5) # PAUSE
    for tr in tableRows:
      # пропускаем незасчитанные игры
      if tr.has_attr('class'): #<tr class="inactive">
        print('Inactive game')
        continue
      matchID, date, duration, winner, loser = d2parser.parseMatchOverview(teamID, tr)
      print('matchID: ', matchID)
      if dateToTimestamp(date) < START_TIMESTAMP:
        print('Stopped:' + date)
        isStop = True
        break
      time.sleep(3) # PAUSE
      wplayers, lplayers, wheroes, lheroes, wgpm, lgpm = [], [], [], [], 0, 0
      try:
        wplayers, lplayers, wheroes, lheroes, wgpm, lgpm = d2parser.parseMatchDetails(matchID)
      except AssertionError as exc: # некорректный матч: https://www.dotabuff.com/matches/2962623862
        print(exc.args)
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


def insertCounters():
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
    
#updateTop500SoloMMR('./assets/top500solommr.txt')
updateMatches(6462126, startPage=1)
#insertCounters()
#getTeamsRecord()
#getTeamsRecord()