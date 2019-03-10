import requests
import io
import os
from wordcloud import WordCloud
from flask import Flask, redirect, url_for, render_template, request, Response
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from helpers import apology, remove_punctuation
from bs4 import BeautifulSoup
from collections import Counter

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

Session(app)

proxies = {
"http": os.environ['QUOTAGUARDSTATIC_URL'],
"https": os.environ['QUOTAGUARDSTATIC_URL']
}



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = str(request.form.get("songlyrics"))
        return redirect(url_for('getlyrics', query = query))
    else:
        method = "GET"
        return render_template("index.html", method = method)

@app.route("/getlyrics", methods=["GET"])
def getlyrics():

    
    # Query database for query
    query = request.args.get('query', None)
    if ' ' in query:
            query = query.replace(' ', '+')
            song_url = 'https://search.azlyrics.com/search.php?q=' + query
    else:
            song_url = 'https://search.azlyrics.com/search.php?q=' + query

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}
    response = requests.get(song_url, headers = headers)

    soup = BeautifulSoup(response.content, 'html.parser')

    #With albums
    with_albums = soup.find_all('div', attrs= 'panel')

    #Without albums
    without_albums = soup.find_all('td', attrs = {'class' : 'text-left visitedlyr'})

    #If album panel is also shown, select the song panel instead
    if len(with_albums) > 2:
        lyric_page = (with_albums[2].find('a').get('href'))
    elif len(with_albums) > 1:
        lyric_page = (with_albums[1].find('a').get('href'))
    elif without_albums:
        lyric_page = (without_albums[0].find('a').get('href'))
    else:
        print('Sorry, we could not find any results for that search. Please modify your search terms.' + '\n')
    
    response2 = requests.get(lyric_page, headers = headers, proxies = proxies)

    #Grab the element from page that contains song lyrics
    #Grab title for item that the search query returned
    soup2 = BeautifulSoup(response2.content, 'html.parser')
    lyric_list = []
    lyrics = str(soup2.find('div', attrs = {'class':None, 'id':None}).get_text())
    for line in lyrics.split("\n"):
        lyric_list.append(line)
    songmetadata = str(soup2.find('title').getText()).split(' -')
    artist = songmetadata[0]
    songtitle = songmetadata[1].split(" |")[0].replace(" Lyrics", "").strip()

    word_count = Counter()

    for line in lyric_list:
        for word in line.split():
            word = word.lower()
            word = remove_punctuation(word)
            word_count[word] += 1

    words = word_count.most_common(12)

    labels = []
    values = []
    for i in range(len(words)):
        labels.append(words[i][0])
        values.append(words[i][1])

    wordcloud_text = ' '.join(map(str, lyric_list)).strip().lower()
    for word in wordcloud_text.split():
        word = remove_punctuation(word)

    return render_template("query.html", artist = artist, songtitle = songtitle, lyric_list = lyric_list, max=values[0], labels=labels, values=values, wordcloud_text = wordcloud_text)

@app.route('/image/<wordcloud_text>/plot.png')
def wordcloud(wordcloud_text):
    wordcloud = WordCloud(stopwords = " ", collocations = False).generate(wordcloud_text)
    img = io.BytesIO()
    wordcloud.to_image().save(img, 'PNG')
    img.seek(0)
    return Response(img.getvalue(), mimetype='image/png')

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
