from flask import Flask, render_template, request, redirect, url_for, jsonify
import bleach 
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config['SECRET_KEY'] = ''
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)
socketio = SocketIO(app, cors_allowed_origins="*")

def status_msg(message):
    return render_template("create.html", status_msg=message)
    
@app.route("/")
@limiter.limit("10 per minute", methods=["POST"])
@limiter.limit("100 per minute", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/home/")
@limiter.limit("10 per minute", methods=["POST"])
@limiter.limit("100 per minute", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/exists/")
@limiter.limit("10 per minute", methods=["POST"])
@limiter.limit("100 per minute", methods=["GET"])
def exists():
    return render_template("Already_Exists.html")

@app.route("/create-room/", methods = ["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
@limiter.limit("100 per minute", methods=["GET"])
def create():
    #sname = stripped name
    sname = None
    status_msg = ""
    if request.method == "POST":
        data = request.get_json()
        name = data.get("name")
        with open("forum_names.txt", "r") as fi:
            fnames = fi.read().split()
        sname = secure_filename(name.strip())

        if sname not in fnames:
            with open("forum_names.txt", "a") as forumnames:
                forumnames.write(secure_filename(name) + "\n")
                room = open("rooms/" + secure_filename(name) + ".txt", "x")
                status_msg = f"Room Succesfully Created, People can now join {bleach.clean(name)}"
                status_redirect = url_for("home")
        elif sname in fnames:
            status_msg = f"Room {bleach.clean(name)} already exists or other Error accured."
            status_redirect = url_for("exists")
        return jsonify(status_msg=status_msg, status_redirect=status_redirect)
    elif request.method == "GET":
        return render_template("create.html")

@app.route("/join-room/", methods = ["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def join():
    if request.method == "POST":
        data = request.get_json()
        name = data.get("name")
        with open("forum_names.txt", "r") as fi:
            fnames = fi.read().split()
        sname = secure_filename(name.strip())
        
        if sname not in fnames:
            status_msg = f"Room {bleach.clean(sname)} doesnt exist."
            status_redirect = url_for("home")
        elif sname in fnames:
            status_msg = f"Room {bleach.clean(sname)} Joined!"
            status_redirect = url_for("room", name=sname)
        return jsonify(status_msg=status_msg, status_redirect=status_redirect)   
        #code for sending messages
        
    elif request.method == "GET":
        return render_template("join_room.html")
        #messages = open("rooms/" + bleach.clean(name) + ".txt").read()

@app.route("/rules")
def rules():
    return render_template("rules.html")
@app.route("/room/<name>")
@limiter.limit("10 per minute", methods=["POST"])
@limiter.limit("100 per minute", methods=["GET"])
def room(name):
        with open("forum_names.txt", "r") as fi:
            fnames = fi.read().split()
            sname = name.strip()
            sname = secure_filename(sname)
        if sname in fnames:
            return render_template("custome_room.html", name=bleach.clean(name))
        elif sname not in fnames:
            return redirect(url_for("index")) 
        return redirect(url_for("index")) 
@socketio.on("join")
@limiter.limit("5 per minute")
def join_socket(data):
    room = secure_filename(data["room"])
    name = secure_filename(data["name"])
    join_room(room)
    with open("forum_names.txt", "r") as fi:
        fnames = fi.read().split()
        sname = name.strip()
        sname = secure_filename(sname)
    if sname in fnames:
        with open(f"rooms/{secure_filename(room)}.txt", "r") as f:
            messages = f.read().replace("\n", "<br>")
        socketio.emit("get_messages", {"messages": messages}, room=request.sid)
    elif sname not in fnames:
        socketio.emit("not_found", {"found": "not"}, room=request.sid)
        leave_room(sname)

@socketio.on("send_message")
@limiter.limit("5 per 10 seconds")
def receive_message(data):
    name = bleach.clean(data.get("input_name", "Anon"))
    message = bleach.clean(data.get("message", ""))
    room_name = secure_filename(data.get("room_name", ""))
    tolong = None
    if name and message:
        if len(message) > 75:
            message = message[:75]
            tolong = "message"
        if len(name) > 15:
            name = name[:15] 
            tolong = "name"
        with open(f"rooms/{secure_filename(room_name)}.txt", "a") as fil:
            fil.write(f"{name}: {message}\n \n")
            socketio.emit("new_message", {"name": name, "message": message}, room=room_name)
        if tolong:
            socketio.emit("too_long", {"long": tolong}, room=request.sid)
        
if __name__ == '__main__':
    socketio.run(app, host="127.0.0.1", port=5000, debug=False)
