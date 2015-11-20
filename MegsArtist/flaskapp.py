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

#initiates Tag table
class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    artists = db.relationship('Artist', backref='tags', lazy='dynamic')

    def __repr__(self):
        return '<Tag %r>' % self.name


#initiates Artist table
class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'))
    description = db.Column(db.String(264), unique=False, index=True)
    image = db.Column(db.String(264), unique=False, index=True)
    songName = db.Column(db.String(64), unique=False, index=True)
    songURL = db.Column(db.String(264), unique=False, index=True)

    def __repr__(self):
        return '<Artist %r>' % self.name


#initiates Track table
class Track(db.Model):
    __tablename__ = 'tracks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))
    url = db.Column(db.String(264), unique=False, index=True)
    def __repr__(self):
        return '<Track %r>' % self.name


#initiates ArtistToTag table
class ArtistToTag(db.Model):
    __tablename__ = 'ArtistToTag'
    id = db.Column(db.Integer,primary_key=True)
    artist_id = db.Column(db.Integer,db.ForeignKey('artists.id'))
    tag_id = db.Column(db.Integer,db.ForeignKey('tags.id'))

    def __repr__(self):
        return '<ArtistToTag %r>' % self.artist_id, self.tag_id


#initiates TrackToTag table
class TrackToTag(db.Model):
    __tablename__ = 'TrackToTag'
    id = db.Column(db.Integer,primary_key=True)
    track_id = db.Column(db.Integer,db.ForeignKey('tracks.id'))
    tag_id = db.Column(db.Integer,db.ForeignKey('tags.id'))

    def __repr__(self):
        return '<TrackToTag %r>' % self.track_id, self.tag_id


class ArtistForm(Form):
    artistName = StringField('Artist Name*', validators=[Required()])
    artistTag = SelectField(u'Tag', coerce=int, validators=[validators.NumberRange(min=1, max=None, message="Not a Valid Option")])
    artistDescription = TextAreaField('Description')
    artistImage = StringField('Image URL')
    artistSongName = StringField('Song Name')
    artistSongURL = StringField('Song URL')
    submit = SubmitField('Submit')

    def reset(self):
        self.artistName.data = self.artistDescription.data = self.artistImage.data = self.artistSongName.data = self.artistSongURL.data = ""


class TrackForm(Form):
    artistName = StringField('Artist Name*', validators=[Required()])
    trackName = StringField('Track Name*', validators=[Required()])
    trackTag = SelectField(u'Tag', coerce=int, validators=[validators.NumberRange(min=1, max=None, message="Not a Valid Option")])
    trackURL = StringField('Track URL')
    submit = SubmitField('Submit')

    def reset(self):
        self.trackName.data=self.trackURL.data=""


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
    choices = [(tag.id, tag.name) for tag in Tag.query.all()]
    choices = sorted(choices,key=lambda x: x[1].upper())
    choices.append((-2, "-------------"))
    choices.append((-1, "**Add Tag**"))
    artistForm.artistTag.choices = choices
    if artistForm.validate_on_submit():
        user = Artist.query.filter_by(name=artistForm.artistName.data).first()
        if user is None:
            user = Artist(name=artistForm.artistName.data,
                      tag_id=artistForm.artistTag.data,
                      description=artistForm.artistDescription.data,
                      image=artistForm.artistImage.data,
                      songName=artistForm.artistSongName.data,
                      songURL=artistForm.artistSongURL.data,
                      )
            db.session.add(user)
            db.session.commit()

            newArtistToTag = ArtistToTag(
                artist_id = Artist.query.filter_by(name=artistForm.artistName.data).first().id,
                tag_id = artistForm.artistTag.data
            )
            db.session.add(newArtistToTag)
            db.session.commit()

            artistForm.reset()  # TODO: reset Tag selector!!

            message = user.name + " Successfully Added.  <a href='/artists/" + user.name + "'>View Page</a>"
            flash(message,"success")

        else:
            message = "Error: " + user.name + " Already Exists.  <a href='/artists/" + user.name + "'>View Page</a>"
            flash(message, "error")
            return render_template('form.html', artistForm=artistForm)
    return render_template('form.html', artistForm=artistForm)


@app.route('/artists/add/tag/', methods=['POST'])
#doesn't render a page, only used for AJAX post
def addTag():
    jsonData = request.json
    newTag = jsonData.get('newTag')
    newTag = Tag.query.filter_by(name=newTag).first()
    if newTag is None:
        newTag = jsonData.get('newTag')
        tag = Tag(name=newTag)
        db.session.add(tag)
        db.session.commit()
        newTagID = Tag.query.filter_by(name=newTag).first().id
        #send back success message to js with new tag ID
        return json.dumps({'success':True,'tag_id':newTagID}), 200, {'ContentType':'application/json'}
    else:
        #-1 means duplicate tag
        return json.dumps({'success':True,'tag_id':-1}), 200, {'ContentType':'application/json'}


@app.route('/tracks/add/<artistName>', methods=['GET', 'POST'])
def addTrack(artistName):
    trackForm = TrackForm(csrf_enabled=False)
    choices = [(tag.id, tag.name) for tag in Tag.query.all()]
    choices = sorted(choices,key=lambda x: x[1].upper())
    choices.append((-2, "-------------"))
    choices.append((-1, "**Add Tag**"))
    trackForm.trackTag.choices = choices
    trackForm.artistName.data=artistName
    if trackForm.validate_on_submit():
        artistName = trackForm.artistName.data
        artist = Artist.query.filter_by(name=artistName).first()
        if artist is None:
            message = "Error: " + artistName + " doesn't exist."
            flash(message,"error")
            return render_template('addTrack.html',trackForm=trackForm)
        else:
            newTrack = Track(
                      artist_id=Artist.query.filter_by(name=artistName).first().id,
                      name = trackForm.trackName.data,
                      tag_id = trackForm.trackTag.data,
                      url=trackForm.trackURL.data
                      )

            db.session.add(newTrack)
            db.session.commit()

            newTrackToTag = TrackToTag(
                track_id = Artist.query.filter_by(name=trackForm.trackName.data).first().id,
                tag_id = trackForm.trackTag.data
            )
            db.session.add(newTrackToTag)
            db.session.commit()

            trackForm.reset()
            message = newTrack.name + " Successfully Added."
            flash(message,"success")

    return render_template('addTrack.html',trackForm=trackForm)


if __name__ == '__main__':
    manager.run()
