
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


def updateMatches(teamID, startPage):
  print('teamID: ', teamID)
  record = d2parser.parseTeamMatchesRecord(teamID)
  # кол-во страниц с матчами
  pagesCount = int(record/20) + 1
  db = d2db.connectDB()
  for page in range(startPage, pagesCount+1):
    print('page: ', page)
    # список матчей на странице
    tableRows = d2parser.parseMatchesOnPage(teamID, page)
    time.sleep(0.5) # PAUSE
    for tr in tableRows:
      # пропускаем незасчитанные игры
      if tr.has_attr('class'): #<tr class="inactive">
        continue
      matchID, date, duration, winner, loser = d2parser.parseMatchOverview(teamID, tr)
      print('matchID: ', matchID)
      time.sleep(0.5) # PAUSE
      wplayers, lplayers, wheroes, lheroes, wgpm, lgpm = d2parser.parseMatchDetails(matchID)
      matchDetails = (matchID, winner, *tuple(wplayers), *tuple(wheroes), 
                      loser, *tuple(lplayers), *tuple(lheroes), wgpm, lgpm, date, duration)
      d2db.insertMatch(db, matchDetails)
  db.close()

#updateMatches('5034643', 4) #Midas Club Victory

#getTeamsRecord()
#getTeamsRecord()