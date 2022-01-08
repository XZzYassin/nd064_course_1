import sqlite3
import os
import logging
import logging.handlers

from flask import Flask, render_template, request, url_for, redirect, flash

db_connection_count = 0
# Function to increase the database connection count.
def increase_db_connection_count():
    global db_connection_count
    db_connection_count += 1

# Function to get the database connection count.
def get_db_connection_count():
    return db_connection_count

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    increase_db_connection_count()
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


def get_post_count():
    connection = get_db_connection()
    count = connection.execute(
        'SELECT count(*) as post_count FROM posts'
    ).fetchone()['post_count']
    connection.close()
    return count


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define the health check route
@app.route('/healthz', methods=('GET', 'POST'))
def healthz():
    return "result: OK - healthy"

# Define the metrics route
@app.route('/metrics', methods=('GET', 'POST'))
def metrics():
    return {
        "status": 'success',
        "code": 0,
        "data": {
            "db_connection_count": get_db_connection_count(),
            "post_count": get_post_count(),
        },
    }

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.error(f'Article #{post_id} not found!')
        return render_template('404.html'), 404
    else:
        title = post['title']
        app.logger.debug(f'Article "{title}" retrieved!')
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.debug('About us page viewed!')
    return render_template('about.html')

# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            app.logger.debug(f'Article "{title}" created!')

            return redirect(url_for('index'))

    return render_template('create.html')


# start the application on port 3111
if __name__ == "__main__":

    # stream logs to app.log file
    logging.basicConfig(
      level=logging.DEBUG,
      format="%(asctime)s - %(message)s",
    )

    app.run(host='0.0.0.0', port='3111')
