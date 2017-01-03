import os
import uuid
from flask import Flask, render_template, send_from_directory, flash, json, Response, request, redirect, url_for, \
    session
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField, validators
from flask_wtf.file import FileField, FileAllowed,FileRequired
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename, generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, AnonymousUserMixin, login_required, login_user, logout_user, current_user

#TODO: fix mobile navbar

basedir = os.path.abspath(os.path.dirname(__file__))

IMG_FOLDER = os.path.join(basedir, 'img/')
TRACK_FOLDER = os.path.join(basedir, 'track/')
app = Flask(__name__)
app.config['SECRET_KEY'] = 's-key'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['IMG_FOLDER'] = IMG_FOLDER
app.config['TRACK_FOLDER'] = TRACK_FOLDER
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

#will be disabled by default in future
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
WTF_CSRF_SECRET_KEY = 'a random string'

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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

class User(UserMixin, db.Model):
    # __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    password_hash = db.Column(db.String(128))


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    def __repr__(self):
        return '<User %r>' % self.name


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

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
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(264), unique=False)
    image = db.Column(db.String(264), unique=False)
    tags = db.relationship('Tag', secondary=artist_to_tag,
                           backref=db.backref('artist', lazy='dynamic'))
    users = db.relationship('User', backref='artist', lazy='dynamic')

    def isInitialized(self):
        return self.description is not None

    def __repr__(self):
        return '<Artist %r>' % self.name

# initiates Track table
class Track(db.Model):
    # __tablename__ = 'track'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    url = db.Column(db.String(264), unique=False)
    tags = db.relationship('Tag', secondary=track_to_tag,
                           backref=db.backref('track', lazy='dynamic'))

    def __repr__(self):
        return '<Track %r>' % self.name

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    address = db.Column(db.String(264), unique=False, index=True)
    city = db.Column(db.String(64), unique=False, index=True)

    def __repr__(self):
        return '<Event %r>' % self.name


class ArtistForm(Form):
    #artistName = StringField('Artist Name*', validators=[Required()])
    # artistTags = SelectMultipleField(u'Tag', coerce=int, validators=[validators.NumberRange(message="Not a Valid Option")])
    artistTags = StringField('Artist Tags (Comma Seperated)')
    artistDescription = TextAreaField('Description')
    artistImage = FileField('Upload a Profile Image',validators=[FileAllowed(['jpg', 'png', 'gif'],
                                                                 "Supported file extensions: .jpg .png .gif")])
    # photo = FileField('Your photo')
    submit = SubmitField('Submit')

    def reset(self):
        self.artistDescription.data = self.artistImage.data = ""

class TrackForm(Form):
    #artistName = StringField('Artist Name*', validators=[Required()])
    trackName = StringField('Track Name*', validators=[Required()])
    trackTags = StringField('Track Tags')
    trackURL = FileField('Upload your track', validators=[FileRequired(), FileAllowed(['mp3', 'wav', 'flac'],
                                                          "Supported file extensions: .mp3 .wav .flac")])
    submit = SubmitField('Submit')

    def reset(self):
        self.trackName.data = self.trackURL.data = ""

class EventForm(Form):
     eventName = StringField('Event Name*', validators=[Required()])
     eventAddress = StringField('Event Address*', validators=[Required()])
     eventCity = StringField('Event City*', validators=[Required()])

     submit = SubmitField('Submit')
     def reset(self):
        self.eventName.data = self.eventAddress.data = self.eventCity.data= ""

class RegistrationForm(Form):
    firstName = StringField('First Name*', validators=[Required()])
    lastName = StringField('Last Name*', validators=[Required()])
    artistName = StringField('Artist/Band Name*', validators=[Required()])
    email = StringField('Email*', validators=[Required()]) #include email validation
    password = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

    submit = SubmitField('Submit')

    def reset(self):
        self.artistName.data = self.email.data = self.password.data = self.confirm.data = ""


