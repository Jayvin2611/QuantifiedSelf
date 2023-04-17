from flask import Flask
from flask import current_app as app
from flask_restful import Resource, fields, marshal_with, reqparse
from flask_mail import Mail,Message
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from application.database import *
from application.validations import *
from passlib.hash  import sha256_crypt
import pytz
import string
import random

IST = pytz.timezone('Asia/Kolkata')


user_parser = reqparse.RequestParser()
user_parser.add_argument("user_id")
user_parser.add_argument("email_id")
user_parser.add_argument("password")
user_parser.add_argument("user_fname")
user_parser.add_argument("user_lname")

mail_parser = reqparse.RequestParser()
mail_parser.add_argument("user_id")
mail_parser.add_argument("otp")

tracker_parser = reqparse.RequestParser()
tracker_parser.add_argument("tracker_id")
tracker_parser.add_argument("user_id")
tracker_parser.add_argument("tracker_name")
tracker_parser.add_argument("tracker_type")
tracker_parser.add_argument("tracker_description")
tracker_parser.add_argument("tracker_settings")

log_parser = reqparse.RequestParser()
log_parser.add_argument("log_id")
log_parser.add_argument("tracker_id")
log_parser.add_argument("user_id")
log_parser.add_argument("log_time")
log_parser.add_argument("log_value")
log_parser.add_argument("log_note")

graph_parser = reqparse.RequestParser()
graph_parser.add_argument("tracker_id")
graph_parser.add_argument("user_id")



user_output = {
    "user_id": fields.Integer,
    "email_id": fields.String,
    "user_fname": fields.String,
    "user_lname": fields.String,
    "email_verified": fields.Boolean
}

tracker_output = {
    "tracker_id": fields.Integer,
    "user_id": fields.Integer,
    "tracker_name": fields.String,
    "tracker_type": fields.String,
    "tracker_description":fields.String,
    "tracker_settings": fields.String,
    "tracker_lastupdate": fields.String
}

log_output= {
    "log_id": fields.Integer,
    "tracker_id": fields.Integer,
    "log_time": fields.String,
    "log_value": fields.String,
    "log_note": fields.String
}

graph_output= {
    "today": fields.String,
    "week": fields.String,
    "month": fields.String
}

mail_output= {
    "sent": fields.String
}

otp_output={
    "otp": fields.Boolean
}

error_messages = {
    "USER01": "User Doesn't Exist.",
    "USER02": "Email id Already Exist Try Another Email id.",
    "USER03": "User Doesn't Have any Traker.",
    "USER04": "Enter Valid Email id.",
    "USER05": "Opps unable to sent OTP to your email id please try again later",
    "OTP01": "OTP is expired please redo the whole process",
    "OTP02": "Wrong OTP please enter right OTP",
    "PASSWORD01": "Wrong Password.",
    "PASSWORD02": "Password Can't Be Empaty.",
    "PASSWORD03": "Old Passwrod and New Password can't be same",
    "TRACKER01": "Tracker Doesn't Exist.",
    "TRACKER02": "Tracker Doesn't Have Any Log.",
    "TRACKER03": "Tracker Already Exist.",
    "TRACKER04": "Multiple Choice Type Tracker can't have Empty Settings.",
    "LOG01": "Log Doesn't Exist.",
    "LOG02": "Log Already Exist."
}

def generate_otp():
    otp=''
    while len(otp)<6:
        a=random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
        if a not in otp:
            otp+=a
    return otp

