from flask import request, render_template, redirect, url_for,flash
from flask import current_app as app
from application.database import *
from flask import session
from flask_mail import Mail, Message
from  datetime import datetime
from application.api import *
import requests
import pytz
import os


IST = pytz.timezone('Asia/Kolkata')

from flask_restful import Resource, Api
app = None
api = None
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy()
db.init_app(app)
api = Api(app)
app.app_context().push()
app.secret_key = 'secret key'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'mahetajayvin@gmail.com'  
app.config['MAIL_PASSWORD'] = 'Enter your password'  
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

db.create_all()
db.session.commit()

api.add_resource(ForgotPasswordAPI, '/api/forgotpassword')
api.add_resource(MailAPI, '/api/mail')
api.add_resource(SignUpAPI, '/api/signup')
api.add_resource(UserAPI, '/api/user')
api.add_resource(TrackerAPI, '/api/tracker')
api.add_resource(LogAPI, '/api/log' )
api.add_resource(GraphAPI, '/api/graph' )


@app.route('/')
@app.route('/signin', methods=["GET","POST"])
def signin():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == "GET":
        return render_template("signin.html")
    elif request.method == "POST":
        form_data={}
        form_data['email_id'] = request.form.get('email_id')
        form_data['password'] =  request.form.get('password')
        api_response=requests.post('http://127.0.0.1:8080/api/user', form_data).json()
        if 'user_id' in api_response:
            if api_response['email_verified']==True:
                session['user_id']=api_response['user_id']
                session['user_fname']=api_response['user_fname']
                return redirect(url_for('dashboard'))
            else:
                session['unverified_user_id']=api_response['user_id']
                session['verify_origin']='signin'
                session['user_fname']=api_response['user_fname']
                api_request={}
                api_request['user_id']=session['unverified_user_id']
                api_response=requests.get('http://127.0.0.1:8080/api/mail', api_request).json()
                if "sent" in api_response:
                    flash(api_response['sent'])
                    return redirect(url_for('otp'))
                elif 'error_code' in api_response:
                    session.pop('_flashes', None)
                    flash(api_response['error_message'])
                    return redirect(url_for('signin'))
        elif 'error_code' in api_response:
            session.pop('_flashes', None)
            flash(api_response['error_message'])
            return redirect(url_for('signin'))

@app.route('/signup', methods=["GET","POST"])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        form_data={}
        form_data['email_id'] = request.form.get('email_id')
        form_data['password'] =  request.form.get('password')
        form_data['user_fname'] = request.form.get('fname')
        form_data['user_lname'] =  request.form.get('lname')
        api_response=requests.post('http://127.0.0.1:8080/api/signup', form_data).json()
        if 'user_id' in api_response:
            session.pop('_flashes', None)
            flash('Signup done successfully')
            return redirect(url_for('signin'))
        elif 'error_code' in api_response:
            session.pop('_flashes', None)
            flash(api_response['error_message'])
            return redirect(url_for('signup'))

