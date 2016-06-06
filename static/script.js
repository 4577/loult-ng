window.onload = function() {
    var ws;
    
    var chatbox = document.getElementById('chatbox');
    var chattbl = document.getElementById('chattbl');
    var userlist = document.getElementById('userlist');
    var input = document.getElementById('input');
    var users = {};
    var muted = [];
    var right = localStorage.right == 'true';
    var waitTime = 1000;
    
    // DOM-related functions
    
    var addline = function(params, msg, backlog) {
        var tr = document.createElement('tr');
        if(backlog) {
            tr.className = 'backlog';
        }
        
        var td = document.createElement('td');
        var img = document.createElement('img');
        img.src = params.img;
        var label = document.createElement('label');
        label.appendChild(document.createTextNode(params.name));
        label.style.color = params.color;
        if(right) {
            td.appendChild(label);
            td.appendChild(document.createTextNode('\xa0'));
            td.appendChild(img);
        }
        else {
            td.appendChild(img);
            td.appendChild(document.createTextNode('\xa0'));
            td.appendChild(label);
        }
        tr.appendChild(td);
        
        td = document.createElement('td');
        td.innerHTML = msg.msg;
        tr.appendChild(td);
        
        td = document.createElement('td');
        var dt = new Date(msg.date).toLocaleString().replace(' à', '').replace(/ /, '\xa0');
        td.appendChild(document.createTextNode(dt));
        tr.appendChild(td);
        
        keepScroll(tr);
    }
    
    var log = function(msg, part) {
        var tr = document.createElement('tr');
        tr.className = 'log' + ['', ' part', ' kick'][part | 0];
        
        var td = document.createElement('td');
        td.appendChild(document.createTextNode('[Info]'));
        tr.appendChild(td);
        
        td = document.createElement('td');
        td.appendChild(document.createTextNode(msg));
        tr.appendChild(td);
        
        td = document.createElement('td');
        var dt = (new Date).toLocaleString().replace(' à', '').replace(/ /, '\xa0');
        td.appendChild(document.createTextNode(dt));
        tr.appendChild(td);
        
        keepScroll(tr);
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
        
        var img = document.createElement('img');
        img.src = params.img;
        div.appendChild(img);
        div.appendChild(document.createTextNode('\xa0'));
        
        var label = document.createElement('label');
        label.appendChild(document.createTextNode(params.name));
        label.style.color = params.color;
        div.appendChild(label);
        
        if(!params.you) {
            var sound = document.createElement('label');
            var soundnode = document.createTextNode(mute ? '🔇' : '🔊');
            sound.appendChild(soundnode);
            sound.className = 'sound';
            div.appendChild(sound);
            
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
        
        userlist.appendChild(div);
        users[userid].dom = div;
    };
    
    var delUser = function(userid) {
        userlist.removeChild(users[userid].dom);
        delete users[userid];
    };
    
    // Scroll-related functions
    
    var keepScroll = function(tr) {
        var atBottom = chatbox.scrollTop === (chatbox.scrollHeight - chatbox.offsetHeight);
        chattbl.appendChild(tr);
        
        if(atBottom) {
            chatbox.scrollTop = chatbox.scrollHeight;
        }
    };
    
    var refocus = function(evt) {
        setTimeout(function() {
            if(!window.getSelection().toString()) {
                input.focus()
            }
        }, evt.target.tagName === 'INPUT' ? 500 : 10);
    };
    document.body.addEventListener('mouseup', refocus, false);
    input.addEventListener('blur', refocus, false);
    
    // Preferences
    
    var gear = document.getElementById('gear');
    var overlay = document.getElementById('overlay');
    if(!overlay) {
        location.reload();
    }
    var cover = document.getElementById('cover');
    var windows = document.getElementById('window').children;
    var close = document.getElementById('close');
    
    var rightbtn = document.getElementById('right');
    
    var openWindow = function(panel) {
        /*for(var i = 0; i < windows.length; i++) {
            var show = windows[i].id === (panel || 'prefs');
            windows[i].style.display = show ? 'block' : 'none';
        }*/
        overlay.style.display = 'block';
    };
    var closeWindow = function() {
        overlay.style.display = 'none';
    };
    gear.onclick = openWindow;
    cover.onclick = closeWindow;
    close.onclick = closeWindow;
    
    rightbtn.checked = right;
    rightbtn.onchange = function(evt) {
        right = rightbtn.checked;
        localStorage.right = right;
        
        var rows = document.querySelectorAll('td:first-child');
        for(var i = 0; i < rows.length; i++) {
            var j = rows[i].childNodes.length;
            while(j--) {
                rows[i].appendChild(rows[i].childNodes[j]);
            }
        }
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
                ws.send(JSON.stringify({type: 'msg', msg: input.value}));
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
                        log('Un ' + msg.params.name + ' sauvage apparaît !');
                        addUser(msg.userid, msg.params);
                        break;
                    
                    case 'disconnect':
                        log('Un ' + users[msg.userid].name + " sauvage s'enfuit !", true);
                        delUser(msg.userid);
                        break;
                    
                    case 'userlist':
                        for(var i = 0; i < msg.users.length; i++) {
                            addUser(msg.users[i].userid, msg.users[i].params);
                        }
                        break;
                    
                    case 'backlog':
                        for(var i = 0; i < msg.msgs.length; i++) {
                            addline(msg.msgs[i].user, msg.msgs[i], true);
                        }
                        log('Vous êtes connecté');
                        break;
                    
                    case 'msg':
                        lastMuted = muted.indexOf(msg.userid) !== -1;
                        if(!lastMuted) {
                            addline(users[msg.userid], msg, false);
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
            
            log('Déconnecté, réessai...');
            
            window.setTimeout(wsConnect, waitTime);
            waitTime = Math.min(waitTime * 2, 120000);
        };
    };
    
    wsConnect();
};
