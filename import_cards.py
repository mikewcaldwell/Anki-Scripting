import parse_site

import sys, os
import functools
import genanki
import random
import argparse
from pathlib import Path

word_model = genanki.Model(
    random.randrange(1 << 30, 1 << 31),
    '中国語の単語',
    css='''.card {
        font-family: arial;
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
        }

        .hint{
        margin: 0.7em auto 0 auto;
        padding: 0.2em;
        border-radius: 5px;
        border: 1px lime outset;
        background-color: lightgreen;
        }

        .answer{
            font-size: 50px;
        }''',
    fields=[
        {'name': '単語'},
        {'name': '翻訳'},
        {'name': '写真'},
        {'name': '定義 (中国語）'},
        {'name': 'ピンイン'},
        {'name': '発音（ファイル）'},
        {'name': '文章（単語なし）'},
        {'name': '他の情報（単語がある文章が含む）'},
    ],
    templates=[
        {
            'name': 'Card 1',
            'qfmt': '{{単語}}',
            'afmt': '''{{FrontSide}}
                    <hr id=answer>

                    <div class='answer'>{{ピンイン}}</div>{{発音（ファイル）}}
                    <br><br>
                    <div style='font-family: Arial; font-size: 20px;'>{{他の情報（単語がある文章が含む）}}</div>
                    {{#定義（中国語）}}<div style='font-family: Arial; font-size: 20px;'>定義：{{定義（中国語）}}</div>{{/定義（中国語）}}
                    <br><button id="hintbutton">翻訳を示す</button>
                    <div class='hint' id="grammar" style="display:none">翻訳<br>{{翻訳}}</div>
                    <script>
                    $("#hintbutton").click(function(){
                        $("#hintbutton").fadeOut();
                        $("#grammar").fadeIn();
                    });
                    </script>''',
        },
        {
            'name': 'Card 2',
            'qfmt': '''単語は何ですか？
                    <div style='font-family: Arial; font-size: 20px;'>{{文章（単語なし）}}</div>
                    <div style='font-family: Arial; font-size: 20px;'>{{ピンイン}}</div>
                    <div style='font-family: Arial; font-size: 20px;'>{{発音（ファイル）}}</div>

                    {{#定義（中国語）}}<div style='font-family: Arial; font-size: 20px;'>定義：{{定義（中国語）}}</div>{{/定義（中国語）}}
                    ''',
            'afmt': '''{{FrontSide}}
                <hr id=answer>
                <div class='answer'>{{単語}}</div>''',
        },
    ])

#sentence, pinyin, translation, audio [sound:ex东西.mp3], grammar     
sentence_model = genanki.Model(
    random.randrange(1 << 30, 1 << 31),
    '中国語の文章',
    css='''.card {
        font-family: arial;
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
        }

        .hint{
        margin: 0.7em auto 0 auto;
        padding: 0.2em;
        border-radius: 5px;
        border: 1px lime outset;
        background-color: lightgreen;
        }''',
    fields=[
        {'name': '文章'},
        {'name': 'ピンイン'},
        {'name': '翻訳'},
        {'name': '発音（ファイル）'},
        {'name': '文法'},
    ],
    templates=[
        {
            'name': 'Card 1',
            'qfmt': '<div style="font-family: Arial; font-size: 20px;">{{発音（ファイル）}}</div>',
            'afmt': '''{{FrontSide}}<hr id=answer>
                    <div style='font-family: Arial; font-size: 20px;'>{{ピンイン}}</div>
                    <div style='font-family: Arial; font-size: 20px;'>{{文章}}</div>
                    <br><button id="transbutton">翻訳を示す</button>
                    <div class='hint' id='translation' style='display:none; font-family: Arial; font-size: 20px;'>翻訳<br>{{翻訳}}</div>
                    <br><button id="grammarbutton">文法を示す</button>
                    <div id="grammar" class='hint' style="display:none">文法<br>{{文法}}</div>
                    <script>
                    $("#grammarbutton").click(function(){
                        $("#grammarbutton").fadeOut();
                        $("#grammar").fadeIn();
                    });
                    $("#transbutton").click(function(){
                        $("#transbutton").fadeOut();
                        $("#translation").fadeIn();
                    });
                    </script>''',
        },
    ])

def import_words(words, deck):
    for word in words:

        sentences_no_word = map(lambda s: s.sentence.replace(word.word, '__'), word.example_sentences)
        sentences_no_word_field=''
        for sentence in sentences_no_word:
            sentences_no_word_field += f'{sentence}\n'
        sentences_field = ''
        for example in word.example_sentences:
            sentences_field += f'{example.sentence}\n'
        #word, translation, picture, defn, pinyin, audio [sound:ex东西.mp3], sentence (no word), additional info
    
        aNote = genanki.Note(
            model=word_model, fields=
            [word.word, word.translation, word.picture, word.definition, word.pronunciation, f'[sound:{word.get_audio_file_name()}]',
            sentences_no_word_field, sentences_field]
        )
        deck.add_note(aNote)
        import_sentences(word.example_sentences, deck)

def import_sentences(sentences, deck):
    for sentence in sentences:
        grammar_field = ''
        for grammar in sentence.grammar_used:
            grammar_field += f'{grammar.point}:{grammar.explanation}\n'

        #sentence, pinyin, translation, audio [sound:ex东西.mp3], grammar     
        aNote = genanki.Note(
            model=sentence_model, fields=[
                sentence.sentence, 
                sentence.pronunciation, 
                sentence.translation, 
                f'[sound:{sentence.get_audio_file_name()}]', 
                grammar_field]
        )
        deck.add_note(aNote) 

def create_chinese_deck(deck_name, url, media_folder):
    deck = genanki.Deck(
        random.randrange(1 << 30, 1 << 31),
        deck_name)
    words = parse_site.parse(
        url,
        True,
        media_folder)
    import_words(words, deck)
    return deck, words

def create_anki_package(media_folder, output, level):
    noun_deck, nouns = create_chinese_deck(
        f'中国語単語 レベル{level}::1. 名詞・代詞・量詞', 
        f'http://chugokugo-script.net/tango/level{level}/meishi.html',
        media_folder)
    verb_deck, verbs = create_chinese_deck(
        f'中国語単語 レベル{level}::2. 動詞・助動詞・助詞', 
        f'http://chugokugo-script.net/tango/level{level}/doushi.html',
        media_folder)
    adj_deck, adjectives = create_chinese_deck(
        f'中国語単語 レベル{level}::3. 形容詞・副詞・その他', 
        f'http://chugokugo-script.net/tango/level{level}/keiyoushi.html',
        media_folder)
    
    media_files = []
    for word in (nouns + verbs + adjectives):
        media_files += word.get_audio_files()
    
    my_package = genanki.Package([noun_deck, verb_deck, adj_deck], media_files)
    output_path = Path(output) / f'Chinese_Level_{level}.apkg'
    my_package.write_to_file(output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create an anki deck based on data from Chinese for Japanese speakers website.')
    parser.add_argument('media_folder', help='Folder to store media (images, audio, etc.)')
    parser.add_argument('output', help='Output folder for package file.')
    parser.add_argument('level', type=int, choices=[1,2,3])
    args = parser.parse_args()
    
    create_anki_package(args.media_folder, args.output, args.level)