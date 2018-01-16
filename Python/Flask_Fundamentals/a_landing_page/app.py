from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def greeting():
  return render_template('index.html')

@app.route('/ninjas')
def ninjas():
  return render_template('ninjas.html')

@app.route('/dojos/new')
def dojos_new():
  return render_template('dojos.html')


app.run(host='0.0.0.0',port=9090,debug=True)

