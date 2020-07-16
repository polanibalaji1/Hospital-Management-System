from flask import Flask,render_template,session, redirect, url_for, request, flash
from flask_mysqldb import MySQL #imported mysql for database
from wtforms import Form,StringField,TextAreaField,IntegerField,PasswordField,validators,SelectMultipleField,SelectField,ValidationError #used wtforms to create forms
from wtforms.fields.html5 import DateField #For date
import datetime #for current time
from functools import wraps #for session management

app = Flask(__name__)
app.secret_key = 'super secret key'

#configuration of MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""   #ENTER THE PASSWORD OF THE MYSQL HERE
app.config['MYSQL_DB'] = "hms"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"

#initialized Mysql
mysql = MySQL(app)

#Home Login page for admission_desk/pharmacist/diagnosist
@app.route('/',methods=['GET','POST'])
def home():
    if request.method == 'POST':
        #Get form fields entered in login form
        username = request.form['username']
        password_candidate = request.form['password']

        #Create cursor for sql connection
        cur = mysql.connection.cursor()

        #get user by username in db
        result = cur.execute("select * from users where username= %s",[username])

        #if the result is fetched then take the password from db
        if result>0:
            #Get Stored Hash
            data = cur.fetchone() #fetch the data in db
            password = data['password'] #get the password

            #compare passwords
            if password_candidate==password: #check the password from login form and database
                #Passed
                session['logged_in']=True  #session started
                session['username'] = username
                if data['position']=='patient':
                    flash('You are now logged in','success')   #flash the message on the screen
                    return redirect(url_for('admission_desk_index'))
                elif data['position']=='pharmacy':
                    flash('You are now logged in','success')
                    return redirect(url_for('pharmacy_index')) 
                elif data['position']=='diagnostics':
                    flash('You are now logged in','success')
                    return redirect(url_for('diagnostics_index'))
            else:
                error = 'Invalid Login Password'           #if password doesn't match then show this error
                return render_template('home.html',error=error)
            #CLose Connection
            cur.close()
        else:          #if no result is fetched, it means there is no such username in db
            error = 'Username Not Found'  #display this error
            return render_template('home.html',error=error)
    return render_template('home.html')

# Check if user logged in #Session Management
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('home'))
    return wrap

#Logout
@app.route('/logout')
def logout():
    session.clear()  #clear entire session and redirect back to home url
    flash('You are Logged out','success')
    return redirect(url_for('home'))

#Patient Index Page
@app.route('/admission_desk_index')
@is_logged_in
def admission_desk_index():
    return render_template("admission_desk_index.html")

#To Add Patient Registration Form
class RegisterForm(Form):
    pat_ssnid = IntegerField('Patient SSN Id', [validators.NumberRange(min=100000000, max=999999999)])
    pname = StringField('Patient Name*',[validators.Length(min=3,max=25)])
    age = IntegerField('Age*')
    doa = DateField('Date Of Admission:*',format='%Y-%m-%d')
    bed =  SelectField('Type of Bed*', choices=[('single','Single'),('semisharing','Shared'),('generalward','General')])
    address = StringField('Address*',[validators.Length(min=3)])
    state = SelectField('State*', choices=[('Andhra Pradesh','Andhra Pradesh'),('Assam','Assam'),('Bihar','Bihar'),('Chhattisgarh','Chhattisgarh'),('Goa','Goa'),('Gujarat','Gujarat'),('Haryana','Haryana'),('Himachal Pradesh','Himachal Pradesh'),('Jammu and Kashmir','Jammu and Kashmir'),('Jharkhand','Jharkhand'),('Karnataka','Karnataka'),('Kerala','Kerala'),('Madya Pradesh','Madya Pradesh'),('Manipur','Manipur'),('Meghalaya','Meghalaya'),('Shillong','Shillong'),('Mizoram','Mizoram'),('Nagaland','Nagaland'),('orissa','orissa'),('Punjab','Punjab'),('Rajasthan','Rajasthan'),('Sikkim','Sikkim'),('Telagana','Telagana'),('Tripura','Tripura'),('Uttaranchal','Uttaranchal'),('Uttar Pradesh','Uttar Pradesh'),('West Bengal','West Bengal'),('Maharashtra', 'Maharashtra'),('Tamil Nadu', 'Tamil Nadu')])

