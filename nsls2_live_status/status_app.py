from flask import (Flask, request, render_template, redirect, url_for,
                   send_from_directory)
from werkzeug import secure_filename
import os
import pdb
from nsls2_build_tools import log_parser

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'auto-build-logs')
DEV_LOG = os.path.join(UPLOAD_FOLDER, 'dev')
TAG_LOG = os.path.join(UPLOAD_FOLDER, 'tag')
for f in [UPLOAD_FOLDER, DEV_LOG, TAG_LOG]:
    if not os.path.exists(f):
        os.makedirs(f)
ALLOWED_EXTENSIONS = set(['log'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEV_LOG'] = DEV_LOG
app.config['TAG_LOG'] = TAG_LOG

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload/dev/', methods=['POST'])
def upload_dev_log():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['DEV_LOG'], filename))
    return ''

@app.route('/upload/tag/', methods=['POST'])
def upload_tag_log():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['TAG_LOG'], filename))
    return ''

@app.route('/uploads/<name>/<filename>')
def uploaded_file(name, filename):
    return send_from_directory(app.config['%s_LOG' % name.upper()] , filename)

@app.route('/')
def status():
    dev_logs = sorted(os.listdir(app.config['DEV_LOG']))
    tag_logs = sorted(os.listdir(app.config['TAG_LOG']))

    dev_log = os.path.join(app.config['DEV_LOG'], dev_logs[-1])
    parsed_dev_log = log_parser.simple_parse(dev_log)
    dev_table = log_parser.summarize(parsed_dev_log)

    tag_log = os.path.join(app.config['TAG_LOG'], tag_logs[-1])
    parsed_tag_log = log_parser.simple_parse(tag_log)
    tag_table = log_parser.summarize(parsed_tag_log)


    template_data = {
        'dev_logs': dev_logs,
        'tag_logs': tag_logs,
        'tables': [(dev_logs[-1], dev_table),
                   (tag_logs[-1], tag_table)]
    }
    return render_template('status.html', **template_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