class MailAPI(Resource):
    @marshal_with(mail_output)
    def get(self):
        mail = Mail(app)
        args = mail_parser.parse_args()
        user_id=args.get("user_id")
        user=User.query.filter_by(user_id=user_id).first()
        if user is None:
            raise BusinessValidationError(400,error_code="USER01",error_msg=error_messages["USER01"])
        mail_id=user.email_id
        otp = generate_otp()
        user_otp=Otp.query.filter_by(user_id=user_id).first()
        if user_otp is None:
            try:
                msg = Message('OTP for QuantifiedSelf',sender ='herbalife.jayvin@gmail.com',recipients = [mail_id])
                msg.body = "Hello User Your OTP is : "+otp+"\n\nJayvin Maheta\nQuantifiedSelf" 
                mail.send(msg)
                otp=sha256_crypt.encrypt(otp)
                otp_time=datetime.datetime.now(IST)
                user_opt=Otp(user_id=user.user_id,otp_value=otp,otp_time=otp_time)
                db.session.add(user_opt)
                db.session.commit()
                output={'sent':'OTP has been sent to your email id if you dont find it in Inbox check Spam folder'}
                return output
            except:
                raise BusinessValidationError(400,error_code="USER05",error_msg=error_messages["USER05"])
        try:
            msg = Message('OTP for QuantifiedSelf',sender ='herbalife.jayvin@gmail.com',recipients = [mail_id])
            msg.body = "Hello "+user.user_fname+" Your OTP is : "+otp+"\n\nJayvin Maheta\nQuantifiedSelf" 
            mail.send(msg)
            user_otp.otp_value=sha256_crypt.encrypt(otp)
            user_otp.otp_time=datetime.datetime.now(IST)
            db.session.commit()
            output={'sent':'OTP has been sent to your email id if you dont find it in Inbox check Spam folder'}
            return output
        except:
            raise BusinessValidationError(400,error_code="USER05",error_msg=error_messages["USER05"])
    
    @marshal_with(otp_output)
    def post(self):
        args = mail_parser.parse_args()
        user_id=args.get("user_id")
        user=User.query.filter_by(user_id=user_id).first()
        if user is None:
            raise BusinessValidationError(400,error_code="USER01",error_msg=error_messages["USER01"])
        otp=args.get("otp")
        user_otp=Otp.query.filter_by(user_id=user_id).first()
        otp_expire_time=user_otp.otp_time+datetime.timedelta(minutes=5)
        current_time=datetime.datetime.now()
        if current_time>otp_expire_time:
            raise BusinessValidationError(400,error_code="OTP01",error_msg=error_messages["OTP01"])
        if sha256_crypt.verify(otp,user_otp.otp_value):
            user.email_verified=True
            db.session.commit()
            return {"otp":True}
        raise BusinessValidationError(400,error_code="OTP02",error_msg=error_messages["OTP02"])
            
class ForgotPasswordAPI(Resource):
    @marshal_with(user_output)
    def get(self):
        args = user_parser.parse_args()
        email_id=args.get("email_id")
        if '@' not in email_id:
            raise BusinessValidationError(400,error_code="USER04",error_msg=error_messages["USER04"])
        user=User.query.filter_by(email_id=email_id).first()
        if user is None:
            raise BusinessValidationError(400,error_code="USER01",error_msg=error_messages["USER01"])
        return user
        

    @marshal_with(user_output)
    def post(self):
        args = user_parser.parse_args()
        user_id=args.get("user_id")
        password=args.get("password")
        user=User.query.filter_by(user_id=user_id).first()
        if user is None:
            raise BusinessValidationError(400,error_code="USER02",error_msg=error_messages["USER02"])
        if password is None:
            raise BusinessValidationError(400,error_code="PASSWORD02",error_msg=error_messages["PASSWORD02"])
        if sha256_crypt.verify(password,user.password):
            raise BusinessValidationError(400,error_code="PASSWORD03",error_msg=error_messages["PASSWORD03"])
        password=sha256_crypt.encrypt(password)
        user.password=password
        db.session.commit()
        return user

class SignUpAPI(Resource):
    @marshal_with(user_output)
    def post(self):
        args = user_parser.parse_args()
        email_id=args.get("email_id")
        password=args.get("password")
        if '@' not in email_id:
            raise BusinessValidationError(400,error_code="USER04",error_msg=error_messages["USER04"])
        user=User.query.filter_by(email_id=email_id).first()
        if user is None:
            if password is None:
                raise BusinessValidationError(400,error_code="PASSWORD02",error_msg=error_messages["PASSWORD02"])
            password=sha256_crypt.encrypt(password)
            user=User(email_id=email_id,password=password,user_fname=args.get("user_fname"),user_lname=args.get("user_lname"),email_verified=False)
            db.session.add(user)
            db.session.commit()
            return user
        raise BusinessValidationError(400,error_code="USER02",error_msg=error_messages["USER02"])

class UserAPI(Resource):
    @marshal_with(user_output)
    def get(self):
        args = user_parser.parse_args()
        user_id=args.get("user_id")
        user=User.query.filter_by(user_id=user_id).first()
        if user is None:
            raise BusinessValidationError(400,error_code="USER01",error_msg=error_messages["USER01"])
        return user
    
    @marshal_with(user_output)
    def post(self):
        args=user_parser.parse_args()
        password=args.get("password")
        if password is None:
            raise BusinessValidationError(400,error_code="PASSWORD02",error_msg=error_messages["PASSWORD02"])
        user=User.query.filter_by(email_id=args.get("email_id")).first()
        if user is None:
            raise BusinessValidationError(400,error_code="USER01",error_msg=error_messages["USER01"])
        if sha256_crypt.verify(password,user.password):
            return user
        raise BusinessValidationError(400,error_code="PASSWORD01",error_msg=error_messages["PASSWORD01"])

