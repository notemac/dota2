#import time
import requests
from bs4 import BeautifulSoup

# Задаем user-agent, чтобы обойти защиту на сервере от анонимных запросов
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}

# Парсит имена геров c www.dotabuff.com в outputFile
def parseHeroes(outputFile):
  URL = 'https://www.dotabuff.com/heroes'
  r = requests.get(URL, headers=HEADERS)
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
  URL = 'https://www.dotabuff.com/players/leaderboard'
  r = requests.get(URL, headers=HEADERS)
  soup = BeautifulSoup(r.text, features='html.parser')
  # <span class="last"> <a href="/players/leaderboard?page=81"></a></span>
  href = soup.find('span', {'class': 'last'}).a['href']
  firstPage, lastPage = 1, int(href[href.find('=')+1:])
  players = []
  for page in range(firstPage, lastPage+1):
    print('parsing page ' + str(page) + '...')
    r = requests.get(URL, headers=HEADERS, params={'page': page})  
    soup = BeautifulSoup(r.text, features='html.parser')
    # <a class=" link-type-player" href="/players/154715080"><i class="fa fa-check color-verified fa-space-right"></i>Fnatic.Abed</a>
    for a in soup.findAll('a', {'class': 'link-type-player'}):
      player_id, player_name = a['href'][a['href'].rfind('/')+1:], a.text
      players.append(player_id + ' ' + player_name)
    # time.sleep(0.5) # Пауза в полсекунды (При 0.5 скрипт отрабатывает за несколько минут!!!)
  with open(outputFile, mode='w', encoding='utf-8') as file:
    file.writelines('\n'.join(players))
  print('parseTop500SoloMMR(outputFile) completed')

#parseHeroes('./assets/heroes.txt')
#parseTop500SoloMMR('./assets/top500solommr.txt')