class LoginForm(Form):
    email = StringField('Email*', validators=[Required()]) #include email validation
    password = PasswordField('Password', [validators.Required()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Submit')

    def reset(self):
        self.email.data = self.password.data = ""

@app.errorhandler(401)
def page_not_found(e):
    form = LoginForm()
    flash("Sorry, you have to be logged in to do that")
    return render_template('login.html',form=form), 401

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    print(e)
    return render_template('500.html', error=e), 500



@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated and not current_user.is_anonymous:
        #return redirect("/artists/"+current_user.artist.name)
        client = app.test_client()
        response = client.get('/artists/'+current_user.artist.name, headers=list(request.headers))
        return response
    else:
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.verify_password(form.password.data):
                login_user(user, form.remember_me.data)
                #return redirect(request.args.get('next') or url_for('index'))
                return render_template('index.html', form=form)
            flash('Invalid username or password.')
        return render_template('index.html', form=form)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    #return render_template('index.html')
    return redirect('/')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    registrationForm=RegistrationForm()
    if registrationForm.validate_on_submit():
        artistName = registrationForm.artistName.data
        email = registrationForm.email.data

        artistCheck = Artist.query.filter_by(name=artistName).first()
        ##todo, check that email is unique
        emailCheck = User.query.filter_by(email=email).first()
        if artistCheck is None and emailCheck is None: #this is checking that the artist doesn't yet exist, if it does it will give them an error
            artist = Artist(name=artistName)
            db.session.add(artist)
            db.session.commit()
            user = User(
                first_name=registrationForm.firstName.data,
                last_name=registrationForm.lastName.data,
                email=registrationForm.email.data,
                password = registrationForm.password.data,
                #Random TODO add attribute to artist to say if initialized, won't be public until true
                artist_id = artist.id
            )
            db.session.add(user)
            db.session.commit()
            flash("User successfully added")
            login_user(user)
            return redirect('artists/add/')
        else:
            if emailCheck is not None:
                message = "Error: "+email+ " Has Already Been Registered.  <a href='/login/" + artistName + "'>Login?</a>"
                flash(message,"error") #TODO
                registrationForm.email.data = ""
            if artistCheck is not None:
                message = "Error: "+artistName + " Already Exists.  <a href='/artists/" + artistName + "'>View Page</a>"
                flash(message,"error") #TODO
                registrationForm.artistName.data = ""
    return render_template('register.html', registrationForm=registrationForm)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash("Successfully Logged In")
            #return render_template('index.html', form=form)
            return redirect('/artists/'+current_user.artist.name)
            #return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)

@app.route('/tags/')
def tags():
    return render_template('tags.html', tagNames=[tag.name for tag in
                                                  Tag.query.all()])


@app.route('/artists/')
def artists():
    artistNamesImages = zip([artist.name for artist in
                             Artist.query.all()], [artist.image for artist in
                                                   Artist.query.all()])

    return render_template('artists.html', artistNamesImages=sorted(artistNamesImages, key=lambda tup: tup[0]))


@app.route('/artists/<artistName>')
def getArtist(artistName):
    artistObj = Artist.query.join(Tag.artist).filter_by(name=artistName).first()
    if artistObj is None:
        artistObj = Artist.query.filter_by(name=artistName).first() #this is a workaround to fix the fact that our first method of querying will return none if no tags
    if artistObj is None or not artistObj.isInitialized():
        return render_template('artist.html', artistName="null")
    else:
        tracks = Track.query.filter_by(artist_id=artistObj.id).all()
        events = Event.query.filter_by(artist_id=artistObj.id).all()
        return render_template('artist.html', artistName=artistObj.name,
                               artistDescription=artistObj.description,
                               artistImageURL=artistObj.image, tags=artistObj.tags,
                               tracks=tracks, events = events
                               )


@app.route('/tags/<tagName>')
def getTag(tagName):
    tagObj = Tag.query.join(Artist.tags).filter_by(name=tagName).first()
    if tagObj is None:
        tagObj = Tag.query.filter_by(name=tagName).first()
        return render_template('tag.html', tagName=tagObj.name)
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
@login_required
def addArtist():
    artistForm = ArtistForm(srf_enabled=False)
    userArtist = current_user.artist
    if artistForm.validate_on_submit():
        tagsText = artistForm.artistTags.data
        print(tagsText,type(tagsText))
        if isinstance(tagsText, basestring):
            formTags = tagsText.split(", ")

        userArtist.description = artistForm.artistDescription.data
        if artistForm.artistImage.has_file():
            filename = secure_filename(str(uuid.uuid1())+artistForm.artistImage.data.filename)
            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            artistForm.artistImage.data.save(os.path.join(app.config['IMG_FOLDER'],filename))
            userArtist.image = filename
        if userArtist.image is None:
            userArtist.image = "no_profile.png"
        for tagName in formTags:
            tag = Tag.query.filter_by(name=tagName).first()
            if tag is None:
                tag = Tag(name=tagName)
            if tag not in userArtist.tags:
                userArtist.tags.append(tag)

        db.session.commit()

        message = "Profile Successfully Modified"
        flash(message, "success")
        return redirect('/artists/'+current_user.artist.name)
    else:
        print("didn't validate")
        if userArtist is not None:
            tags = []
            for tag in userArtist.tags:
                tags.append(tag.name)
            tags = ", ".join(tags)
            artistForm.artistTags.data = tags
            artistForm.artistDescription.data = userArtist.description
    return render_template('form.html', artistForm=artistForm)


@app.route('/getTags/', methods=['GET'])
def getTags():
    tags = [tag.name for tag in Tag.query.all()]
    return Response(json.dumps(tags), mimetype='application/json')


@app.route('/getArtists/', methods=['GET'])
def getArtists():
    artists = [artist.name for artist in Artist.query.all()]
    return Response(json.dumps(artists), mimetype='application/json')


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

@app.route('/events/add/', methods=['GET', 'POST'])
@login_required
def addEvent():
    userArtist = current_user.artist
    eventForm = EventForm(csrf_enabled=False)
    if eventForm.validate_on_submit():
        event = Event(
            name=eventForm.eventName.data,
            artist_id=userArtist.id,
            address = eventForm.eventAddress.data,
            city = eventForm.eventCity.data
        )
        db.session.add(event)
        db.session.commit
        message = event.name + " Successfully Added to " + userArtist.name + ".  <a href='/artists/" + userArtist.name + "'>View Page</a>"
        flash(message, "success")
    return render_template('addEvent.html', eventForm=eventForm);

@app.route('/tracks/add/', methods=['GET', 'POST'])
@login_required
def addTrack():
    trackForm = TrackForm(csrf_enabled=False)
    artistName = current_user.artist.name
    trackTags = trackForm.trackTags.data
    if isinstance(trackTags, basestring):
        trackTags = trackTags.split(", ")
    if trackForm.validate_on_submit():
        userArtist = current_user.artist
        if userArtist is None:
            print("This shouldn't happen, should only have access if logged in")
            message = "Error: " + userArtist.name + " Does Not Exists."
            flash(message, "error")
            return render_template('form.html', trackForm=trackForm)
        else:
            filename = secure_filename(str(uuid.uuid1())+trackForm.trackURL.data.filename)
            track = Track(
                name=trackForm.trackName.data,
                artist_id=userArtist.id,
                url=filename
            )
            trackForm.trackURL.data.save(os.path.join(app.config['TRACK_FOLDER'],filename))

        for tagName in trackTags:
            tag = Tag.query.filter_by(name=tagName).first()
            if tag is None:
                tag = Tag(name=tagName)
            track.tags.append(tag)
            db.session.add(track)
            db.session.commit()

        message = track.name + " Successfully Added to " + userArtist.name + ".  <a href='/artists/" + userArtist.name + "'>View Page</a>"
        flash(message, "success")
    return render_template('addTrack.html', trackForm=trackForm)


if __name__ == '__main__':
    manager.run()
