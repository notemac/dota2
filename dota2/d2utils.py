
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


#getTeamsRecord()
#getTeamsRecord()