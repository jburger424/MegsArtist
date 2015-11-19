import os
from flask import Flask, render_template, session, redirect, url_for, flash, jsonify, request, json
from flask.ext.script import Manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, SelectField, validators
from wtforms.validators import Required
from flask.ext.sqlalchemy import SQLAlchemy


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
WTF_CSRF_SECRET_KEY = 'a random string'

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)

#initiates Genre table
class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    artists = db.relationship('Artist', backref='genre', lazy='dynamic')

    def __repr__(self):
        return '<Genre %r>' % self.name

#initiates Artist table
class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'))
    description = db.Column(db.String(264), unique=False, index=True)
    image = db.Column(db.String(264), unique=False, index=True)
    songName = db.Column(db.String(64), unique=False, index=True)
    songURL = db.Column(db.String(264), unique=False, index=True)

    def __repr__(self):
        return '<Artist %r>' % self.name


class ArtistForm(Form):
    artistName = StringField('Artist Name*', validators=[Required()])
    artistGenre = SelectField(u'Genre', coerce=int, validators=[validators.NumberRange(min=1, max=None, message="Not a Valid Option")])
    artistDescription = TextAreaField('Description')
    artistImage = StringField('Image URL')
    artistSongName = StringField('Song Name')
    artistSongURL = StringField('Song URL')
    submit = SubmitField('Submit')

    def reset(self):
        self.artistName.data = self.artistDescription.data = self.artistImage.data = self.artistSongName.data = self.artistSongURL.data = ""


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    print(e)
    return render_template('500.html', error=e), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/artists/')
def artists():
    return render_template('artists.html', artistNames=[artist.name for artist in
                                                        Artist.query.all()])  # artistNames=session.get('artistNameList')


@app.route('/artists/<artistName>')
def artist(artistName):
    artistObj = Artist.query.filter_by(name=artistName).first()
    if artistObj is None:
        return render_template('artist.html', artistName="null")
    else:
        return render_template('artist.html', artistName=artistObj.name,
                               artistDescription=artistObj.description,
                               artistImageURL=artistObj.image,
                               songName=artistObj.songName,
                               songURL=artistObj.songURL
                               )


@app.route('/artists/add/', methods=['GET', 'POST'])
def addArtist():
    artistForm = ArtistForm(csrf_enabled=False)
    choices = [(genre.id, genre.name) for genre in Genre.query.all()]
    choices = sorted(choices,key=lambda x: x[1].upper())
    choices.append((-2, "-------------"))
    choices.append((-1, "**Add Genre**"))
    artistForm.artistGenre.choices = choices
    if artistForm.validate_on_submit():
        user = Artist.query.filter_by(name=artistForm.artistName.data).first()
        if user is None:
            user = Artist(name=artistForm.artistName.data,
                      genre_id=artistForm.artistGenre.data,
                      description=artistForm.artistDescription.data,
                      image=artistForm.artistImage.data,
                      songName=artistForm.artistSongName.data,
                      songURL=artistForm.artistSongURL.data,
                      )
            db.session.add(user)
            db.session.commit()
            artistForm.reset()  # TODO: reset genre selector!!
            message = user.name + " Successfully Added.  <a href='/artists/" + user.name + "'>View Page</a>"
            flash(message,"error")

        else:
            message = "Error: " + user.name + " Already Exists.  <a href='/artists/" + user.name + "'>View Page</a>"
            flash(message, "error")
            return render_template('form.html', artistForm=artistForm)
    return render_template('form.html', artistForm=artistForm)


@app.route('/artists/add/genre/', methods=['POST'])
#doesn't render a page, only used for AJAX post
def addGenre():
    jsonData = request.json
    newGenre = jsonData.get('newGenre')
    newGenre = Genre.query.filter_by(name=newGenre).first()
    if newGenre is None:
        newGenre = jsonData.get('newGenre')
        genre = Genre(name=newGenre)
        db.session.add(genre)
        db.session.commit()
        newGenreID = Genre.query.filter_by(name=newGenre).first().id
        #send back success message to js with new genre ID
        return json.dumps({'success':True,'genre_id':newGenreID}), 200, {'ContentType':'application/json'}
    else:
        #-1 means duplicate genre
        return json.dumps({'success':True,'genre_id':-1}), 200, {'ContentType':'application/json'}


if __name__ == '__main__':
    manager.run()
