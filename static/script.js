document.addEventListener('DOMContentLoaded', function() {
	var audio = (window.AudioContext || typeof webkitAudioContext !== 'undefined');
	var chatbox = document.getElementById('chatbox');
	var chattbl = document.getElementById('chattbl');
	var usertbl = document.getElementById('usertbl');
	var input = document.getElementById('input');
	var left = (localStorage.left == 'true');
	var dt = (localStorage.dt == 'true');
	var hr = (localStorage.hr == 'true');
	var waitTime = 1000;
	var users = {};
	var muted = [];
	var you = null;
	var ws;
	
	// DOM-related functions
	
	var addLine = function(pkmn, txt, datemsg, trclass) {
		var tr = document.createElement('tr');
		if(trclass)
			tr.className = trclass;
		
		var td = document.createElement('td');
		if(pkmn == 'info')
			td.appendChild(document.createTextNode('[Info]'));
		else
		{
			var label = document.createElement('label');
			label.appendChild(document.createTextNode(pkmn.name));
			label.style.color = pkmn.color;
			label.style.backgroundImage = 'url(".' + pkmn.img + '")';
			label.className = (left ? 'left' : 'right');
			td.appendChild(label);
		}
		tr.appendChild(td);
		
		td = document.createElement('td');
		txt = String(txt).replace(/\*{2}([^\*]+)\*{2}/g, '<span>$1</span>');
		txt = String(txt).replace(/(.+)?\{{4}(.+)?\}{4}(.+)?/, '<marquee>$1$2$3</marquee>');
		td.innerHTML = txt;
		if(txt.match(/^&gt;/))
			td.className = 'greentext';
		tr.appendChild(td);
		
		td = document.createElement('td');
		var dat = (new Date(datemsg)).toLocaleDateString().replace(/ /, '\xa0');
		var sp = document.createElement('span');
		if(dt)
			sp.className = 'show';
		sp.appendChild(document.createTextNode(dat));
		td.appendChild(sp);
		
		sp = document.createElement('span');
		if(dt && hr)
			sp.className = 'show';
		sp.appendChild(document.createTextNode(',\xa0'));
		td.appendChild(sp);

		dat = (new Date(datemsg)).toLocaleTimeString().replace(/ /, '\xa0');
		sp = document.createElement('span');
		if(hr)
			sp.className = 'show';
		sp.appendChild(document.createTextNode(dat));
		td.appendChild(sp);
		tr.appendChild(td);
		
		var atBottom = (chatbox.scrollTop == (chatbox.scrollHeight - chatbox.offsetHeight));
		chattbl.appendChild(tr);
		if(atBottom)
			chatbox.scrollTop = chatbox.scrollHeight;
	};
	
	var addUser = function(userid, params) {
		if(userid in users)
			return;
		
		users[userid] = params;
		var mute = (muted.indexOf(userid) != -1);
		var tr = document.createElement('tr');
		var td = document.createElement('td');
		var label = document.createElement('label');
		if(mute)
			tr.className = 'mute';
		
		label.appendChild(document.createTextNode(params.name));
		label.style.color = params.color;
		label.style.backgroundImage = 'url(".' + params.img + '")';
		label.className = 'left';
		td.appendChild(label);
		tr.appendChild(td);
		td = document.createElement('td');
		
		if(!params.you) {
			var sound = document.createElement('img');
			sound.src = (mute ? './img/mute.png' : './img/speaker.png');
			sound.className = 'sound';
			td.appendChild(sound);
			
			sound.onmousedown = function() {
				var mt = (muted.indexOf(userid) != -1);
				if(!mt) {
					muted.push(userid);
					sound.src = './img/mute.png';
					tr.className = 'mute';
				}
				else {
					muted.splice(muted.indexOf(userid), 1);
					sound.src = './img/speaker.png';
					tr.className = '';
				}
			};
		}
		else
			you = userid;
		
		tr.appendChild(td);
		usertbl.appendChild(tr);
		users[userid].dom = tr;
	};
	
	var delUser = function(userid) {
		usertbl.removeChild(users[userid].dom);
		delete users[userid];
	};
	
	// Preferences
	
	var gear = document.getElementById('gear');
	var overlay = document.getElementById('overlay');
	var cover = document.getElementById('cover');
	var close = document.getElementById('close');
	var rightbtn = document.getElementById('right');
	var dtbtn = document.getElementById('dt');
	var hrbtn = document.getElementById('hr');
	// var ckwipe = document.getElementById('ckwipe');
	var head = document.getElementById('head');
	var main = document.getElementById('main');
	
	var openWindow = function() {
		overlay.style.display = 'block';
		head.className = 'blur-in';
		main.className = 'blur-in';
	};
	var closeWindow = function() {
		overlay.style.display = 'none';
		head.className = '';
		main.className = '';
	};
	
	gear.onclick = openWindow;
	cover.onclick = closeWindow;
	close.onclick = closeWindow;
	
	rightbtn.checked = !left;
	rightbtn.onchange = function(evt) {
		left = !rightbtn.checked;
		localStorage.left = left;
		var rows = document.querySelectorAll('#chattbl td:first-child label');
		for(var i = 0; i < rows.length; i++)
			rows[i].className = (left ? 'left' : 'right');
	};
	
	dtbtn.checked = dt;
	dtbtn.onchange = function(evt) {
		dt = dtbtn.checked;
		localStorage.dt = dt;
		var atBottom = (chatbox.scrollTop == (chatbox.scrollHeight - chatbox.offsetHeight));
		var rows = document.querySelectorAll('#chattbl td:last-child span:first-child');
		for(var i = 0; i < rows.length; i++)
			rows[i].className = (dt ? 'show' : '');
		mid(atBottom);
	};
	
	hrbtn.checked = hr;
	hrbtn.onchange = function(evt) {
		hr = hrbtn.checked;
		localStorage.hr = hr;
		var atBottom = (chatbox.scrollTop == (chatbox.scrollHeight - chatbox.offsetHeight));
		var rows = document.querySelectorAll('#chattbl td:last-child span:last-child');
		for(var i = 0; i < rows.length; i++)
			rows[i].className = (hr ? 'show' : '');
		mid(atBottom);
	};
	
	var mid = function(atBottom) {
		var rows = document.querySelectorAll('#chattbl td:last-child span:nth-child(2)');
		for(var i = 0; i < rows.length; i++)
			rows[i].className = ((dt && hr) ? 'show' : '');
		if(atBottom)
			chatbox.scrollTop = chatbox.scrollHeight;
	}
	
	// ckwipe.onclick = function(evt) {
		// evt.preventDefault();
		// if(confirm('Supprimer le cookie ?')) {
			// document.cookie = 'id=; expires=Thu, 01 Jan 1970 00:00:01 GMT; Path=/';
			// location.reload();
		// }
	// }; 
	
	// Languages
	
	var select = document.getElementById('lang');
	var lang = document.cookie.match(/lang=(\w{2})/);
	
	if(!lang) {
		var l = navigator.language.substr(0, 2);
		switch(l) {
			case 'fr':
			case 'es':
			case 'de':
				lang = l;
			break;
			default:
				lang = 'en';
		}
		document.cookie = 'lang=' + lang + '; Path=/';
	}
	else
		lang = lang[1];
	
	select.value = lang;
	
	select.onchange = function() {
		lang = this.value;
		document.cookie = 'lang=' + lang + '; Path=/';
	};
	
	// Focus-related functions
	
	var dontFocus = false;
	select.addEventListener('focus', function() {
		dontFocus = true;
	}, false);
	
	var refocus = function(evt) {
		setTimeout(function() {
			if(!dontFocus && !window.getSelection().toString())
				input.focus();
			else if(dontFocus)
				dontFocus = false;
		}, 10);
	};
	
	window.addEventListener('focus', refocus, false);
	document.body.addEventListener('mouseup', refocus, false);
	
	window.addEventListener('resize', function(evt) {
		chatbox.scrollTop = chatbox.scrollHeight;
	});
	
	// Sound and volume
	
	if(audio)
	{
		var speaker = document.getElementById('speaker');
		var volrange = document.getElementById('volrange');
		var context = new (window.AudioContext || webkitAudioContext)();
		var volume = (context.createGain ? context.createGain() : context.createGainNode());
		volume.connect(context.destination);
		
		if(localStorage.volume) {
			volrange.value = localStorage.volume * 100;
			volume.gain.value = localStorage.volume;
		}
		
		speaker.onclick = function() {
			if(this.src.indexOf('mute') == -1) {
				volume.gain.value = 0;
				this.src = './img/mute.png';
			}
			else {
				volume.gain.value = volrange.value / 100;
				this.src = './img/speaker.png';
			}
		};
		volrange.oninput = function() {
			if(speaker.src.indexOf('mute') == -1) {
				volume.gain.value = volrange.value / 100;
				localStorage.volume = volume.gain.value;
			}
		};
	}
	
	// Speech
	
	if('webkitSpeechRecognition' in window) {
		var recognition = new webkitSpeechRecognition();
		var recognizing = false;
		
		var chatentry = document.getElementById('chatentry');
		var img = document.createElement('img');
        img.src = './img/micro_off.png';
		chatentry.appendChild(img);
		img.onclick = startDictation;
		
		recognition.continuous = true;
		recognition.interimResults = true;
		
		recognition.onstart = function() {
			recognizing = true;
		};
		
		recognition.onerror = function(event) {
			// console.log(event.error);
		};
		
		recognition.onend = function() {
			recognizing = false;
		};
		
		recognition.onresult = function(event) {
			var interim_transcript = '';
			for(var i = event.resultIndex; i < event.results.length; i++) {
				if(event.results[i].isFinal) {
					var m = input.value.trim();
					if(m.length > 0) {
						ws.send(JSON.stringify({type: 'msg', msg: m, lang: lang}));
						input.value = '';
					}
				}
				else {
					interim_transcript += event.results[i][0].transcript;
				}
			}
			input.value = interim_transcript.trim();
			input.value = input.value.charAt(0).toUpperCase() + input.value.slice(1);
		};
		
		function startDictation() {
			if(recognizing) {
				recognition.stop();
				img.src = './img/micro_off.png';
				return;
			}
			var l = 'en-US';
			switch(lang) {
				case 'fr':
					l = 'fr-FR';
				break;
				case 'es':
					l = 'es-ES';
				break;
				case 'de':
					l = 'de-DE';
				break;
				default:
					l = 'en-US';
			}
			img.src = './img/micro_on.png';
			recognition.lang = l;
			recognition.start();
			input.value = '';
		}
	}
	
	// Users list display
	
	var userlist = document.getElementById('userlist');
	var userswitch = document.getElementById('userswitch');
	
	userswitch.onclick = function() {
		var atBottom = (chatbox.scrollTop == (chatbox.scrollHeight - chatbox.offsetHeight));
		userlist.style.width = (userlist.style.width == '0px' ? '185px' : '0px');
		if(atBottom)
			chatbox.scrollTop = chatbox.scrollHeight;
	};
	
	// WebSocket-related functions
	
	var wsConnect = function() {
		ws = new WebSocket(location.origin.replace('http', 'ws') + '/socket' + location.pathname);
		// ws = new WebSocket('ws://loult.family/socket' + location.pathname);
		
		var lastMuted = false;
		ws.binaryType = 'arraybuffer';
		
		input.onkeydown = function(evt) {
			if(evt.keyCode == 13 && input.value) {
				if(input.value.match(/^\/atta(ck|que)\s/i)) {
					splitted = input.value.split(' ');
					ws.send(JSON.stringify({ type : 'attack', target : splitted[1], order : ((splitted.length == 3) ? parseInt(splitted[2]) : 0) }));
				}
				else
					ws.send(JSON.stringify({type: 'msg', msg: input.value.trim(), lang: lang}));
				
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
						addLine('info', 'Un ' + msg.params.name + ' sauvage apparaît !', (new Date), 'log');
						addUser(msg.userid, msg.params);
					break;
					
					case 'disconnect':
						addLine('info', 'Le ' + users[msg.userid].name + " sauvage s'enfuit !", (new Date), 'log part');
						delUser(msg.userid);
					break;
					
					case 'attack':
						switch(msg['event']) {
							case 'attack':
								addLine('info', users[msg.attacker_id].name + ' attaque ' + users[msg.defender_id].name + ' !', msg.date, 'log');
							break;
							case 'dice':
								addLine('info', users[msg.attacker_id].name + ' tire un ' + msg.attacker_dice + ' + ('+ msg.attacker_bonus + '), ' + users[msg.defender_id].name + ' tire un ' + msg.defender_dice + ' + (' + msg.defender_bonus + ') !', msg.date, 'log');
							break;
							case 'effect':
								addLine('info', users[msg.target_id].name + " est maintenant affecté par l'effet " + msg.effect + ' !', msg.date, 'log');
								if(msg.target_id == you)
								{
									var d = new Date(msg.date);
									d.setSeconds(d.getSeconds() + msg.timeout);
									setTimeout(function() { addLine('info', "L'effet " + msg.effect + ' est terminé.', d, 'log part'); }, msg.timeout * 1000);
								}
							break;
							case 'invalid':
								addLine('info', "Impossible d'attaquer pour le moment, ou pokémon invalide", msg.date, 'log part');
							break;
							case 'nothing':
								addLine('info', 'Il ne se passe rien...', msg.date, 'log part');
							break;
						}
					break;
					
					case 'userlist':
						for(var i = 0; i < msg.users.length; i++)
							addUser(msg.users[i].userid, msg.users[i].params);
					break;
					
					case 'backlog':
						for(var i = 0; i < msg.msgs.length; i++)
							addLine(msg.msgs[i].user, msg.msgs[i].msg, msg.msgs[i].date, 'backlog');
						addLine('info', 'Vous êtes connecté', (new Date), 'log');
					break;
					
					case 'msg':
						lastMuted = (muted.indexOf(msg.userid) != -1);
						if(!lastMuted)
							addLine(users[msg.userid], msg.msg, msg.date, null);
					break;
				}
			}
			else if(!lastMuted && audio) {
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
			for(var i in users)
				delUser(i);
			
			addLine('info', 'Déconnecté, réessai...', (new Date), 'log part');
			
			window.setTimeout(wsConnect, waitTime);
			waitTime = Math.min(waitTime * 2, 120000);
		};
	};
	
	wsConnect();
});
