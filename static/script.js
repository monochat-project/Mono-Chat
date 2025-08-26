function createroom() {
    const name = document.getElementById("name");
    axios.post('http://127.0.0.1:5000/create-room/', {
    name: name.value}, {headers: { "Content-Type": "application/json"}
})
.then((res) => {
  alert(res.data.status_msg);
  window.location.replace(res.data.status_redirect);
    })
}

function joinroom() {
  const name = document.getElementById("name");
    axios.post('http://127.0.0.1:5000/join-room/', {
    name: name.value}, {headers: { "Content-Type": "application/json"}
})
.then((res) => {
  alert(res.data.status_msg);
  window.location.replace(res.data.status_redirect);
    })
}