#Add Patient Page
@app.route('/add_patient',methods=['GET','POST'])
@is_logged_in
def add_patient():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate(): #check the form is validated and method is post
        pat_ssnid = form.pat_ssnid.data #takes data from the form
        pname = form.pname.data
        age = int(request.form['age'])
        if age>110:
            flash("Age Must Be Less than 111",'danger')
            return redirect(url_for('add_patient'))
        doa = form.doa.data
        bed = form.bed.data
        address = form.address.data
        state = form.state.data
        today = str(datetime.date.today())
        pyear=int(today[0:4])
        pmonth = int(today[5:7])
        doamonth=doa.month
        doayr=doa.year
        if doamonth>pmonth and doayr>=pyear:
            flash("date of admission should be less than present date",'danger')
            return redirect(url_for('add_patient'))
        #created cursor for mysql connection
        cur = mysql.connection.cursor()

        #get ssnid by patient in db
        result = cur.execute("select * from patients where pat_ssnid= %s",[pat_ssnid])

        #if the result is fetched then redirect with message as ssnid already used
        if result>0:
            flash("SSNID Already Used Please Use Another",'danger')
            return redirect(url_for('add_patient'))
        #Else insert the data into Table
        status = "active"
        messages= "Patient Account is Created"
        cur.execute("INSERT INTO patients(pat_ssnid,pname,age,doa,bed,address,state,status,messages) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(pat_ssnid,pname,age,doa,bed,address,state,status,messages))

        #commit to db
        mysql.connection.commit()

        #close connection
        cur.close()

        flash("New Patient is Created",'success') #flash msg that patient record is created and redirect
        return redirect(url_for('admission_desk_index'))
    return render_template('add_patient.html',form=form)

#----------------------------------------------------------------------------------------------------------------------------------------------
#To Update Patient Form
class UpdateForm(Form):
    pname = StringField('Patient Name*',[validators.Length(min=3,max=25)])
    age = IntegerField('Age*')
    address = StringField('Address*',[validators.Length(min=3)])

#Update patient View Page
@app.route('/update_patient',methods=['GET','POST'])
@is_logged_in
def update_patient():
    form = UpdateForm(request.form)
    if request.method == 'POST':
        pid= request.form['pid'] #takes the data from search form
        pat_ssnid = request.form['pat_ssnid']
        #create cursor
        cur = mysql.connection.cursor()
        data = cur.execute('select * from patients where pid = %s or pat_ssnid=%s',[pid,pat_ssnid])
        if data==1:
            result = cur.fetchall()
            cur.close()
            return render_template('update_patient.html',form=form,result=result)
        elif data==2:
            error = 'Enter Only 1 Field'
            return render_template('search.html',error=error)
        else:
            error = "No such Patient data is present"
            return render_template('search.html',error=error,form=form)
    return render_template('search.html',form=form)

#Updated patient
@app.route('/update_patient/<string:pid>',methods=['GET','POST']) #takes PID/PAT_SSNID from update_patient html form
@is_logged_in
def update_pat(pid):
    form = UpdateForm(request.form)
    if request.method == 'POST':
        pname = request.form['pname'] #takes the data from update_patient form
        age = request.form['age']
        address = request.form['address']
        cur = mysql.connection.cursor()
        messages = "Patient details are Updated"
        # Execute Update Command
        res = cur.execute("Update patients set pname = %s, age = %s, address = %s , messages = %s WHERE pid = %s", [pname,age,address,messages,pid])
        # Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()
        flash('Patient Details Updated Successfully', 'success')
        return redirect(url_for('admission_desk_index'))

#--------------------------------------------------------------------------------------------------------------
#Delete Patient View Page
@app.route('/del_patient',methods=['GET','POST'])
@is_logged_in
def del_patient():
    if request.method == "POST":
        pid= request.form['pid'] #takes the data from search form
        pat_ssnid = request.form['pat_ssnid']
        #create cursor for connection
        cur = mysql.connection.cursor()
        #get the data from db
        data = cur.execute('select * from patients where pid = %s or pat_ssnid=%s',[pid,pat_ssnid])

        if data==1: #if data is present then render the page to del_customer along with all the data
            result = cur.fetchall()
            cur.close()
            return render_template('del_patient.html',result=result) # <- Here you jump away from whatever result you create
        elif data==2:
            error = 'Enter Only 1 Field'
            return render_template('search.html',error=error)
        else:     #Else display there is no such data in db
            error = "No such Patient data is present"
            return render_template('search.html',error=error)
    return render_template('search.html')

# Delete Customer From db
@app.route('/del_pat/<string:pid>', methods=['GET','POST']) #takes the cid from the del_customer html form
@is_logged_in
def del_pat(pid):
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute
    cur.execute('Delete from mtrack where pid = %s',[pid])
    cur.execute('Delete from dtrack where pid = %s',[pid])
    cur.execute('Delete from patients where pid = %s',[pid])
    # Commit to DB
    mysql.connection.commit()
    #Close connection
    cur.close()
    flash('patient Data Deleted', 'success')
    return redirect(url_for('admission_desk_index'))


#---------------------------------------------------------------------------------------------------------------
#View Patient Details
@app.route('/view_patient',methods=['POST','GET'])
@is_logged_in
def view_patient():
    if request.method=='POST':
        pid= request.form['pid']
        cur = mysql.connection.cursor()
        data = cur.execute('select * from patients where pid = %s',[pid])
        if data > 0:
            result = cur.fetchall()
            cur.close()
            return render_template('view_patient.html', result=result)
        else :
            return render_template('view_patient.html')
    limit=10 #it will display only top 10 patient details
    st = 'active'
    cur = mysql.connection.cursor() #connection created
    data1 = cur.execute('select * from patients where status = %s order by timestamp desc limit %s',[st,limit])
    if data1 > 0: #display the patient details whose status is active
        result1 = cur.fetchall()
        cur.close()
        return render_template('view_patient.html' , result = result1)
    else :
        flash("No patient Created Till Now",'danger')
        return render_template('view_patient.html')

#--------------------------------------------------------------------------------------------------------------------------
#Search Patient
@app.route('/search_patient',methods=['GET','POST'])
@is_logged_in
def search_patient():
    if request.method == "POST":
        pid= request.form['pid'] #takes the data from search form
        pat_ssnid = request.form['pat_ssnid']
        #create cursor for connection
        cur = mysql.connection.cursor()
        #get the data from db
        data = cur.execute('select * from patients where pid = %s or pat_ssnid=%s',[pid,pat_ssnid])

        if data==1: #if data is present then render the page to del_customer along with all the data
            result = cur.fetchall()
            cur.close()
            return render_template('patient_detail.html',result=result) # <- Here you jump away from whatever result you get
        elif data==2:
            error = 'Enter Only 1 Field'
            return render_template('search.html',error=error)
        else:     #Else display there is no such data in db
            error = "No such Patient data is present"
            return render_template('search.html',error=error)
    return render_template('search.html')

#-------------------------------------------------------------------------------------------------------
#Billing The Cost Of Patient
@app.route('/billing',methods=['GET','POST'])
@is_logged_in
def billing():
     status = 'active'
     if request.method == "POST":
        pid= request.form['pid'] #takes the data from search form
        #create cursor for connection
        cur = mysql.connection.cursor()
        #get the data from db
        data = cur.execute('select * from patients where pid = %s',[pid])
        if data==1: #if data is present
            result = cur.fetchall()
            cur.close()
            if result[0]['status']=='active':
                cur = mysql.connection.cursor()
                data1 = cur.execute('select * from mtrack where pid=%s', [pid])
                if data1>0: #checks whether any medicine is issued or not
                    res = cur.fetchall()
                    cur.close()
                    cur = mysql.connection.cursor()
                    sum = cur.execute('select sum(amount) from mtrack where pid=%s', [pid])
                    res1 = cur.fetchall()
                    cur.close()
                else: #if not present then returns none and cost as 0
                    res = None
                    res1 = None
                    sum = 0
                cur = mysql.connection.cursor()
                data2 = cur.execute('select * from dtrack where pid=%s', [pid])
                if data2>0: #checks whether any diagnosis treatment is performed or not
                    res2 = cur.fetchall()
                    cur.close()
                    cur = mysql.connection.cursor()
                    dsum = cur.execute('select sum(amount) from dtrack where pid=%s', [pid])
                    res3 = cur.fetchall()
                    # print(res3)
                    cur.close()
                else: #if not present then returns none and cost as 0
                    res2 = None
                    res3 = None
                    dsum=0
                cur = mysql.connection.cursor()
                days = cur.execute('select DATEDIFF(timestamp,doa)  from patients where pid=%s', [pid]) #returns no of days by taking difference
                res4 = cur.fetchall()
                cur.close()
                cur = mysql.connection.cursor()
                #to take amount based on the bed assigned
                amount = cur.execute('select  case when bed = "generalward" then 2000 when bed = "semisharing" then 4000 else 8000 end as amount from patients where pid=%s',[pid])
                res5 = cur.fetchall()
                cur.close()
                return render_template('billing.html', result=result, res=res, res1=res1, res2=res2, res3=res3,res4=res4, res5=res5,pid=pid)  # <- Here you jump away from whatever result you create
            else:
                error = "Patient is discharged and paid the Bill Already"
                return render_template('search3.html', error=error)
        else:     #Else display there is no such data in db
            error = "No such Patient data is present"
            return render_template('search3.html',error=error)
     return render_template('search3.html')

#Pharmacy Index Page
@app.route('/pharmacy_index')
@is_logged_in
def pharmacy_index():
    return render_template("pharmacy_index.html")

#Issue Medicine
@app.route('/issue_medicine',methods=['GET','POST'])
@is_logged_in
def issue_medicine():
    if request.method == "POST":
        pid= request.form['pid'] #takes the data from search form
        #create cursor for connection
        cur = mysql.connection.cursor()
        #get the data from db
        st = 'active'
        #takes the data where patient is present and status is active
        data = cur.execute('select * from patients where pid = %s and status = %s',[pid,st])
        if data==1: #if data is present
            result = cur.fetchall()
            cur.close()
            cur = mysql.connection.cursor()
            dat = cur.execute('select * from medicines') #takes all the medicine present in the db for issuing it.
            res1 = cur.fetchall()
            cur.close()
            cur = mysql.connection.cursor()
            data1 = cur.execute('select * from mtrack where pid=%s',[pid]) #to take the history of medicine issued
            res = cur.fetchall()
            cur.close()
            return render_template('issue_medicine.html',result=result,res=res,res1=res1,piddata=pid) # <- Here you jump away from whatever result you create
        else:     #Else display there is no such data in db
            error = "No such Patient data is present or Patient is Discharged"
            return render_template('search1.html',error=error)
    return render_template('search1.html') 

#Issue Quantity
@app.route('/issue_quant/<pid>/<string:mid>', methods=['GET','POST']) #takes the mid and pid from the issue_medicine html form
@is_logged_in
def issue_quant(pid,mid): 
    # Create cursor
    cur = mysql.connection.cursor()
    data = cur.execute("select * from medicines where mid = %s",[mid])
    res = cur.fetchall()
    return render_template('issue_quant.html',res = res,pid=pid)

#Issued
@app.route('/issued/<pid1>/<string:mid>',methods=['GET','POST'])
@is_logged_in
def issued(pid1,mid):
    if request.method == 'POST':
        qu = request.form['quantity']
        q = int(qu)
        cur = mysql.connection.cursor()
        # Execute
        data = cur.execute('select * from medicines where mid = %s',[mid])
        res = cur.fetchall()
        cur.close()
        cur = mysql.connection.cursor()
        data1 = cur.execute('select * from patients where pid = %s',[pid1])
        cur.close()
        if data1>0:
        # Execute
            if res[0]['quant_avail']>=q: #if quantity of medicine required is present
                cur = mysql.connection.cursor()
                cur.execute("Update medicines set quant_avail = %s WHERE mid = %s", [res[0]['quant_avail']-int(q),mid])
                cur.execute('insert into mtrack(pid,mid,mname,qissued,rate,amount) values(%s,%s,%s,%s,%s,%s)',[pid1,mid,res[0]['mname'],q,res[0]['cost'],res[0]['cost']*int(q)])
                mysql.connection.commit()
                cur.close()
                flash("Medicine Issued",'success')
                return redirect(url_for('issue_medicine'))
            else:
                flash("This much Quantity not available!!Sry",'danger')
                return redirect(url_for('issue_medicine'))
        else:
            flash("Patient Id Wrongly Typed!!!Check again",'danger')
            return render_template("pharmacy_index.html")

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Diagnostics Index Page
@app.route('/diagnostics_index')
@is_logged_in
def diagnostics_index():
    return render_template("diagnostics_index.html")

#Add Diagnostics
@app.route('/diagnostics',methods=['GET','POST'])
@is_logged_in
def diagnostics():
    if request.method == "POST":
        pid= request.form['pid'] #takes the data from search form
        #create cursor for connection
        cur = mysql.connection.cursor()
        #get the data from db
        st = 'active'
        data = cur.execute('select * from patients where pid = %s and status = %s',[pid,st])
        if data==1: #if data is present then render the page along with all the data
            result = cur.fetchall()
            cur.close()
            cur = mysql.connection.cursor()
            dat = cur.execute('select * from diagnosistest')
            res1 = cur.fetchall()
            cur.close()
            cur = mysql.connection.cursor()
            data1 = cur.execute('select * from dtrack where pid=%s',[pid])
            res = cur.fetchall()
            cur.close()
            return render_template('diagnostics.html',result=result,res=res,res1=res1,piddata=pid) # <- Here you jump away from whatever result you create
        else:     #Else display there is no such data in db
            error = "No such Patient data is present or Patient is Discharged"
            return render_template('search2.html',error=error)
    return render_template('search2.html')


#Issued
@app.route('/add_diagnostics/<pid1>/<string:testid>',methods=['GET','POST'])
@is_logged_in
def add_diagnostics(pid1,testid):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        # Execute
        data = cur.execute('select * from diagnosistest where testid = %s',[testid])
        res = cur.fetchall()
        cur.close()
        cur = mysql.connection.cursor()
        data1 = cur.execute('select * from patients where pid = %s',[pid1])
        cur.close()
        if data1>0:
            cur = mysql.connection.cursor()
            cur.execute('insert into dtrack(pid,testid,testname,amount) values(%s,%s,%s,%s)',[pid1,testid,res[0]['testname'],res[0]['amount']])
            mysql.connection.commit()
            cur.close()
            flash("Diagnostic Added",'success')
            return redirect(url_for('diagnostics'))
        else:
            flash("This test is currently ot available!!",'danger')
            return redirect(url_for('diagnostics'))
    else:
        flash("Patient Id Wrongly Typed!!!Check again",'danger')
        return render_template("diagnostics_index.html")

#-------------------------------------------------------------------------------------------------------
#Bill Payment of the Total Amount
@app.route('/bill_payment/<pid>',methods=['POST','GET']) #takes the pid from the billing html form
@is_logged_in
def bill_payment(pid): 
    if request.method == 'POST':
        status = 'discharge' #convert the status to discharge once payment is done
        cur = mysql.connection.cursor()
        cur.execute('update patients set status=%s where pid=%s',[status,pid]) #patient status is updated
        mysql.connection.commit()
        cur.close()
        flash("Bill Paid",'success') #Flash the message of Bill Paid and take back to home screen
        return redirect('/admission_desk_index')
    return redirect('/admission_desk_index')

if __name__ == '__main__':
    app.run(debug=True)