class TrackerAPI(Resource):
    @marshal_with(tracker_output)
    def get(self):
        args=tracker_parser.parse_args()
        user_id=args.get("user_id")
        tracker_id=args.get("tracker_id")
        user=User.query.filter_by(user_id=user_id).first()
        if user is None :
            raise BusinessValidationError(400,error_code="USER01",error_msg=error_messages["USER01"])
        if tracker_id is None:
            trackerlist=Tracker.query.filter_by(user_id=user_id).all()
            if len(trackerlist)>0:
                return trackerlist
            raise BusinessValidationError(400,error_code="USER03",error_msg=error_messages["USER03"])
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker is None:
            raise BusinessValidationError(400,error_code="TRACKER01",error_msg=error_messages["TRACKER01"])
        return tracker
    
    @marshal_with(tracker_output)
    def post(self):
        args = tracker_parser.parse_args()
        user_id=args.get("user_id")
        tracker_name=args.get("tracker_name")
        tracker_type=args.get("tracker_type")
        tracker_description=args.get("tracker_description")
        tracker_settings=args.get("tracker_settings")
        if tracker_type=='Multiple Choice' and tracker_settings is None:
            raise BusinessValidationError(400,error_code="TRACKER04",error_msg=error_messages["TRACKER04"])
        if tracker_type=='Boolean':
            tracker_settings='Yes,No'
        user=User.query.filter_by(user_id=user_id).first()
        if user is None :
            raise BusinessValidationError(400,error_code="USER01",error_msg=error_messages["USER01"])
        tracker=Tracker.query.filter((Tracker.tracker_name==tracker_name) & (Tracker.user_id==user_id)).first()
        if tracker is None:
            tracker=Tracker(user_id=user_id,tracker_name=tracker_name,tracker_type=tracker_type,tracker_settings=tracker_settings,tracker_description=tracker_description)
            db.session.add(tracker)
            db.session.commit()
            return tracker
        raise BusinessValidationError(400,error_code="TRACKER03",error_msg=error_messages["TRACKER03"])
    
    @marshal_with(tracker_output)
    def put(self):
        args = tracker_parser.parse_args()
        user_id=args.get("user_id")
        tracker_id=args.get("tracker_id")
        tracker_name=args.get("tracker_name")
        tracker_description=args.get("tracker_description")
        user=User.query.filter_by(user_id=user_id).first()
        if user is None :
            raise BusinessValidationError(400,error_code="USER01",error_msg=error_messages["USER01"])
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker is None:
            raise BusinessValidationError(400,error_code="TRACKER01",error_msg=error_messages["TRACKER01"])
        tracker.tracker_name=tracker_name
        tracker.tracker_description=tracker_description
        db.session.commit()
        return tracker
    
    @marshal_with(tracker_output)
    def delete(self):
        args = tracker_parser.parse_args()
        user_id=args.get("user_id")
        tracker_id=args.get("tracker_id")
        user=User.query.filter_by(user_id=user_id).first()
        if user is None :
            raise BusinessValidationError(400,error_code="USER01",error_msg=error_messages["USER01"])
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker is None:
            raise BusinessValidationError(400,error_code="TRACKER01",error_msg=error_messages["TRACKER01"])
        db.session.delete(tracker)
        db.session.commit()
        raise BusinessValidationSuccessful()
            

