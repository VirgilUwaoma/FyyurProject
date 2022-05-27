from email.policy import default
from app import db
import datetime as dt


class Venue(db.Model):
    '''defines the venue model'''
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120))
    genres = db.Column(db.PickleType, nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False,
                             default=dt.datetime.now())
    shows = db.relationship('Show', backref='venue',
                            lazy="dynamic", cascade="all, delete")


class Artist(db.Model):
    '''defines the artist model'''
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.PickleType, nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False,
                             default=dt.datetime.now())
    shows = db.relationship('Show', backref='artist',
                            lazy="dynamic", cascade="all, delete")


class Show(db.Model):
    '''defines the show model'''
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer,
                          db.ForeignKey('artists.id', ondelete="CASCADE"),
                          nullable=False)
    venue_id = db.Column(db.Integer,
                         db.ForeignKey('venues.id', ondelete="CASCADE"),
                         nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
