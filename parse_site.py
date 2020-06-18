import requests
import sys
from lxml import html
from bs4 import BeautifulSoup
from collections import namedtuple
from pathlib import Path
import argparse
from urllib.parse import urljoin
 
class WordInfo:
    def __init__(
        self, 
        word, 
        translation, 
        definition, 
        pronunciation, 
        audio, 
        example_sentences, 
        additional_info, 
        picture):

        self.word = word
        self.translation = translation
        self.pronunciation = pronunciation
        self.audio = audio
        self.example_sentences = example_sentences
        self.additional_info = additional_info
        self.picture = picture

    def __str__(self):
        return f'''Word: {self.word}, Pronunciation: {self.pronunciation}, Audio: {self.audio} 
        Additional Info: {self.additional_info}, Picture: {self.picture}
        Examples: {self.example_sentences}
        '''

class SentenceInfo:
    def __init__(self, sentence, translation, pronunciation, audio, grammar_used):
        self.sentence = sentence
        self.translation = translation
        self.pronunciation = pronunciation
        self.audio = audio
        self.grammar_used = grammar_used

class GrammarInfo:
    def __init__(self, grammar_point, grammar_explanation):
        self.grammar_point = grammar_point
        self.grammar_explanation = grammar_explanation

def parse_grammars(grammar_set):
    grammar_used=[]
    for grammar_html in grammar_set:
        grammar_item = grammar_html.summary.string
        grammar_explanation = grammar_html.div.string
        grammar_used.append(GrammarInfo(grammar_item, grammar_explanation)) 
    return grammar_used

def parse_sentences(sentence_set):
    example_sentences=[]
    for sentence_html in sentence_set:
        sentence = sentence_html.find(class_='divBunruiExC').string
        translation = sentence_html.find(class_='divBunruiExN').string
        pronunciation = sentence_html.find(class_='divBunruiExP').string
        audio = sentence_html.find(class_='divBunruiExA').audio.source['src']
        grammar_used = parse_grammars(sentence_html.find_all(class_='detailsExBunpou'))
        example_sentences.append(SentenceInfo(sentence,translation,pronunciation,audio,grammar_used))
    return example_sentences

def parse_word(word_html):
    word = word_html.find(class_='divBunruiC').string
    translation = word_html.find(class_='divBunruiN').string
    pronunciation = word_html.find(class_='divBunruiP').string
    audio = word_html.find(class_='divBunruiA').audio.source['src']
    example_sentences = parse_sentences(word_html.find_all(class_='divBunruiExMain'))
    word_info = WordInfo(word,translation,None,pronunciation,audio,example_sentences,None,None)
    return word_info

def fetch_text(url):
    page = requests.get(url)
    #need to enforce utf-8 or else encoding is messed up
    page.encoding = 'utf-8'
    return page.text

def parse_site(url, use_cache):
    #this page doesn't change very often if at all, so just cache it
    if use_cache:
        local_path = Path('cache.html')
        if not local_path.exists():
            text = fetch_text(url)
            local_path.write_text(text)
        else:
            text = local_path.read_text()
    else:
        text = fetch_text(url)
    
    soup = BeautifulSoup(text, 'html.parser')
    word_set = soup.find_all('div', { 'class': 'divBunruiRight'})
    words = []
    for word_html in word_set:
        word_info = parse_word(word_html)
        words.append(word_info)
    return words

def download_file(url, local_path):
    filename = url.split('/').pop()
    local_path = Path(local_path) / filename

    #http://chugokugo-script.net/tango/level1/../audio/人.mp3
    if not local_path.exists():
        content = requests.get(url).content          
        local_path.write_bytes(content)
    return str(local_path)

def download_audio_files(words, base_url, media_folder):
    for word in words:
        word.audio = download_file(urljoin(base_url, word.audio), media_folder) 
        for sentence in word.example_sentences:
            sentence.audio = download_file(urljoin(base_url, sentence.audio), media_folder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Go to a website and retrieve word information')
    parser.add_argument('url', help='Folder to monitor for images.')
    parser.add_argument('media_folder', help='Folder to store media (images, audio, etc.)')

    args = parser.parse_args()
    words = parse_site(args.url, True)
    download_audio_files(words, args.url, args.media_folder)
    for word in words:
        print(word)

    