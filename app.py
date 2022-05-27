#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from operator import concat
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  venues = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()
  time = dt.datetime.now()
  data = []
  cityState=''

  for venue in venues:
    num_upcoming_shows = venue.shows.filter(Show.start_time > time).count()
    if cityState == venue.city+venue.state:
      data[-1]['venues'].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": num_upcoming_shows
      })
    else:
      cityState = venue.city+venue.state
      data.append({
        "city": venue.city,
        "state": venue.state,
        "venues": [{
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows":num_upcoming_shows
          }]
      })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  searchTerm = request.form.get('search_term')
  venues = Venue.query.filter(Venue.name.ilike('%'+searchTerm+'%'))
  response={
    "count": venues.count(),
    "data": []
  }
  for venue in venues:
    details = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": 0
    }
    response['data'].append(details)
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  if venue:
    today = dt.datetime.now()
    shows = Show.query.filter(Show.venue_id==venue_id).order_by('venue_id')
    data={
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "seeking_talent": venue.seeking_talent,
      "seeking_description":venue.seeking_description,
      "website":venue.website_link,
      "facebook_link":venue.facebook_link,
      "image_link":venue.image_link,
      "past_shows": [],
      "upcoming_shows": [],
      "past_shows_count": 0,
      "upcoming_shows_count": 0,
    }

    for show in shows:
      details = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%A %Y-%B-%-dT%H:%m:%S.000Z')
      }
      if show.start_time < today:
        data['past_shows'].append(details)
        data['past_shows_count'] += 1
      else:
        data['upcoming_shows'].append(details)
        data['upcoming_shows_count'] +=1
      
    return render_template('pages/show_venue.html', venue=data)
  else:
    return render_template('errors/404.html')

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  form = VenueForm(request.form) 
  try:
    venue = Venue()
    form.populate_obj(venue)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    db.session.close()
    flash('Venue was successfully Deleted!')
    return render_template('pages/home.html')
  except:
    db.session.rollback()
    db.session.close()
    flash('An error occurred. Venue could not be deleted.')
    return render_template('pages/home.html')   

  return None

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: populate form with values from venue with ID <venue_id>

  venue = Venue.query.get(venue_id)
  if venue:
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)
  

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  venue = Venue.query.get(venue_id)
  if venue:
    try:
      
      form = VenueForm(formdata=request.form, obj=venue) 
      form.populate_obj(venue)
      flash('Venue ' + request.form['name'] + ' was successfully edited!')
      db.session.commit()
      return redirect(url_for('show_venue', venue_id=venue_id))
    except:
      db.session.rollback()
      flash('Venue ' + request.form['name'] + ' could not be edited!')
      return render_template('pages/venues.html')
    finally:
      db.session.close()
  
  return render_template('errors/404.html')

    

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  searchTerm = request.form.get('search_term')
  artists = Artist.query.filter(Artist.name.ilike('%'+searchTerm+'%'))
  response={
    "count": artists.count(),
    "data": []
  }
  for artist in artists:
    details = {
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": 0
    }
    response['data'].append(details)
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)
  if artist:
    today = dt.datetime.now()
    shows = Show.query.filter(Show.artist_id==artist_id).order_by('venue_id')
    data={
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "seeking_venue": artist.seeking_venue,
      "seeking_description":artist.seeking_description,
      "website":artist.website_link,
      "facebook_link":artist.facebook_link,
      "image_link":artist.image_link,
      "past_shows": [],
      "upcoming_shows": [],
      "past_shows_count": 0,
      "upcoming_shows_count": 0,
    }
    for show in shows:
      details = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%A %Y-%B-%-dT%H:%m:%S.000Z')
      }
      if show.start_time < today:
        data['past_shows'].append(details)
        data['past_shows_count'] += 1
      else:
        data['upcoming_shows'].append(details)
        data['upcoming_shows_count'] +=1
    return render_template('pages/show_artist.html', artist=data)
  
  return render_template('errors/404.html')


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # TODO: populate form with fields from artist with ID <artist_id>
  artist = Artist.query.get(artist_id)
  if artist:
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)
  return render_template('errors/404.html')

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  artist = Artist.query.get(artist_id)
  if artist:
    try:
      form = ArtistForm(formdata=request.form, obj=artist) 
      form.populate_obj(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully edited!')
      return redirect(url_for('show_artist', artist_id=artist_id))
    except:
      db.session.rollback()
      flash('Artist ' + request.form['name'] + ' could not be edited!')
      return render_template('pages/artists.html')
    finally:
      db.session.close()  
  return render_template('errors/404.html')

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form) 
  try:
    artist = Artist()
    form.populate_obj(artist)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name']+ ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  shows = Show.query.order_by('venue_id', 'start_time').all()
  for show in shows:
    details = {
    "venue_id": show.venue_id,
    "venue_name": show.venue.name,
    "artist_id": show.artist_id,
    "artist_name": show.artist.name,
    "artist_image_link": show.artist.image_link,
    "start_time": show.start_time.strftime('%A %Y-%B-%-dT%H:%m:%S.000Z')
    }
    data.append(details)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)
  try:
    show = Show()
    form.populate_obj(show)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
