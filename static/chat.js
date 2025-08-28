var socket = io("http://localhost:5000");
var roomName = document.getElementById("roomName").value;
socket.emit("join", { room: roomName, name: roomName});

socket.on("get_messages", function(data) {
  let msg_box = document.getElementById("messages_show");
  msg_box.innerHTML = data.messages
});

socket.on("not_found", function(data) {
  const notfound = data.found; 
  if (notfound === "not") {
    window.location.replace("http://127.0.0.1:5000/")
  }
});

function send() {
  input_name = document.getElementById("input_name").value
  message = document.getElementById("message").value
  if (input_name && message) {
    socket.emit("send_message", { input_name: input_name, message: message, room_name: roomName});
  }
}

socket.on("new_message", function(data) {
    let msg_box = document.getElementById("messages_show");
    msg_box.innerHTML += `${data.name}: ${data.message}<br> <br>`;
});

socket.on("rate_limited", function(data) {
  errormsg = data.errormsg;
  alert(errormsg)
})

socket.on("too_long", function(data) {
  if (data.long === "message") {
    alert("Message has to be under 75 characters.")
  } else if (data.long === "name") {
   alert("Name has to be under 15 characters.")
}
})
