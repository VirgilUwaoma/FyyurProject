# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
from operator import concat, le
import sys
import logging
from logging import Formatter, FileHandler
import datetime as dt
import dateutil.parser
import babel
from flask import (
  Flask,
  render_template,
  request, Response,
  flash, redirect,
  url_for
  )
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

from models import *

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    '''renders app home page'''
    venues = Venue.query.order_by(desc(Venue.created_date)).limit(10).all()
    artists = Artist.query.order_by(desc(Artist.created_date)).limit(10).all()
    return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    '''renders venue by city and state'''
    venues = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()
    time = dt.datetime.now()
    data = []
    city_state = ''

    for venue in venues:
        num_upcoming_shows = venue.shows.filter(Show.start_time > time).count()
        if city_state == venue.city+venue.state:
            data[-1]['venues'].append({
              "id": venue.id,
              "name": venue.name,
              "num_upcoming_shows": num_upcoming_shows
            })
        else:
            city_state = venue.city + venue.state
            data.append({
              "city": venue.city,
              "state": venue.state,
              "venues": [{
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": num_upcoming_shows
                }]
            })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    '''search for venues using partial string matching'''
    search_term = request.form.get('search_term')
    venues = Venue.query.filter(Venue.name.ilike('%'+search_term+'%'))
    response = {
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
    return render_template('pages/search_venues.html', results=response, 
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    '''renders venue with the venue id'''
    venue = Venue.query.get(venue_id)
    if venue:
        today = dt.datetime.now()
        past_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id == venue_id).filter(Show.start_time < today).all()
        past_shows = []
        upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id == venue_id).filter(Show.start_time > today).all()
        upcoming_shows = []

        for show in past_shows_query:
            past_shows.append({
              "artist_id": show.artist_id,
              "artist_name": show.artist.name,
              "artist_image_link": show.artist.image_link,
              "start_time": show.start_time.strftime('%A %Y-%B-%-dT%H:%m:%S')
            })

        for show in upcoming_shows_query:
            upcoming_shows.append({
              "artist_id": show.artist_id,
              "artist_name": show.artist.name,
              "artist_image_link": show.artist.image_link,
              "start_time": show.start_time.strftime("%A %Y-%B-%-dT%H:%m:%S")    
            })

        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "website": venue.website_link,
            "facebook_link": venue.facebook_link,
            "image_link": venue.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows_query,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows)
        }
        return render_template('pages/show_venue.html', venue=data)
    return render_template('errors/404.html')

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    '''renders the venue create form'''
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    '''creates venue and adds to the db'''
    form = VenueForm(request.form)
    try:
        venue = Venue()
        form.populate_obj(venue)
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as ex:
        db.session.rollback()
        print(sys.exc_info(ex))
        flash('An error occurred. Venue ' + request.form['name'] +
              ' could not be listed.')
    finally:
        db.session.close()
    return redirect(url_for('index'))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    '''delete a venue from the db using the id'''
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        db.session.close()
        flash('Venue was successfully Deleted!')
        return render_template('pages/home.html')
    except Exception as ex:
        db.session.rollback()
        db.session.close()
        print(sys.exc_info(ex))
        flash('An error occurred. Venue could not be deleted.')
        return render_template('pages/home.html')
    return None


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    '''retrieve venue data for the edit form'''
    venue = Venue.query.get(venue_id)
    if venue:
        form = VenueForm(obj=venue)
        return render_template('forms/edit_venue.html', form=form, venue=venue)
    return redirect(url_for('index'))


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    '''updates the venue data to the db'''
    venue = Venue.query.get(venue_id)
    if venue:
        try:
            form = VenueForm(formdata=request.form, obj=venue)
            form.populate_obj(venue)
            flash('Venue ' + request.form['name'] +
                  ' was successfully edited!')
            db.session.commit()
            return redirect(url_for('show_venue', venue_id=venue_id))
        except Exception as ex:
            db.session.rollback()
            print(sys.exc_info(ex))
            flash('Venue ' + request.form['name'] + ' could not be edited!')
            return render_template('pages/venues.html')
        finally:
            db.session.close()
    return render_template('errors/404.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    '''renders list of artists'''
    data = Artist.query.with_entities(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    '''search for artist using partial string matching'''
    search_term = request.form.get('search_term')
    artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%'))
    response = {
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
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    '''renders artist page using the artist id'''
    artist = Artist.query.get(artist_id)
    if artist:
        today = dt.datetime.now()
        past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time<today).all()
        past_shows = []
        upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>today).all()
        upcoming_shows = []

        for show in past_shows_query:
            past_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%A %Y-%B-%-dT%H:%m:%S.000Z')
            })

        for show in upcoming_shows_query:
            upcoming_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%A %Y-%B-%-dT%H:%m:%S.000Z')    
            })

        data = {
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
          "past_shows": past_shows,
          "upcoming_shows": upcoming_shows,
          "past_shows_count": len(past_shows),
          "upcoming_shows_count": len(upcoming_shows),
        }
        return render_template('pages/show_artist.html', artist=data)    
    return render_template('errors/404.html')


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    '''retrieve artistt data for the edit form'''
    artist = Artist.query.get(artist_id)
    if artist:
        form = ArtistForm(obj=artist)
        return render_template('forms/edit_artist.html',
                               form=form, artist=artist)
    return render_template('errors/404.html')


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    '''updates the artist data to the db'''
    artist = Artist.query.get(artist_id)
    if artist:
        try:
            form = ArtistForm(formdata=request.form, obj=artist)
            form.populate_obj(artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] +
                  ' was successfully edited!')
            return redirect(url_for('show_artist', artist_id=artist_id))
        except Exception as ex:
            db.session.rollback()
            print(sys.exc_info(ex))
            flash('Artist ' + request.form['name'] + ' could not be edited!')
            return render_template('pages/artists.html')
        finally:
            db.session.close() 
    return render_template('errors/404.html')

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    '''renders artist create form'''
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    '''creates new artirst object and adds it to the db'''
    form = ArtistForm(request.form)
    try:
        artist = Artist()
        form.populate_obj(artist)
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as ex:
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] +
              ' could not be listed.')
        print(sys.exc_info(ex))
    finally:
        db.session.close()
    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    '''displays list of shows at /shows'''
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
    '''renders show create form. do not touch.'''
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    '''creates new shows in the db, upon submitting new show listing form'''
    form = ShowForm(request.form)
    try:
        show = Show()
        form.populate_obj(show)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except Exception as ex:
        db.session.rollback()
        print(sys.exc_info(ex))
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    '''error handler'''
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    '''error handler'''
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    '''error handler'''
    return render_template('errors/403.html'), 403


@app.errorhandler(405)
def invalid_method_error(error):
    '''error handler'''
    return render_template('errors/405.html'), 405


@app.errorhandler(409)
def duplicate_resource_error(error):
    '''error handler'''
    return render_template('errors/409.html'), 409


@app.errorhandler(422)
def not_processable_error(error):
    '''error handler'''
    return render_template('errors/422.html'), 422


@app.errorhandler(401)
def unauthorized_error(error):
    '''error handler'''
    return render_template('errors/401.html'), 401


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s:%(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()
