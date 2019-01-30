
import re
import pickle
import urllib
from bs4 import BeautifulSoup

f = open('allJournalLinks.pckl', 'rb')
links = pickle.load(f)
f.close()

jIdx = 10
jour = list(links.keys())[jIdx]
jourLinks = links[jour]
len(jourLinks)

baseURL = 'https://www.nature.com'

jIdx = 10
jour = list(links.keys())[jIdx]
jourDir = os.path.join(thisDir, jour)
if not os.path.exists(jourDir):
    os.makedirs(jourDir)

jourLinks = links[jour]
lCntr = 448
numLinks = len(jourLinks)
for link in jourLinks[lCntr-1:]:
    print('Processing journal {}. Link {} of {}.'.format(jour, lCntr, numLinks), end='\r')
    url = baseURL+link
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html, from_encoding='utf8')
    dateTime = str(soup.find_all(attrs={"href" : "#article-info"}))
    dateTime = re.findall("\d{4}-\d{2}-\d{2}", dateTime)

    abstract = ''
    contents = soup.find_all('div', {'id':"abstract-content"})
    
    if len(contents) == 0:
        contents = soup.find_all('div', {'id':"Abs1-content"})
    
    if len(contents) == 0:
        continue
    
    for content in contents:
        pars = content.find_all('p')
        for par in pars:
            abstract += par.get_text()
            abstract += '\n'

    f = open(os.path.join(jourDir, '{}_{}_{}.txt'.format(jour, lCntr, dateTime[0])), 'w', encoding='utf-8')
    f.write('Published: '+dateTime[0]+'\n')
    f.write(abstract)
    f.close()
    lCntr += 1
    time.sleep(2)
    
baseURL = 'https://www.nature.com'
soup = BeautifulSoup(urllib.request.urlopen(baseURL+jourLinks[197]), from_encoding='utf8')
contents = soup.find_all('div', {'id':"Abs1-content"})
contents
