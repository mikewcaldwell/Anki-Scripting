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
        self.definition = definition
        self.audio = audio
        self.example_sentences = example_sentences
        self.additional_info = additional_info
        self.picture = picture

    def __str__(self):
        sentence_string = ''
        for sentence in self.example_sentences:
            sentence_string += f'\t {str(sentence)}'
        return f'''Word: {self.word}
    Translation: {self.translation}
    Pronunciation: {self.pronunciation}
    Audio: {self.audio} 
    Additional Info: {self.additional_info}\t
    Picture: {self.picture}
    Examples:\n {sentence_string}'''

    def get_audio_file_name(self):
        return Path(self.audio).name
    
    def get_audio_files(self):
        audio_file_names = []
        if Path(self.audio).exists():
            audio_file_names.append(self.audio)
        for sentence in self.example_sentences:
            if Path(sentence.audio).exists():
                audio_file_names.append(sentence.audio)
        return audio_file_names
        

class SentenceInfo:
    def __init__(self, sentence, translation, pronunciation, audio, grammar_used):
        self.sentence = sentence
        self.translation = translation
        self.pronunciation = pronunciation
        self.audio = audio
        self.grammar_used = grammar_used
    
    def __str__(self):
        grammar_string = ''
        for grammar in self.grammar_used:
            grammar_string += str(grammar)
        return f'''Sentence: {self.sentence}
            Translation: {self.translation}
            Pronunciation: {self.pronunciation}
            Audio: {self.audio} 
            Grammar:\n {grammar_string}'''
    
    def get_audio_file_name(self):
        return Path(self.audio).name

class GrammarInfo:
    def __init__(self, point, explanation):
        self.point = point
        self.explanation = explanation
    def __str__(self):
        return f'               Grammar Point: {self.point}, Explanation: {self.explanation}'

def __parse_grammars(grammar_set):
    grammar_used=[]
    for grammar_html in grammar_set:
        grammar_item = grammar_html.summary.string or ''
        grammar_explanation = grammar_html.div.string or ''
        if grammar_item == '' and grammar_explanation == '':
            continue
        grammar_used.append(GrammarInfo(grammar_item, grammar_explanation)) 
    return grammar_used

def __parse_sentences(sentence_set):
    example_sentences=[]
    for sentence_html in sentence_set:
        sentence = sentence_html.find(class_='divBunruiExC').string
        if sentence in [None, '']:
            continue
        translation = sentence_html.find(class_='divBunruiExN').string or ''
        pronunciation = sentence_html.find(class_='divBunruiExP').string
        audio = sentence_html.find(class_='divBunruiExA').audio.source['src']
        grammar_used = __parse_grammars(sentence_html.find_all(class_='detailsExBunpou'))
        example_sentences.append(SentenceInfo(sentence,translation,pronunciation,audio,grammar_used))
    return example_sentences

def __parse_word(word_html):
    word = word_html.find(class_='divBunruiC').string
    translation = word_html.find(class_='divBunruiN').string
    pronunciation = word_html.find(class_='divBunruiP').string
    audio = word_html.find(class_='divBunruiA').audio.source['src']
    example_sentences = __parse_sentences(word_html.find_all(class_='divBunruiExMain'))
    word_info = WordInfo(word,translation,'',pronunciation,audio,example_sentences,'','')
    return word_info

def __fetch_text(url):
    page = requests.get(url)
    #need to enforce utf-8 or else encoding is messed up
    page.encoding = 'utf-8'
    return page.text

def __parse_text(text):
    soup = BeautifulSoup(text, 'html.parser')
    word_set = soup.find_all('div', { 'class': 'divBunruiRight'})
    words = []
    for word_html in word_set:
        word_info = __parse_word(word_html)
        words.append(word_info)
    return words

def __parse_site(url, use_cache):
    #this page doesn't change very often if at all, so just cache it
    if use_cache:
        parts = url.split('/')
        filename = parts.pop()
        subpath = parts.pop()

        cache_dir  = Path('./cache') / subpath
        cache_dir.mkdir(parents=True, exist_ok=True)
          
        local_path = cache_dir / filename
        if not local_path.exists():
            text = __fetch_text(url)
            local_path.write_text(text)
        else:
            text = local_path.read_text()
    else:
        text = __fetch_text(url)
    return __parse_text(text)

def __parse_file(file):
    local_path = Path(file)
    text = local_path.read_text()
    return __parse_text(text)

def __download_file(url, local_path):
    #make a path that looks like: http://chugokugo-script.net/tango/level1/../audio/人.mp3
    filename = url.split('/').pop()
    local_path = Path(local_path) / filename

    if not local_path.exists():
        content = requests.get(url).content          
        local_path.write_bytes(content)
    return str(local_path)

def __download_audio_files(words, base_url, media_folder):
    for word in words:
        word.audio = __download_file(urljoin(base_url, word.audio), media_folder) 
        for sentence in word.example_sentences:
            sentence.audio = __download_file(urljoin(base_url, sentence.audio), media_folder)

def parse(url, use_cache, media_folder):
    words = __parse_site(url, use_cache)
    if media_folder is None:
        return words
    
    media_folder_path = Path(media_folder)
    if not media_folder_path.exists():
        media_folder_path.mkdir()
    __download_audio_files(words, url, media_folder)
    return words

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Go to a website and retrieve word information')
    parser.add_argument('url', help='Folder to monitor for images.')
    parser.add_argument('media_folder', help='Folder to store media (images, audio, etc.)')

    args = parser.parse_args()
    words = parse(args.url, True, args.media_folder)
    for word in words:
        print(word)