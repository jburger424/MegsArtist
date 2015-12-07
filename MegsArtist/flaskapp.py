import os

from flask import Flask, render_template, send_from_directory, flash, json, Response,request, redirect, url_for
from flask.ext.script import Manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField
from flask_wtf.file import FileField
from wtforms.validators import Required
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import secure_filename

IMG_FOLDER = '/Users/rebeccahong/Desktop/MegsArtist/MegsArtist/img/'
TRACK_FOLDER = '/Users/rebeccahong/Desktop/MegsArtist/MegsArtist/track/'

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['IMG_FOLDER'] = IMG_FOLDER
app.config['TRACK_FOLDER'] = TRACK_FOLDER
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
WTF_CSRF_SECRET_KEY = 'a random string'

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)



artist_to_tag = db.Table('artist_to_tag',
                             db.Column('artist_id', db.Integer, db.ForeignKey('artist.id')),
                             db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                             db.PrimaryKeyConstraint('artist_id', 'tag_id')
                             )

track_to_tag = db.Table('track_to_tag',
                        db.Column('track_id', db.Integer, db.ForeignKey('track.id')),
                        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                        db.PrimaryKeyConstraint('track_id', 'tag_id')
                        )
# initiates Tag table
class Tag(db.Model):
    # __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # artist = db.relationship('Artist', backref='tag', lazy='dynamic')
    # TODO: relationship with tag and track
    artists = db.relationship('Artist', secondary=artist_to_tag,
                              backref=db.backref('tag', lazy='dynamic'))
    tracks = db.relationship('Track', secondary=track_to_tag,
                             backref=db.backref('tag', lazy='dynamic'))

    def __repr__(self):
        return '<Tag %r>' % self.name


# IMPORTANT: Get ALl Artists by tag: x = Artist.query.filter(Artist.tags.any(name="Test")).all()
# Get Artist object by name, with Tags

# initiates Artist table
class Artist(db.Model):
    # __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    description = db.Column(db.String(264), unique=False, index=True)
    image = db.Column(db.String(264), unique=False, index=True)
    tags = db.relationship('Tag', secondary=artist_to_tag,
                           backref=db.backref('artist', lazy='dynamic'))

    def __repr__(self):
        return '<Artist %r>' % self.name


# initiates Track table
class Track(db.Model):
    #__tablename__ = 'track'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    url = db.Column(db.String(264), unique=False, index=True)
    tags = db.relationship('Tag', secondary=track_to_tag,
                           backref=db.backref('track', lazy='dynamic'))

    def __repr__(self):
        return '<Track %r>' % self.name




class ArtistForm(Form):
    artistName = StringField('Artist Name*', validators=[Required()])
    # artistTags = SelectMultipleField(u'Tag', coerce=int, validators=[validators.NumberRange(message="Not a Valid Option")])
    artistTags = StringField('Artist Tags')
    artistDescription = TextAreaField('Description')
    artistImage = FileField('Upload an Image')
    # photo = FileField('Your photo')
    submit = SubmitField('Submit')

    def reset(self):
        self.artistName.data = self.artistDescription.data = self.artistImage.data = ""


class TrackForm(Form):
    artistName = StringField('Artist Name*', validators=[Required()])
    trackName = StringField('Track Name*', validators=[Required()])
    trackTags = StringField('Track Tags')
    trackURL = FileField('Upload your track',validators=[Required()])
    submit = SubmitField('Submit')

    def reset(self):
        self.trackName.data = self.trackURL.data = ""


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


@app.route('/tags/')
def tags():
    return render_template('tags.html', tagNames=[tag.name for tag in
                                                  Tag.query.all()])  # artistNames=session.get('artistNameList')


@app.route('/artists/')
def artists():
    return render_template('artists.html', artistNames=[artist.name for artist in
                                                        Artist.query.all()])  # artistNames=session.get('artistNameList')


@app.route('/artists/<artistName>')
def getArtist(artistName):
    # artistObj = Artist.query.filter_by(name=artistName).first()
    artistObj = Artist.query.join(Tag.artist).filter_by(name=artistName).first()
    tracks = Track.query.filter_by(id = artistObj.id).all()
    print(artistObj.tags)
    if artistObj is None:
        return render_template('artist.html', artistName="null")
    else:
        return render_template('artist.html', artistName=artistObj.name,
                               artistDescription=artistObj.description,
                               artistImageURL=artistObj.image, tags=artistObj.tags,
                               tracks=tracks
                               )


