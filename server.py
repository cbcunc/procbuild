from flask import Flask, render_template, url_for, send_file, jsonify
import json
import os
from os.path import join as joinp
from glob import glob
from futil import age as file_age

from builder import build as build_paper, cache

app = Flask(__name__)

pr_info = json.load(open('data/pr_info.json'))

papers = [(str(n), pr) for n, pr in enumerate(pr_info)]


if not app.debug:
    import logging
    from logging import FileHandler
    file_handler = FileHandler("/tmp/flask.log")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)


def status_file(nr):
    return joinp(cache(), str(nr) + '.status')

def status_from_cache(nr):
    if nr == '*':
        status_files = glob(status_file(nr))
    else:
        status_files = [status_file(nr)]

    data = {}

    for fn in status_files:
        nr = fn.split('/')[-1].split('.')[0]

        if not os.path.exists(fn):
            data[nr] = {'success': False}
        else:
            with open(fn, 'r') as f:
                data[nr] = json.load(f)

    # Unpack status if only one record requested
    if nr != '*':
        return data[nr]
    else:
        return data

@app.route('/')
def index():
    return render_template('index.html', papers=papers,
                           build_url=url_for('build', nr=''),
                           download_url=url_for('download', nr=''))


@app.route('/build/<nr>')
def build(nr):
    pr = pr_info[int(nr)]

    age = file_age(status_file(nr))
    if age is None or age > 5:
        status = build_paper(user=pr['user'], branch=pr['branch'], target=nr)

        with open(status_file(nr), 'w') as f:
            json.dump(status, f)

    return jsonify({'status': 'OK'})


@app.route('/status')
@app.route('/status/<nr>')
def status(nr=None):
    data = []

    if nr is None:
        nr = '*'

    return jsonify(status_from_cache(nr))


@app.route('/download/<nr>')
def download(nr):
    status = status_from_cache(nr)

    if not status['success']:
        return "Paper has not been successfully rendered yet."

    return send_file(status['pdf_path'])


if __name__ == "__main__":
    app.run(debug=True)