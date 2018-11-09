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
    file.writelines('\n'.join(names))
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
    file.writelines('\n'.join(players))
  print('parseTop500SoloMMR(outputFile) completed')

# Парсит самые популярные команды с www.dotabuff.com и www.opendota.com
def parseTeams():
  # STEP 1
  # Team Standings. Dota Pro Circuit 2017-2018 Season
  url = 'https://www.dotabuff.com/procircuit/2017-2018/team-standings'
  r = requests.get(url, headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  teamsID = []
  # <a class="esports-team large esports-link team-link" href="/esports/teams/3477208-virtus-pro">
  # <span>SPAN 1</span><span class="team-text team-text-tag">Virtus Pro</span></a>
  for a in soup.findAll('a', {'class': 'esports-team large esports-link team-link'}):
    id, name = a['href'].rpartition('/')[2].partition('-')[0], a('span')[1].text
    teamsID.append(id)
  teamsID = list(set(teamsID)) # Удаляем лишние/повторные записи
  # Парсим DPC-points за 2017-2018 сезон
  # <td class="large" data-value="1250.30"></td>
  points = []
  for td in soup.findAll('td', {'class': 'large'}):
    points.append(int(float(td['data-value'])))
  # Парсим название команды и дату основания
  url = 'https://www.dotabuff.com/esports/teams/'
  for id in teamsID:
      r = requests.get(url + str(id), headers=HEADERS)
      soup = BeautifulSoup(r.text, features='html.parser')
  print(len(teamsID), len(points))
  

  # STEP 2
  # Team Elo Rankings
  url = 'https://www.opendota.com/teams'
  driver = webdriver.Chrome('D:\\programFiles\\chromedriver.exe') 
  driver.implicitly_wait(10) # time.sleep(10) to wait page loading
  driver.get('https://www.opendota.com/teams');
  textHtml = driver.page_source
  driver.quit()
  soup = BeautifulSoup(textHtml, features='html.parser')
  # <a href="/teams/[0-9]">...</a>
  for a in soup.findAll('a', href=re.compile('/teams/\d*')):
    teams.append(a['href'].rpartition('/')[2])
  # Удаляем лишние/повторные записи
  teamsID = list(set(teamsID))
  

  #https://www.dotabuff.com/procircuit/team-standings
  #https://www.dotabuff.com/esports/teams

parseTeams()
#parseHeroes('./assets/heroes.txt')
#parseTop500SoloMMR('./assets/top500solommr.txt')