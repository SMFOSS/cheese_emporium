import os
from flask import Flask
from flask import render_template, make_response, flash
from flask import request, redirect

from werkzeug import secure_filename

from utils import regenerate_index, search_pypi, package_details
import tempfile
from pipext import parse_reqs

app = Flask(__name__)
app.config.from_pyfile('base.cfg')
app.config.from_object(__name__)
app.config.from_envvar('EMPORIUM_SETTINGS')

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
FILE_ROOT = os.path.join(PROJECT_ROOT, 'files/')

@app.route('/simple', methods=['POST'])
def upload():
    f = request.files['content']
    f.save(os.path.join(app.config['FILE_ROOT'],secure_filename(f.filename)))
    regenerate_index(app.config['FILE_ROOT'],'index.html')
    response = make_response()
    response.headers['X-Swalow-Status'] = 'SUCCESS'
    return response

@app.route('/')
def index():
    return render_template('instructions.html')

@app.route('/search', methods=['GET','POST'])
def find_packages():
    #search pypi on post
    releases = None
    search_term = None
    if request.method == "POST":
        search_term = request.form['search_box']
        releases = search_pypi(search_term)
        
    return render_template('find_packages.html', releases=releases, search_term=search_term)

from urllib2 import Request, urlopen, URLError, HTTPError
@app.route('/package/<name>/<version>')
def package(name, version):
    details = package_details(name, version)
    if details:
        details = details[0]
        url = details['url']
        filename = details['filename']
        try:
            req = Request(url)
            f = urlopen(req)
            print "downloading " + url

        	# Open our local file for writing
            local_file = open(os.path.join(app.config['FILE_ROOT'],filename), "w")
            #Write to our local file
            local_file.write(f.read())
            local_file.close()
            print 'finished downloading'
        #handle errors
        except HTTPError, e:
            print "HTTP Error:",e.code , url
        except URLError, e:
            print "URL Error:",e.reason , url
        regenerate_index(app.config['FILE_ROOT'],'index.html')
        flash('%s-%s was installed into the index successfully.' % (name, version))
    return redirect('/')
    
@app.route('/requirements',methods=['POST','GET'])
def from_requirements():
    if request.method == "POST":
        f = request.files['req_file']
        
        filename = os.path.join(tempfile.gettempdir(),'temp-req.txt')
        f.save(filename)
        try:
            names = parse_reqs(filename, app.config['FILE_ROOT'])
        except:
            flash('There were some errors getting files from the uploaded requirements')
        else:
            flash('packages were installed from the requirements file. %s' % names)
        finally:
            regenerate_index(app.config['FILE_ROOT'],'index.html')
        
        return redirect('/requirements')
    return render_template('requirements_upload.html')
        