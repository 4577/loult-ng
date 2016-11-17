document.addEventListener('DOMContentLoaded', function() {
    var ws;
    
    var chatbox = document.getElementById('chatbox');
    var chattbl = document.getElementById('chattbl');
    var input = document.getElementById('input');
    
    var select = document.getElementById('lang');
    var users = {};
    var muted = [];
    var waitTime = 1000;
	
	var timeouts = [];
    
    // DOM-related functions
    
    var addline = function(params, msg) {
        var p = document.createElement('p');
        p.innerHTML = msg.msg;
        document.getElementById('bubble_' + msg.userid).style.opacity = 1;
        document.getElementById('bubble_' + msg.userid).appendChild(p);
		p.style.maxHeight = '500px';
		setTimeout(function(){ p.style.maxHeight = '0'; }, 5000);
		clearTimeout(timeouts['bubble_' + msg.userid]);
		timeouts['bubble_' + msg.userid] = setTimeout(function(){ document.getElementById('bubble_' + msg.userid).style.opacity = 0; }, 5000);
    }
    
    var addUser = function(userid, params) {
        if(userid in users) {
            return;
        }
        
        users[userid] = params;
        var mute = muted.indexOf(userid) !== -1;
        
        var div = document.createElement('div');
        if(mute) {
            div.className = 'mute';
        }
        
		var bubble = document.createElement('div');
		bubble.id = 'bubble_' + userid;
		bubble.className = 'bubble';
        bubble.style.color = params.color;
        bubble.style.borderColor = params.color;
        div.appendChild(bubble);
        
        var img = document.createElement('img');
        img.src = '.' + params.img.replace('gif', 'png');
        div.appendChild(img);
        
        var label = document.createElement('label');
        label.appendChild(document.createTextNode(params.name));
        label.style.color = params.color;
        div.appendChild(label);
		
        if(!params.you) {
            var sound = document.createElement('label');
            var soundnode = document.createTextNode(mute ? '🔇' : '🔊');
            sound.appendChild(soundnode);
            sound.className = 'sound';
            label.appendChild(sound);
            
            sound.onmousedown = function() {
                mute = muted.indexOf(userid) !== -1;
                if(!mute) {
                    muted.push(userid);
                    soundnode.nodeValue = '🔇';
                    div.className = 'mute';
                }
                else {
                    muted.splice(muted.indexOf(userid), 1);
                    soundnode.nodeValue = '🔊';
                    div.className = '';
                }
            };
        }
		
		div.style.position = 'absolute';
		div.style.left = Math.ceil(Math.random() * (window.innerWidth - 450)) + 'px';
		div.style.top = Math.ceil(270 + (Math.random() * (window.innerHeight - 570))) + 'px';
        
        chatbox.appendChild(div);
        users[userid].dom = div;
    };
    
    var delUser = function(userid) {
        chatbox.removeChild(users[userid].dom);
        delete users[userid];
    };
    
    // Scroll-related functions
    
    var dontFocus = false;
    select.addEventListener('focus', function() {
        dontFocus = true;
    }, false);
    
    var refocus = function(evt) {
        setTimeout(function() {
            if(!dontFocus && !window.getSelection().toString()) {
                input.focus();
            }
            else if(dontFocus) {
                dontFocus = false;
            }
        }, 10);
    };
    window.addEventListener('focus', refocus, false);
    document.body.addEventListener('mouseup', refocus, false);
    
    // Languages
    
    var lang = document.cookie.match(/lang=(\w\w)/);
    
    if(!lang) {
        switch(navigator.language.substr(0, 2)) {
            case 'fr':
            case 'es':
            case 'de':
                lang = navigator.language.substr(0, 2);
                break;
            default:
                lang = 'en';
        }
        document.cookie = 'lang=' + lang + '; Path=/';
    }
    else {
        lang = lang[1];
    }
    select.value = lang;
    
    select.onchange = function() {
        lang = this.value;
        document.cookie = 'lang=' + lang + '; Path=/';
    };
    
    // Sound and volume
    
    var context = new (window.AudioContext || webkitAudioContext)();
    
    var volume = context.createGain ? context.createGain() : context.createGainNode();
    volume.connect(context.destination);
    
    var speaker = document.getElementById('speaker');
    var volrange = document.getElementById('volrange');
    
    if(localStorage.volume) {
        volrange.value = localStorage.volume * 100;
        volume.gain.value = localStorage.volume;
    }
    
    speaker.onclick = function() {
        if(this.src.indexOf('mute') == -1) {
            volume.gain.value = 0;
            this.src = '/img/mute.png';
        }
        else {
            volume.gain.value = volrange.value / 100;
            this.src = '/img/speaker.png';
        }
    };
    volrange.oninput = function() {
        if(speaker.src.indexOf('mute') == -1) {
            volume.gain.value = volrange.value / 100;
            localStorage.volume = volume.gain.value;
        }
    };
    
    // WebSocket-related functions
    
    var wsConnect = function() {
        ws = new WebSocket(location.origin.replace('http', 'ws') + '/socket' + location.pathname);
        
        var lastMuted = false;
        ws.binaryType = 'arraybuffer';
        
        input.onkeydown = function(evt) {
            if(evt.keyCode == 13 && input.value) {
                ws.send(JSON.stringify({type: 'msg', msg: input.value, lang: lang}));
                input.value = '';
            }
        };
        
        ws.onopen = function() {
            waitTime = 1000;
        };
        
        ws.onmessage = function(msg) {
            if(typeof msg.data == 'string') {
                msg = JSON.parse(msg.data);
                
                switch(msg.type) {
                    case 'connect':
                        addUser(msg.userid, msg.params);
                        break;
                    
                    case 'disconnect':
                        delUser(msg.userid);
                        break;
                    
                    case 'userlist':
                        for(var i = 0; i < msg.users.length; i++) {
                            addUser(msg.users[i].userid, msg.users[i].params);
                        }
                        break;
                    
                    case 'msg':
                        lastMuted = muted.indexOf(msg.userid) !== -1;
                        if(!lastMuted) {
                            addline(users[msg.userid], msg);
                        }
                        break;
                }
            }
            else if(!lastMuted) {
                context.decodeAudioData(msg.data, function(buf) {
                    var source = context.createBufferSource();
                    source.buffer = buf;
                    source.connect(volume);
                    source.start();
                });
            }
        };
        
        ws.onerror = function(e) {
            console.log(['error', e]);
        };
        
        ws.onclose = function() {
            for(var i in users) {
                delUser(i);
            }
            
            // log('Déconnecté, réessai...');
            
            window.setTimeout(wsConnect, waitTime);
            waitTime = Math.min(waitTime * 2, 120000);
        };
    };
    
    wsConnect();
});
