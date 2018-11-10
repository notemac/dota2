import re
#import time
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

def parseTeamLastMatchDate(teamID):
  url = 'https://www.dotabuff.com/esports/teams/'
  r = requests.get(url + str(teamID) + '/matches', headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  table = soup.find('table', {'class': 'table table-striped recent-esports-matches'})
  span = table.find('span', {'class': 'r-none-mobile'})#find('time')
  date = span.time['datetime'].replace('T', ' ').rpartition('+')[0]
  return date


# main     
def main():
  parseTeamLastMatchDate(1838315)

#main()
#parseTeams('./assets/teams9.txt')
#parseHeroes('./assets/heroes.txt')
#parseTop500SoloMMR('./assets/top500solommr.txt')