#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import phonenumbers
from phonenumbers.phonenumber import PhoneNumber as BasePhoneNumber
from phonenumbers.phonenumberutil import NumberParseException
from datetime import datetime
import json, os, sys
import dateutil.parser
import babel
from flask import Flask, abort, jsonify, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy_utils import PhoneNumberType
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

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(PhoneNumberType())
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)   
    seeking_description = db.Column(db.String())
    show = db.relationship('Show', backref='venue_show', lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)    
    seeking_description = db.Column(db.String())
    show = db.relationship('Show', backref='artist_show', lazy=True)

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime)

# TODO: implement any missing fields, as a database migration using Flask-Migrate
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

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
# Helpers Functions
#----------------------------------------------------------------------------#
def check_id(one_id, arr):
  for i in arr :
    if (i == one_id):
      return True  
  return False

def future_past_shows(item_id, item_type):
  date_now = datetime.now()
  upcoming_shows = []
  past_shows = []
  upcoming_shows_count = 0
  past_shows_count = 0

  if item_type == "venue":    
    venue_shows = Show.query.filter_by(venue_id=item_id).order_by('id').all()      
    for vshow in venue_shows :
      start_time_obj = datetime.strptime(vshow.start_time, '%Y-%m-%dT%H:%M:%S')
      artist = Artist.query.get(vshow.artist_id)
      if start_time_obj < date_now:
        past_shows_count += 1
        past_shows.append({
          "artist_id": vshow.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": vshow.start_time,
        })
      elif start_time_obj > date_now:
        upcoming_shows_count += 1
        upcoming_shows.append({
          "artist_id": vshow.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": vshow.start_time,
        })

  if item_type == "artist":    
    artist_shows = Show.query.filter_by(artist_id=item_id).order_by('id').all()     
    for vshow in artist_shows :
      start_time_obj = datetime.strptime(vshow.start_time, '%Y-%m-%dT%H:%M:%S')
      venue = Venue.query.get(vshow.venue_id)
      if start_time_obj < date_now:
        past_shows_count += 1
        past_shows.append({
          "venue_id": vshow.venue_id,
          "venue_name": venue.name,
          "venue_image_link": venue.image_link,
          "start_time": vshow.start_time,
        })
      elif start_time_obj > date_now:
        upcoming_shows_count += 1
        upcoming_shows.append({
          "venue_id": vshow.venue_id,
          "venue_name": venue.name,
          "venue_image_link": venue.image_link,
          "start_time": vshow.start_time,
        })
  return {
    "upcoming_shows" : upcoming_shows,
    "past_shows" : past_shows,
    "upcoming_shows_count" : upcoming_shows_count,
    "past_shows_count" : past_shows_count
  }
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
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.  

  data = []
  states_cities=[]
  
  for venue in Venue.query.all():
    states_cities.append([venue.city,venue.state])
  # Remove duplicate pairs
  for idx1, sc1 in enumerate(states_cities):
	  for idx2, sc2 in enumerate(states_cities):
		  if (idx1 != idx2 and sc1[0] == sc2[0] and sc1[1] == sc2[1]) :
			  states_cities.pop(idx2)
			  break
  
  for sc in states_cities:    
    sc_item = {
      "city": sc[0],
      "state": sc[1],
      "venues":[]
    }
    venues = Venue.query.filter_by(city=sc[0], state=sc[1]).order_by('id').all()
    for venue in venues:
      sc_item["venues"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": 0,
      })
    data.append(sc_item)
  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"  

  search_term = request.form.get('search_term', '').lower()
  count = 0
  data = []
  for venue in Venue.query.all():
    if (venue.name.lower().find(search_term) != -1):
      count += 1
      fp_shows = future_past_shows(venue.id, "venue")

      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": fp_shows['upcoming_shows_count'],
      })

  response = {
    "count": count,
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  venue = Venue.query.get(venue_id)
  venue_genres = []
  if (venue.genres != None):
    venue_genres = json.loads(venue.genres)
  
  fp_shows = future_past_shows(venue_id, "venue")
  
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue_genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": fp_shows['past_shows'],
    "upcoming_shows": fp_shows['upcoming_shows'],
    "past_shows_count": fp_shows['past_shows_count'],
    "upcoming_shows_count": fp_shows['upcoming_shows_count'],
  }

  # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=data)

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
  error = False
  try:    
    venue = Venue(
      name = request.form.get('name', ''),
      city = request.form.get('city', ''),
      state = request.form.get('state', ''),
      address = request.form.get('address', ''),
      phone = request.form.get('phone', ''),
      image_link = request.form.get('image_link', ''),
      genres = json.dumps(request.form.getlist('genres')),
      facebook_link = request.form.get('facebook_link', ''),
      website = request.form.get('website_link', ''),
      seeking_talent = request.form.get('seeking_talent','') == 'y',
      seeking_description = request.form.get('seeking_description','')
    )
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    return redirect(url_for('create_venue_form'))
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  venue_name = Venue.query.get(venue_id).name
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + venue_name + ' could not be deleted.')
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    
    flash('Venue ' + venue_name + ' was successfully deleted!')
    return render_template('pages/home.html')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  # data=[{
  #   "id": 4,
  #   "name": "Guns N Petals",
  # }, {
  #   "id": 5,
  #   "name": "Matt Quevedo",
  # }, {
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  # }]

  data = []

  for artist in Artist.query.all():
    data.append({
      "id": artist.id,
      "name": artist.name
    })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  search_term = request.form.get('search_term', '').lower()
  count = 0
  data = []
  for artist in Artist.query.all():
    if (artist.name.lower().find(search_term) != -1):
      count += 1
      fp_shows = future_past_shows(artist.id, "artist")
      data.append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": fp_shows['upcoming_shows_count'],
      })

  response = {
    "count": count,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  artist = Artist.query.get(artist_id)
  artist_genres = []
  if (artist.genres != None):
    artist_genres = json.loads(artist.genres)
  
  fp_shows = future_past_shows(artist.id, "artist")

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist_genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": fp_shows['past_shows'],
    "upcoming_shows": fp_shows['upcoming_shows'],
    "past_shows_count": fp_shows['past_shows_count'],
    "upcoming_shows_count": fp_shows['upcoming_shows_count'],
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  
  error = False
  try:
    db.session.query(Artist).filter(Artist.id == artist_id).update({
      'name' : request.form.get('name', ''),
      'city' : request.form.get('city', ''),
      'state' : request.form.get('state', ''),
      'phone' : request.form.get('phone', ''),
      'image_link' : request.form.get('image_link', ''),
      'genres' : json.dumps(request.form.getlist('genres')),
      'facebook_link' : request.form.get('facebook_link', ''),
      'website' : request.form.get('website_link', ''),
      'seeking_venue' : request.form.get('seeking_venue','') == 'y',
      'seeking_description' : request.form.get('seeking_description','')
      })    

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    return redirect(url_for('edit_artist', artist_id=artist_id))
  else:
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  try:
    db.session.query(Venue).filter(Venue.id == venue_id).update({
      'name' : request.form.get('name', ''),
      'city' : request.form.get('city', ''),
      'state' : request.form.get('state', ''),
      'phone' : request.form.get('phone', ''),
      'address' : request.form.get('address', ''),
      'image_link' : request.form.get('image_link', ''),
      'genres' : json.dumps(request.form.getlist('genres')),
      'facebook_link' : request.form.get('facebook_link', ''),
      'website' : request.form.get('website_link', ''),
      'seeking_talent' : request.form.get('seeking_talent','') == 'y',
      'seeking_description' : request.form.get('seeking_description','')
      })    

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    return redirect(url_for('edit_venue', venue_id=venue_id))
  else:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

  

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

  error = False
  try:    
    artist = Artist(
      name = request.form.get('name', ''),
      city = request.form.get('city', ''),
      state = request.form.get('state', ''),
      phone = request.form.get('phone', ''),
      image_link = request.form.get('image_link', ''),
      genres = json.dumps(request.form.getlist('genres')),
      facebook_link = request.form.get('facebook_link', ''),
      website = request.form.get('website_link', ''),
      seeking_venue = request.form.get('seeking_venue','') == 'y',
      seeking_description = request.form.get('seeking_description','')
    )
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    return redirect(url_for('create_artist_form'))
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  # return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  
  data = []
  for show in Show.query.all():
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)
    data.append({
      "venue_id" : show.venue_id,
      "venue_name" : venue.name,
      "artist_id" : show.artist_id,
      "artist_name" : artist.name,
      "artist_image_link" : artist.image_link,
      "start_time" : str(show.start_time),
    })

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

  error = False
  artists_ids = []
  venues_ids = []
  
  for artist in Artist.query.all():
    artists_ids.append(int(artist.id))
  
  for venue in Venue.query.all():
    venues_ids.append(int(venue.id))
  
  try:  
    artist_id = request.form.get('artist_id',type=int),
    venue_id = request.form.get('venue_id',type=int), 
    if (check_id(artist_id[0], artists_ids) and check_id(venue_id[0], venues_ids)):
      show = Show(
        artist_id = request.form.get('artist_id', ''),
        venue_id = request.form.get('venue_id', ''),
        start_time = request.form.get('start_time', ''),
      )
      db.session.add(show)
      db.session.commit()
    else:
      raise ValueError('One of the ids is not correct.')
      raise Exception()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show could not be listed.')
    return redirect(url_for('create_shows'))
  else:
    flash('Show was successfully listed!')
    return render_template('pages/home.html')

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
# if __name__ == '__main__':
    # app.run()

# Or specify port manually:
# '''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    app.debug=True
# '''
