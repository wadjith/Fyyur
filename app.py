#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from unittest import result
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
from models import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

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
  venueList = Venue.query.all()
  print(f'Number of venue = {len(venueList)}')
  data = []
  for venue in venueList:
    dataObj = {'city': '', 'state': '', 'venues': []}
    venueObj = {'id': 0, 'name': '', 'num_upcoming_shows': 0}
    # construct the data result
    if len(data) == 0:
      # first element of data
      venueObj["id"] = venue.id
      venueObj["name"] = venue.name
      venueObj["num_upcoming_shows"] = get_num_upcoming_shows_for_venue(venue.id)

      dataObj["city"] = venue.city
      dataObj["state"] = venue.state
      dataObj["venues"].append(venueObj)
      data.append(dataObj)

    else:
    # Loop data in order to save the venue
      for d in data:
        if d["city"] == venue.city:
          # City is already in data. Append to venues list
          venueObj["id"] = venue.id
          venueObj["name"] = venue.name
          venueObj["num_upcoming_shows"] = get_num_upcoming_shows_for_venue(venue.id)
          d['venues'].append(venueObj)
          break
        else:
          # append a new element in data
          venueObj["id"] = venue.id
          venueObj["name"] = venue.name
          venueObj["num_upcoming_shows"] = get_num_upcoming_shows_for_venue(venue.id)

          dataObj["city"] = venue.city
          dataObj["state"] = venue.state
          dataObj["venues"].append(venueObj)
          data.append(dataObj)
          break

  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  response = {"count": 0, "data": []}
  search_term = "%{}%".format(request.form.get('search_term', ''))
  venues = Venue.query.filter(Venue.name.ilike(search_term)).all()
  if len(venues) > 0:
    response["count"] = len(venues)
    for venue in venues:
      obj = {}
      obj["id"] = venue.id
      obj["name"] = venue.name
      obj["num_upcoming_shows"] = get_num_upcoming_shows_for_venue(venue.id)
      response["data"].append(obj)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = {}
  venue = Venue.query.get(venue_id)
  if venue:
    data["id"] = venue.id
    data["name"] = venue.name
    data["genres"] = []
    data["genres"] = venue.genres.split(':')
    data["address"] = venue.address
    data["city"] = venue.city
    data["state"] = venue.state
    data["phone"] = venue.phone
    data["website"] = venue.website_link
    data["facebook_link"] = venue.facebook_link,
    data["seeking_talent"] = venue.seeking_talent
    data["seeking_description"] = venue.seeking_description,
    data["image_link"] = venue.image_link
    data["past_shows"] = []
    data["upcoming_shows"] = []
    # Get the shows
    past_shows = Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
    upcoming_shows = Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
    data["past_shows_count"] = len(past_shows)
    data["upcoming_shows_count"] = len(upcoming_shows)

    for show in past_shows: # Fill past_shows list
      showDict = {}
      showDict["artist_id"] = show.artist_id
      showDict["artist_name"] = show.artist.name
      showDict["artist_image_link"] = show.artist.image_link
      showDict["start_time"] = show.start_time.isoformat()
      data["past_shows"].append(showDict)

    for show in upcoming_shows: # Fill upcoming_shows
      showDict = {}
      showDict["artist_id"] = show.artist_id
      showDict["artist_name"] = show.artist.name
      showDict["artist_image_link"] = show.artist.image_link
      showDict["start_time"] = show.start_time.isoformat()
      data["upcoming_shows"].append(showDict)

  else:
    flash(f'Venue with id = {venue_id} not found', 'error')
    abort(404)
  
  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm(request.form)
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  obj = {}
  try:
    # get data from form in request and set the model
    venue = Venue(name=form.name.data,
                  city=form.city.data,
                  state=form.state.data,
                  address=form.address.data,
                  phone=form.phone.data,
                  image_link=form.image_link.data,
                  facebook_link=form.facebook_link.data,
                  website_link=form.website_link.data,
                  seeking_talent=form.seeking_talent.data,
                  seeking_description=form.seeking_description.data
                  )
    # join string in the list "form.genres.data" with :
    venue.genres = ':'.join(form.genres.data)
    db.session.add(venue)
    db.session.commit()
    obj['name'] = venue.name
    flash('Venue ' + obj['name'] + ' is successfully saved!')
  except Exception as ex:
    db.session.rollback()
    print(ex)
    obj['name'] = form.name.data
    flash('An error occured. Venue ' + obj['name'] + ' is not saved!', "error")
    abort(500)
  finally:
    db.session.close()
  
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if venue:
    try:
      db.session.delete(venue)
      db.session.commit()
    except Exception as e:
      db.session.rollback()
      flash('An error occured. Venue ' + venue.name + ' is not deleted!', "error")
      abort(500)
  return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  artists = Artist.query.all()
  for artist in artists:
    obj={}
    obj["id"] = artist.id
    obj["name"] = artist.name
    data.append(obj)

  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  response = {"count": 0, "data": []}
  search_term = "%{}%".format(request.form.get('search_term', ''))
  artists = Artist.query.filter(Artist.name.ilike(search_term)).all()
  if len(artists) > 0:
    response["count"] = len(artists)
    for artist in artists:
      obj = {}
      obj["id"] = artist.id
      obj["name"] = artist.name
      obj["num_upcoming_shows"] = get_num_upcoming_shows_for_artist(artist.id)
      response["data"].append(obj)

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = {}
  artist = Artist.query.get(artist_id)
  if artist:
    data["id"] = artist.id
    data["name"] = artist.name
    data["genres"] = []
    data["genres"] = artist.genres.split(':')
    data["city"] = artist.city
    data["state"] = artist.state
    data["phone"] = artist.phone
    data["website"] = artist.website_link
    data["facebook_link"] = artist.facebook_link,
    data["seeking_venue"] = artist.seeking_venue
    data["seeking_description"] = artist.seeking_description,
    data["image_link"] = artist.image_link
    data["past_shows"] = []
    data["upcoming_shows"] = []

    # Get the shows
    past_shows = Show.query.join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
    upcoming_shows = Show.query.join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
    data["past_shows_count"] = len(past_shows)
    data["upcoming_shows_count"] = len(upcoming_shows)

    for show in past_shows: # Fill past_shows list
      showDict = {}
      showDict["venue_id"] = show.venue_id
      showDict["venue_name"] = show.venue.name
      showDict["venue_image_link"] = show.venue.image_link
      showDict["start_time"] = show.start_time.isoformat()
      data["past_shows"].append(showDict)

    for show in upcoming_shows: # Fill upcoming_shows
      showDict = {}
      showDict["venue_id"] = show.venue_id
      showDict["venue_name"] = show.venue.name
      showDict["venue_image_link"] = show.venue.image_link
      showDict["start_time"] = show.start_time.isoformat()
      data["upcoming_shows"].append(showDict)
  
  else:
    flash(f'Artist with id = {artist_id} not found', 'error')
    abort(404)
  
  return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  if artist:
    artistDict = {}
    artistDict["name"] = artist.name
    artistDict["genres"] = artist.genres.split(':')
    artistDict["city"] = artist.city
    artistDict["state"] = artist.state
    artistDict["phone"] = artist.phone
    artistDict["website_link"] = artist.website_link
    artistDict["facebook_link"] = artist.facebook_link
    artistDict["seeking_venue"] = artist.seeking_venue
    artistDict["seeking_description"] = artist.seeking_description
    artistDict["image_link"] = artist.image_link
    form = ArtistForm(data=artistDict) # form = ArtistForm(obj=artist)
    
  else:
    flash(f'Artist with id = {artist_id} not found', 'error')
    abort(404)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  if artist:
    form = ArtistForm(request.form)
    try:
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = ':'.join(form.genres.data)
      artist.image_link = form.image_link.data
      artist.website_link = form.website_link.data
      artist.facebook_link = form.facebook_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data
      db.session.commit()
      flash(f'Artist with id = {artist_id} successfully updated!')

    except Exception as e:
      db.session.rollback()
      print(e)
      flash(f'An error occured while editing artist with id = {artist_id}', 'error')
      abort(500)

    finally:
      db.session.close()

  else:
    flash(f'Artist with id = {artist_id} not found', 'error')
    abort(404)

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  if venue:
    venueDict = {}
    venueDict["name"] = venue.name
    venueDict["genres"] = venue.genres.split(':')
    venueDict["address"] = venue.address
    venueDict["city"] = venue.city
    venueDict["state"] = venue.state
    venueDict["phone"] = venue.phone
    venueDict["website_link"] = venue.website_link
    venueDict["facebook_link"] = venue.facebook_link
    venueDict["seeking_talent"] = venue.seeking_talent
    venueDict["seeking_description"] = venue.seeking_description
    venueDict["image_link"] = venue.image_link
    form = VenueForm(data=venueDict)
  else:
    flash(f'Venue with id = {venue_id} not found', 'error')
    abort(404)
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  if venue:
    form = VenueForm(request.form)
    try:
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = ':'.join(form.genres.data)
      venue.image_link = form.image_link.data
      venue.website_link = form.website_link.data
      venue.facebook_link = form.facebook_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      db.session.commit()
      
    except Exception as e:
      db.session.rollback()
      print(e)
      flash(f'An error occured while editing venue with id = {venue_id}', 'error')
      abort(500)

    finally:
      db.session.close()

  else:
    flash(f'Venue with id = {venue_id} not found', 'error')
    abort(404)
  
  flash(f'Venue with id = {venue_id} successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  body = {}
  try:
    # get data from form in request and set the model
    artist = Artist(name=form.name.data,
                  city=form.city.data,
                  state=form.state.data,
                  phone=form.phone.data,
                  image_link=form.image_link.data,
                  facebook_link=form.facebook_link.data,
                  website_link=form.website_link.data,
                  seeking_venue=form.seeking_venue.data,
                  seeking_description=form.seeking_description.data
                  )
    # join string in the list "form.genres.data" with :
    artist.genres = ':'.join(form.genres.data)
    db.session.add(artist)
    db.session.commit()
    body['name'] = artist.name
    flash('Artist ' + body['name'] + ' is successfully saved!')

  except Exception as ex:
    db.session.rollback()
    print(ex)
    body['name'] = form.name.data
    flash('An error occured. Artist ' + body['name'] + ' is not saved!', "error")
    abort(500)
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  shows = Show.query.join(Artist).join(Venue).all()
  for show in shows:
    obj = {}
    #venue = show.venue
    #artist = show.artist
    obj["venue_id"] = show.venue_id
    obj["venue_name"] = show.venue.name #venue.name
    obj["artist_id"] = show.artist_id
    obj["artist_name"] = show.artist.name #artist.name
    obj["artist_image_link"] = show.artist.image_link #artist.image_link
    obj["start_time"] = show.start_time.isoformat()
    data.append(obj)
  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  try:
    # get data from form in request and set the model
    show = Show(artist_id=form.artist_id.data, venue_id=form.venue_id.data, start_time=form.start_time.data)
    db.session.add(show)
    db.session.commit()
    flash('Show is successfully created!')

  except Exception as ex:
    db.session.rollback()
    print(ex)
    flash('An error occured. Show is not saved!', "error")
    abort(500)
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
# Private functions
#----------------------------------------------------------------------------#
def get_num_upcoming_shows_for_venue(venue_id):
  query = Show.query.join(Venue).filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now())
  return query.count()

def get_num_upcoming_shows_for_artist(artist_id):
  query = Show.query.join(Artist).filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now())
  return query.count()
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