@app.route('/verify', methods=["GET","POST"])
def otp():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == "GET":
        if "unverified_user_id" in session:
            flag=False
            if session['verify_origin']=='forgotpassword':
                flag=True
            return render_template("otp verify.html",flag=flag)
        else:
            return redirect(url_for('signin'))
    elif request.method == "POST":
        if "unverified_user_id" in session:
            api_request={}
            api_request['user_id']=session['unverified_user_id']
            api_request['otp']=request.form.get('otp')
            api_response=requests.post('http://127.0.0.1:8080/api/mail', api_request).json()
            if 'otp' in api_response:
                if session['verify_origin']=='signin':
                    session['user_id']=session['unverified_user_id']
                    session.pop('unverified_user_id', None)
                    session.pop('verify_origin', None)
                    flash('OTP verification done successfully.')
                    return redirect(url_for('dashboard'))
                elif session['verify_origin']=='forgotpassword':
                    api_request={}
                    api_request['user_id']=session['unverified_user_id']
                    api_request['password']=request.form.get('new_password')
                    api_response=requests.post('http://127.0.0.1:8080/api/forgotpassword', api_request).json()
                    if 'user_id' in api_response:
                        session['user_id']=api_response['user_id']
                        session.pop('unverified_user_id', None)
                        session.pop('verify_origin', None)
                        flash('password changed successfully.')
                        return redirect(url_for('dashboard'))
                    elif 'error_code' in api_response:
                        if api_response['error_code']=='OTP01':
                            flash(api_response['error_message'])
                            return redirect(url_for(session['verify_origin']))
                        else:
                            flash(api_response['error_message'])
                            return redirect(url_for('otp'))
            elif 'error_code' in api_response:
                if api_response['error_code']=='OTP01':
                    flash(api_response['error_message'])
                    return redirect(url_for(session['verify_origin']))
                else:
                    flash(api_response['error_message'])
                    return redirect(url_for('otp'))

