import os
from datetime import datetime
from flask import Flask, render_template, session, flash
from flask.ext.script import Manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import Required
from flask.ext.sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)


class Artist(db.Model):
    __tablename__ = 'Artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    genre_id = db.Column(db.Integer, db.ForeignKey('Genre.id'))

    def __repr__(self):
        return '<artist %r>' % self.name


class Genre(db.Model):
    __tablename__ = 'Genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    artists = db.relationship('Artist', backref='genre', lazy='dynamic')

    def __repr__(self):
        return '<genre %r>' % self.name


class NameForm(Form):
    name = StringField('Band Name: ', validators=[Required()])
    genre_id = SelectField(u'Genre', coerce=int)
    description = TextAreaField('Description: ', validators=[Required()])
    submit = SubmitField('Submit')


def edit():
        form = NameForm()
        form.genre_id.choices = [(g.id, g.name) for g in Genre.query.order_by('name')]
        return form


class GenreForm(Form):
    name = StringField('Tag Name: ', validators=[Required()])
    submit = SubmitField('Submit')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/')
def index():
    return render_template('index.html',
                           current_time=datetime.utcnow())


@app.route('/artists')
def artists():
    session["artists"] = {}
    for item in Artist.query.all():
        genre = Genre.query.get(item.genre_id)
        session['artists'][item.name]={}
        session['artists'][item.name]['genre']= genre.name
        session['artists'][item.name]['description']= item.description
    return render_template('artists.html',session=session)


@app.route('/artists/<name1>')
def artist(name1):
    for item in session["artists"]:
        if item == name1:
            return render_template('artist.html', name1=name1, session=session)
    return render_template('404.html'), 404


@app.route('/newArtist', methods=['GET', 'POST'])
def newartist():
    form = edit()
    if form.validate_on_submit():
        new_artist = Artist(name=form.name.data, description=form.description.data, genre_id=form.genre_id.data)
        db.session.add_all([new_artist])
        db.session.commit()
        flash('You have successfully submitted your band: '+form.name.data+'!')
    return render_template('newArtist.html', form=form)


@app.route('/newGenre', methods=['GET', 'POST'])
def newgenre():
    form = GenreForm()
    if form.validate_on_submit():
        genre = Genre(name=form.name.data)
        error = Genre.query.filter_by(name=form.name.data).first()
        if error is None:
            db.session.add_all([genre])
            db.session.commit()
            flash('You have successfully submitted your genre: '+form.name.data+'!')
        else:
            flash(form.name.data+' already exists!')
    return render_template('newGenre.html', form=form)



if __name__ == '__main__':
    manager.run()
