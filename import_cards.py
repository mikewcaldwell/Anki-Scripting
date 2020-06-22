import parse_site

import sys, os
import functools
import genanki

word_model = genanki.Model(
    2042686211,
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
    2042686212,
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

if __name__ == "__main__":
    deck = genanki.Deck(
        1724897887,
        'Chinese')
    user_media_folder = "/Users/mike/Downloads/media"
    site_data = parse_site.parse(
        "http://chugokugo-script.net/tango/level1/meishi.html", 
        True, 
        user_media_folder)
    import_words(site_data, deck)
    media_files = []
    for word in site_data:
        media_files += word.get_audio_files()
    my_package = genanki.Package(deck)
    my_package.media_files = media_files
    my_package.write_to_file('/Users/mike/Chinese_with_media_test.apkg')