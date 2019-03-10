import os
import requests

from flask import Flask, flash, jsonify, redirect, url_for, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from helpers import apology
from bs4 import BeautifulSoup


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


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/simple_chart")
def chart():
    labels = [
        'JAN', 'FEB', 'MAR', 'APR',
        'MAY', 'JUN', 'JUL', 'AUG',
        'SEP', 'OCT', 'NOV', 'DEC'
    ]

    values = [
        967.67, 1190.89, 1079.75, 1349.19,
        2328.91, 2504.28, 2873.83, 4764.87,
        4349.29, 6458.30, 9907, 16297
    ]

    colors = [
        "#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
        "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
        "#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]

    bar_labels=labels
    bar_values=values
    return render_template('chart.html', title='Word Chart', max=17000, labels=bar_labels, values=bar_values)

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


    response = requests.get(song_url)

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

    response2 = requests.get(lyric_page)

    #Grab the element from page that contains song lyrics
    #Grab title for item that the search query returned
    soup2 = BeautifulSoup(response2.content, 'html.parser')
    lyric_list = []
    lyrics = str(soup2.find('div', attrs = {'class':None, 'id':None}).get_text())
    for line in lyrics.split("\n"):
        lyric_list.append(line)
    songmetadata = str(soup2.find('title').getText()).split(' -')
    print(songmetadata)
    artist = songmetadata[0]
    songtitle = songmetadata[1].split(" |")[0].replace(" Lyrics", "").strip()
    print(songtitle)
    print(artist)
    print("Returned lyrics for %s by %s" % (songtitle, artist))

    return render_template("query.html", artist = artist, songtitle = songtitle, lyric_list = lyric_list)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
