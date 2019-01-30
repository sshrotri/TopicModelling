
import urllib
from bs4 import BeautifulSoup
import re
import pickle

journals = ['cgt', 'ejhg', 'gt', 'gim', 'gene', 'jhg', 'ng', 'nrg', 'npjregenmed', 'onc', 'oncsis']
baseURL = 'https://www.nature.com/'
suffix = '/articles?searchType=journalSearch&sort=PubDate&page='


allJournalLinks = {}
for jou in journals:
    # open url
    url = baseURL+jou+'/articles/'
    # get soup for given page
    soup = BeautifulSoup(urllib.request.urlopen(url), 'html.parser')
    # each journal has multiple pages, we need to extract links from all pages, first step is to find number of pages
    numPages = str(soup.find_all(attrs={"data-page" : re.compile("\d+")})[-1])
    match = re.search("page=\d+", numPages).span()
    numPages = numPages[match[0]:match[1]]
    numPages = int(re.findall("\d+", numPages)[0])
    # based on number of pages create page links
    pageLinks = [baseURL+jou+suffix+str(p) for p in range(1, numPages+1)]
    
    thisJournalArticles = []
    pCntr = 1
    numPages = len(pageLinks)
    for page in pageLinks:
        print('Processing Journal: {}. Page {} of {}'.format(jou, pCntr, numPages), end='\r')
        # now for each page extract soup
        psoup = BeautifulSoup(urllib.request.urlopen(page), 'html.parser')
        # find href which contain links to articles
        articleLinks = str(psoup.find_all(attrs={"href" : re.compile("/articles/")}))
        # once we have those, extract just the links
        articleLinks = re.findall("/articles/[\w,-]+", articleLinks)
        thisJournalArticles.extend(articleLinks)
        pCntr += 1
    
    allJournalLinks[jou] = thisJournalArticles
    
print("Saving to pickle...")
f = open('allJournalLinks.pckl', 'wb')
pickle.dump(allJournalLinks, f)
f.close()
print("Done!")
