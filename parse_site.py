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
        self.word = word or ''
        self.translation = translation or ''
        self.pronunciation = pronunciation or ''
        self.definition = definition or ''
        self.audio = audio or ''
        self.example_sentences = example_sentences or ''
        self.additional_info = additional_info or ''
        self.picture = picture or ''

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
        #Return just the name (ie: file.mp3) for the audio of this word.
        return Path(self.audio).name
    
    def get_audio_file_paths(self):
        #Returns an array of all audio files for this word (including example sentences).
        audio_file_names = []
        audio_file_names.append(self.audio)
        for sentence in self.example_sentences:
            audio_file_names.append(sentence.audio)
        return audio_file_names

class SentenceInfo:
    def __init__(self, sentence, translation, pronunciation, audio, grammar_used):
        self.sentence = sentence or ''
        self.translation = translation or ''
        self.pronunciation = pronunciation or ''
        self.audio = audio or ''
        self.grammar_used = grammar_used or ''
    
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
        #Return the name (ie: file1.mp3) for the audio file for this sentence.
        return Path(self.audio).name

class GrammarInfo:
    def __init__(self, point, explanation):
        self.point = point or ''
        self.explanation = explanation or ''
    def __str__(self):
        return f'               Grammar Point: {self.point}, Explanation: {self.explanation}'

def __parse_grammars(grammar_set):
    #take the soup representing grammar information and parse out the contents
    grammar_used=[]
    for grammar_html in grammar_set:
        grammar_item = grammar_html.summary.string or ''
        grammar_explanation = grammar_html.div.string or ''
        if grammar_item == '' and grammar_explanation == '':
            continue
        grammar_used.append(GrammarInfo(grammar_item, grammar_explanation)) 
    return grammar_used

def __parse_sentences(sentence_set):
    #take the soup representing an example sentence and parse out the contents
    example_sentences=[]
    for sentence_html in sentence_set:
        sentence = sentence_html.find(class_='divBunruiExC').string
        if sentence in [None, '']:
            continue
        translation = sentence_html.find(class_='divBunruiExN').string
        pronunciation = sentence_html.find(class_='divBunruiExP').string
        audio = sentence_html.find(class_='divBunruiExA').audio.source['src']
        grammar_used = __parse_grammars(sentence_html.find_all(class_='detailsExBunpou'))
        example_sentences.append(SentenceInfo(sentence,translation,pronunciation,audio,grammar_used))
    return example_sentences

def __parse_word(word_html):
    #take the soup representing word and parse out the contents
    word = word_html.find(class_='divBunruiC').string
    translation = word_html.find(class_='divBunruiN').string
    pronunciation = word_html.find(class_='divBunruiP').string
    audio = word_html.find(class_='divBunruiA').audio.source['src']
    example_sentences = __parse_sentences(word_html.find_all(class_='divBunruiExMain'))
    word_info = WordInfo(word, translation, None, pronunciation, audio,example_sentences, None, None)
    return word_info

def __fetch_text(url):
    #return text for the website.
    page = requests.get(url)
    #need to enforce utf-8 or else encoding is messed up
    page.encoding = 'utf-8'
    return page.text

def __parse_text(text):
    #parse soup for the website, returning an array of all the word information
    soup = BeautifulSoup(text, 'html.parser')
    word_set = soup.find_all('div', { 'class': 'divBunruiRight'})
    words = []
    for word_html in word_set:
        word_info = __parse_word(word_html)
        words.append(word_info)
    return words

def __parse_site(url, use_cache):
    #Read a webpage from online and parse out the information. 
    #If use_cache is True, we will save the file into a cache folder.
    #this page doesn't change very often if at all, so just cache it
    #cache it under a subfolder:
    # 'http://chugokugo-script.net/tango/level1/keiyoushi.html'
    #     -> ./cache/level1/keiyoushi.html
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

def __download_audio_files(words, base_url, media_folder):
    """Download audio files for the words and their sentence(s), then update to the local path.
    """
    for word in words:
        word.audio = download_file(urljoin(base_url, word.audio), media_folder) 
        for sentence in word.example_sentences:
            sentence.audio = download_file(urljoin(base_url, sentence.audio), media_folder)

def download_file(url, directory, filename = None):
    """
    Given a path to the url, download it the given directory.
    Defaults to the filename specified in the url, but can be overwritten.

    url - URL to the file to download.
    directory - Local directory to download the file too.
    filename - The name to give the downloaded file.
    """
    if not filename:
        filename = url.split('/').pop()
    
    local_path = Path(directory) / filename

    if not local_path.exists():
        content = requests.get(url).content          
        local_path.write_bytes(content)
    return str(local_path)


def parse(url, use_cache, media_folder):
    """
    Take a url, parse it, and download any referenced media files (mp3 in this case) to the media folder.
    url - url to parse
    use_cache - If true, check the cache for the file first.
    media_folder - Where to download files to.
    """
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