class LogAPI(Resource):
    @marshal_with(log_output)
    def get(self):
        args = log_parser.parse_args()
        user_id=args.get("user_id")
        tracker_id=args.get("tracker_id")
        log_id=args.get("log_id")
        if log_id is None:
            loglist=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id)).all()
            if len(loglist)>0:
                return loglist
            raise BusinessValidationError(400,error_code="TRACKER02",error_msg=error_messages["TRACKER02"])
        log=Log.query.filter((Log.log_id==log_id) & (Log.user_id==user_id) & (Log.tracker_id==tracker_id)).first()
        if log is None:
            raise BusinessValidationError(400,error_code="LOG01",error_msg=error_messages["LOG01"])
        return log
            
    
    @marshal_with(log_output)
    def post(self):
        args = log_parser.parse_args()
        user_id=args.get("user_id")
        tracker_id=args.get("tracker_id")
        t=args.get("log_time")
        log_time = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M")
        log_value=args.get("log_value")
        log_note=args.get("log_note")
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker is None:
            raise BusinessValidationError(400,error_code="TRACKER01",error_msg=error_messages["TRACKER01"])
        log=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time==log_time)).first()
        if log is None:
            log=Log(user_id=user_id,tracker_id=tracker_id,log_time=log_time,log_value=log_value,log_note=log_note)
            if tracker.tracker_lastupdate:
                if log_time>tracker.tracker_lastupdate:
                    tracker.tracker_lastupdate=log_time
            else:
                tracker.tracker_lastupdate=log_time
            db.session.add(log)
            db.session.commit()
            return log
        raise BusinessValidationError(400,error_code="LOG02",error_msg=error_messages["LOG02"])

    @marshal_with(log_output)
    def put(self):
        args = log_parser.parse_args()
        user_id=args.get("user_id")
        tracker_id=args.get("tracker_id")
        log_id=args.get("log_id")
        t=args.get("log_time")
        log_time = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M")
        log_value=args.get("log_value")
        log_note=args.get("log_note")
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker is None:
            raise BusinessValidationError(400,error_code="TRACKER01",error_msg=error_messages["TRACKER01"])
        log=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_id==log_id)).first()
        if log is None:
            raise BusinessValidationError(400,error_code="LOG01",error_msg=error_messages["LOG01"])
        if tracker.tracker_lastupdate:
            if log_time>tracker.tracker_lastupdate:
                tracker.tracker_lastupdate=log_time
        else:
            tracker.tracker_lastupdate=log_time
        log.log_time=log_time
        log.log_value=log_value
        log.log_note=log_note
        db.session.commit()
        return log
            

    @marshal_with(log_output)
    def delete(self):
        args = log_parser.parse_args()
        user_id=args.get("user_id")
        tracker_id=args.get("tracker_id")
        log_id=args.get("log_id")
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker is None:
            raise BusinessValidationError(400,error_code="TRACKER01",error_msg=error_messages["TRACKER01"])
        log=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_id==log_id)).first()
        if log is None:
            raise BusinessValidationError(400,error_code="LOG01",error_msg=error_messages["LOG01"])
        db.session.delete(log)
        db.session.commit()
        log=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id)).order_by(Log.log_time.desc()).first()
        if log:
            tracker.tracker_lastupdate=log.log_time
        else:
            tracker.tracker_lastupdate=None
        db.session.commit()
        raise BusinessValidationSuccessful()

class GraphAPI(Resource):

    @marshal_with(graph_output)
    def get(self):
        args = graph_parser.parse_args()
        user_id=args.get("user_id")
        tracker_id=args.get("tracker_id")
        d={'today':'No','week':'No','month':'No'}
        date={}
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker is None:
            return d
        datetoday=datetime.datetime.now(IST).replace(hour=0,minute=0,second=0,microsecond=0)
        date['today']=datetoday
        date['week']=datetoday-datetime.timedelta(days=datetoday.weekday())
        date['month']=datetoday.replace(day=1)
        for time in date:
            if tracker.tracker_type=='Numerical':
                loglisttoday=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=date[time])).order_by(Log.log_time.asc()).all()
                if len(loglisttoday)>0:
                    x=[]
                    y=[]
                    for i in loglisttoday:
                        x.append(i.log_time)
                        y.append(int(i.log_value))
                    plt.plot_date(x,y,'o-')
                    plt.ylim(min(0,min(y)-1),max(y)+1)
                    plt.gcf().autofmt_xdate()
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_'+time+'.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d[time]='Yes'
            elif tracker.tracker_type=='Multiple Choice':
                settings=tracker.tracker_settings
                settings=settings.split(',')
                data=[]
                name=[]
                for i in settings:
                    count=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=date[time])&(Log.log_value==i)).count()
                    if count>0:
                        data.append(count)
                        name.append(i)
                if len(data)>0:
                    plt.pie(data, labels = name)
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_'+time+'.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d[time]='Yes'
            elif tracker.tracker_type=='Boolean':
                settings=tracker.tracker_settings
                settings=settings.split(',')
                data=[]
                name=[]
                for i in settings:
                    count=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=date[time])&(Log.log_value==i)).count()
                    if count>0:
                        data.append(count)
                        name.append(i)
                if len(data)>0:
                    x=range(len(data))
                    plt.xticks(x,name)
                    plt.bar(x,data)
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_'+time+'.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d[time]='Yes'
        return d