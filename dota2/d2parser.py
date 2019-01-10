import re
import time
import requests
from bs4 import BeautifulSoup
# Для парсинга динамически подгружаемых страниц используем модуль selenium + chromedriver.exe
from selenium import webdriver 

# Задаем user-agent, чтобы обойти защиту на сервере от анонимных запросов
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}

# Парсит имена геров c www.dotabuff.com в outputFile
def parseHeroes(outputFile):
  url = 'https://www.dotabuff.com/heroes'
  r = requests.get(url, headers=HEADERS)
  names = []
  soup = BeautifulSoup(r.text, features='html.parser')
  # <div class="name">Text</div>
  for div in soup.findAll('div', {'class': 'name'}):
    names.append(div.text);
  with open(outputFile, mode='w', encoding='utf-8') as file:
    file.write('\n'.join(names))
  return

# Парсит топ-500 ММР игроков c www.dotabuff.com в outputFile
# Возможны повторяющиеся записи, т.к. данные на сервере могут обновиться во время парсинга
def parseTop500SoloMMR(outputFile):
  print('parseTop500SoloMMR(outputFile) starting')
  url = 'https://www.dotabuff.com/players/leaderboard'
  r = requests.get(url, headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  # <span class="last"> <a href="/players/leaderboard?page=81"></a></span>
  href = soup.find('span', {'class': 'last'}).a['href']
  firstPage, lastPage = 1, int(href[href.find('=')+1:])
  players = []
  for page in range(firstPage, lastPage+1):
    time.sleep(0.3)
    print('parsing page ' + str(page) + '...')
    r = requests.get(url, headers=HEADERS, params={'page': page})  
    soup = BeautifulSoup(r.text, features='html.parser')
    # <a class=" link-type-player" href="/players/154715080"><i class="fa fa-check color-verified fa-space-right"></i>Fnatic.Abed</a>
    for a in soup.findAll('a', {'class': 'link-type-player'}):
      player_id, player_name = a['href'][a['href'].rfind('/')+1:], a.text
      players.append(player_id + ' ' + player_name)
  with open(outputFile, mode='w', encoding='utf-8') as file:
    file.write('\n'.join(players))
  print('parseTop500SoloMMR(outputFile) completed')

# Парсит название команды и дату основания
def parseTeamNameAndFounded(teamID):
  url = 'https://www.dotabuff.com/esports/teams/'
  r = requests.get(url + str(teamID), headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  #<div>class="header-content-title"><h1>Virtus Pro<small>Summary</small></h1></div>
  div = soup.find('div', {'class': 'header-content-title'})
  name = div.h1.contents[0]
  #datetime="2018-09-06T04:55:39+00:00"
  date = soup.find('div', {'class': 'header-content-secondary'}).find('time')
  if date is None: #когда на сайте не указана дата, т.е. значение "Unknown"
    return None
  founded = date['datetime'].replace('T', ' ').rpartition('+')[0]
  return [name, founded]

# Парсит самые популярные/активные команды с www.dotabuff.com и www.opendota.com
def parseTeams(outputFile):
  # STEP 1
  # Team Standings. Dota Pro Circuit 2017-2018 Season
  #url = 'https://www.dotabuff.com/procircuit/2017-2018/team-standings'
  #r = requests.get(url, headers=HEADERS)
  #soup = BeautifulSoup(r.text, features='html.parser')
  #teamsID = []
  ## <a class="esports-team large esports-link team-link" href="/esports/teams/3477208-virtus-pro">
  ## <span>SPAN 1</span><span class="team-text team-text-tag">Virtus Pro</span></a>
  #for a in soup.findAll('a', {'class': 'esports-team large esports-link team-link'}):
  #  id, name = a['href'].rpartition('/')[2].partition('-')[0], a('span')[1].text
  #  teamsID.append(id)
  ## Удаляем каждую вторую повторную запись
  #teamsID = [teamsID[i] for i in range(0, len(teamsID), 2)]
  ## Парсим DPC-points за 2017-2018 сезон
  ## <td class="large" data-value="1250.30"></td>
  #points1718 = []
  #for td in soup.findAll('td', {'class': 'large'}):
  #  points1718.append(str(int(float(td['data-value']))))
  ## Парсим название команды и дату основания
  #names, founded = [], []
  #for id in teamsID[:]:
  #  pair = parseTeamNameAndFounded(id)
  #  names.append(pair[0])
  #  founded.append(pair[1])
  #  print(pair)
  ## DPC-points за текущий сезон
  #points1819 = len(points1718)*['0']
  #with open('./assets/teams1.txt', mode='w', encoding='utf-8') as file:
  #  for i in range(0, len(points1819)):
  #    file.write(teamsID[i] + '\n')
  #    file.write(names[i] + '\n')
  #    file.write(points1819[i] + '\n')
  #    file.write(points1718[i] + '\n')
  #    file.write(founded[i] + '\n')
  

  # STEP 2
  # Team Elo Rankings
  #url = 'https://www.opendota.com/teams'
  #driver = webdriver.Chrome('D:\\programFiles\\chromedriver.exe') 
  #driver.implicitly_wait(10) # time.sleep(10) 10 секунд а щагрузку страницы
  #driver.get('https://www.opendota.com/teams');
  #textHtml = driver.page_source
  #driver.quit()
  #soup = BeautifulSoup(textHtml, features='html.parser')
  #teamsID = []
  ## <a href="/teams/[0-9]">...</a>
  #for a in soup.findAll('a', href=re.compile('/teams/\d*')):
  #  teamsID.append(a['href'].rpartition('/')[2])
  ## Удаляем лишние/повторные записи
  #teamsID = list(set(teamsID))
  #names, founded = [], []
  #for id in teamsID[:]:
  #  pair = parseTeamNameAndFounded(id)
  #  if pair is None:
  #    teamsID.remove(id)
  #    continue
  #  names.append(pair[0])
  #  founded.append(pair[1])
  #  print(pair)
  #points1819, points1718 = len(teamsID)*['0'], len(teamsID)*['0']
  #with open('./assets/teams2.txt', mode='w', encoding='utf-8') as file:
  #  for i in range(0, len(teamsID)):
  #    file.write(teamsID[i] + '\n')
  #    file.write(names[i] + '\n')
  #    file.write(points1819[i] + '\n')
  #    file.write(points1718[i] + '\n')
  #    file.write(founded[i] + '\n')

  # STEP 3
  # Team Standings. Dota Pro Circuit Leaderboard
  #url = 'https://www.dotabuff.com/procircuit/team-standings'
  #r = requests.get(url, headers=HEADERS)
  #soup = BeautifulSoup(r.text, features='html.parser')
  #teamsID = []
  ## <a class="esports-team large esports-link team-link" href="/esports/teams/3477208-virtus-pro">
  ## <span>SPAN 1</span><span class="team-text team-text-tag">Virtus Pro</span></a>
  #for a in soup.findAll('a', {'class': 'esports-team large esports-link team-link'}):
  #  id, name = a['href'].rpartition('/')[2].partition('-')[0], a('span')[1].text
  #  teamsID.append(id)
  ## Удаляем каждую вторую повторную запись
  #teamsID = [teamsID[i] for i in range(0, len(teamsID), 2)]
  ## Парсим название команды и дату основания
  #names, founded = [], []
  #for id in teamsID[:]:
  #  pair = parseTeamNameAndFounded(id)
  #  if pair is None:
  #    teamsID.remove(id)
  #    continue
  #  names.append(pair[0])
  #  founded.append(pair[1])
  #  print(pair)
  #points1718, points1819 = len(teamsID)*['0'], len(teamsID)*['0']
  #with open('./assets/teams3.txt', mode='w', encoding='utf-8') as file:
  #  for i in range(0, len(teamsID)):
  #    file.write(teamsID[i] + '\n')
  #    file.write(names[i] + '\n')
  #    file.write(points1819[i] + '\n')
  #    file.write(points1718[i] + '\n')
  #    file.write(founded[i] + '\n')
  

  # STEP 4. Остальное
  # https://www.dotabuff.com/esports/teams
  # https://www.dotabuff.com/esports/leagues/3454-weplay-league-season-3/teams
  # https://www.dotabuff.com/esports/leagues/8055-galaxy-battles-emerging-worlds/teams
  # https://www.dotabuff.com/esports/leagues/9870-the-international-2018/teams
  # https://www.dotabuff.com/esports/leagues/5609-esl-one-hamburg-2017/teams
  url = 'https://www.dotabuff.com/esports/leagues/10296-the-kuala-lumpur-major/teams'
  r = requests.get(url, headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  teamsID = []
  for a in soup.findAll('a', {'class': 'esports-team esports-link team-link'}):
    id = a['href'].rpartition('/')[2].partition('-')[0]
    teamsID.append(id)
  # Удаляем каждую вторую повторную запись
  teamsID = [teamsID[i] for i in range(0, len(teamsID), 2)]
  # Парсим название команды и дату основания
  names, founded = [], []
  # В первом блоке на странице только 36 записей
  for id in teamsID[:]:
    print(id)
    pair = parseTeamNameAndFounded(id)
    if pair is None:
      teamsID.remove(id)
      continue
    names.append(pair[0])
    founded.append(pair[1])
    print(pair)
  points1718, points1819 = len(teamsID)*['0'], len(teamsID)*['0']
  with open(outputFile, mode='w', encoding='utf-8') as file:
    for i in range(0, len(teamsID)):
      file.write(teamsID[i] + '\n')
      file.write(names[i] + '\n')
      file.write(points1819[i] + '\n')
      file.write(points1718[i] + '\n')
      file.write(founded[i] + '\n')
  return

# Парсит общее количество сыгранных матчей командой
def parseTeamRecord(teamID):
  url = 'https://www.dotabuff.com/esports/teams/'
  r = requests.get(url + str(teamID), headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  soup = soup.find('div', {'class': 'header-content-secondary'})
  soup = soup.find('span', {'class': 'game-record'})
  #<span class="game-record"><span class="wins">1,034</span><span>-</span><span class="losses">632</span></span>
  record = int(soup.contents[0].text.replace(',', '')) + int(soup.contents[2].text)
  return record

# Парсит дату последнего матча команды
def parseTeamLastMatchDate(teamID):
  url = 'https://www.dotabuff.com/esports/teams/'
  r = requests.get(url + str(teamID) + '/matches', headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  table = soup.find('table', {'class': 'table table-striped recent-esports-matches'})
  span = table.find('span', {'class': 'r-none-mobile'})#find('time')
  date = span.time['datetime'].replace('T', ' ').rpartition('+')[0]
  return date


# Парсит общее количество сыгранных матчей командой доступных для просмотра
def parseTeamMatchesRecord(teamID):
  url = 'https://www.dotabuff.com/esports/teams/'
  r = requests.get(url + str(teamID) + '/matches', headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  #<div class="viewport">1 - 20 of 1717</div>
  record = int(soup.find('div', {'class': 'viewport'}).text.rpartition(' ')[2])
  return record

# Парсит Gold Per Minute для обеих команд в матче
def parseMatchGPM(matchID):
  url = 'https://www.dotabuff.com/matches/'
  r = requests.get(url + str(matchID) + '/farm', headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  if 'Not Found' in soup.html.head.title.text:
    return ['0', '0']
  # блок farm
  div = soup.find('div', {'class': 'match-show'})
  # блок сил света
  section = div.find('section', {'class': 'radiant'})
  tr = section.find('article', {'class': 'r-tabbed-table'}).find('tfoot').find('tr')
  gpm1 =  tr.contents[5].contents[0].replace(',', '')
  # блок сил тьмы
  section = div.find('section', {'class': 'dire'})
  tr = section.find('article', {'class': 'r-tabbed-table'}).find('tfoot').find('tr')
  gpm2 =  tr.contents[5].contents[0].replace(',', '')
  return [gpm1, gpm2]

def parseMatchDetails(matchID):
  url = 'https://www.dotabuff.com/matches/'
  r = requests.get(url + str(matchID), headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  # блок с данными о матче
  div = soup.find('div', {'class': 'team-results'})
  radiant = div.find('section', {'class': 'radiant'}) # блок сил света
  dire = div.find('section', {'class': 'dire'}) # блок сил тьмы
  if (radiant is None) or (dire is None):
    raise AssertionError('Exception: Radiant or Dire block is None!')

  rowsRadiant = radiant.find('article', {'class': 'r-tabbed-table'}).find('tbody').findAll('tr')
  rowsDire = dire.find('article', {'class': 'r-tabbed-table'}).find('tbody').findAll('tr')
  gpm = parseMatchGPM(matchID)
  wplayers, lplayers, wheroes, lheroes = [], [], [], []
  if len(radiant.header.contents) > 1: #значит силы света победили
    wgpm, lgpm = gpm[0], gpm[1]
    for tr in rowsRadiant:
      #<tr class="col-hints faction-radiant player-86715129">
      wplayers.append(tr['class'][2].partition('-')[2]) #player id
      #<a href="/heroes/winter-wyvern">
      wheroes.append(tr.contents[0].div.a['href'].rpartition('/')[2])
    for tr in rowsDire:
      lplayers.append(tr['class'][2].partition('-')[2])
      lheroes.append(tr.contents[0].div.a['href'].rpartition('/')[2])
  else:
    wgpm, lgpm = gpm[1], gpm[0]
    for tr in rowsRadiant:
      lplayers.append(tr['class'][2].partition('-')[2])
      lheroes.append(tr.contents[0].div.a['href'].rpartition('/')[2])
    for tr in rowsDire:
      wplayers.append(tr['class'][2].partition('-')[2])
      wheroes.append(tr.contents[0].div.a['href'].rpartition('/')[2])
  return wplayers, lplayers, wheroes, lheroes, wgpm, lgpm

# Парсит список матчей на странице
def parseMatchesOnPage(teamID, page):
  url = 'https://www.dotabuff.com/esports/teams/'
  r = requests.get(url + str(teamID) + '/matches', params={'page': page}, headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  # Таблица с матчами на текущей странице
  #<table class="table table-striped recent-esports-matches">
  table = soup.find('table', {'class': 'table table-striped recent-esports-matches'})
  tbody = table.find('tbody')
  return tbody.findAll('tr')

def parseMatchOverview(teamID, tr):
  #<a class="won" href="/matches/4103964624">Won Match</a>
  matchID = tr.contents[1].div.a['href'].rpartition('/')[2]
  # WTF: tr.contents[1].div.a['class'] returns LIST but not STRING
  result = tr.contents[1].div.a['class'][0] #won/lost
  #<time datetime="2018-09-06T22:50:03+00:00">
  date = tr.contents[1].span.time['datetime'].replace('T', ' ').rpartition('+')[0]
  # извлекаем id команды соперника
  a = tr.contents[5].find('a')
  opponent = '0' # неизвестная команда (Unknown)
  if a is not None:
    #href="/esports/teams/4482169-incubus-gaming"
    opponent = a['href'].partition('-')[0].rpartition('/')[2]
  # длительность матча
  duration = tr.contents[3].text
  if duration.count(':') == 1:
    duration = '00:' + duration
  # победитель
  winner = (teamID if (result == 'won') else opponent)
  loser = (teamID if (winner != teamID) else opponent)
  return matchID, date, duration, winner, loser


# Парсит 10 героев, против которых у указанного героя наибольший винрейт за последний год
def parseHeroCounters(hero):
  url = 'https://www.dotabuff.com/heroes/'
  r = requests.get(url + hero + '/counters', params={'date': 'year'}, headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  counters = []
  for tr in soup.find('table', {'class': 'sortable' }).find('tbody').findAll('tr'):
    # <tr data-link-to="/heroes/earth-spirit"
    counter = tr['data-link-to'].rpartition('/')[2]
    # <td data-value="-4.8156" class> //это столбец DISADVANTAGE
    disadvantage = tr.findAll('td')[2]['data-value']
    counters.append((counter, float(disadvantage)))
  #return counters[len(counters)-10:] # последние 10 героев из списка
  return counters


# main     
def main():
  parseHeroCounters('alchemist')
  #parseTeamLastMatchDate(1838315)

#main()
#parseTeams('./assets/teams9.txt')
#parseHeroes('./assets/heroes.txt')
#parseTop500SoloMMR('./assets/top500solommr.txt')