@app.route('/tags/<tagName>')
def getTag(tagName):
    # artistObj = Artist.query.filter_by(name=artistName).first()
    tagObj = Tag.query.join(Artist.tags).filter_by(name=tagName).first()
    print(tagObj.artists)
    if tagObj is None:
        return render_template('tag.html', tagName="null")
    else:
        return render_template('tag.html', tagName=tagObj.name, artists=tagObj.artists)


@app.route('/uploadedImg/<filename>')
def uploaded_img(filename):
    return send_from_directory(app.config['IMG_FOLDER'],
                               filename)

@app.route('/uploadedTrack/<filename>')
def uploaded_song(filename):
    return send_from_directory(app.config['TRACK_FOLDER'],
                               filename)


@app.route('/artists/add/', methods=['GET', 'POST'])
def addArtist():
    artistForm = ArtistForm(srf_enabled=False)
    artistTags = artistForm.artistTags.data

    if isinstance(artistTags, str):
        artistTags = artistTags.split(", ")

    if artistForm.validate_on_submit():
        user = Artist.query.filter_by(name=artistForm.artistName.data).first()

        if user is None:
            user = Artist(
                name=artistForm.artistName.data,
                description=artistForm.artistDescription.data
            )
            if artistForm.artistImage.has_file():
                filename = secure_filename(artistForm.artistImage.data.filename)
                artistForm.artistImage.data.save(IMG_FOLDER + filename)
                user.image = filename

            for tagName in artistTags:
                tag = Tag.query.filter_by(name=tagName).first()
                if tag is None:
                    tag = Tag(name=tagName)
                user.tags.append(tag)
                db.session.add(user)
                db.session.commit()

            message = user.name + " Successfully Added.  <a href='/artists/" + user.name + "'>View Page</a>"
            flash(message, "success")

        else:
            message = "Error: " + user.name + " Already Exists.  <a href='/artist/" + user.name + "'>View Page</a>"
            flash(message, "error")
            return render_template('form.html', artistForm=artistForm)

    return render_template('form.html', artistForm=artistForm)

@app.route('/getTags/', methods=['GET'])
def getTags():
    tags = [tag.name for tag in Tag.query.all()]
    return Response(json.dumps(tags), mimetype='application/json')


@app.route('/artists/add/tag/', methods=['POST'])
# doesn't render a page, only used for AJAX post
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
        # send back success message to js with new tag ID
        return json.dumps({'success': True, 'tag_id': newTagID}), 200, {'ContentType': 'application/json'}
    else:
        # -1 means duplicate tag
        return json.dumps({'success': True, 'tag_id': -1}), 200, {'ContentType': 'application/json'}

#add track
@app.route('/tracks/add/', methods=['GET', 'POST'])
def addTrack():
    trackForm = TrackForm(csrf_enabled=False)
    trackTags = trackForm.trackTags.data
    if isinstance(trackTags, str):
        trackTags = trackTags.split(", ")
    if trackForm.validate_on_submit():
        #user = Artist.query.filter_by(name=trackForm.artistName.data).first()
        user = Artist.query.join(Tag.artist).filter_by(name=trackForm.artistName.data).first()
        if user is None:
            message = "Error: " + user.name + " Does Not Exists."
            flash(message, "error")
            return render_template('form.html', trackForm=trackForm)
        else:
            track = Track(
                name=trackForm.trackName.data,
                artist_id = user.id,
                url = trackForm.trackURL.data.filename
            )
            filename = secure_filename(trackForm.trackURL.data.filename)
            trackForm.trackURL.data.save(TRACK_FOLDER + filename)

        for tagName in trackTags:
            tag = Tag.query.filter_by(name=tagName).first()
            if tag is None:
                tag = Tag(name=tagName)
            track.tags.append(tag)
            db.session.add(track)
            db.session.commit()

        message = user.name + " Successfully Added.  <a href='/artists/" + user.name + "'>View Page</a>"
        flash(message, "success")
    return render_template('addTrack.html', trackForm=trackForm)

if __name__ == '__main__':
    manager.run()