@app.route('/forgotpassword', methods=["GET","POST"])
def forgotpassword():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == "GET":
        return render_template("forgotpassword.html")
    elif request.method == "POST":
        api_request={}
        api_request['email_id']=request.form.get('email_id')
        api_response=requests.get('http://127.0.0.1:8080/api/forgotpassword', api_request).json()
        if 'user_id' in api_response:
            session['unverified_user_id']=api_response['user_id']
            session['verify_origin']='forgotpassword'
            session['user_fname']=api_response['user_fname']
            api_request={}
            api_request['user_id']=session['unverified_user_id']
            api_response=requests.get('http://127.0.0.1:8080/api/mail', api_request).json()
            if "sent" in api_response:
                flash(api_response['sent'])
                return redirect(url_for('otp'))
            elif 'error_code' in api_response:
                session.pop('_flashes', None)
                flash(api_response['error_message'])
                return redirect(url_for('forgotpassword'))
            return redirect(url_for('otp'))
        elif 'error_code' in api_response:
            flash(api_response['error_message'])
            return redirect(url_for('forgotpassword'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if request.method == "GET":
        api_request={}
        api_request['user_id']=session['user_id']
        flag=True
        api_response=requests.get('http://127.0.0.1:8080/api/tracker', api_request).json()
        if  "error_code" in api_response:
            flag=False
        else:
            for i in api_response:
                if i['tracker_lastupdate']==None:
                    i['tracker_lastupdate']='No Logs'
                else:
                    tracker_lastupdate=i['tracker_lastupdate'][:-3]
                    tracker_lastupdate = datetime.datetime.strptime(tracker_lastupdate, "%Y-%m-%d %H:%M")
                    i['tracker_lastupdate']=tracker_lastupdate.strftime('%Y-%m-%d %I:%M %p')
        return render_template("dashboard.html",trackers=api_response,flag=flag)

@app.route('/tracker',methods=["GET","POST"])
def tracker():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if request.method == "GET":
        type=request.args.get('type')
        tracker_id=request.args.get('t_id')
        if type is not None and tracker_id is not None:
            if type=='delete':
                api_request={}
                api_request['user_id']=session['user_id']
                api_request['tracker_id']=tracker_id
                api_response=requests.delete('http://127.0.0.1:8080/api/tracker',params=api_request).json()
                if 'code' in api_response:
                    session.pop('_flashes', None)
                    flash('Tracker has Been Delete.')
                    return redirect(url_for('dashboard'))
                elif 'error_code' in api_response:
                    session.pop('_flashes', None)
                    flash(api_response['error_message'])
                    return redirect(url_for('dashboard'))
            elif type=='update':
                api_request={}
                api_request['user_id']=session['user_id']
                api_request['tracker_id']=tracker_id
                api_response=requests.get('http://127.0.0.1:8080/api/tracker', api_request).json()
                if 'tracker_id' in api_response:
                    return render_template("update tracker.html",tracker=api_response)
                elif 'error_code' in api_response:
                    session.pop('_flashes', None)
                    flash(api_response['error_message'])
                    return redirect(url_for('dashboard'))

        elif type==None and tracker_id is not None:
            api_request={}
            api_request['user_id']=session['user_id']
            api_request['tracker_id']=tracker_id
            api_request['log_id']=None
            trackerdata=requests.get('http://127.0.0.1:8080/api/tracker', api_request).json()
            if 'tracker_id' in trackerdata:
                logdata=requests.get('http://127.0.0.1:8080/api/log', api_request).json()
                flag=False
                if 'error_code' in logdata:
                    session.pop('_flashes', None)
                    flash(logdata['error_message'])
                    return redirect(url_for('dashboard'))
                user_fname=session['user_fname']
                tracker_name=trackerdata['tracker_name']
                tracker_type=trackerdata['tracker_type']
                if 'log_id' in logdata[0]:
                    flag=True
                    graphdata=requests.get('http://127.0.0.1:8080/api/graph', api_request).json()
                    for i in logdata:
                        log_time=i['log_time'][:-3]
                        log_time = datetime.datetime.strptime(log_time, "%Y-%m-%d %H:%M")
                        i['log_time']=log_time.strftime('%Y-%m-%d %I:%M %p')
                    return render_template("tracker.html",user_fname=user_fname,logs=logdata,tracker_id=tracker_id,tracker_name=tracker_name,flag=flag,tracker_type=tracker_type,graphdata=graphdata)
            else:
                flash(trackerdata['error_message'])
                return redirect(url_for('dashboard'))
        return render_template("add tracker.html",user_fname=session['user_fname'])

    elif request.method == "POST":
        type=request.args.get('type')
        tracker_id=request.args.get('t_id')
        if type is not None and tracker_id is not None:
            api_request={}
            api_request['user_id']=session['user_id']
            api_request['tracker_id']=tracker_id
            api_request['tracker_name'] = request.form.get('name')
            api_request['tracker_description'] = request.form.get('description')
            api_response=requests.put('http://127.0.0.1:8080/api/tracker', api_request).json()
            if 'tracker_id' in api_response:
                session.pop('_flashes', None)
                flash('Tracker has Been Upated Succesfully.')
                return redirect(url_for('dashboard'))
            elif 'error_code' in api_response:
                session.pop('_flashes', None)
                flash(api_response['error_message'])
                return redirect(url_for('dashboard'))
        else:
            api_request={}
            api_request['user_id']=session['user_id']
            api_request['tracker_name'] = request.form.get('name')
            api_request['tracker_type'] =  request.form.get('type')
            api_request['tracker_description'] = request.form.get('description')
            api_request['tracker_settings'] =  request.form.get('settings')
            api_response=requests.post('http://127.0.0.1:8080/api/tracker', api_request).json()
            if 'tracker_id' in api_response:
                session.pop('_flashes', None)
                flash('Tracker has Been Added Succesfully.')
                return redirect(url_for('dashboard'))
            elif 'error_code' in api_response:
                session.pop('_flashes', None)
                flash(api_response['error_message'])
                return redirect(url_for('tracker'))
        


@app.route('/log',methods=["GET","POST"])
def log():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if request.method == "GET":
        type=request.args.get('type')
        tracker_id=request.args.get('t_id')
        tracker_type=request.args.get('t_type')
        log_id=request.args.get('l_id')
        if type is not None and tracker_id is not None and log_id is not None:
            if type=='delete':
                api_request={}
                api_request['user_id']=session['user_id']
                api_request['tracker_id']=tracker_id
                api_request['log_id']=log_id
                api_response=requests.delete('http://127.0.0.1:8080/api/log',params=api_request).json()
                if 'code' in api_response:
                    session.pop('_flashes', None)
                    flash('Log Has Been Deleted')
                    return redirect(url_for('tracker')+'?t_id='+str(tracker_id))
                elif 'error_code' in api_response:
                    session.pop('_flashes', None)
                    flash(api_response['error_message'])
                    return redirect(url_for('tracker')+'?t_id='+str(tracker_id))
            elif type=='update':
                api_request={}
                api_request['user_id']=session['user_id']
                api_request['tracker_id']=tracker_id
                api_request['log_id']=log_id
                logdata=requests.get('http://127.0.0.1:8080/api/log', api_request).json()
                if 'log_id' in logdata:
                    log_time= logdata['log_time']
                    log_time=log_time.split(' ')
                    log_time=log_time[0]+'T'+log_time[1][:-3]
                    trackerdata=requests.get('http://127.0.0.1:8080/api/tracker', api_request).json()
                    settings=trackerdata['tracker_settings'].split(',')
                    tracker_type=trackerdata['tracker_type']
                    return render_template("update log.html",log=logdata,tracker_type=tracker_type,tracker_id=tracker_id,log_time=log_time,settings=settings,user_fname=session['user_fname'])
                elif 'error_code' in logdata:
                    session.pop('_flashes', None)
                    flash(logdata['error_message'])
                    return redirect(url_for('tracker')+'?t_id='+str(tracker_id))

        elif tracker_id is not None and tracker_type is not None and log_id is None :
            time=datetime.datetime.now(IST)
            time=time.strftime('%Y-%m-%dT%H:%M')
            api_request={}
            api_request['user_id']=session['user_id']
            api_request['tracker_id']=tracker_id
            api_response=requests.get('http://127.0.0.1:8080/api/tracker', api_request).json()
            settings=api_response['tracker_settings'].split(',')
            return render_template("add log.html",tracker_id=tracker_id,tracker_type=tracker_type,time=time,settings=settings)

    elif request.method == "POST":
        type=request.args.get('type')
        tracker_id=request.args.get('t_id')
        log_id=request.args.get('l_id')
        tracker_type=request.args.get('t_type')
        if type is not None and tracker_id is not None and log_id is not None:
            api_request={}
            api_request['user_id']=session['user_id']
            api_request['tracker_id']=tracker_id
            api_request['log_id']=log_id
            log_time= request.form['log_time']
            log_time=log_time.split('T')
            log_time=log_time[0]+' '+log_time[1]
            api_request['log_time']=log_time
            api_request['log_value'] = request.form.get('log_value')
            api_request['log_note'] = request.form.get('log_note')
            api_response=requests.put('http://127.0.0.1:8080/api/log', api_request).json()
            if 'log_id' in api_response:
                session.pop('_flashes', None)
                flash('Log has Been Upated Succesfully.')
                return redirect(url_for('tracker')+'?t_id='+str(tracker_id))
            elif 'error_code' in api_response:
                session.pop('_flashes', None)
                flash(api_response['error_message'])
                return redirect(url_for('tracker')+'?t_id='+str(tracker_id))
        else:
            api_request={}
            api_request['user_id']=session['user_id']
            api_request['tracker_id']=tracker_id
            log_time= request.form.get('log_time')
            log_time=log_time.split('T')
            log_time=log_time[0]+' '+log_time[1]
            api_request['log_time']=log_time
            api_request['log_value'] = request.form.get('log_value')
            api_request['log_note'] = request.form.get('log_note')
            api_response=requests.post('http://127.0.0.1:8080/api/log', api_request).json()
            if 'log_id' in api_response:
                session.pop('_flashes', None)
                flash('Log has Been Added Succesfully.')
                return redirect(url_for('tracker')+'?t_id='+str(tracker_id))
            elif 'error_code' in api_response:
                session.pop('_flashes', None)
                flash(api_response['error_message'])
                return redirect(url_for('tracker')+'?t_id='+str(tracker_id))

@app.route('/signout')
def signout():
    session.clear()
    return redirect(url_for('signin'))

if __name__ == "__main__" :
    app.run(host="0.0.0.0", debug=True, port=8080)
