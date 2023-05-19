from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
import requests

MOVIE_API_KEY = "010707595b9029a65f6037b6a6bc384e"
SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
MOVIE_INFO_URL = "https://api.themoviedb.org/3/movie"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top10-movies-collection.db'
app.app_context().push()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer)
    description = db.Column(db.String(1000))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(2000))
    img_url = db.Column(db.String(1000))

    def __repr__(self):
        return '<Movie {self.title}>'


class RateMovie(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class FindMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


# db.create_all()
# new_movie = Movie(
    # title="Phone Booth",
    # year=2002,
    # description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    # rating=7.3,
    # ranking=10,
    # review="My favourite character was the caller.",
    # img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )

# db.session.add(new_movie)
# db.session.commit()


movies = []


@app.route("/")
def home():
    global movies
    movies = db.session.query(Movie).all()
    sorted_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(sorted_movies)):
        sorted_movies[i].ranking = len(sorted_movies) - i
    db.session.commit()
    return render_template("index.html", all_movies=movies)


# @app.route("/edit", methods=["GET", "POST"])
# def edit():
    # if request.method == "POST":
    # movie_id = request.form["id"]
    # movie_to_update = Movie.query.get(id)
    # movie_to_update.rating = request.form["rating"]
    # db.session.commit()
    # return redirect(url_for('home'))
    # movie_id = request.args.get('id')
    # movie_selected = Movie.query.get(movie_id)
    # return render_template("edit.html", movie=movie_selected)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovie()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')

    movie_to_delete = Movie.query.get(movie_id)
    print(movie_to_delete)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = FindMovie()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(SEARCH_URL, params={"api_key": MOVIE_API_KEY, "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
