# Importing required libs
import re
import gc
# Tika is used to import text data from pdf,docx,txt files
# Parser provides an interface for python's internal byte-code compiler
from tika import parser
import tika

tika.initVM()
# API keys
# to load the .env file
from dotenv import load_dotenv
import os

# Microsoft azure translator API
load_dotenv()
API_KEY = os.getenv("API_KEY")
LOCATION = os.getenv("LOCATION")

# Using nltk tokenizer to divide strings into lists of substrings - to indentify punctuations and etc
from nltk.tokenize import sent_tokenize

# function to translate input language into english (Microsoft Translation API)
import requests, uuid, json


def translate(text, language):
    # subscription key and endpoint
    subscription_key = API_KEY
    endpoint = "https://api.cognitive.microsofttranslator.com"
    # location, also known as region. The default is global.
    # This is required if using a Cognitive Services resource.
    location = LOCATION
    path = '/translate'
    constructed_url = endpoint + path
    params = {
        'api-version': '3.0',
        'from': language,
        'to': ['en']
    }
    constructed_url = endpoint + path
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    # can pass more than one object in body.
    body = [{
        'text': text
    }]
    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()
    gc.collect()
    return response[0]['translations'][0]['text']


def extractData(path):
    raw = parser.from_file(path)
    data = raw['content']
    return data


# function to clean the data
def cleanData(data):
    # remove extra space
    data = " ".join(data.split())
    # remove links
    data = re.sub(r'http\S+', '', data)
    # remove quoted text
    data = re.sub(r'"[\w\s]+"', '', data)
    # remove names/
    prefixes = ['Mr', 'Mrs', 'Shri', 'Sri', 'Dr', 'Phd']
    data = re.sub(r'\b(?:' + '|'.join(prefixes) + ')\.\s*\S+', '', data)
    return data


# function to extract the english text data from files and return it
def extractText(path):
    # extract
    data = extractData(path)
    # clean
    data = cleanData(data)
    # break into sentences
    data = sent_tokenize(data)
    # return array of sentences
    return data


# function to extract the multilingual text data from files and return it
def extractMultilingualText(path, language):
    data = extractData(path)
    data = cleanData(data)
    # since MS API support translation upto 5000 characters only
    if len(data) >= 5000:
        raise "text limit exceeded"
    translatedData = translate(data, language)
    translatedData = sent_tokenize(translatedData)
    # translatedData=translatedData.split('. ')
    return translatedData, data


# function to extract the multilingual text data from text area input and return it
def inputMultilingualDataExtract(data, language):
    data = cleanData(data)
    if len(data) >= 5000:
        raise "text limit exceeded"
    translatedData = translate(data, language)
    translatedData = sent_tokenize(translatedData)
    # translatedData=translatedData.split('. ')
    return translatedData, data


# function to extract the english text data from text area input and return it
def inputDataExtract(data):
    data = cleanData(data)
    data = sent_tokenize(data)
    return data

# file validation function
def allowed_file(filename):
    # excluding incorrect file formats
    if not "." in filename:
        return False

    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]

    # Check if the extension is in allowed
    allowed = ["PDF", "TXT", "DOCX", "ODT"]
    if ext.upper() in allowed:
        return True
    else:
        return False


# Scrapper - Can pull data from html and xml files
from bs4 import BeautifulSoup
# Creat and manage thread pools
from concurrent.futures import ThreadPoolExecutor


# function that return a link if exact match of the query is found
def findPlag(text, session, sourceFilter=""):
    # search in the bing search
    url = f'https://www.bing.com/search?q=%2B"{text}"&qs=n&form=QBRE&sp=-1&pq=%2B"{text.lower()}"'
    # Crafting the proper request
    header = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'}
    with session.get(url, headers=header, allow_redirects=True) as response:
        page = response
    # extracting data from html and xml files
    content = BeautifulSoup(page.content, 'html.parser')
    gc.collect()
    # return content
    try:
        element = content.find('li', class_='b_algo').h2
        link = element.find('a')['href']
        if link == sourceFilter:
            return ""
        else:
            return link
    except:
        return ""


# function that return a link for relevant match of the query is found
def findPlagNormal(text, session, sourceFilter=""):
    # text = text.replace(" ","+")
    # print(text)
    url = f'https://www.bing.com/search?q="{text}"&qs=n&form=QBRE&sp=-1&pq="{text.lower()}"'
    # Crafting the proper request
    header = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'}
    with session.get(url, headers=header, allow_redirects=True) as response:
        page = response
    content = BeautifulSoup(page.content, 'html.parser')
    gc.collect()
    # print(content.prettify())
    # return content
    # link= content.find('h2')
    try:
        element = content.find('li', class_='b_algo').h2
        link = element.find('a')['href']
        if link == sourceFilter:
            return ""
        else:
            return link
        return link
    except:
        return ""


# function that takes array of sentences as input and returns associated links, plagiarism count
# total sentences, mostProbable sentences using exact match function
# defaultdict stores data values like a map
from collections import defaultdict, Counter


def checkPlag(data, sourceFilter=""):
    res = {}
    websites = defaultdict(int)
    with ThreadPoolExecutor(max_workers=100) as executor:
        with requests.Session() as session:
            results = list(executor.map(findPlag, data, [session] * len(data), [sourceFilter] * len(data)))
    for link in results:
        if link != '':
            websites[link] += 1
    k = Counter(websites)
    mostProbable = k.most_common(3)
    # calculating the plagiarism percentage
    plagCount = len(results) - results.count("")
    total = len(data)
    res = dict(zip(data, results))
    return res, plagCount, total, mostProbable


# function that takes array of sentences as input and returns associated links, plagiarism count
# total sentences, mostProbable sentences using relevant match function
def checkPlagNormal(data, sourceFilter=""):
    res = {}
    websites = defaultdict(int)
    with ThreadPoolExecutor(max_workers=100) as executor:
        with requests.Session() as session:
            results = list(executor.map(findPlagNormal, data, [session] * len(data), [sourceFilter] * len(data)))
    for link in results:
        if link != '':
            websites[link] += 1
    k = Counter(websites)
    mostProbable = k.most_common(3)
    plagCount = len(results) - results.count("")
    total = len(data)
    res = dict(zip(data, results))
    return res, plagCount, total, mostProbable
