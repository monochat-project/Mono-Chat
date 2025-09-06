from flask import Flask, render_template, request, redirect, url_for, jsonify
import bleach 
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # replace with secure key
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
def home():
    return render_template("home.html")

@app.route("/exists/")
def exists():
    return render_template("Already_Exists.html")

@app.route("/create-room/", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        data = request.get_json()
        name = data.get("name")
        with open("forum_names.txt", "r") as fi:
            fnames = fi.read().split()
        sname = secure_filename(name.strip())

        if sname not in fnames:
            with open("forum_names.txt", "a") as forumnames:
                forumnames.write(sname + "\n")
            with open("rooms/" + sname + ".txt", "x"):
                pass
            status_msg = f"Room Succesfully Created, People can now join {bleach.clean(name)}"
            status_redirect = url_for("home")
        else:
            status_msg = f"Room {bleach.clean(name)} already exists or other Error occurred."
            status_redirect = url_for("exists")
        return jsonify(status_msg=status_msg, status_redirect=status_redirect)

    return render_template("create.html")

@app.route("/join-room/", methods=["GET", "POST"])
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
        else:
            status_msg = f"Room {bleach.clean(sname)} Joined!"
            status_redirect = url_for("room", name=sname)
        return jsonify(status_msg=status_msg, status_redirect=status_redirect)

    return render_template("join_room.html")

@app.route("/rules")
def rules():
    return render_template("rules.html")

@app.route("/room/<name>")
def room(name):
    with open("forum_names.txt", "r") as fi:
        fnames = fi.read().split()
    sname = secure_filename(name.strip())
    if sname in fnames:
        return render_template("custome_room.html", name=bleach.clean(name))
    return redirect(url_for("index"))

@socketio.on("join")
def join_socket(data):
    room = secure_filename(data["room"])
    name = secure_filename(data["name"])
    join_room(room)
    with open("forum_names.txt", "r") as fi:
        fnames = fi.read().split()
    sname = secure_filename(name.strip())
    if sname in fnames:
        with open(f"rooms/{room}.txt", "r") as f:
            messages = f.read().replace("\n", "<br>")
        socketio.emit("get_messages", {"messages": messages}, room=request.sid)
    else:
        socketio.emit("not_found", {"found": "not"}, room=request.sid)
        leave_room(sname)

@socketio.on("send_message")
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
        with open(f"rooms/{room_name}.txt", "a") as fil:
            fil.write(f"{name}: {message}\n \n")
        socketio.emit("new_message", {"name": name, "message": message}, room=room_name)
        if tolong:
            socketio.emit("too_long", {"long": tolong}, room=request.sid)

# NOTE: No socketio.run() here – Render uses gunicorn via Procfile
