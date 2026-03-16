var socket = io();
const messageInput = document.getElementById("message");
const messagesContainer = document.getElementById("messages");
const typingDiv = document.getElementById("typing");
const imageInput = document.getElementById("imageInput");

// Send text message
function sendMessage(){
    const msg = messageInput.value.trim();
    if(msg==="") return;
    socket.emit("message", { user: me, to: toUser, message: msg });
    messageInput.value = "";
}

// Send image
function sendImage(){
    const file = imageInput.files[0];
    if(!file) return;
    const reader = new FileReader();
    reader.onload = function(e){
        const dataURL = e.target.result; // Base64
        socket.emit("image", { user: me, to: toUser, image: dataURL });
        imageInput.value = ""; // clear input after send
    }
    reader.readAsDataURL(file);
}

// Listen for text messages
socket.on("new_message", function(data){
    if(data.user===me || data.to===me){
        const div = document.createElement("div");
        div.classList.add("message", data.user===me?"me":"other");
        div.innerHTML = `<strong>${data.user}</strong>: ${data.message}`;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});

// Listen for image messages
socket.on("new_image", function(data){
    if(data.user===me || data.to===me){
        const div = document.createElement("div");
        div.classList.add("message", data.user===me?"me":"other");
        div.innerHTML = `<strong>${data.user}</strong>: <br>
                         <img src="${data.image}" style="max-width:200px; border-radius:10px;">`;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});

// Typing indicator
messageInput.addEventListener("keyup", function(e){
    if(e.key==="Enter"){ sendMessage(); }
    socket.emit("typing", { user: me, typing: messageInput.value.length>0 });
});

socket.on("typing", function(data){
    if(data.user!==me){
        typingDiv.innerText = data.typing ? `${data.user} is typing...` : "";
    }
});
let localStream;
let peerConnection;
const config = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };

// Start Voice or Video Call
function startCall(video=false){
    navigator.mediaDevices.getUserMedia({audio:true, video:video}).then(stream=>{
        localStream = stream;
        if(video) localVideo.srcObject = stream;
        if(video) localVideo.style.display = "block";

        peerConnection = new RTCPeerConnection(config);
        localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

        peerConnection.ontrack = (event) => {
            if(video) remoteVideo.srcObject = event.streams[0];
            else remoteAudio.srcObject = event.streams[0];
            if(video) remoteVideo.style.display = "block";
        };

        peerConnection.onicecandidate = e => {
            if(e.candidate){
                socket.emit("ice_candidate", {to: toUser, candidate: e.candidate});
            }
        };

        peerConnection.createOffer().then(offer => {
            peerConnection.setLocalDescription(offer);
            socket.emit("call_offer", {to: toUser, offer: offer, video: video, user: me});
        });
    }).catch(err => alert("Camera/Microphone access denied: " + err));
}

// Incoming offer
socket.on("call_offer", async data => {
    if(data.to !== me) return;
    navigator.mediaDevices.getUserMedia({audio:true, video:data.video}).then(async stream=>{
        localStream = stream;
        if(data.video) { localVideo.srcObject = stream; localVideo.style.display = "block"; }

        peerConnection = new RTCPeerConnection(config);
        localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

        peerConnection.ontrack = (event) => {
            if(data.video) { remoteVideo.srcObject = event.streams[0]; remoteVideo.style.display="block"; }
            else remoteAudio.srcObject = event.streams[0];
        };

        peerConnection.onicecandidate = e => {
            if(e.candidate) socket.emit("ice_candidate", {to: data.user, candidate: e.candidate});
        };

        await peerConnection.setRemoteDescription(data.offer);
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        socket.emit("call_answer", {to: data.user, answer: answer});
    });
});

// Incoming answer
socket.on("call_answer", async data => {
    if(data.to !== me) return;
    await peerConnection.setRemoteDescription(data.answer);
});

// ICE candidates
socket.on("ice_candidate", async data => {
    if(data.to !== me) return;
    try { await peerConnection.addIceCandidate(data.candidate); } catch(e){ console.log(e); }
});